import json
import os
import base64
import asyncio
from typing import Optional

from groq import AsyncGroq

_client = None

TEXT_MODEL = "llama-3.3-70b-versatile"
VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

MAX_RETRIES = 3
BASE_DELAY = 2


def _get_client():
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY", "")
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Get a free key at https://console.groq.com/keys"
            )
        _client = AsyncGroq(api_key=api_key)
    return _client


async def _chat(messages: list[dict], use_vision: bool = False) -> str:
    """Send a chat completion with exponential-backoff retry on rate limits."""
    client = _get_client()
    model = VISION_MODEL if use_vision else TEXT_MODEL

    for attempt in range(MAX_RETRIES):
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=4096,
            )
            return response.choices[0].message.content
        except Exception as e:
            err = str(e).lower()
            is_rate_limit = "rate_limit" in err or "429" in str(e)
            if is_rate_limit and attempt < MAX_RETRIES - 1:
                delay = BASE_DELAY * (2 ** attempt)
                await asyncio.sleep(delay)
                continue
            raise


ANALYSIS_PROMPT = """You are an expert Instagram content strategist.
Analyze the following Instagram post and return a JSON object with these fields:

- "content_category": one of ["lifestyle", "fashion", "food", "travel", "fitness", "tech", "beauty", "art", "business", "education", "entertainment", "nature", "pets", "sports", "music", "photography", "other"]
- "themes": list of 3-5 specific content themes detected (e.g. "minimalist interior", "vegan recipe", "street photography")
- "visual_elements": list of key visual elements detected in the image (e.g. "sunset", "coffee cup", "urban skyline"). Empty list if no image.
- "target_audience": short description of who this content appeals to
- "mood": one of ["inspiring", "informative", "entertaining", "emotional", "casual", "professional", "humorous", "aesthetic"]
- "niche_keywords": list of 8-12 niche-specific keywords relevant to this content (single words or short phrases, NOT hashtags)
- "engagement_potential": one of ["low", "medium", "high", "viral"] with a brief reason

Only output valid JSON, no markdown fences or extra text.

POST CAPTION:
{caption}

POST TYPE: {post_type}
EXISTING HASHTAGS: {existing_hashtags}
"""


HASHTAG_PROMPT = """You are an expert Instagram hashtag strategist in 2026.
Instagram's late-2025 algorithm update prioritizes quality over quantity. Use 3-5 highly targeted hashtags per set.

Based on the content analysis below, generate three sets of Instagram hashtags:

1. "maximum_reach" - 5 hashtags mixing trending/broad tags (100K-5M posts range) that maximize discoverability
2. "niche_targeted" - 5 hashtags that are niche-specific (10K-500K posts range) for high engagement
3. "low_competition" - 5 hashtags with lower competition (1K-50K posts range) ideal for growth

Also provide:
- "recommended_set": the single best set of 3-5 hashtags to use (picked and mixed from all three sets above)
- "avoid_hashtags": list of 3-5 hashtags to AVOID (banned, shadowban-risk, or overly saturated)

Rules:
- All hashtags must start with #
- Be specific to the content — no generic filler
- Consider the current day ({day_of_week}) for any day-specific trending tags
- Factor in the post type ({post_type}) for format-specific tags

CONTENT ANALYSIS:
{analysis_json}

ORIGINAL CAPTION:
{caption}

Return valid JSON only, no markdown fences.
"""


BOOST_PROMPT = """You are an expert Instagram growth strategist in 2026.
Based on the content analysis and post details below, provide an organic boost strategy.

Return a JSON object with:
- "best_posting_times": list of 3 optimal posting windows for {day_of_week} (e.g. "11:00 AM - 1:00 PM EST")
- "caption_rewrite": a rewritten/improved version of the caption that's more engaging (keep the same tone, add a hook and CTA)
- "first_comment": suggested first comment to post immediately after publishing (question or engagement hook)
- "engagement_hooks": list of 3 engagement strategies specific to this content
- "content_tips": list of 3 tips to improve this specific post's performance
- "reel_suggestion": if this is a photo post, a brief suggestion for turning it into a Reel. null if already a video/reel.
- "follow_up_ideas": list of 3 related content ideas for follow-up posts to maintain momentum
- "community_actions": list of 3 specific actions to take in the niche community (e.g. "engage with 10 posts under #specifichashtag before posting")

CONTENT ANALYSIS:
{analysis_json}

ORIGINAL CAPTION:
{caption}

POST TYPE: {post_type}

Return valid JSON only, no markdown fences.
"""


def _parse_json_response(text: str) -> dict | None:
    text = text.strip()
    text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


async def analyze_content(
    caption: str,
    post_type: str = "photo",
    existing_hashtags: list[str] | None = None,
    image_bytes: Optional[bytes] = None,
) -> dict:
    """Analyze post content using Groq (text + optional vision)."""
    tags_str = ", ".join(existing_hashtags) if existing_hashtags else "none"

    prompt_text = ANALYSIS_PROMPT.format(
        caption=caption or "(no caption)",
        post_type=post_type,
        existing_hashtags=tags_str,
    )

    if image_bytes:
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt_text},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                },
            ],
        }]
        text = await _chat(messages, use_vision=True)
    else:
        messages = [{"role": "user", "content": prompt_text}]
        text = await _chat(messages)

    parsed = _parse_json_response(text)

    if parsed:
        return parsed

    return {
        "content_category": "other",
        "themes": [],
        "visual_elements": [],
        "target_audience": "general audience",
        "mood": "casual",
        "niche_keywords": [],
        "engagement_potential": "medium",
        "raw_response": text,
    }


async def generate_hashtags(
    analysis: dict,
    caption: str,
    post_type: str,
    day_of_week: str,
) -> dict:
    """Generate optimized hashtag sets using Groq."""
    prompt = HASHTAG_PROMPT.format(
        analysis_json=json.dumps(analysis, indent=2),
        caption=caption or "(no caption)",
        post_type=post_type,
        day_of_week=day_of_week,
    )

    messages = [{"role": "user", "content": prompt}]
    text = await _chat(messages)
    parsed = _parse_json_response(text)
    return parsed or {"error": "Failed to parse hashtag response", "raw": text}


async def generate_boost_strategy(
    analysis: dict,
    caption: str,
    post_type: str,
    day_of_week: str,
) -> dict:
    """Generate organic boost strategy using Groq."""
    prompt = BOOST_PROMPT.format(
        analysis_json=json.dumps(analysis, indent=2),
        caption=caption or "(no caption)",
        post_type=post_type,
        day_of_week=day_of_week,
    )

    messages = [{"role": "user", "content": prompt}]
    text = await _chat(messages)
    parsed = _parse_json_response(text)
    return parsed or {"error": "Failed to parse boost strategy", "raw": text}
