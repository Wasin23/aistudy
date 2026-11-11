"""
Smartblocks Post Image Generator v4
- 9:16 (1080x1920) for Instagram/Reels/TikTok
- Harmonious color system: each post has ONE palette, used consistently
- Clean typographic hierarchy: big hook → context → proof → CTA
- Full developer value prop: speed, reach, compliance, liquidity, $50 min, 9K community
"""

import os
import sys
import base64
import requests
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
from io import BytesIO

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-image-preview:generateContent?key={GEMINI_API_KEY}"

OUTPUT_DIR = Path(__file__).parent.parent / "images"
OUTPUT_DIR.mkdir(exist_ok=True)

W, H = 1080, 1920  # 9:16 vertical

# ─── COLOR PALETTES ───────────────────────────────────────────────────────────
# Each post gets ONE palette. All text + accents pull from it only.

PALETTES = {
    "blood":    {"bg": (12,8,8),    "primary": (220,40,40),   "secondary": (255,180,180), "text": (255,255,255), "muted": (180,160,160), "bar": (30,10,10)},
    "navy":     {"bg": (6,10,28),   "primary": (60,120,255),  "secondary": (120,180,255), "text": (255,255,255), "muted": (160,180,220), "bar": (12,20,50)},
    "emerald":  {"bg": (6,20,14),   "primary": (30,200,100),  "secondary": (120,255,180), "text": (255,255,255), "muted": (160,210,185), "bar": (10,35,22)},
    "obsidian": {"bg": (10,10,14),  "primary": (200,160,80),  "secondary": (255,220,140), "text": (255,255,255), "muted": (180,170,150), "bar": (18,16,10)},
    "slate":    {"bg": (14,18,26),  "primary": (100,160,240), "secondary": (180,210,255), "text": (255,255,255), "muted": (160,175,200), "bar": (20,26,40)},
}

# ─── POSTS ────────────────────────────────────────────────────────────────────

POSTS = [
    {
        "id": "post1",
        "palette": "blood",
        "design": "grief_hook",
        "eyebrow": "TRUE STORY",
        "hook": "He lost\nthe deal.",
        "context": "Not because the deal was bad.\nBecause his capital raise took\n11 weeks.",
        "proof": "The seller walked. Went with an all-cash buyer.\nThe deal was worth $3.8M in unrealized equity.",
        "value": "On Smartblocks:\n→  Raise in 3-7 days\n→  9,000+ investors notified instantly\n→  Compliance automated",
        "cta": "The next deal doesn't have to go this way.",
        "prompt": "Cinematic vertical photo of an empty modern boardroom at night, single overhead light illuminating an abandoned deal term sheet on the table, chairs in disarray, dramatic shadows, dark moody red-black tones, photorealistic, no people, no text, 9:16 portrait"
    },
    {
        "id": "post2",
        "palette": "obsidian",
        "design": "comparison",
        "eyebrow": "LET'S BE HONEST",
        "hook": "Traditional syndication\nvs. Smartblocks.",
        "rows": [
            ("Time to raise",      "3–7 days ✓",     "60–90 days"),
            ("Investor pool",      "9,000+ global ✓", "Your network"),
            ("Min. investment",    "$50 ✓",           "$50,000+"),
            ("Cap table updates",  "Automated ✓",     "Manual/lawyer"),
            ("Distributions",      "Programmatic ✓",  "Manual wires"),
            ("Compliance",         "Built-in ✓",      "Expensive counsel"),
            ("Secondary market",   "Available ✓",     "None"),
        ],
        "cta": "Same legal backbone. Way better infrastructure.",
        "prompt": "Dark cinematic vertical photo of two paths diverging in a dramatic landscape — one dark and overgrown, one bright and modern — moody golden hour lighting, no text, no people, 9:16 portrait"
    },
    {
        "id": "post3",
        "palette": "navy",
        "design": "founder",
        "eyebrow": "12 YEARS IN THE MAKING",
        "hook": "I watched\ngood deals die\nfor dumb reasons.",
        "bullets": [
            "A $6M raise fell apart over an LLC\nstructure a compliance dept didn't recognize.",
            "A developer missed a portfolio deal\nbecause he couldn't verify investors\nfast enough. The seller needed\nproof of funds by Friday.",
            "An LP waited 5 months for a\ndistribution check that should\nhave taken 5 days.",
        ],
        "closing": "The system wasn't broken.\nIt was just designed in 1985.\n\nWe built Smartblocks to fix that.",
        "cta": "9,000 investors. Ready now.",
        "prompt": "Dramatic vertical cinematic photo of a real estate construction site at golden hour, unfinished building skeleton silhouette against a deep blue and orange sky, no people, moody and aspirational, photorealistic, 9:16 portrait"
    },
    {
        "id": "post4",
        "palette": "emerald",
        "design": "benefits_stack",
        "eyebrow": "WHAT YOU ACTUALLY GET",
        "hook": "List on\nSmartblocks.\nHere's what\nhappens.",
        "steps": [
            ("DAY 1",   "Your listing goes live to 9,000+\nverified investors globally."),
            ("DAY 2",   "Automated accreditation checks.\nNo chasing paperwork."),
            ("DAY 3-7", "Capital commits start arriving.\nCap table updates in real time."),
            ("CLOSE",   "Distributions run automatically.\nK-1s delivered programmatically."),
        ],
        "cta": "Minimum investment: $50.\nYour raise, finally democratized.",
        "prompt": "Clean vertical cinematic photo of a modern luxury residential tower at dawn, first light catching glass and steel, deep emerald-green sky gradient, aspirational and clean, no text, no people, photorealistic, 9:16 portrait"
    },
    {
        "id": "post5",
        "palette": "slate",
        "design": "objection_killer",
        "eyebrow": "HEARD THIS ONE BEFORE",
        "hook": '"I don\'t\nunderstand\nblockchain."',
        "reframe": "Good. You don't need to.",
        "analogy": "You use email every day.\nCan you explain SMTP protocols?\nDoesn't matter. You hit send, it works.\n\nTokenization is the same.",
        "what_you_touch": [
            "A dashboard showing your cap table",
            "Automated investor distributions",
            "Compliance that runs itself",
            "9,000 investors, ready to deploy",
        ],
        "cta": "The developers winning right now\naren't crypto experts.\nThey're operators who found better tools.",
        "prompt": "Clean moody vertical photo of a developer's hands reviewing blueprints on a glass desk with a tablet showing a dashboard, cool blue ambient lighting, professional and modern, no readable text on screen, photorealistic, 9:16 portrait"
    },
]

