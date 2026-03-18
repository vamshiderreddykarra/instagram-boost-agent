import traceback
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

load_dotenv()

from .services.instagram import (
    PostData,
    fetch_post_data,
    fetch_profile_latest,
    build_manual_post,
    is_instagram_url,
    is_username,
)
from .services.hashtag_service import generate_optimized_hashtags
from .services.boost_strategy import get_boost_plan

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Instagram AI Boost Agent")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/analyze")
async def analyze(
    request: Request,
    query: str = Form(""),
    caption: str = Form(""),
    image: UploadFile | None = File(None),
):
    """
    Main analysis endpoint.
    Accepts either:
      - query: an Instagram post URL or @username
      - caption + optional image: manual fallback input
    """
    day_of_week = datetime.now().strftime("%A")
    post_data: PostData | None = None
    extraction_error: str | None = None

    query = query.strip()
    caption = caption.strip()

    if query:
        try:
            if is_instagram_url(query):
                post_data = await fetch_post_data(query)
            elif is_username(query):
                post_data = await fetch_profile_latest(query)
            else:
                return JSONResponse(
                    {"error": "Input must be an Instagram post URL or @username"},
                    status_code=400,
                )
        except Exception as e:
            extraction_error = str(e)

    if post_data is None and (caption or image):
        image_bytes = None
        if image and image.filename:
            image_bytes = await image.read()
        post_data = build_manual_post(caption, image_bytes)

    if post_data is None:
        msg = "Could not retrieve post data."
        if extraction_error:
            msg += f" ({extraction_error}) Please use manual input instead."
        return JSONResponse({"error": msg}, status_code=400)

    try:
        result = await generate_optimized_hashtags(
            caption=post_data.caption,
            post_type=post_data.post_type,
            existing_hashtags=post_data.hashtags or None,
            image_bytes=post_data.image_bytes,
            day_of_week=day_of_week,
        )
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(
            {"error": f"AI analysis failed: {e}"},
            status_code=500,
        )

    try:
        boost = await get_boost_plan(
            analysis=result["analysis"],
            caption=post_data.caption,
            post_type=post_data.post_type,
            day_of_week=day_of_week,
        )
    except Exception as e:
        traceback.print_exc()
        boost = {"error": f"Boost strategy generation failed: {e}"}

    return JSONResponse({
        "post": {
            "caption": post_data.caption,
            "username": post_data.username,
            "post_type": post_data.post_type,
            "likes": post_data.likes,
            "comments": post_data.comments,
            "existing_hashtags": post_data.hashtags,
            "image_url": post_data.image_url,
            "is_manual": post_data.is_manual,
        },
        "analysis": result["analysis"],
        "image_tags": result.get("image_tags", []),
        "hashtags": result["hashtags"],
        "boost_strategy": boost,
        "day_of_week": day_of_week,
        "extraction_warning": extraction_error,
    })
