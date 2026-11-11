"""
Smartblocks Post Image Generator
- Calls DALL-E 3 for background image
- Overlays post text using Pillow
- Saves final post-ready PNG to images/
"""

import os
import sys
import json
import requests
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OUTPUT_DIR = Path(__file__).parent.parent / "images"
OUTPUT_DIR.mkdir(exist_ok=True)

POSTS = [
    {
        "id": "post1",
        "headline": "He lost the deal.\nNot because it was bad.\nBecause his raise took 11 weeks.",
        "subtext": "Tokenized raises close in days, not quarters.",
        "dalle_prompt": "Professional architectural photography of a completed modern luxury apartment building, clean blue sky, sharp lines, real estate portfolio style, neutral tones, no text, no people, photorealistic, high-end corporate photography"
    },
    {
        "id": "post2",
        "headline": "The SEC just killed\nthe gray zone.",
        "subtext": "Here's what the January 2026 ruling actually means for developers.",
        "dalle_prompt": "Clean minimalist photo of a modern glass office tower in a financial district, daylight, navy blue and white tones, professional corporate real estate photography, no text, no people, crisp and sharp"
    },
    {
        "id": "post3",
        "headline": "I spent 12 years watching\ndeals die for dumb reasons.",
        "subtext": "So I built something to fix it.",
        "dalle_prompt": "Professional photography of a real estate developer reviewing architectural blueprints and a laptop on a clean modern desk, soft natural window light, muted warm neutrals, no text visible, photorealistic, high-end corporate style"
    },
    {
        "id": "post4",
        "headline": "Tokenization vs syndication.\nSame legal backbone.\nBetter infrastructure.",
        "subtext": "Here's what actually changes for developers.",
        "dalle_prompt": "Clean professional photo of a modern financial dashboard on a large monitor in a sleek office, showing charts and cap table data, dark navy background, subtle blue accent lighting, no readable text, corporate photography style"
    },
    {
        "id": "post5",
        "headline": '"I don\'t understand\nblockchain."',
        "subtext": "You don't need to. Here's why.",
        "dalle_prompt": "Overhead flat lay of architect tools — blueprints, ruler, pen, and a smartphone — on a clean white desk, professional product photography style, soft shadows, neutral tones, no text visible"
    },
]

def generate_background(prompt: str) -> Image.Image:
    resp = requests.post(
        "https://api.openai.com/v1/images/generations",
        headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
        json={"model": "dall-e-3", "prompt": prompt, "n": 1, "size": "1792x1024", "quality": "standard"}
    )
    resp.raise_for_status()
    url = resp.json()["data"][0]["url"]
    img_resp = requests.get(url)
    return Image.open(BytesIO(img_resp.content)).convert("RGBA")

def overlay_text(img: Image.Image, headline: str, subtext: str) -> Image.Image:
    img = img.convert("RGBA")
    W, H = img.size

    # Strong dark gradient covering bottom 55% for guaranteed contrast
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    for i in range(H):
        alpha = int(230 * max(0, (i - H * 0.3) / (H * 0.7)))
        draw_overlay.line([(0, i), (W, i)], fill=(10, 15, 30, alpha))
    img = Image.alpha_composite(img, overlay)

    # Navy accent bar at very bottom
    bar = Image.new("RGBA", (W, 70), (10, 25, 70, 255))
    img.paste(bar, (0, H - 70), bar)

    draw = ImageDraw.Draw(img)

    try:
        font_headline = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 68)
        font_sub = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 38)
        font_brand = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
    except:
        font_headline = ImageFont.load_default()
        font_sub = font_headline
        font_brand = font_headline

    margin = 80
    headline_lines = headline.split("\n")
    total_headline_h = len(headline_lines) * 82
    subtext_lines = textwrap.wrap(subtext, width=58)
    total_sub_h = len(subtext_lines) * 50
    total_h = total_headline_h + 20 + total_sub_h
    y = H - 100 - total_h

    # Text shadow pass
    shadow_offset = 3
    for line in headline_lines:
        draw.text((margin + shadow_offset, y + shadow_offset), line, font=font_headline, fill=(0, 0, 0, 180))
        y += 82
    y = H - 100 - total_h

    # Headline white
    for line in headline_lines:
        draw.text((margin, y), line, font=font_headline, fill=(255, 255, 255, 255))
        y += 82

    y += 20

    # Accent line
    draw.rectangle([(margin, y), (margin + 60, y + 4)], fill=(80, 140, 255, 255))
    y += 20

    # Subtext — solid white, heavier weight
    for line in subtext_lines:
        draw.text((margin + shadow_offset, y + shadow_offset), line, font=font_sub, fill=(0, 0, 0, 140))
        draw.text((margin, y), line, font=font_sub, fill=(220, 230, 255, 255))
        y += 50

    # Brand in bottom bar
    brand = "SMARTBLOCKS"
    bbox = draw.textbbox((0, 0), brand, font=font_brand)
    bw = bbox[2] - bbox[0]
    bh = bbox[3] - bbox[1]
    draw.text((W - bw - margin, H - 35 - bh // 2), brand, font=font_brand, fill=(255, 255, 255, 230))

    return img.convert("RGB")

def main():
    posts_to_run = sys.argv[1:] if len(sys.argv) > 1 else [p["id"] for p in POSTS]

    for post in POSTS:
        if post["id"] not in posts_to_run:
            continue
        print(f"Generating {post['id']}...")
        try:
            bg = generate_background(post["dalle_prompt"])
            final = overlay_text(bg, post["headline"], post["subtext"])
            out_path = OUTPUT_DIR / f"{post['id']}.png"
            final.save(out_path)
            print(f"  Saved: {out_path}")
        except Exception as e:
            print(f"  ERROR on {post['id']}: {e}")

if __name__ == "__main__":
    main()
