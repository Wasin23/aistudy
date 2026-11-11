"""
Smartblocks Post Image Generator v3 — Scroll-Stop Edition
- Nano Banana 2 (Gemini 3.1 Flash Image) for backgrounds
- 9:16 vertical format (1080x1920) for Instagram/Reels/TikTok
- 5 completely different design templates — no corporate sameness
"""

import os
import sys
import base64
import requests
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from io import BytesIO

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-image-preview:generateContent?key={GEMINI_API_KEY}"

OUTPUT_DIR = Path(__file__).parent.parent / "images"
OUTPUT_DIR.mkdir(exist_ok=True)

W, H = 1080, 1920  # 9:16 vertical — Instagram/Reels/TikTok

POSTS = [
    {
        "id": "post1",
        "design": "split_grief",
        "headline": "He lost the deal.",
        "subline": "Not because it was bad.",
        "kicker": "Because his raise\ntook 11 weeks.",
        "cta": "Tokenized raises close in days,\nnot quarters.",
        "prompt": "Dramatic cinematic vertical portrait photo of an empty modern conference room, chairs pushed back in chaos, one chair knocked over, a deal term sheet left on the table, harsh overhead fluorescent lighting, dark and moody, photorealistic, no people, no text, 9:16 vertical"
    },
    {
        "id": "post2",
        "design": "tombstone",
        "headline": "R.I.P.",
        "subline": "THE GRAY ZONE",
        "kicker": "Jan 2026 – Jan 2026",
        "cta": "The SEC ruling just changed everything\nfor real estate developers.\nHere's what it actually means.",
        "prompt": "Dark dramatic vertical portrait photo of a lone gravestone in a foggy cemetery at dusk, moody cinematic lighting, deep charcoal and dark green tones, photorealistic, no text on gravestone, eerie but professional, 9:16 vertical"
    },
    {
        "id": "post3",
        "design": "split_screen",
        "left_label": "THEN",
        "left_text": ["Cold calls.", "90-day closes.", "Deals lost\nto slow money."],
        "right_label": "NOW",
        "right_text": ["Verified investors.", "72-hour raises.", "Deals done\non your timeline."],
        "cta": "12 years watching it break.\nBuilt to fix it.",
        "prompt": "Dramatic vertical portrait split image concept: top half dark and gritty old brick office building at night in rain, bottom half clean and bright modern glass tower in golden hour light, dramatic contrast, photorealistic, no text, 9:16 vertical"
    },
    {
        "id": "post4",
        "design": "scoreboard",
        "headline": "TOKENIZATION\nvs SYNDICATION",
        "rows": [
            ("Time to close",     "3-7 days",        "60-90 days"),
            ("Investor reach",    "Global + digital", "Local network"),
            ("Cap table",         "Automatic",        "Manual / lawyer"),
            ("Min. raise",        "Any size",         "$500K+"),
            ("Legal overhead",    "Low",              "High"),
        ],
        "cta": "Same legal backbone.\nBetter infrastructure.",
        "prompt": "Clean dark navy blue abstract textured background, subtle geometric diagonal lines, professional minimal, no text, no people, 9:16 vertical"
    },
    {
        "id": "post5",
        "design": "meme_two_panel",
        "top_text": 'DEVELOPER\nHEARING\n"BLOCKCHAIN"',
        "bottom_text": 'DEVELOPER\nHEARING\n"RAISE IN 72 HRS"',
        "top_reaction": "😰",
        "bottom_reaction": "🤑",
        "cta": "You don't need to understand blockchain.\nYou need deals to close.",
        "prompt": "Two contrasting vertical portrait scenes: top half shows stressed businessman at cluttered desk looking overwhelmed, dark moody tones; bottom half shows same businessman celebrating fist pump looking thrilled, bright tones — split scene, photorealistic, no text, 9:16 vertical"
    },
]

# ─── GEMINI ───────────────────────────────────────────────────────────────────

