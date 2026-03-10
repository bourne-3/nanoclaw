---
name: image-describe
description: Describe an image in detail using AI vision models. Supports model selection (gpt-4o-mini, gemini), and outputs beautiful Markdown with structured information.
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
# Describe an image by file path
image-describe /path/to/photo.jpg

# Use specific model
image-describe --model gemini /path/to/photo.jpg
```

## Usage Pattern

When user sends an image with description request:
1. Save the image attachment to a temp path (e.g. `/tmp/photo.jpg`)
2. Call `image-describe` with the file path
3. Return the formatted Markdown output

## Supported Image Formats

| Extension | MIME Type |
|-----------|-----------|
| `.jpg` / `.jpeg` | `image/jpeg` |
| `.png` | `image/png` |
| `.gif` | `image/gif` |
| `.webp` | `image/webp` |
| `.bmp` | `image/bmp` |

The tool reads the file, detects the MIME type automatically, and converts to base64 internally before calling the API.

## Models

| Model | Description |
|-------|-------------|
| `gpt-4o-mini` | Default, fast and cost-effective |
| `gemini` | Google's Gemini vision model |
| `gpt-4o` | OpenAI's GPT-4o (full version) |

Specify model with `--model` flag:
```bash
image-describe --model gemini /path/to/photo.jpg
```

## Output Format

The tool outputs beautiful Markdown with:
- Detailed description in Chinese
- Key information as bullet points
- Scene, objects, people, mood, lighting, colors, text content, composition

## Examples

### Single Image
```bash
image-describe /tmp/photo.jpg
```

### Different Model
```bash
image-describe --model gemini /tmp/photo.jpg
```

## Error Handling

- **File not found**: Returns a friendly error if the path does not exist
- **Unsupported format**: Returns an error listing supported extensions
- **API key invalid**: Outputs a message asking user to check VISION_API_KEY configuration
