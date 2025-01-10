"""Vision tool for analyzing images using OpenAI's Vision API."""

import base64
from typing import Optional
import requests
from openai import OpenAI

__all__ = ["analyze_image"]


def analyze_image(image_path_url: str) -> str:
    """
    Analyze an image using OpenAI's Vision API.

    Args:
        image_path_url: Local path or URL to the image

    Returns:
        str: Description of the image contents
    """
    client = OpenAI()

    if not image_path_url:
        return "Image Path or URL is required."

    if "http" in image_path_url:
        return _analyze_web_image(client, image_path_url)
    return _analyze_local_image(client, image_path_url)


def _analyze_web_image(client: OpenAI, image_path_url: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What's in this image?"},
                    {"type": "image_url", "image_url": {"url": image_path_url}},
                ],
            }
        ],
        max_tokens=300,
    )
    return response.choices[0].message.content  # type: ignore[return-value]


def _analyze_local_image(client: OpenAI, image_path: str) -> str:
    base64_image = _encode_image(image_path)
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {client.api_key}"}
    payload = {
        "model": "gpt-4-vision-preview",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What's in this image?"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                ],
            }
        ],
        "max_tokens": 300,
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    return response.json()["choices"][0]["message"]["content"]


def _encode_image(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")
