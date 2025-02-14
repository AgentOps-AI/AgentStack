"""Vision tool for analyzing images using OpenAI's Vision API and Claude."""

import base64
from typing import Optional, Literal
import requests
from openai import OpenAI
import anthropic

__all__ = ["analyze_image"]


def analyze_image(image_path_url: str, model: Literal["openai", "claude"] = "openai") -> str:
    """
    Analyze an image using either OpenAI's Vision API or Claude.

    Args:
        image_path_url: Local path or URL to the image
        model: Which model to use ("openai" or "claude"). Defaults to "openai"

    Returns:
        str: Description of the image contents
    """
    if not image_path_url:
        return "Image Path or URL is required."

    if model == "openai":
        client = OpenAI()
        if "http" in image_path_url:
            return _analyze_web_image_openai(client, image_path_url)
        return _analyze_local_image_openai(client, image_path_url)
    elif model == "claude":
        client = Anthropic()
        if "http" in image_path_url:
            return _analyze_web_image_claude(client, image_path_url)
        return _analyze_local_image_claude(client, image_path_url)
    else:
        raise ValueError("Model must be either 'openai' or 'claude'")


def _analyze_web_image_openai(client: OpenAI, image_url: str) -> str:
    """Analyze a web-hosted image using OpenAI's Vision API."""
    try:
        response = client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "What's in this image?"
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": image_url}
                    }
                ]
            }],
            max_tokens=300
        )
        return response.choices[0].message.content or "No description available"
    except Exception as e:
        return f"Error analyzing image: {str(e)}"


def _analyze_local_image_openai(client: OpenAI, image_path: str) -> str:
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


def _analyze_web_image_claude(client: Anthropic, image_path_url: str) -> str:
    response = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=300,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": "What's in this image?"},
                {"type": "image", "source": {"type": "url", "url": image_path_url}}
            ]
        }]
    )
    return response.content[0].text


def _analyze_local_image_claude(client: Anthropic, image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        media_data = image_file.read()
    
    response = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=300,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": "What's in this image?"},
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": base64.b64encode(media_data).decode()
                    }
                }
            ]
        }]
    )
    return response.content[0].text


def _encode_image(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")