import re
import io
import httpx
import instaloader
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PostData:
    caption: str = ""
    hashtags: list[str] = field(default_factory=list)
    image_url: str = ""
    image_bytes: Optional[bytes] = None
    likes: int = 0
    comments: int = 0
    post_type: str = "photo"
    username: str = ""
    is_manual: bool = False


def extract_shortcode(url: str) -> Optional[str]:
    """Pull the shortcode out of an Instagram post/reel URL."""
    patterns = [
        r"instagram\.com/p/([A-Za-z0-9_-]+)",
        r"instagram\.com/reel/([A-Za-z0-9_-]+)",
        r"instagram\.com/tv/([A-Za-z0-9_-]+)",
    ]
    for pat in patterns:
        m = re.search(pat, url)
        if m:
            return m.group(1)
    return None


def is_instagram_url(text: str) -> bool:
    return "instagram.com/" in text


def is_username(text: str) -> bool:
    return bool(re.match(r"^@?[A-Za-z0-9._]{1,30}$", text))


async def fetch_post_data(url: str) -> PostData:
    """Fetch post data from an Instagram URL using instaloader."""
    shortcode = extract_shortcode(url)
    if not shortcode:
        raise ValueError("Could not extract post shortcode from URL")

    loader = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        quiet=True,
    )

    try:
        post = instaloader.Post.from_shortcode(loader.context, shortcode)

        caption = post.caption or ""
        hashtags = list(post.caption_hashtags) if post.caption_hashtags else []

        post_type = "photo"
        if post.is_video:
            post_type = "reel" if post.video_view_count else "video"
        elif post.mediacount and post.mediacount > 1:
            post_type = "carousel"

        image_url = post.url
        image_bytes = None
        if image_url:
            try:
                async with httpx.AsyncClient(timeout=15) as client:
                    resp = await client.get(image_url)
                    if resp.status_code == 200:
                        image_bytes = resp.content
            except Exception:
                pass

        return PostData(
            caption=caption,
            hashtags=hashtags,
            image_url=image_url,
            image_bytes=image_bytes,
            likes=post.likes,
            comments=post.comments,
            post_type=post_type,
            username=post.owner_username,
        )
    except Exception as e:
        raise RuntimeError(f"Failed to fetch post data: {e}")


async def fetch_profile_latest(username: str) -> PostData:
    """Fetch the latest post from a public profile."""
    username = username.lstrip("@")

    loader = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        quiet=True,
    )

    try:
        profile = instaloader.Profile.from_username(loader.context, username)
        posts = profile.get_posts()
        post = next(iter(posts))

        caption = post.caption or ""
        hashtags = list(post.caption_hashtags) if post.caption_hashtags else []

        post_type = "photo"
        if post.is_video:
            post_type = "reel" if post.video_view_count else "video"
        elif post.mediacount and post.mediacount > 1:
            post_type = "carousel"

        image_url = post.url
        image_bytes = None
        if image_url:
            try:
                async with httpx.AsyncClient(timeout=15) as client:
                    resp = await client.get(image_url)
                    if resp.status_code == 200:
                        image_bytes = resp.content
            except Exception:
                pass

        return PostData(
            caption=caption,
            hashtags=hashtags,
            image_url=image_url,
            image_bytes=image_bytes,
            likes=post.likes,
            comments=post.comments,
            post_type=post_type,
            username=username,
        )
    except Exception as e:
        raise RuntimeError(f"Failed to fetch profile data for @{username}: {e}")


def build_manual_post(caption: str, image_bytes: Optional[bytes] = None) -> PostData:
    """Build PostData from manual user input."""
    hashtags = re.findall(r"#(\w+)", caption)
    return PostData(
        caption=caption,
        hashtags=hashtags,
        image_bytes=image_bytes,
        is_manual=True,
    )
