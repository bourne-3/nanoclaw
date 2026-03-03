#!/usr/bin/env python3
"""
Image Description Tool for NanoClaw
Uses 360.cn Vision API to describe images in detail.

Usage:
  describe-images [--model MODEL] [--max-images N] [image_base64...]

Environment:
  VISION_API_KEY - API key for 360.cn Vision API

Models:
  gpt-4o-mini (default) - Fast, cost-effective
  gemini - Google's Gemini vision model
"""

import base64
import json
import os
import sys
import concurrent.futures
from typing import List, Dict, Any, Optional

import requests

API_ENDPOINT = "https://api.360.cn/v1/chat/completions"


def get_api_key() -> str:
    """Get API key from environment or fail."""
    api_key = os.environ.get("VISION_API_KEY")
    if not api_key:
        raise ValueError("VISION_API_KEY environment variable not set")
    return api_key


def describe_single_image(
    base64_data: str,
    model: str,
    api_key: str,
    image_index: int,
) -> Dict[str, Any]:
    """
    Describe a single image using the Vision API.

    Args:
        base64_data: Base64-encoded image data
        model: Model to use (gpt-4o-mini or gemini)
        api_key: API key for authentication
        image_index: Index of the image for logging

    Returns:
        Dict with description and metadata
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
   }

    # Build the prompt for detailed image description
    prompt = """请用中文详细描述这张照片。尝试识别和描述：
1. 场景：这是在哪里拍摄的？室内还是室外？
2. 主要物体：照片中最重要的物体或元素是什么？
3. 人物（如果有）：年龄、表情、动作、服装特点
4. 情绪：这张照片传达出什么情绪？
5. 光线：光线条件如何？自然光还是人工光？
6. 颜色：主要颜色有哪些？色调是暖还是冷？
7. 文字内容：照片中是否有文字？如果有，写的是什么？
8. 构图：主体在哪里？是否使用了三分法、对称或其他构图技巧？

请以JSON格式输出，包含以下字段：
- "场景": 简短描述
- "主要物体": 物体列表
- "人物特征": 人物描述（如果有）
- "情绪": 情绪描述
- "光线": 光线描述
- "颜色": 颜色描述
- "文字内容": 照片中的文字（如果有）
- "构图": 构图分析
- "详细描述": 200字左右的详细描述"""

    # Build request payload
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
                            "url": f"data:image/jpeg;base64,{base64_data}"
                        },
                    },
                ],
            }
        ],
        "max_tokens": 1000,
        "temperature": 0.7,
    }

    try:
        response = requests.post(
            API_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=60,
        )

        if response.status_code == 401:
            return {
                "error": "API key无效或已过期，请检查VISION_API_KEY配置",
                "image_index": image_index,
            }

        response.raise_for_status()

        result = response.json()
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")

        # Try to parse JSON from the response
        try:
            # Find JSON in the response (may be wrapped in markdown)
            import re
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                description = json.loads(json_match.group())
            else:
                description = {"详细描述": content}
        except json.JSONDecodeError:
            # If JSON parsing fails, use the raw content
            description = {"详细描述": content}

        return {
            "description": description,
            "raw_response": content,
            "image_index": image_index,
        }

    except requests.exceptions.Timeout:
        return {
            "error": f"图片 {image_index + 1} 描述超时，请稍后重试",
            "image_index": image_index,
        }
    except requests.exceptions.RequestException as e:
        return {
            "error": f"图片 {image_index + 1} 描述失败: {str(e)}",
            "image_index": image_index,
        }


def format_markdown_output(results: List[Dict[str, Any]]) -> str:
    """
    Format the description results as beautiful Markdown.

    Args:
        results: List of description results

    Returns:
        Formatted Markdown string
    """
    output_lines = []

    # Filter out errors
    successful = [r for r in results if "error" not in r]
    errors = [r for r in results if "error" in r]

    for i, result in enumerate(successful):
        desc = result.get("description", {})
        idx = result.get("image_index", i)

        output_lines.append(f"## 📷 图片 {idx + 1}")
        output_lines.append("")

        # Detailed description
        detailed = desc.get("详细描述", "")
        if detailed:
            output_lines.append(detailed)
            output_lines.append("")

        # Key points as bullet list
        output_lines.append("### 关键信息")
        output_lines.append("")

        # Extract key info
        key_points = []

        scene = desc.get("场景")
        if scene:
            key_points.append(f"**场景**: {scene}")

        main_objects = desc.get("主要物体")
        if main_objects:
            if isinstance(main_objects, list):
                main_objects = ", ".join(main_objects)
            key_points.append(f"**主要物体**: {main_objects}")

        people = desc.get("人物特征")
        if people:
            key_points.append(f"**人物**: {people}")

        mood = desc.get("情绪")
        if mood:
            key_points.append(f"**情绪**: {mood}")

        lighting = desc.get("光线")
        if lighting:
            key_points.append(f"**光线**: {lighting}")

        colors = desc.get("颜色")
        if colors:
            key_points.append(f"**颜色**: {colors}")

        text_content = desc.get("文字内容")
        if text_content:
            key_points.append(f"**文字内容**: {text_content}")

        composition = desc.get("构图")
        if composition:
            key_points.append(f"**构图**: {composition}")

        for point in key_points:
            output_lines.append(f"- {point}")

        output_lines.append("")
        output_lines.append("---")
        output_lines.append("")

    # Add errors at the end if any
    if errors:
        output_lines.append("## ⚠️ 错误")
        output_lines.append("")
        for err in errors:
            output_lines.append(f"- {err['error']}")
        output_lines.append("")

    return "\n".join(output_lines)


def main():
    """Main entry point for the image description tool."""
    args = sys.argv[1:]

    if not args or "--help" in args or "-h" in args:
        print(__doc__)
        sys.exit(0)

    # Parse arguments
    model = "gpt-4o-mini"  # Default model
    base64_images = []

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--model" and i + 1 < len(args):
            model = args[i + 1]
            i += 2
        elif arg == "--max-images" and i + 1 < len(args):
            # Skip, we handle max images internally
            i += 2
        elif arg.startswith("-"):
            i += 1  # Skip unknown flags
        else:
            # Assume it's a base64 string
            base64_images.append(arg)
            i += 1

    # Limit to 3 images
    base64_images = base64_images[:3]

    if not base64_images:
        print("Error: No images provided", file=sys.stderr)
        print(__doc__, file=sys.stderr)
        sys.exit(1)

    # Validate model
    valid_models = ["gpt-4o-mini", "gpt-4o", "gemini"]
    if model not in valid_models:
        print(f"Warning: Unknown model '{model}', using gpt-4o-mini", file=sys.stderr)
        model = "gpt-4o-mini"

    try:
        api_key = get_api_key()
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Process images concurrently (max 3 at a time)
    results = []

    # Use ThreadPoolExecutor for concurrent API calls
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(
                describe_single_image,
                img_data,
                model,
                api_key,
                idx,
            )
            for idx, img_data in enumerate(base64_images)
        ]

        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                results.append({"error": str(e)})

    # Sort results by image index
    results.sort(key=lambda x: x.get("image_index", 0))

    # Format and output
    output = format_markdown_output(results)
    print(output)


if __name__ == "__main__":
    main()