# ─── GEMINI ───────────────────────────────────────────────────────────────────

def generate_background(prompt: str) -> Image.Image:
    payload = {
        "contents": [{"parts": [{"text": f"Generate this exact photorealistic image: {prompt}"}]}],
        "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]}
    }
    resp = requests.post(GEMINI_URL, headers={"Content-Type": "application/json"}, json=payload, timeout=60)
    resp.raise_for_status()
    for part in resp.json()["candidates"][0]["content"]["parts"]:
        if "inlineData" in part:
            return Image.open(BytesIO(base64.b64decode(part["inlineData"]["data"]))).convert("RGBA")
    raise ValueError("No image in response")

# ─── FONTS ────────────────────────────────────────────────────────────────────

def load_fonts():
    bold = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    reg  = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    def tf(path, size):
        try: return ImageFont.truetype(path, size)
        except: return ImageFont.load_default()
    return {
        "hook":    tf(bold, 104),
        "lg":      tf(bold, 72),
        "md":      tf(bold, 52),
        "sm":      tf(bold, 40),
        "body":    tf(reg,  36),
        "label":   tf(bold, 28),
        "eyebrow": tf(bold, 26),
        "brand":   tf(bold, 24),
    }

# ─── HELPERS ──────────────────────────────────────────────────────────────────

def shadow(draw, pos, text, font, fill, offset=3, shadow_alpha=180):
    x, y = pos
    draw.text((x+offset, y+offset), text, font=font, fill=(0,0,0,shadow_alpha))
    draw.text((x, y), text, font=font, fill=fill)

