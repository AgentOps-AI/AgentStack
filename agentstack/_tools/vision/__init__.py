from typing import IO, Optional
import os
from pathlib import Path
import base64
import tempfile
import requests
import anthropic

__all__ = ["analyze_image"]

PROMPT = os.getenv('VISION_PROMPT', "What's in this image?")
MODEL = os.getenv('VISION_MODEL', "claude-3-5-sonnet-20241022")
MAX_TOKENS: int = int(os.getenv('VISION_MAX_TOKENS', 1024))

MEDIA_TYPES = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "gif": "image/gif",
    "webp": "image/webp",
}
ALLOWED_MEDIA_TYPES = list(MEDIA_TYPES.keys())

# image sizes that will not be resized
# TODO is there any value in resizing pre-upload?
# 1:1	1092x1092 px
# 3:4	951x1268 px
# 2:3	896x1344 px
# 9:16	819x1456 px
# 1:2	784x1568 px


def _get_media_type(image_filename: str) -> Optional[str]:
    """Get the media type from an image filename."""
    for ext, media_type in MEDIA_TYPES.items():
        if image_filename.endswith(ext):
            return media_type
    return None


def _encode_image(image_handle: IO) -> str:
    """Encode a file handle to base64."""
    return base64.b64encode(image_handle.read()).decode("utf-8")


def _make_anthropic_request(image_handle: IO, media_type: str) -> anthropic.types.Message:
    """Make a request to the Anthropic API using an image."""
    client = anthropic.Anthropic()
    data = _encode_image(image_handle)
    return client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=[
            {
                "role": "user",
                "content": [
                    {  # type: ignore
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": data,
                        },
                    },
                    {  # type: ignore
                        "type": "text",
                        "text": PROMPT,
                    },
                ],
            }
        ],
    )


def _analyze_web_image(image_url: str, media_type: str) -> str:
    """Analyze an image from a URL."""
    with tempfile.NamedTemporaryFile() as temp_file:
        temp_file.write(requests.get(image_url).content)
        temp_file.flush()
        temp_file.seek(0)
        response = _make_anthropic_request(temp_file, media_type)
        return response.content[0].text  # type: ignore


def _analyze_local_image(image_path: str, media_type: str) -> str:
    """Analyze an image from a local file."""
    with open(image_path, "rb") as image_file:
        response = _make_anthropic_request(image_file, media_type)
        return response.content[0].text  # type: ignore


def analyze_image(image_path_or_url: str) -> str:
    """
    Analyze an image using OpenAI's Vision API.

    Args:
        image_path_or_url: Local path or URL to the image.

    Returns:
        str: Description of the image contents
    """
    if not image_path_or_url:
        return "Image Path or URL is required."

    media_type = _get_media_type(image_path_or_url)
    if not media_type:
        return f"Unsupported image type use {ALLOWED_MEDIA_TYPES}."

    if "http" in image_path_or_url:
        return _analyze_web_image(image_path_or_url, media_type)
    return _analyze_local_image(image_path_or_url, media_type)
