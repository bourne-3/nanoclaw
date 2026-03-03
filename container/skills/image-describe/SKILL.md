---
name: image-describe
description: Describe images in detail using AI vision models. Supports multiple images (max 3), model selection (gpt-4o-mini, gemini), and outputs beautiful Markdown with structured information.
allowed-tools: Bash(image-describe:*)
---

# Image Description with image-describe

Use this skill when user wants to describe, analyze, or understand images. Triggered by phrases like:
- "描述照片" / "描述图片"
- "describe photo" / "describe image"
- "看照片" / "看图片"
- "分析图片" / "分析照片"
- Or when user sends images with text like "这是什么?"

## Quick Start

```bash
# Describe images (pass base64 directly)
image-describe <base64_image_data>

# Use specific model
image-describe --model gemini <base64_image_data>

# Multiple images (max 3)
image-describe <img1_base64> <img2_base64> <img3_base64>
```

## Usage Pattern

When user sends images with description request:
1. Extract base64 from the `<image>` tags in the message XML
2. Call `image-describe` with the base64 data
3. Return the formatted Markdown output

## Image Data Format

Images are passed as base64 strings in the message:
```
<image filename="photo.jpg" mimeType="image/jpeg">BASE64_DATA_HERE</image>
```

Extract the BASE64_DATA_HERE and pass to image-describe.

## Models

| Model | Description |
|-------|-------------|
| `gpt-4o-mini` | Default, fast and cost-effective |
| `gemini` | Google's Gemini vision model |
| `gpt-4o` | OpenAI's GPT-4o (full version) |

Specify model with `--model` flag:
```bash
image-describe --model gemini <base64>
```

## Output Format

The tool outputs beautiful Markdown with:
- Detailed description in Chinese
- Key information as bullet points
- Scene, objects, people, mood, lighting, colors, text content, composition

## Examples

### Single Image
```bash
image-describe iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==
```

### Multiple Images
```bash
image-describe iVBORw0KGgo... iVBORw0KGgo... iVBORw0KGgo...
```

### Different Model
```bash
image-describe --model gemini iVBORw0KGgo...
```

## Error Handling

If API key is invalid or expired, the tool will output a friendly error message asking user to check VISION_API_KEY configuration.