def generate_background(prompt: str) -> Image.Image:
    payload = {
        "contents": [{"parts": [{"text": f"Generate this exact image, photorealistic: {prompt}"}]}],
        "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]}
    }
    resp = requests.post(GEMINI_URL, headers={"Content-Type": "application/json"}, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    for part in data["candidates"][0]["content"]["parts"]:
        if "inlineData" in part:
            img_bytes = base64.b64decode(part["inlineData"]["data"])
            return Image.open(BytesIO(img_bytes)).convert("RGBA")
    raise ValueError("No image in Gemini response")

def load_fonts():
    bold = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    reg  = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    def tf(path, size):
        try: return ImageFont.truetype(path, size)
        except: return ImageFont.load_default()
    return {
        "xxl":  tf(bold, 120),
        "xl":   tf(bold, 96),
        "lg":   tf(bold, 72),
        "md":   tf(bold, 56),
        "sm":   tf(bold, 44),
        "xs":   tf(reg,  36),
        "xxs":  tf(reg,  28),
        "label":tf(bold, 52),
        "sh":   tf(bold, 38),
        "sr":   tf(reg,  34),
    }

def darken(img, factor=0.4):
    return ImageEnhance.Brightness(img).enhance(factor)

def brand_tag(draw, fonts):
    txt = "SMARTBLOCKS"
    bbox = draw.textbbox((0, 0), txt, font=fonts["xxs"])
    tw = bbox[2] - bbox[0]
    draw.text((W - tw - 40, H - 50), txt, font=fonts["xxs"], fill=(255, 255, 255, 160))

def shadow_text(draw, pos, text, font, fill=(255,255,255,255), offset=4):
    x, y = pos
    draw.text((x+offset, y+offset), text, font=font, fill=(0,0,0,200))
    draw.text((x, y), text, font=font, fill=fill)

def centered_text(draw, y, text, font, fill=(255,255,255,255), offset=4):
    for line in text.split("\n"):
        bbox = draw.textbbox((0,0), line, font=font)
        tw = bbox[2]-bbox[0]
        shadow_text(draw, (W//2 - tw//2, y), line, font, fill, offset)
        y += bbox[3]-bbox[1] + 16
    return y

# ─── DESIGN TEMPLATES ─────────────────────────────────────────────────────────

def design_split_grief(bg, post, fonts):
    img = bg.resize((W, H), Image.LANCZOS).convert("RGBA")
    img = darken(img, 0.30)

    # Heavy gradient bottom 60%
    ov = Image.new("RGBA", (W, H), (0,0,0,0))
    dv = ImageDraw.Draw(ov)
    for i in range(H):
        a = int(220 * max(0, (i - H*0.25) / (H*0.75)))
        dv.line([(0,i),(W,i)], fill=(5,8,20,a))
    img = Image.alpha_composite(img, ov)

    # Red top stripe
    stripe = Image.new("RGBA", (W, 12), (220,30,30,255))
    img.paste(stripe, (0,0), stripe)

    draw = ImageDraw.Draw(img)
    mx = 80

    # Big headline near top third
    y = int(H * 0.42)
    shadow_text(draw, (mx, y), post["headline"], fonts["xl"], (255,255,255,255))
    y += 115
    shadow_text(draw, (mx, y), post["subline"], fonts["md"], (200,200,200,220))
    y += 80

    # Red kicker — the gut punch
    for line in post["kicker"].split("\n"):
        shadow_text(draw, (mx, y), line, fonts["lg"], (255,80,80,255))
        y += 90

    y += 30
    # Accent line
    draw.rectangle([(mx, y), (mx+100, y+6)], fill=(220,30,30,255))
    y += 30

    # CTA
    for line in post["cta"].split("\n"):
        shadow_text(draw, (mx, y), line, fonts["xs"], (200,220,255,220))
        y += 50

    brand_tag(draw, fonts)
    return img.convert("RGB")


def design_tombstone(bg, post, fonts):
    img = bg.resize((W, H), Image.LANCZOS).convert("RGBA")
    img = darken(img, 0.25)

    ov = Image.new("RGBA", (W, H), (0,0,0,140))
    img = Image.alpha_composite(img, ov)

    draw = ImageDraw.Draw(img)
    cx = W // 2

    y = int(H * 0.18)
    y = centered_text(draw, y, "⚰️", fonts["xxl"], (255,255,255,255))
    y += 30
    y = centered_text(draw, y, post["headline"], fonts["xxl"], (255,255,255,255))
    y += 20

    # Tombstone divider
    draw.rectangle([(cx-220, y), (cx+220, y+5)], fill=(255,255,255,200))
    y += 30

    y = centered_text(draw, y, post["subline"], fonts["lg"], (255,255,255,255))
    y += 10
    y = centered_text(draw, y, post["kicker"], fonts["sm"], (180,180,180,220))

    # CTA bottom bar
    bar = Image.new("RGBA", (W, 200), (5,5,5,240))
    img.paste(bar, (0, H-200), bar)
    draw = ImageDraw.Draw(img)
    y = H - 185
    for line in post["cta"].split("\n"):
        bbox = draw.textbbox((0,0), line, font=fonts["xs"])
        tw = bbox[2]-bbox[0]
        draw.text((cx - tw//2, y), line, font=fonts["xs"], fill=(200,220,255,230))
        y += 50

    brand_tag(draw, fonts)
    return img.convert("RGB")


def design_split_screen(bg, post, fonts):
    img = bg.resize((W, H), Image.LANCZOS).convert("RGBA")

    # Top half = THEN (dark/gritty)
    top = img.crop((0, 0, W, H//2))
    top = darken(top, 0.22)
    img.paste(top, (0,0))

    # Bottom half = NOW (brighter)
    bot = img.crop((0, H//2, W, H))
    bot = darken(bot, 0.42)
    img.paste(bot, (0, H//2))

    # Center horizontal divider
    div = Image.new("RGBA", (W, 6), (255,255,255,200))
    img.paste(div, (0, H//2-3), div)

    draw = ImageDraw.Draw(img)
    mx = 70

    # THEN label box — top half
    draw.rectangle([(mx, 60), (mx+180, 120)], fill=(180,30,30,255))
    draw.text((mx+18, 68), post["left_label"], font=fonts["label"], fill=(255,255,255,255))

    y = 155
    for line_text in post["left_text"]:
        for line in line_text.split("\n"):
            shadow_text(draw, (mx, y), f"✗  {line}", fonts["sm"], (255,160,160,230))
            y += 65

    # NOW label box — bottom half
    draw.rectangle([(mx, H//2+50), (mx+170, H//2+110)], fill=(30,160,90,255))
    draw.text((mx+18, H//2+58), post["right_label"], font=fonts["label"], fill=(255,255,255,255))

    y = H//2 + 145
    for line_text in post["right_text"]:
        for line in line_text.split("\n"):
            shadow_text(draw, (mx, y), f"✓  {line}", fonts["sm"], (160,255,180,230))
            y += 65

    # CTA bottom
    bar = Image.new("RGBA", (W, 160), (5,5,5,230))
    img.paste(bar, (0, H-160), bar)
    draw = ImageDraw.Draw(img)
    cy = H - 148
    cx = W // 2
    for line in post["cta"].split("\n"):
        bbox = draw.textbbox((0,0), line, font=fonts["sm"])
        tw = bbox[2]-bbox[0]
        draw.text((cx - tw//2, cy), line, font=fonts["sm"], fill=(220,220,220,230))
        cy += 56

    brand_tag(draw, fonts)
    return img.convert("RGB")


def design_scoreboard(bg, post, fonts):
    # Programmatic background — navy + geometric lines
    img = Image.new("RGBA", (W, H), (8, 12, 28, 255))
    draw_bg = ImageDraw.Draw(img)
    for x in range(0, W, 90):
        draw_bg.line([(x,0),(x,H)], fill=(20,30,60,255), width=1)
    for y in range(0, H, 90):
        draw_bg.line([(0,y),(W,y)], fill=(20,30,60,255), width=1)
    for i in range(0, 900, 50):
        draw_bg.line([(W-i,0),(W,i)], fill=(25,50,110,255), width=1)

    draw = ImageDraw.Draw(img)
    cx = W // 2

    # Title
    y = 80
    for line in post["headline"].split("\n"):
        bbox = draw.textbbox((0,0), line, font=fonts["lg"])
        tw = bbox[2]-bbox[0]
        draw.text((cx - tw//2, y), line, font=fonts["lg"], fill=(255,255,255,255))
        y += 90

    y += 20
    draw.rectangle([(60, y), (W-60, y+4)], fill=(255,255,255,60))
    y += 30

    # Column headers
    c1, c2, c3 = 60, 460, 790
    draw.text((c2, y), "SMARTBLOCKS", font=fonts["sh"], fill=(80,220,130,255))
    draw.text((c3, y), "SYNDICATION", font=fonts["sh"], fill=(150,150,150,200))
    y += 60
    draw.rectangle([(60, y), (W-60, y+3)], fill=(255,255,255,40))
    y += 20

    for i, (label, good, bad) in enumerate(post["rows"]):
        if i % 2 == 0:
            draw.rectangle([(60, y), (W-60, y+80)], fill=(255,255,255,12))
        draw.text((c1, y+18), label, font=fonts["sr"], fill=(190,205,230,230))
        draw.text((c2, y+18), "✓ "+good, font=fonts["sh"], fill=(80,220,130,255))
        draw.text((c3, y+18), "✗ "+bad,  font=fonts["sh"], fill=(160,100,100,200))
        y += 82

    y += 40
    draw.rectangle([(60, y), (W-60, y+6)], fill=(255,255,255,60))
    y += 50

    # CTA
    for line in post["cta"].split("\n"):
        bbox = draw.textbbox((0,0), line, font=fonts["md"])
        tw = bbox[2]-bbox[0]
        draw.text((cx - tw//2, y), line, font=fonts["md"], fill=(255,255,255,230))
        y += 70

    brand_tag(draw, fonts)
    return img.convert("RGB")


def design_meme_two_panel(bg, post, fonts):
    img = bg.resize((W, H), Image.LANCZOS).convert("RGBA")

    top = img.crop((0, 0, W, H//2))
    top = darken(top, 0.22)
    img.paste(top, (0,0))

    bot = img.crop((0, H//2, W, H))
    bot = darken(bot, 0.42)
    img.paste(bot, (0, H//2))

    div = Image.new("RGBA", (W, 8), (255,255,255,220))
    img.paste(div, (0, H//2-4), div)

    draw = ImageDraw.Draw(img)
    cx = W // 2

    def meme_outline(draw, x, y, text, font, fill=(255,255,255,255)):
        for dx, dy in [(-3,-3),(-3,3),(3,-3),(3,3),(-3,0),(3,0),(0,-3),(0,3)]:
            draw.text((x+dx, y+dy), text, font=font, fill=(0,0,0,255))
        draw.text((x, y), text, font=font, fill=fill)

    def centered_meme(y_start, text, font, fill=(255,255,255,255)):
        y = y_start
        for line in text.split("\n"):
            bbox = draw.textbbox((0,0), line, font=font)
            tw = bbox[2]-bbox[0]
            meme_outline(draw, cx - tw//2, y, line, font, fill)
            y += bbox[3]-bbox[1] + 12
        return y

    # Top panel text
    y = centered_meme(60, post["top_text"], fonts["lg"], (255,255,255,255))
    # Top emoji — bottom right of top panel
    draw.text((W - 130, H//2 - 130), post["top_reaction"], font=fonts["xl"])

    # Bottom panel text
    y = centered_meme(H//2 + 50, post["bottom_text"], fonts["lg"], (255,240,80,255))
    # Bottom emoji
    draw.text((W - 130, H - 160), post["bottom_reaction"], font=fonts["xl"])

    # CTA bottom bar
    bar = Image.new("RGBA", (W, 130), (0,0,0,220))
    img.paste(bar, (0, H-130), bar)
    draw = ImageDraw.Draw(img)
    cy = H - 118
    for line in post["cta"].split("\n"):
        bbox = draw.textbbox((0,0), line, font=fonts["xs"])
        tw = bbox[2]-bbox[0]
        draw.text((cx - tw//2, cy), line, font=fonts["xs"], fill=(200,200,200,220))
        cy += 48

    brand_tag(draw, fonts)
    return img.convert("RGB")


# ─── ROUTER ───────────────────────────────────────────────────────────────────

DESIGNERS = {
    "split_grief":    design_split_grief,
    "tombstone":      design_tombstone,
    "split_screen":   design_split_screen,
    "scoreboard":     design_scoreboard,
    "meme_two_panel": design_meme_two_panel,
}

def main():
    posts_to_run = sys.argv[1:] if len(sys.argv) > 1 else [p["id"] for p in POSTS]
    fonts = load_fonts()

    for post in POSTS:
        if post["id"] not in posts_to_run:
            continue
        print(f"Generating {post['id']} [{post['design']}] at {W}x{H}...")
        try:
            if post["design"] == "scoreboard":
                # Scoreboard uses programmatic bg — no Gemini needed
                bg = Image.new("RGBA", (W, H), (8,12,28,255))
            else:
                bg = generate_background(post["prompt"])
            renderer = DESIGNERS[post["design"]]
            final = renderer(bg, post, fonts)
            out_path = OUTPUT_DIR / f"{post['id']}_v3.png"
            final.save(out_path)
            print(f"  Saved: {out_path}")
        except Exception as e:
            import traceback
            print(f"  ERROR on {post['id']}: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    main()