def centered(draw, y, text, font, fill, W=W, offset=3):
    for line in text.split("\n"):
        bbox = draw.textbbox((0,0), line, font=font)
        tw = bbox[2]-bbox[0]
        shadow(draw, (W//2 - tw//2, y), line, font, fill, offset)
        y += (bbox[3]-bbox[1]) + 14
    return y

def wrap_lines(text, width=38):
    result = []
    for paragraph in text.split("\n"):
        result.extend(textwrap.wrap(paragraph, width) if paragraph.strip() else [""])
    return result

def draw_pill(draw, x, y, text, font, bg_color, text_color):
    bbox = draw.textbbox((0,0), text, font=font)
    tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
    pad_x, pad_y = 22, 10
    draw.rounded_rectangle([(x, y), (x+tw+pad_x*2, y+th+pad_y*2)], radius=8, fill=bg_color)
    draw.text((x+pad_x, y+pad_y), text, font=font, fill=text_color)
    return th + pad_y*2

def make_base(bg_img, palette, darken_factor=0.28):
    img = bg_img.resize((W, H), Image.LANCZOS).convert("RGBA")
    img = ImageEnhance.Brightness(img).enhance(darken_factor)
    # Color tint overlay matching palette
    r, g, b = palette["bg"]
    tint = Image.new("RGBA", (W, H), (r, g, b, 80))
    img = Image.alpha_composite(img, tint)
    # Gradient: heavy dark bottom 50%
    grad = Image.new("RGBA", (W, H), (0,0,0,0))
    gd = ImageDraw.Draw(grad)
    for i in range(H):
        a = int(240 * max(0, (i - H*0.3) / (H*0.7)))
        gd.line([(0,i),(W,i)], fill=(*palette["bg"], a))
    img = Image.alpha_composite(img, grad)
    return img

def add_eyebrow(draw, y, text, palette, fonts, mx=70):
    pill_h = draw_pill(draw, mx, y, text, fonts["eyebrow"], palette["primary"], palette["bg"])
    return y + pill_h + 28

def add_brand(draw, palette, fonts):
    txt = "SMARTBLOCKS"
    bbox = draw.textbbox((0,0), txt, font=fonts["brand"])
    tw = bbox[2]-bbox[0]
    draw.text((W - tw - 40, H - 44), txt, font=fonts["brand"], fill=(*palette["muted"], 200))

def accent_line(draw, x, y, palette, width=80):
    draw.rectangle([(x, y), (x+width, y+5)], fill=(*palette["primary"], 255))
    return y + 18

# ─── DESIGN TEMPLATES ─────────────────────────────────────────────────────────

def design_grief_hook(bg, post, fonts):
    p = PALETTES[post["palette"]]
    img = make_base(bg, p, darken_factor=0.25)
    draw = ImageDraw.Draw(img)
    mx = 70
    y = 100

    y = add_eyebrow(draw, y, post["eyebrow"], p, fonts, mx)
    y += 20

    # Giant hook
    for line in post["hook"].split("\n"):
        shadow(draw, (mx, y), line, fonts["hook"], p["text"])
        bbox = draw.textbbox((0,0), line, font=fonts["hook"])
        y += bbox[3]-bbox[1] + 10
    y += 20

    y = accent_line(draw, mx, y, p, 90)
    y += 10

    # Context
    for line in post["context"].split("\n"):
        shadow(draw, (mx, y), line, fonts["body"], p["secondary"])
        bbox = draw.textbbox((0,0), line, font=fonts["body"])
        y += bbox[3]-bbox[1] + 10
    y += 30

    # Proof
    for line in post["proof"].split("\n"):
        shadow(draw, (mx, y), line, fonts["label"], p["muted"])
        bbox = draw.textbbox((0,0), line, font=fonts["label"])
        y += bbox[3]-bbox[1] + 8
    y += 40

    # Value box
    vbox_y = y
    vbox = Image.new("RGBA", (W - mx*2, 240), (*p["bar"], 220))
    img.paste(vbox, (mx, vbox_y), vbox)
    draw = ImageDraw.Draw(img)
    vy = vbox_y + 22
    for line in post["value"].split("\n"):
        col = p["primary"] if line.startswith("→") else p["text"]
        shadow(draw, (mx+24, vy), line, fonts["body"], col)
        bbox = draw.textbbox((0,0), line, font=fonts["body"])
        vy += bbox[3]-bbox[1] + 14
    y = vbox_y + 260

    # CTA
    for line in post["cta"].split("\n"):
        shadow(draw, (mx, y), line, fonts["sm"], p["text"])
        bbox = draw.textbbox((0,0), line, font=fonts["sm"])
        y += bbox[3]-bbox[1] + 10

    add_brand(draw, p, fonts)
    return img.convert("RGB")


def design_comparison(bg, post, fonts):
    p = PALETTES[post["palette"]]
    # Use programmatic bg for comparison — cleaner
    img = Image.new("RGBA", (W, H), (*p["bg"], 255))
    # Subtle texture lines
    td = ImageDraw.Draw(img)
    for x in range(0, W, 70):
        td.line([(x,0),(x,H)], fill=(*[c+8 for c in p["bg"]], 255), width=1)
    for y in range(0, H, 70):
        td.line([(0,y),(W,y)], fill=(*[c+8 for c in p["bg"]], 255), width=1)

    draw = ImageDraw.Draw(img)
    mx = 50
    y = 90

    y = add_eyebrow(draw, y, post["eyebrow"], p, fonts, mx)
    y += 16

    for line in post["hook"].split("\n"):
        shadow(draw, (mx, y), line, fonts["lg"], p["text"])
        bbox = draw.textbbox((0,0), line, font=fonts["lg"])
        y += bbox[3]-bbox[1] + 8
    y += 24

    y = accent_line(draw, mx, y, p, 70)
    y += 20

    # Column headers
    c_label = mx
    c_good  = 480
    c_bad   = 790

    draw.text((c_good, y), "SMARTBLOCKS", font=fonts["label"], fill=(*p["primary"], 255))
    draw.text((c_bad,  y), "TRADITIONAL", font=fonts["label"], fill=(*p["muted"], 200))
    y += 38
    draw.rectangle([(mx, y), (W-mx, y+2)], fill=(*p["primary"], 80))
    y += 16

    for i, (label, good, bad) in enumerate(post["rows"]):
        row_fill = (*p["bar"], 200) if i % 2 == 0 else (0,0,0,0)
        draw.rectangle([(mx, y), (W-mx, y+62)], fill=row_fill)
        draw.text((c_label+8, y+14), label, font=fonts["label"], fill=(*p["muted"], 220))
        draw.text((c_good,    y+14), good,  font=fonts["label"], fill=(*p["primary"], 255))
        draw.text((c_bad,     y+14), bad,   font=fonts["label"], fill=(*p["muted"], 160))
        y += 64

    y += 30
    draw.rectangle([(mx, y), (W-mx, y+2)], fill=(*p["primary"], 60))
    y += 30

    for line in post["cta"].split("\n"):
        bbox = draw.textbbox((0,0), line, font=fonts["sm"])
        tw = bbox[2]-bbox[0]
        draw.text((W//2 - tw//2, y), line, font=fonts["sm"], fill=(*p["text"], 230))
        y += bbox[3]-bbox[1] + 12

    add_brand(draw, p, fonts)
    return img.convert("RGB")


def design_founder(bg, post, fonts):
    p = PALETTES[post["palette"]]
    img = make_base(bg, p, darken_factor=0.22)
    draw = ImageDraw.Draw(img)
    mx = 70
    y = 90

    y = add_eyebrow(draw, y, post["eyebrow"], p, fonts, mx)
    y += 20

    for line in post["hook"].split("\n"):
        shadow(draw, (mx, y), line, fonts["hook"], p["text"])
        bbox = draw.textbbox((0,0), line, font=fonts["hook"])
        y += bbox[3]-bbox[1] + 8
    y += 16

    y = accent_line(draw, mx, y, p, 80)
    y += 20

    for bullet in post["bullets"]:
        # Bullet dot in primary color
        draw.ellipse([(mx, y+12), (mx+12, y+24)], fill=(*p["primary"], 255))
        bx = mx + 28
        for line in bullet.split("\n"):
            shadow(draw, (bx, y), line, fonts["body"], p["secondary"])
            bbox = draw.textbbox((0,0), line, font=fonts["body"])
            y += bbox[3]-bbox[1] + 8
        y += 20

    y += 10
    y = accent_line(draw, mx, y, p, 60)
    y += 16

    for line in post["closing"].split("\n"):
        col = p["text"] if line.strip() else p["text"]
        shadow(draw, (mx, y), line, fonts["sm"], p["text"] if line.strip() else p["text"])
        bbox = draw.textbbox((0,0), line or " ", font=fonts["sm"])
        y += bbox[3]-bbox[1] + 8
    y += 30

    # CTA pill — prominent
    draw_pill(draw, mx, y, post["cta"], fonts["md"], p["primary"], p["bg"])

    add_brand(draw, p, fonts)
    return img.convert("RGB")


def design_benefits_stack(bg, post, fonts):
    p = PALETTES[post["palette"]]
    img = make_base(bg, p, darken_factor=0.20)
    draw = ImageDraw.Draw(img)
    mx = 70
    y = 90

    y = add_eyebrow(draw, y, post["eyebrow"], p, fonts, mx)
    y += 20

    for line in post["hook"].split("\n"):
        shadow(draw, (mx, y), line, fonts["hook"], p["text"])
        bbox = draw.textbbox((0,0), line, font=fonts["hook"])
        y += bbox[3]-bbox[1] + 8
    y += 24

    y = accent_line(draw, mx, y, p, 80)
    y += 24

    for day_label, desc in post["steps"]:
        # Step card
        card = Image.new("RGBA", (W - mx*2, 150), (*p["bar"], 230))
        img.paste(card, (mx, y), card)
        draw = ImageDraw.Draw(img)

        # Day label pill
        draw_pill(draw, mx+18, y+18, day_label, fonts["eyebrow"], p["primary"], p["bg"])

        # Description
        dy = y + 22
        for line in desc.split("\n"):
            shadow(draw, (mx+160, dy), line, fonts["body"], p["secondary"])
            bbox = draw.textbbox((0,0), line, font=fonts["body"])
            dy += bbox[3]-bbox[1] + 6

        y += 168

    y += 20

    for line in post["cta"].split("\n"):
        shadow(draw, (mx, y), line, fonts["sm"], p["text"])
        bbox = draw.textbbox((0,0), line, font=fonts["sm"])
        y += bbox[3]-bbox[1] + 10

    add_brand(draw, p, fonts)
    return img.convert("RGB")


def design_objection_killer(bg, post, fonts):
    p = PALETTES[post["palette"]]
    img = make_base(bg, p, darken_factor=0.25)
    draw = ImageDraw.Draw(img)
    mx = 70
    y = 90

    y = add_eyebrow(draw, y, post["eyebrow"], p, fonts, mx)
    y += 20

    # Quote hook — italic style with quote marks
    for line in post["hook"].split("\n"):
        shadow(draw, (mx, y), line, fonts["lg"], p["muted"])
        bbox = draw.textbbox((0,0), line, font=fonts["lg"])
        y += bbox[3]-bbox[1] + 10
    y += 10

    # Reframe — big, primary color
    shadow(draw, (mx, y), post["reframe"], fonts["md"], p["primary"])
    bbox = draw.textbbox((0,0), post["reframe"], font=fonts["md"])
    y += bbox[3]-bbox[1] + 24

    y = accent_line(draw, mx, y, p, 70)
    y += 16

    # Analogy
    for line in post["analogy"].split("\n"):
        col = p["text"] if line.strip() else p["text"]
        shadow(draw, (mx, y), line, fonts["body"], p["secondary"] if line.strip() else p["text"])
        bbox = draw.textbbox((0,0), line or " ", font=fonts["body"])
        y += bbox[3]-bbox[1] + 8
    y += 24

    # What you touch list
    draw.text((mx, y), "What you actually touch:", font=fonts["label"], fill=(*p["primary"], 255))
    y += 40
    for item in post["what_you_touch"]:
        draw.ellipse([(mx, y+10), (mx+10, y+20)], fill=(*p["primary"], 255))
        shadow(draw, (mx+22, y), item, fonts["body"], p["text"])
        bbox = draw.textbbox((0,0), item, font=fonts["body"])
        y += bbox[3]-bbox[1] + 12
    y += 24

    y = accent_line(draw, mx, y, p, 60)
    y += 16

    for line in post["cta"].split("\n"):
        shadow(draw, (mx, y), line, fonts["sm"], p["text"])
        bbox = draw.textbbox((0,0), line, font=fonts["sm"])
        y += bbox[3]-bbox[1] + 10

    add_brand(draw, p, fonts)
    return img.convert("RGB")


# ─── ROUTER ───────────────────────────────────────────────────────────────────

DESIGNERS = {
    "grief_hook":        design_grief_hook,
    "comparison":        design_comparison,
    "founder":           design_founder,
    "benefits_stack":    design_benefits_stack,
    "objection_killer":  design_objection_killer,
}

def main():
    posts_to_run = sys.argv[1:] if len(sys.argv) > 1 else [p["id"] for p in POSTS]
    fonts = load_fonts()

    for post in POSTS:
        if post["id"] not in posts_to_run:
            continue
        print(f"  {post['id']} [{post['design']}] palette={post['palette']}...")
        try:
            if post["design"] == "comparison":
                bg = Image.new("RGBA", (W, H), (*PALETTES[post["palette"]]["bg"], 255))
            else:
                bg = generate_background(post["prompt"])
            final = DESIGNERS[post["design"]](bg, post, fonts)
            out = OUTPUT_DIR / f"{post['id']}_v4.png"
            final.save(out)
            print(f"    Saved: {out}")
        except Exception as e:
            import traceback
            print(f"    ERROR: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    main()
