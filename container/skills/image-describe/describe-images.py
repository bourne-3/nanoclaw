#!/usr/bin/env python3
"""
Image Description Tool for NanoClaw
Uses 360.cn Vision API to describe images in detail.

Usage:
  describe-images [--model MODEL] <image_path>

Environment:
  VISION_API_KEY - API key for 360.cn Vision API

Models:
  gpt-4o-mini (default) - Fast, cost-effective
  gemini - Google's Gemini vision model
"""

import base64
import json
import mimetypes
import os
import re
import sys
from typing import Dict, Any

import requests

API_ENDPOINT = "https://api.360.cn/v1/chat/completions"


def get_api_key() -> str:
    """Get API key from environment or fail."""
    api_key = os.environ.get("VISION_API_KEY")
    if not api_key:
        raise ValueError("VISION_API_KEY environment variable not set")
    return api_key


def image_path_to_base64(image_path: str) -> tuple[str, str]:
    """
    Read an image file and return (base64_data, mime_type).

    Args:
        image_path: Absolute or relative path to the image file

    Returns:
        Tuple of (base64_encoded_string, mime_type)

    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If the file is not a supported image type
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"图片文件不存在: {image_path}")

    mime_type, _ = mimetypes.guess_type(image_path)
    if not mime_type or not mime_type.startswith("image/"):
        ext = os.path.splitext(image_path)[1].lower()
        ext_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".bmp": "image/bmp",
        }
        mime_type = ext_map.get(ext)
        if not mime_type:
            raise ValueError(f"不支持的图片格式: {image_path}")

    with open(image_path, "rb") as f:
        base64_data = base64.b64encode(f.read()).decode("utf-8")

    return base64_data, mime_type


def describe_image(image_path: str, model: str, api_key: str) -> Dict[str, Any]:
    """
    Describe an image using the Vision API.

    Args:
        image_path: Path to the image file
        model: Model to use (gpt-4o-mini or gemini)
        api_key: API key for authentication

    Returns:
        Dict with description and metadata
    """
    try:
        base64_data, mime_type = image_path_to_base64(image_path)
    except (FileNotFoundError, ValueError) as e:
        return {"error": str(e)}

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    prompt = """请用中文分析这张图片，提取所有有价值的信息。

分析要点：
1. 图片类型：判断这是什么类型的图片（如：照片、发票、收据、病历、报告、截图、证件、表格、图表等）
2. 主要内容：图片中包含哪些核心内容或元素
3. 文字信息：完整提取图片中所有可见文字（金额、日期、姓名、编号等关键数据需单独列出）
4. 结构信息：如果是文档类图片，描述其结构和布局
5. 详细描述：对图片内容做完整、客观的描述

请以JSON格式输出，包含以下字段：
- "图片类型": 图片的类型或用途
- "主要内容": 核心内容概述
- "文字信息": 图片中提取的所有关键文字和数据
- "结构信息": 文档结构或布局描述（非文档类图片可省略）
- "详细描述": 对图片内容的完整描述"""

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{base64_data}"
                        },
                    },
                ],
            }
        ],
        "max_tokens": 1000,
        "temperature": 0.7,
    }

    try:
        response = requests.post(API_ENDPOINT, headers=headers, json=payload, timeout=60)

        if response.status_code == 401:
            return {"error": "API key无效或已过期，请检查VISION_API_KEY配置"}

        response.raise_for_status()

        content = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")

        try:
            json_match = re.search(r'\{[\s\S]*\}', content)
            description = json.loads(json_match.group()) if json_match else {"详细描述": content}
        except json.JSONDecodeError:
            description = {"详细描述": content}

        return {"description": description}

    except requests.exceptions.Timeout:
        return {"error": "请求超时，请稍后重试"}
    except requests.exceptions.RequestException as e:
        return {"error": f"请求失败: {str(e)}"}


def format_markdown_output(result: Dict[str, Any]) -> str:
    """Format the description result as Markdown."""
    if "error" in result:
        return f"## ⚠️ 错误\n\n{result['error']}\n"

    desc = result.get("description", {})
    lines = []

    detailed = desc.get("详细描述", "")
    if detailed:
        lines.append(detailed)
        lines.append("")

    lines.append("### 关键信息")
    lines.append("")

    key_fields = [
        ("图片类型", "图片类型"),
        ("主要内容", "主要内容"),
        ("文字信息", "文字信息"),
        ("结构信息", "结构信息"),
    ]

    for field_key, label in key_fields:
        value = desc.get(field_key)
        if value:
            if isinstance(value, list):
                value = ", ".join(value)
            lines.append(f"- **{label}**: {value}")

    return "\n".join(lines)


def main():
    """Main entry point for the image description tool."""
    args = sys.argv[1:]

    if not args or "--help" in args or "-h" in args:
        print(__doc__)
        sys.exit(0)

    model = "gpt-4o-mini"
    image_path = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--model" and i + 1 < len(args):
            model = args[i + 1]
            i += 2
        elif arg.startswith("-"):
            i += 1
        else:
            image_path = arg
            i += 1

    if not image_path:
        print("Error: No image path provided", file=sys.stderr)
        print(__doc__, file=sys.stderr)
        sys.exit(1)

    valid_models = ["gpt-4o-mini", "gpt-4o", "gemini"]
    if model not in valid_models:
        print(f"Warning: Unknown model '{model}', using gpt-4o-mini", file=sys.stderr)
        model = "gpt-4o-mini"

    try:
        api_key = get_api_key()
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    result = describe_image(image_path, model, api_key)
    print(format_markdown_output(result))


if __name__ == "__main__":
    main()
