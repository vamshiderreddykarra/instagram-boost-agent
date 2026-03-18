from datetime import datetime
from typing import Optional

from .ai_engine import generate_boost_strategy


async def get_boost_plan(
    analysis: dict,
    caption: str,
    post_type: str = "photo",
    day_of_week: Optional[str] = None,
) -> dict:
    """Generate a complete organic boost plan for the post."""
    if day_of_week is None:
        day_of_week = datetime.now().strftime("%A")

    strategy = await generate_boost_strategy(
        analysis=analysis,
        caption=caption,
        post_type=post_type,
        day_of_week=day_of_week,
    )

    strategy["day_of_week"] = day_of_week
    strategy["post_type"] = post_type

    return strategy
