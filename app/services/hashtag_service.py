import httpx
from typing import Optional
from datetime import datetime

from .ai_engine import analyze_content, generate_hashtags


AUTO_TAG_API = "https://api.aiautotagging.com/auto-tag"


async def get_image_tags(image_bytes: bytes) -> list[str]:
    """Get auto-generated tags from the AI Auto Tagging API (free, no key)."""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            files = {"file": ("image.jpg", image_bytes, "image/jpeg")}
            resp = await client.post(AUTO_TAG_API, files=files)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("tags", [])
    except Exception:
        pass
    return []


async def generate_optimized_hashtags(
    caption: str,
    post_type: str = "photo",
    existing_hashtags: Optional[list[str]] = None,
    image_bytes: Optional[bytes] = None,
    day_of_week: Optional[str] = None,
) -> dict:
    """
    Full pipeline: analyze content -> get image tags -> generate hashtags.
    Returns a dict with analysis, image_tags, and hashtag sets.
    """
    if day_of_week is None:
        day_of_week = datetime.now().strftime("%A")

    analysis = await analyze_content(
        caption=caption,
        post_type=post_type,
        existing_hashtags=existing_hashtags,
        image_bytes=image_bytes,
    )

    image_tags = []
    if image_bytes:
        image_tags = await get_image_tags(image_bytes)
        if image_tags:
            analysis["image_auto_tags"] = image_tags

    hashtags = await generate_hashtags(
        analysis=analysis,
        caption=caption,
        post_type=post_type,
        day_of_week=day_of_week,
    )

    return {
        "analysis": analysis,
        "image_tags": image_tags,
        "hashtags": hashtags,
        "day_of_week": day_of_week,
    }
