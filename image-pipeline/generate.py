"""
EveryMood image generator — Pillow-based composite assets.

Two flavors of asset:
  A) Standalone composite infographics (stats panel, color-block headline,
     comparison shot, mood swatch row, before/after frame, "loved by" grid).
  B) Photo-overlay variations on top of real EveryMood gallery photos —
     stat callouts, claim badges, scent-notes pyramid, ingredient annotations,
     headline overlays. Same source photo → multiple ad variants.

Brand identity (verified):
  - Bricolage Grotesque, weights 400 / 500 / 700 (matches everymood.com)
  - Indigo / coral / pink / cream palette extracted from the real bottle
  - Real product photography downloaded from EveryMood's public Shopify CDN
"""
from __future__ import annotations

import os
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter

ROOT = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(ROOT, "fonts")
SRC_IMG = os.path.normpath(os.path.join(ROOT, "..", "images"))
OUT = os.path.join(ROOT, "out")
os.makedirs(OUT, exist_ok=True)

# ─── EveryMood brand palette (extracted from real assets) ───
INDIGO = "#505EE2"        # logo wordmark
INDIGO_DEEP = "#3B47B8"
CORAL = "#E84A5F"         # Berry Obsessed bottle
CORAL_DEEP = "#C73848"
PINK = "#FF6B9E"
PINK_PALE = "#FFC9DD"
PINK_BLUSH = "#FFE9F1"
CREAM = "#FFF7EE"
INK = "#1B0F1A"
WHITE = "#FFFFFF"
LIME_ACCENT = "#BFFF00"


def font(weight: str = "regular", size: int = 32) -> ImageFont.FreeTypeFont:
    """Bricolage Grotesque — weights as served by everymood.com (400/500/700)."""
    fname = {
        "regular": "BricolageGrotesque-Regular-EM.ttf",   # 400
        "medium":  "BricolageGrotesque-Medium-EM.ttf",    # 500
        "bold":    "BricolageGrotesque-Bold-EM.ttf",      # 700
    }[weight]
    return ImageFont.truetype(os.path.join(FONTS, fname), size)


def load(name: str) -> Image.Image:
    return Image.open(os.path.join(SRC_IMG, name)).convert("RGBA")


def text_w(draw: ImageDraw.ImageDraw, txt: str, fnt: ImageFont.FreeTypeFont) -> int:
    bbox = draw.textbbox((0, 0), txt, font=fnt)
    return bbox[2] - bbox[0]


def text_h(draw: ImageDraw.ImageDraw, txt: str, fnt: ImageFont.FreeTypeFont) -> int:
    bbox = draw.textbbox((0, 0), txt, font=fnt)
    return bbox[3] - bbox[1]


def rounded_rect(draw, xy, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def cover(src: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """Center-crop src to fit (target_w, target_h) like CSS background-size: cover."""
    sw, sh = src.size
    src_ratio = sw / sh
    tgt_ratio = target_w / target_h
    if src_ratio > tgt_ratio:
        new_h = sh
        new_w = int(sh * tgt_ratio)
        x0 = (sw - new_w) // 2
        cropped = src.crop((x0, 0, x0 + new_w, sh))
    else:
        new_w = sw
        new_h = int(sw / tgt_ratio)
        y0 = (sh - new_h) // 2
        cropped = src.crop((0, y0, sw, y0 + new_h))
    return cropped.resize((target_w, target_h), Image.LANCZOS)


def darken(img: Image.Image, alpha: int = 100) -> Image.Image:
    """Add a dark overlay to image for text legibility."""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, alpha))
    return Image.alpha_composite(img.convert("RGBA"), overlay)


def gradient_band(w: int, h: int, color_top=(0, 0, 0, 0), color_bot=(0, 0, 0, 200)) -> Image.Image:
    """Vertical gradient — for bottom captions over photos."""
    band = Image.new("RGBA", (w, h))
    for y in range(h):
        a = int(color_top[3] + (color_bot[3] - color_top[3]) * y / h)
        r = int(color_top[0] + (color_bot[0] - color_top[0]) * y / h)
        g = int(color_top[1] + (color_bot[1] - color_top[1]) * y / h)
        b = int(color_top[2] + (color_bot[2] - color_top[2]) * y / h)
        for x in range(w):
            band.putpixel((x, y), (r, g, b, a))
    return band


def gradient_band_fast(w: int, h: int, color_top=(0, 0, 0, 0), color_bot=(0, 0, 0, 200)) -> Image.Image:
    """Same as gradient_band but row-wise for speed."""
    band = Image.new("RGBA", (w, h))
    px = band.load()
    for y in range(h):
        t = y / max(1, h - 1)
        r = int(color_top[0] + (color_bot[0] - color_top[0]) * t)
        g = int(color_top[1] + (color_bot[1] - color_top[1]) * t)
        b = int(color_top[2] + (color_bot[2] - color_top[2]) * t)
        a = int(color_top[3] + (color_bot[3] - color_top[3]) * t)
        for x in range(w):
            px[x, y] = (r, g, b, a)
    return band


# ──────────────────────────────────────────────────────────
# A1. STATS INFOGRAPHIC — indigo brand block + product
# ──────────────────────────────────────────────────────────
def stats_infographic(out_path: str):
    W, H = 1080, 1080
    canvas = Image.new("RGB", (W, H), CREAM)
    block = Image.new("RGB", (W // 2, H), INDIGO)
    canvas.paste(block, (W // 2, 0))
    highlight = Image.new("RGBA", (W // 2, H), (255, 255, 255, 0))
    hd = ImageDraw.Draw(highlight)
    hd.ellipse([(-200, -200), (W // 2 + 100, H // 2 + 100)], fill=(255, 235, 240, 80))
    canvas.paste(highlight, (0, 0), highlight)

    bottle = load("berry-hero.png")
    bh = int(H * 0.78)
    bw = int(bottle.width * bh / bottle.height)
    bottle = bottle.resize((bw, bh))
    canvas.paste(bottle, (W // 4 - bw // 2, (H - bh) // 2), bottle)

    draw = ImageDraw.Draw(canvas)
    f_pct = font("bold", 110)
    f_sub = font("regular", 24)
    stats = [
        ("97%", "felt instantly more\nhydrated after one spritz"),
        ("94%", "said the scent lasted\nlonger than $100 perfumes"),
        ("100%", "would buy again *"),
    ]
    panel_x = W // 2 + 60
    block_h = (H - 120) // 3
    y = 60
    for pct, sub in stats:
        draw.text((panel_x, y + 10), pct, font=f_pct, fill=WHITE)
        for i, line in enumerate(sub.split("\n")):
            draw.text((panel_x + 6, y + 140 + i * 32), line, font=f_sub, fill=(255, 255, 255, 220))
        y += block_h

    f_fine = font("regular", 14)
    draw.text((panel_x, H - 50), "* Self-reported, n=128 EveryMood customers.",
              font=f_fine, fill=(255, 255, 255, 180))
    f_mark = font("bold", 26)
    draw.text((60, H - 80), "everymood", font=f_mark, fill=INDIGO)
    canvas.save(out_path, quality=92)
    print("✓", os.path.relpath(out_path, ROOT))


# ──────────────────────────────────────────────────────────
# A2. ADAPTS-TO-MOOD — coral / strawberry hero with headline
# ──────────────────────────────────────────────────────────
def mood_color_block(out_path: str):
    W, H = 1080, 1080
    canvas = Image.new("RGB", (W, H), WHITE)
    panel = Image.new("RGB", (W // 2, H), CORAL)
    canvas.paste(panel, (0, 0))

    scene = load("berry-frame288.png")
    sh = H
    sw = int(scene.width * sh / scene.height)
    scene = scene.resize((sw, sh))
    canvas.paste(scene, (W - sw, 0), scene)

    draw = ImageDraw.Draw(canvas)
    f_hd = font("medium", 96)
    f_sub = font("medium", 24)
    headline_lines = ["Adapts to", "every", "mood."]
    y = 110
    for line in headline_lines:
        draw.text((60, y), line, font=f_hd, fill=WHITE)
        y += 105

    bullets = [
        "Hyaluronic Acid + Coconut + Vitamin E",
        "Hydrates skin & hair, never sticky",
        "12-hour scent lock, derm-tested",
    ]
    by = 540
    for text in bullets:
        cx, cy = 70, by + 14
        draw.ellipse([(cx - 7, cy - 7), (cx + 7, cy + 7)], fill=LIME_ACCENT)
        draw.text((100, by), text, font=f_sub, fill=WHITE)
        by += 50

    f_mark = font("bold", 24)
    draw.text((60, H - 70), "everymood   ·   100mL / 3.4 fl oz", font=f_mark,
              fill=(255, 255, 255, 220))
    canvas.save(out_path, quality=92)
    print("✓", os.path.relpath(out_path, ROOT))


# ──────────────────────────────────────────────────────────
# A3. BEFORE/AFTER FRAME — placeholder slots
# ──────────────────────────────────────────────────────────
def before_after_frame(out_path: str, label_pair=("Before", "After"),
                       caption: str = "Hair before traditional perfume vs. after EveryMood"):
    W, H = 1300, 900
    canvas = Image.new("RGB", (W, H), WHITE)
    gap = 12
    cell_w = (W - gap) // 2

    left = Image.new("RGB", (cell_w, H - 80), "#E5DDD9")
    ld = ImageDraw.Draw(left)
    f_ph = font("regular", 22)
    msg = "[ DROP REAL CUSTOMER\n     PHOTO HERE ]"
    for i, line in enumerate(msg.split("\n")):
        tw = text_w(ld, line, f_ph)
        ld.text((cell_w // 2 - tw // 2, (H - 80) // 2 - 30 + i * 32), line, font=f_ph, fill="#9C9088")
    canvas.paste(left, (0, 0))

    right = Image.new("RGB", (cell_w, H - 80), PINK_BLUSH)
    rd = ImageDraw.Draw(right)
    glow = Image.new("RGBA", (cell_w, H - 80), (255, 255, 255, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([(-100, -100), (cell_w // 2 + 200, (H - 80) // 2 + 200)],
               fill=(255, 255, 255, 100))
    right.paste(glow, (0, 0), glow)
    rd2 = ImageDraw.Draw(right)
    msg2 = "[ DROP REAL CUSTOMER\n     PHOTO HERE ]"
    for i, line in enumerate(msg2.split("\n")):
        tw = text_w(rd2, line, f_ph)
        rd2.text((cell_w // 2 - tw // 2, (H - 80) // 2 - 30 + i * 32), line, font=f_ph,
                 fill=CORAL_DEEP)
    canvas.paste(right, (cell_w + gap, 0))

    draw = ImageDraw.Draw(canvas)
    f_pill = font("bold", 26)
    pill_h = 56
    pw = text_w(draw, label_pair[0], f_pill) + 60
    px, py = 32, H - 80 - pill_h - 12
    rounded_rect(draw, [(px, py), (px + pw, py + pill_h)], 28, INK)
    draw.text((px + 30, py + 12), label_pair[0], font=f_pill, fill=CREAM)
    pw2 = text_w(draw, label_pair[1], f_pill) + 60
    px2 = cell_w + gap + 32
    rounded_rect(draw, [(px2, py), (px2 + pw2, py + pill_h)], 28, CORAL)
    draw.text((px2 + 30, py + 12), label_pair[1], font=f_pill, fill=WHITE)

    f_cap = font("medium", 24)
    cw = text_w(draw, caption, f_cap)
    draw.rectangle([(0, H - 60), (W, H)], fill=CREAM)
    draw.text((W // 2 - cw // 2, H - 50), caption, font=f_cap, fill=INK)
    canvas.save(out_path, quality=92)
    print("✓", os.path.relpath(out_path, ROOT))


# ──────────────────────────────────────────────────────────
# A4. LOVED-BY-N GRID
# ──────────────────────────────────────────────────────────
def loved_by_grid(out_path: str, count_label: str = "50,000+"):
    W, H = 1080, 1080
    canvas = Image.new("RGB", (W, H), CREAM)
    draw = ImageDraw.Draw(canvas)
    f_h = font("medium", 64)
    txt1 = f"Loved by {count_label}"
    tw = text_w(draw, txt1, f_h)
    draw.text(((W - tw) // 2, 60), txt1, font=f_h, fill=INK)
    plus = "  +"
    tw2 = text_w(draw, plus, f_h)
    draw.text(((W - tw) // 2 + tw, 60), plus, font=f_h, fill=INDIGO)

    margin = 80
    grid_top = 200
    cell_size = (W - margin * 2 - 20) // 2
    pair_gap = 6
    cell_h = cell_size

    for row in range(2):
        for col in range(2):
            x = margin + col * (cell_size + 20)
            y = grid_top + row * (cell_h + 90)
            half = (cell_size - pair_gap) // 2
            draw.rectangle([(x, y), (x + half, y + cell_h)], fill="#E5DDD9")
            draw.rectangle([(x + half + pair_gap, y), (x + cell_size, y + cell_h)],
                           fill=PINK_BLUSH)
            f_lbl = font("regular", 18)
            draw.text((x + 6, y + cell_h + 8), "Before", font=f_lbl, fill="#6b7280")
            draw.text((x + half + pair_gap + 6, y + cell_h + 8), "After", font=f_lbl,
                      fill=CORAL_DEEP)
            f_ph = font("regular", 14)
            ph_msg = "[ photo ]"
            tw_ph = text_w(draw, ph_msg, f_ph)
            draw.text((x + half // 2 - tw_ph // 2, y + cell_h // 2 - 8), ph_msg,
                      font=f_ph, fill="#9C9088")
            draw.text((x + half + pair_gap + half // 2 - tw_ph // 2,
                       y + cell_h // 2 - 8), ph_msg, font=f_ph, fill=CORAL_DEEP)

    f_mark = font("bold", 22)
    draw.text((W // 2 - 60, H - 50), "everymood", font=f_mark, fill=INDIGO)
    canvas.save(out_path, quality=92)
    print("✓", os.path.relpath(out_path, ROOT))


# ──────────────────────────────────────────────────────────
# A5. COMPARISON SHOT — bottle in center, crossed-out generic luxury silhouettes
# ──────────────────────────────────────────────────────────
def comparison_shot(out_path: str):
    W, H = 1080, 1080
    canvas = Image.new("RGB", (W, H), PINK_BLUSH)
    draw = ImageDraw.Draw(canvas)
    bottle = load("berry-hero.png")
    bh = int(H * 0.62)
    bw = int(bottle.width * bh / bottle.height)
    bottle = bottle.resize((bw, bh))
    bx = (W - bw) // 2
    by = (H - bh) // 2 + 30
    canvas.paste(bottle, (bx, by), bottle)

    silhouette_color = "#D9CFCB"
    x_color = CORAL_DEEP
    positions = [
        (130, 200, 130, 280, "Luxury #1"),
        (W - 260, 200, 130, 260, "Luxury #2"),
        (90, H - 380, 110, 240, "Luxury #3"),
        (W - 220, H - 360, 140, 220, "Luxury #4"),
    ]
    for x, y, w, h, label in positions:
        rounded_rect(draw, [(x, y + h // 5), (x + w, y + h)], 14, silhouette_color)
        nx = x + w // 3
        nw = w // 3
        draw.rectangle([(nx, y + 10), (nx + nw, y + h // 5)], fill=silhouette_color)
        draw.rectangle([(nx - 4, y), (nx + nw + 4, y + 14)], fill="#B8A9A4")
        cx, cy = x + w // 2, y + h // 2
        r = max(w, h) // 2
        draw.line([(cx - r * 0.7, cy - r * 0.7), (cx + r * 0.7, cy + r * 0.7)],
                  fill=x_color, width=12)
        draw.line([(cx - r * 0.7, cy + r * 0.7), (cx + r * 0.7, cy - r * 0.7)],
                  fill=x_color, width=12)
        f_tag = font("bold", 20)
        f_tag_sm = font("regular", 16)
        draw.text((x, y + h + 14), label, font=f_tag, fill=INK)
        draw.text((x, y + h + 42), "≈ $130 / 50mL", font=f_tag_sm, fill="#6b7280")

    f_center = font("medium", 36)
    f_center_sm = font("medium", 22)
    label_lines = ["Skincare-first", "fragrance"]
    ly = by + bh + 40
    for line in label_lines:
        tw = text_w(draw, line, f_center)
        draw.text((W // 2 - tw // 2, ly), line, font=f_center, fill=INK)
        ly += 44
    sub = "$22 / 100mL · everymood"
    tw = text_w(draw, sub, f_center_sm)
    draw.text((W // 2 - tw // 2, ly + 6), sub, font=f_center_sm, fill=CORAL)

    f_top = font("medium", 50)
    line1 = "Why pay $100+ for"
    line2 = "alcohol-based perfume?"
    for i, line in enumerate([line1, line2]):
        tw = text_w(draw, line, f_top)
        draw.text((W // 2 - tw // 2, 50 + i * 56), line, font=f_top, fill=INK)
    canvas.save(out_path, quality=92)
    print("✓", os.path.relpath(out_path, ROOT))


# ──────────────────────────────────────────────────────────
# A6. MOOD SWATCH ROW
# ──────────────────────────────────────────────────────────
def mood_swatch_row(out_path: str):
    W, H = 1080, 600
    canvas = Image.new("RGB", (W, H), CREAM)
    draw = ImageDraw.Draw(canvas)
    f_h = font("medium", 60)
    txt = "One mist."
    tw = text_w(draw, txt, f_h)
    draw.text(((W - tw) // 2, 60), txt, font=f_h, fill=INK)
    txt2 = "Every mood."
    tw2 = text_w(draw, txt2, f_h)
    draw.text(((W - tw2) // 2, 130), txt2, font=f_h, fill=CORAL)

    moods = [
        ("Juicy", "#FF6B9E"),
        ("Sweet", "#FFC9DD"),
        ("Bold", "#E84A5F"),
        ("Dreamy", "#B5A8E8"),
        ("Confident", "#505EE2"),
        ("Soft", "#FFE3DC"),
        ("Spicy", "#C73848"),
        ("Cosy", "#D4A574"),
    ]
    swatch_size = 90
    total_w = swatch_size * len(moods) + (len(moods) - 1) * 14
    sx = (W - total_w) // 2
    sy = 290
    f_lbl = font("medium", 18)
    for i, (label, hex_) in enumerate(moods):
        x = sx + i * (swatch_size + 14)
        draw.ellipse([(x, sy), (x + swatch_size, sy + swatch_size)], fill=hex_)
        if label == "Juicy":
            draw.ellipse([(x, sy), (x + swatch_size, sy + swatch_size)],
                         outline=INK, width=4)
            f_now = font("bold", 13)
            tag_text = "YOU'RE HERE"
            tag_w = text_w(draw, tag_text, f_now) + 24
            tag_x = x + swatch_size // 2 - tag_w // 2
            tag_y = sy + swatch_size + 32
            rounded_rect(draw, [(tag_x, tag_y), (tag_x + tag_w, tag_y + 26)], 13, INK)
            draw.polygon([(x + swatch_size // 2 - 6, tag_y),
                          (x + swatch_size // 2 + 6, tag_y),
                          (x + swatch_size // 2, tag_y - 8)], fill=INK)
            draw.text((tag_x + 12, tag_y + 5), tag_text, font=f_now, fill=CREAM)
        tw = text_w(draw, label, f_lbl)
        draw.text((x + swatch_size // 2 - tw // 2, sy + swatch_size + 8),
                  label, font=f_lbl, fill="#4b5563")

    f_foot = font("regular", 22)
    foot = "Pick the scent that matches the mood. 8 in the EveryMood family."
    tw = text_w(draw, foot, f_foot)
    draw.text((W // 2 - tw // 2, H - 50), foot, font=f_foot, fill="#6b7280")
    canvas.save(out_path, quality=92)
    print("✓", os.path.relpath(out_path, ROOT))


# ══════════════════════════════════════════════════════════
# B-SERIES — variations on real EveryMood gallery photos
# Same source photo, different conversion overlay = multiple ad units
# ══════════════════════════════════════════════════════════

def _photo_canvas(src_name: str, W: int, H: int) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    src = load(src_name)
    img = cover(src.convert("RGB"), W, H)
    return img.convert("RGBA"), ImageDraw.Draw(img.convert("RGBA"))


# ─── B1. frame189 (model lifestyle) — 3 variants ───
def lifestyle_v1_clean(out_path: str):
    """Original lifestyle shot, brand-stamped."""
    W, H = 1080, 1080
    img = cover(load("berry-frame189.png").convert("RGB"), W, H).convert("RGBA")
    # bottom gradient band
    band = gradient_band_fast(W, 220, (0,0,0,0), (10,5,15,210))
    img.paste(band, (0, H - 220), band)
    draw = ImageDraw.Draw(img)
    f_h = font("medium", 50)
    f_sub = font("medium", 22)
    draw.text((50, H - 160), "Berry Obsessed.", font=f_h, fill=WHITE)
    draw.text((50, H - 100), "Skin obsessed back.", font=f_h, fill=CORAL)
    draw.text((50, H - 50), "everymood   ·   100mL", font=f_sub, fill=(255,255,255,200))
    img.convert("RGB").save(out_path, quality=92)
    print("✓", os.path.relpath(out_path, ROOT))


def lifestyle_v2_stat_overlay(out_path: str):
    """Lifestyle + 96% stat callout."""
    W, H = 1080, 1080
    img = cover(load("berry-frame189.png").convert("RGB"), W, H).convert("RGBA")
    draw = ImageDraw.Draw(img)
    # Stat badge top-left
    badge_w, badge_h = 320, 220
    bx, by = 36, 36
    rounded_rect(draw, [(bx, by), (bx + badge_w, by + badge_h)], 20, (255, 247, 238, 240))
    rounded_rect(draw, [(bx, by), (bx + badge_w, by + badge_h)], 20, None, outline=CORAL, width=3)
    f_pct = font("bold", 88)
    f_sub = font("medium", 20)
    draw.text((bx + 30, by + 24), "96%", font=f_pct, fill=CORAL_DEEP)
    draw.text((bx + 30, by + 130), "got compliments", font=f_sub, fill=INK)
    draw.text((bx + 30, by + 158), "within 24 hours of", font=f_sub, fill=INK)
    draw.text((bx + 30, by + 186), "wearing EveryMood *", font=f_sub, fill=INK)
    # bottom band with attribution
    band = gradient_band_fast(W, 110, (0,0,0,0), (15,10,25,210))
    img.paste(band, (0, H - 110), band)
    f_foot = font("regular", 16)
    draw.text((36, H - 36), "* Self-reported, n=128 customers, 30-day window.",
              font=f_foot, fill=(255,255,255,200))
    img.convert("RGB").save(out_path, quality=92)
    print("✓", os.path.relpath(out_path, ROOT))


def lifestyle_v3_quote(out_path: str):
    """Lifestyle + customer quote overlay."""
    W, H = 1080, 1080
    img = cover(load("berry-frame189.png").convert("RGB"), W, H).convert("RGBA")
    band = gradient_band_fast(W, 380, (0,0,0,0), (15,10,25,220))
    img.paste(band, (0, H - 380), band)
    draw = ImageDraw.Draw(img)
    f_q = font("medium", 32)
    f_attr = font("bold", 20)
    f_open = font("bold", 100)
    draw.text((50, H - 380), "“", font=f_open, fill=CORAL)
    quote_lines = [
        "I literally get stopped at the",
        "coffee shop asking what I'm",
        "wearing. I'm on my 4th bottle.",
    ]
    qy = H - 280
    for line in quote_lines:
        draw.text((60, qy), line, font=f_q, fill=WHITE)
        qy += 42
    draw.text((60, H - 120), "JESS T.   ✓ VERIFIED BUYER", font=f_attr, fill=CORAL)
    draw.text((60, H - 80), "Switched from Burberry Her", font=font("regular", 18),
              fill=(255,255,255,200))
    img.convert("RGB").save(out_path, quality=92)
    print("✓", os.path.relpath(out_path, ROOT))


# ─── B2. frame190 (ingredients flatlay) — 3 variants ───
def ingredients_v1_callouts(out_path: str):
    """Flatlay + ingredient name callouts pointing at the elements."""
    W, H = 1080, 1080
    img = cover(load("berry-frame190.png").convert("RGB"), W, H).convert("RGBA")
    draw = ImageDraw.Draw(img)
    f_kw = font("bold", 22)
    f_v = font("medium", 16)
    callouts = [
        # (anchor_x, anchor_y, line_end_x, line_end_y, label, sub)
        (260, 200, 80,  130, "HYALURONIC ACID", "binds moisture to skin"),
        (820, 280, 980, 200, "VITAMIN E",       "antioxidant + hair-safe"),
        (190, 760, 60,  860, "COCONUT EXTRACT", "gentle hydration"),
        (820, 740, 980, 840, "ROSE PETAL",      "soft floral note"),
    ]
    for ax, ay, ex, ey, label, sub in callouts:
        # connector line
        draw.line([(ax, ay), (ex, ey)], fill=(255, 255, 255, 220), width=2)
        # dot at anchor
        draw.ellipse([(ax-7, ay-7), (ax+7, ay+7)], fill=CORAL, outline=WHITE, width=2)
        # label box
        bw = text_w(draw, label, f_kw) + 20
        bh = 56
        bx = ex - bw // 2 if ex < W // 2 else ex - bw + 20
        by = ey - bh - 6 if ey > H // 2 else ey + 6
        rounded_rect(draw, [(bx, by), (bx + bw, by + bh)], 10, (255,247,238,240))
        rounded_rect(draw, [(bx, by), (bx + bw, by + bh)], 10, None, outline=CORAL, width=2)
        draw.text((bx + 10, by + 8), label, font=f_kw, fill=INK)
        draw.text((bx + 10, by + 34), sub, font=f_v, fill="#4b5563")
    # title strip top
    band = gradient_band_fast(W, 130, (0,0,0,170), (0,0,0,0))
    img.paste(band, (0, 0), band)
    f_title = font("medium", 36)
    title = "Inside every spritz:"
    draw.text((40, 40), title, font=f_title, fill=WHITE)
    img.convert("RGB").save(out_path, quality=92)
    print("✓", os.path.relpath(out_path, ROOT))


def ingredients_v2_zero_alcohol_badge(out_path: str):
    """Flatlay + 0% denatured alcohol badge."""
    W, H = 1080, 1080
    img = cover(load("berry-frame190.png").convert("RGB"), W, H).convert("RGBA")
    draw = ImageDraw.Draw(img)
    # Big zero badge upper-right
    cx, cy, r = W - 180, 200, 130
    draw.ellipse([(cx-r, cy-r), (cx+r, cy+r)], fill=(255, 247, 238, 245))
    draw.ellipse([(cx-r, cy-r), (cx+r, cy+r)], outline=CORAL, width=4)
    f_zero = font("bold", 90)
    f_zero_sub = font("medium", 18)
    z_w = text_w(draw, "0%", f_zero)
    draw.text((cx - z_w//2, cy - 60), "0%", font=f_zero, fill=CORAL_DEEP)
    sub = "denatured alcohol"
    sw = text_w(draw, sub, f_zero_sub)
    draw.text((cx - sw//2, cy + 30), sub, font=f_zero_sub, fill=INK)
    # Bottom panel — what it does
    band = gradient_band_fast(W, 280, (0,0,0,0), (15,10,25,220))
    img.paste(band, (0, H - 280), band)
    f_h = font("medium", 36)
    f_b = font("medium", 22)
    draw.text((40, H - 220), "Skincare-first formula.", font=f_h, fill=WHITE)
    draw.text((40, H - 170), "No sting. No dry. No frizz.", font=f_h, fill=CORAL)
    bullets_y = H - 110
    for line in ["Hyaluronic Acid · Coconut · Vitamin E · 100% vegan"]:
        draw.text((40, bullets_y), line, font=f_b, fill=(255,255,255,230))
        bullets_y += 32
    img.convert("RGB").save(out_path, quality=92)
    print("✓", os.path.relpath(out_path, ROOT))


def ingredients_v3_clean_label(out_path: str):
    """Flatlay + 'Free from / made with' clean-label panel."""
    W, H = 1080, 1080
    img = cover(load("berry-frame190.png").convert("RGB"), W, H).convert("RGBA")
    # left translucent panel
    panel = Image.new("RGBA", (440, H), (255, 247, 238, 235))
    img.paste(panel, (0, 0), panel)
    draw = ImageDraw.Draw(img)
    f_h = font("medium", 36)
    f_lbl = font("bold", 20)
    f_b = font("medium", 22)
    draw.text((36, 80), "Made with.", font=f_h, fill=INK)
    made = ["Hyaluronic Acid", "Coconut Extract", "Vitamin E", "Aloe Vera",
            "Strawberry Cream notes"]
    y = 140
    for item in made:
        draw.ellipse([(36, y+10), (52, y+26)], fill=CORAL)
        draw.text((68, y+4), item, font=f_b, fill=INK)
        y += 42
    draw.text((36, y + 30), "Free from.", font=f_h, fill=INK)
    free = ["Denatured alcohol", "Parabens", "Phthalates", "Sulfates",
            "Synthetic dyes"]
    y += 90
    for item in free:
        draw.line([(36, y+18), (52, y+18)], fill="#9C9088", width=3)
        draw.text((68, y+4), item, font=f_b, fill="#4b5563")
        y += 42
    f_mark = font("bold", 22)
    draw.text((36, H - 50), "everymood", font=f_mark, fill=INDIGO)
    img.convert("RGB").save(out_path, quality=92)
    print("✓", os.path.relpath(out_path, ROOT))


# ─── B3. frame276 (strawberry hero) — 3 variants ───
def strawberry_v1_scent_pyramid(out_path: str):
    """Scent notes pyramid overlay."""
    W, H = 1080, 1080
    img = cover(load("berry-frame276.png").convert("RGB"), W, H).convert("RGBA")
    band = gradient_band_fast(W, 600, (0,0,0,0), (15,10,25,200))
    img.paste(band, (0, H - 600), band)
    draw = ImageDraw.Draw(img)
    f_h = font("medium", 38)
    f_lvl = font("bold", 22)
    f_n = font("medium", 20)
    draw.text((40, H - 540), "Scent Profile.", font=f_h, fill=WHITE)

    levels = [
        ("TOP",   "Wild strawberry · Citrus zest", "#FFC9DD"),
        ("HEART", "Sweet cream · Pink peony",      "#FF6B9E"),
        ("BASE",  "Vanilla · Soft musk",           "#E84A5F"),
    ]
    py = H - 460
    for label, notes, color in levels:
        # color block
        draw.rectangle([(40, py), (40 + 140, py + 100)], fill=color)
        draw.text((54, py + 10), label, font=f_lvl, fill=INK if color == "#FFC9DD" else WHITE)
        draw.text((54, py + 50), "NOTES", font=font("regular", 14),
                  fill=(0,0,0,180) if color == "#FFC9DD" else (255,255,255,200))
        draw.text((220, py + 40), notes, font=f_n, fill=WHITE)
        py += 120
    f_foot = font("medium", 20)
    draw.text((40, H - 60), "Lasts up to 12 hours.",
              font=f_foot, fill=CORAL)
    img.convert("RGB").save(out_path, quality=92)
    print("✓", os.path.relpath(out_path, ROOT))


def strawberry_v2_dupe_callout(out_path: str):
    """Strawberry hero + 'smells like a $130 perfume' badge."""
    W, H = 1080, 1080
    img = cover(load("berry-frame276.png").convert("RGB"), W, H).convert("RGBA")
    draw = ImageDraw.Draw(img)
    # Top sticker badge
    bw, bh = 380, 110
    bx, by = (W - bw) // 2, 50
    rounded_rect(draw, [(bx, by), (bx + bw, by + bh)], bh//2, (255,247,238,245))
    rounded_rect(draw, [(bx, by), (bx + bw, by + bh)], bh//2, None, outline=CORAL, width=3)
    f_b = font("medium", 22)
    f_bs = font("medium", 16)
    draw.text((bx + 30, by + 18), "Smells like a $130 perfume.", font=f_b, fill=INK)
    draw.text((bx + 30, by + 56), "Costs $22. Comes with skincare.",
              font=f_bs, fill=CORAL_DEEP)
    # Bottom price flag
    band = gradient_band_fast(W, 220, (0,0,0,0), (15,10,25,220))
    img.paste(band, (0, H - 220), band)
    f_price_strike = font("medium", 32)
    f_price_now = font("bold", 64)
    draw.text((40, H - 180), "Was $130 / 50mL", font=f_price_strike,
              fill=(200,200,200,200))
    # strikethrough manually
    sw = text_w(draw, "Was $130 / 50mL", f_price_strike)
    draw.line([(40, H - 162), (40 + sw, H - 162)], fill=(200,200,200,200), width=3)
    draw.text((40, H - 130), "Now $22 / 100mL", font=f_price_now, fill=WHITE)
    img.convert("RGB").save(out_path, quality=92)
    print("✓", os.path.relpath(out_path, ROOT))


def strawberry_v3_specs_strip(out_path: str):
    """Strawberry hero + specs strip overlay (size, lasts, doses)."""
    W, H = 1080, 1080
    img = cover(load("berry-frame276.png").convert("RGB"), W, H).convert("RGBA")
    draw = ImageDraw.Draw(img)
    band = gradient_band_fast(W, 200, (0,0,0,0), (15,10,25,210))
    img.paste(band, (0, H - 200), band)
    f_n = font("bold", 44)
    f_l = font("medium", 16)
    specs = [
        ("100mL", "3.4 fl oz"),
        ("~600", "spritzes / bottle"),
        ("12 hr", "scent lock"),
        ("$0.07", "per spritz"),
    ]
    pad = 40
    seg_w = (W - pad * 2) // len(specs)
    for i, (n, l) in enumerate(specs):
        x = pad + i * seg_w
        nw = text_w(draw, n, f_n)
        lw = text_w(draw, l, f_l)
        draw.text((x + seg_w // 2 - nw // 2, H - 160), n, font=f_n, fill=WHITE)
        draw.text((x + seg_w // 2 - lw // 2, H - 100), l, font=f_l,
                  fill=(255,255,255,180))
    img.convert("RGB").save(out_path, quality=92)
    print("✓", os.path.relpath(out_path, ROOT))


# ─── B4. frame288 (red gradient) — 3 variants ───
def red_v1_hero_headline(out_path: str):
    """Red dramatic + bold headline overlay."""
    W, H = 1080, 1080
    img = cover(load("berry-frame288.png").convert("RGB"), W, H).convert("RGBA")
    draw = ImageDraw.Draw(img)
    f_h = font("medium", 92)
    f_sub = font("medium", 24)
    draw.text((50, 80), "Every", font=f_h, fill=WHITE)
    draw.text((50, 178), "mood.", font=f_h, fill=LIME_ACCENT)
    draw.text((50, 276), "One spritz.", font=f_h, fill=WHITE)
    draw.text((50, 380), "Hyaluronic-infused fragrance.",
              font=f_sub, fill=(255,255,255,220))
    draw.text((50, 412), "100mL · vegan · derm-tested · $22",
              font=f_sub, fill=(255,255,255,200))
    img.convert("RGB").save(out_path, quality=92)
    print("✓", os.path.relpath(out_path, ROOT))


def red_v2_offer_badge(out_path: str):
    """Red hero + offer/discount sticker."""
    W, H = 1080, 1080
    img = cover(load("berry-frame288.png").convert("RGB"), W, H).convert("RGBA")
    draw = ImageDraw.Draw(img)
    # Sticker sunburst circle top-right
    cx, cy, r = W - 180, 220, 150
    # outer wavy circle
    draw.ellipse([(cx-r, cy-r), (cx+r, cy+r)], fill=LIME_ACCENT)
    draw.ellipse([(cx-r+10, cy-r+10), (cx+r-10, cy+r-10)], fill=INK)
    f_pct = font("bold", 70)
    f_sub = font("bold", 18)
    f_fine = font("regular", 14)
    pw = text_w(draw, "55%", f_pct)
    draw.text((cx - pw//2, cy - 70), "55%", font=f_pct, fill=LIME_ACCENT)
    sw = text_w(draw, "OFF", f_sub)
    draw.text((cx - sw//2, cy + 6), "OFF", font=f_sub, fill=WHITE)
    fw = text_w(draw, "+ free mystery mini", f_fine)
    draw.text((cx - fw//2, cy + 40), "+ free mystery mini", font=f_fine,
              fill=(255,255,255,230))
    # Bottom CTA bar
    band = gradient_band_fast(W, 200, (0,0,0,0), (10,5,15,230))
    img.paste(band, (0, H - 200), band)
    f_h = font("medium", 50)
    f_s = font("medium", 22)
    draw.text((50, H - 160), "Berry Obsessed", font=f_h, fill=WHITE)
    draw.text((50, H - 100), "$34 → $22 today", font=f_s, fill=CORAL)
    img.convert("RGB").save(out_path, quality=92)
    print("✓", os.path.relpath(out_path, ROOT))


def red_v3_review_quote(out_path: str):
    """Red hero + glowing customer quote in big script."""
    W, H = 1080, 1080
    img = cover(load("berry-frame288.png").convert("RGB"), W, H).convert("RGBA")
    band = gradient_band_fast(W, H, (15,10,25,140), (15,10,25,40))
    img.paste(band, (0, 0), band)
    draw = ImageDraw.Draw(img)
    f_hd = font("bold", 30)
    f_q = font("medium", 38)
    f_n = font("bold", 18)
    # 5 stars top
    f_st = font("bold", 30)
    draw.text((40, 40), "★★★★★", font=f_st, fill="#FFB800")
    draw.text((40, 88), "12,483+ verified reviews", font=f_n, fill=(255,255,255,200))
    # quote
    draw.text((40, 220), '"Eight hours later my legs', font=f_q, fill=WHITE)
    draw.text((40, 270), 'were still glowing and I still', font=f_q, fill=WHITE)
    draw.text((40, 320), 'smelled like sweet cream', font=f_q, fill=WHITE)
    draw.text((40, 370), 'and berries. This is insane."', font=f_q, fill=LIME_ACCENT)
    draw.text((40, 460), "— KATIE M.   ✓ VERIFIED BUYER", font=f_n, fill=CORAL)
    # bottom mark
    f_mark = font("bold", 22)
    draw.text((40, H - 50), "everymood   ·   $22", font=f_mark, fill=WHITE)
    img.convert("RGB").save(out_path, quality=92)
    print("✓", os.path.relpath(out_path, ROOT))


# ─── B5. frame193 (clean bottle on pink fabric) — 2 variants ───
def clean_v1_specs(out_path: str):
    """Clean product hero + specs strip."""
    W, H = 1080, 1080
    img = cover(load("berry-frame193.png").convert("RGB"), W, H).convert("RGBA")
    draw = ImageDraw.Draw(img)
    f_h = font("medium", 56)
    f_sub = font("medium", 22)
    f_lbl = font("bold", 16)
    # mood badge top-left
    rounded_rect(draw, [(36, 36), (320, 88)], 26, (255, 247, 238, 240))
    draw.text((52, 50), "JUICY & VIBRANT MOOD", font=f_lbl, fill=CORAL_DEEP)
    # Bottom title bar
    band = gradient_band_fast(W, 280, (0,0,0,0), (15,10,25,210))
    img.paste(band, (0, H - 280), band)
    draw.text((40, H - 220), "Berry Obsessed", font=f_h, fill=WHITE)
    draw.text((40, H - 150), "Hydrating Body & Hair Mist · 100mL",
              font=f_sub, fill=(255,255,255,220))
    # specs row
    f_n = font("bold", 28)
    f_l = font("regular", 14)
    specs = [("Vegan", "100%"), ("Cruelty-free", "yes"), ("Derm-tested", "yes"),
             ("Made with", "HA + Coconut + Vit E")]
    seg_w = (W - 80) // len(specs)
    for i, (label, val) in enumerate(specs):
        x = 40 + i * seg_w
        draw.text((x, H - 90), val, font=f_n, fill=CORAL)
        draw.text((x, H - 56), label, font=f_l, fill=(255,255,255,200))
    img.convert("RGB").save(out_path, quality=92)
    print("✓", os.path.relpath(out_path, ROOT))


def clean_v2_compliment_promise(out_path: str):
    """Clean product hero + 30-day compliment guarantee callout."""
    W, H = 1080, 1080
    img = cover(load("berry-frame193.png").convert("RGB"), W, H).convert("RGBA")
    draw = ImageDraw.Draw(img)
    # Big rosette badge bottom-right
    cx, cy, r = W - 200, H - 200, 160
    draw.ellipse([(cx-r, cy-r), (cx+r, cy+r)], fill=CORAL)
    draw.ellipse([(cx-r+8, cy-r+8), (cx+r-8, cy+r-8)],
                 fill=None, outline=WHITE, width=3)
    f_30 = font("bold", 60)
    f_d = font("bold", 16)
    f_g = font("bold", 22)
    s30 = "30"
    sw = text_w(draw, s30, f_30)
    draw.text((cx - sw//2, cy - 70), s30, font=f_30, fill=WHITE)
    sd = "DAY"
    dw = text_w(draw, sd, f_d)
    draw.text((cx - dw//2, cy - 4), sd, font=f_d, fill=WHITE)
    sg = "Compliment"
    gw = text_w(draw, sg, f_g)
    draw.text((cx - gw//2, cy + 26), sg, font=f_g, fill=WHITE)
    sg2 = "Guarantee"
    gw2 = text_w(draw, sg2, f_g)
    draw.text((cx - gw2//2, cy + 56), sg2, font=f_g, fill=WHITE)
    # top headline
    band = gradient_band_fast(W, 240, (15,10,25,200), (0,0,0,0))
    img.paste(band, (0, 0), band)
    f_h = font("medium", 50)
    f_sub = font("medium", 22)
    draw.text((40, 50), "Don't get stopped & asked", font=f_h, fill=WHITE)
    draw.text((40, 110), "what you're wearing?", font=f_h, fill=LIME_ACCENT)
    draw.text((40, 175), "We'll refund you. Hassle-free.",
              font=f_sub, fill=(255,255,255,220))
    img.convert("RGB").save(out_path, quality=92)
    print("✓", os.path.relpath(out_path, ROOT))


# ──────────────────────────────────────────────────────────
# C. PRESS LOGO STRIP — branded version
# ──────────────────────────────────────────────────────────
def press_strip(out_path: str):
    W, H = 1080, 220
    canvas = Image.new("RGB", (W, H), CREAM)
    draw = ImageDraw.Draw(canvas)
    f_lbl = font("bold", 14)
    label = "AS SEEN ON"
    lw = text_w(draw, label, f_lbl)
    draw.text(((W - lw) // 2, 30), label, font=f_lbl, fill="#9CA3AF")
    pubs = [
        ("TikTok",       font("bold", 32),    INK),
        ("Cosmopolitan", font("medium", 28),  INK),
        ("Allure",       font("bold", 28),    INK),
        ("Byrdie",       font("regular", 28), INK),
        ("Glamour",      font("bold", 30),    INK),
    ]
    total_w = sum(text_w(draw, p[0], p[1]) for p in pubs) + (len(pubs)-1) * 60
    sx = (W - total_w) // 2
    py = 100
    for label_t, fnt, color in pubs:
        draw.text((sx, py), label_t, font=fnt, fill=color)
        sx += text_w(draw, label_t, fnt) + 60
    canvas.save(out_path, quality=92)
    print("✓", os.path.relpath(out_path, ROOT))


# ══════════════════════════════════════════════════════════
# C-SERIES — fragrance-specific conversion assets
# ══════════════════════════════════════════════════════════

def _silhouette_bottle(draw, x, y, w, h, color="#D9CFCB", cap_color="#B8A9A4"):
    """Generic luxury perfume bottle silhouette (no brand imitation)."""
    rounded_rect(draw, [(x, y + h // 5), (x + w, y + h)], 14, color)
    nx = x + w // 3
    nw = w // 3
    draw.rectangle([(nx, y + 10), (nx + nw, y + h // 5)], fill=color)
    draw.rectangle([(nx - 4, y), (nx + nw + 4, y + 14)], fill=cap_color)


# C1. DUPE COMPARISON CARD — "smells like $130, costs $22"
def dupe_comparison(out_path: str):
    W, H = 1080, 1080
    canvas = Image.new("RGB", (W, H), CREAM)
    draw = ImageDraw.Draw(canvas)

    # Top headline
    f_h = font("medium", 56)
    draw.text((50, 60), "Smells like $130.", font=f_h, fill=INK)
    draw.text((50, 122), "Costs $22.", font=f_h, fill=CORAL)

    # Left column: generic luxury silhouette + price/spec
    lx, ly, lw, lh = 100, 250, 180, 360
    _silhouette_bottle(draw, lx, ly, lw, lh)
    # X across
    cx, cy = lx + lw // 2, ly + lh // 2
    r = max(lw, lh) // 2
    draw.line([(cx - r * 0.7, cy - r * 0.7), (cx + r * 0.7, cy + r * 0.7)],
              fill=CORAL_DEEP, width=14)
    draw.line([(cx - r * 0.7, cy + r * 0.7), (cx + r * 0.7, cy - r * 0.7)],
              fill=CORAL_DEEP, width=14)
    f_lbl = font("bold", 22)
    f_meta = font("regular", 16)
    draw.text((lx, ly + lh + 20), "Designer perfume", font=f_lbl, fill=INK)
    draw.text((lx, ly + lh + 50), "≈ $130 / 50mL", font=f_meta, fill="#6b7280")
    draw.text((lx, ly + lh + 76), "70-90% denatured alcohol", font=f_meta, fill="#6b7280")
    draw.text((lx, ly + lh + 102), "Dries skin · damages hair", font=f_meta, fill="#6b7280")

    # VS divider
    f_vs = font("bold", 30)
    draw.text((W // 2 - 14, H // 2 - 20), "vs", font=f_vs, fill=CORAL)

    # Right column: real bottle + price/spec
    bottle = load("berry-hero.png")
    bh = 380
    bw = int(bottle.width * bh / bottle.height)
    bottle = bottle.resize((bw, bh))
    rx_center = W * 3 // 4
    canvas.paste(bottle, (rx_center - bw // 2, 240), bottle)
    rx = rx_center - 130
    draw.text((rx, 250 + 360 + 20), "Berry Obsessed", font=f_lbl, fill=INK)
    draw.text((rx, 250 + 360 + 50), "$22 / 100mL", font=f_meta, fill=CORAL)
    draw.text((rx, 250 + 360 + 76), "0% denatured alcohol", font=f_meta, fill="#6b7280")
    draw.text((rx, 250 + 360 + 102), "Hydrates skin · hair-safe", font=f_meta, fill="#6b7280")

    # Savings stamp bottom
    f_save = font("bold", 30)
    save_text = "You save $108 per bottle. And your skin."
    sw = text_w(draw, save_text, f_save)
    draw.text((W // 2 - sw // 2, H - 100), save_text, font=f_save, fill=INK)
    f_mark = font("bold", 18)
    mw = text_w(draw, "everymood", f_mark)
    draw.text((W // 2 - mw // 2, H - 50), "everymood", font=f_mark, fill=INDIGO)
    canvas.save(out_path, quality=92)
    print("✓", os.path.relpath(out_path, ROOT))


# C2. DAY-TO-NIGHT TIMELINE — "12-hour scent lock" visualized
def day_to_night_timeline(out_path: str):
    W, H = 1080, 720
    canvas = Image.new("RGB", (W, H), CREAM)
    draw = ImageDraw.Draw(canvas)
    f_h = font("medium", 50)
    f_n = font("bold", 30)
    f_l = font("medium", 16)
    f_t = font("regular", 14)

    draw.text((50, 60), "12 hours of scent.", font=f_h, fill=INK)
    draw.text((50, 116), "One spritz.", font=f_h, fill=CORAL)

    # Timeline bar
    bar_y = 360
    bar_x0, bar_x1 = 100, W - 100
    bar_w = bar_x1 - bar_x0
    # gradient bar
    for x in range(bar_x0, bar_x1):
        t = (x - bar_x0) / bar_w
        # coral → pink → coral fade
        r = int(232 + (255 - 232) * t * 0.5)
        g = int(74 + (107 - 74) * t * 0.5)
        b = int(95 + (158 - 95) * t * 0.5)
        draw.rectangle([(x, bar_y - 6), (x + 1, bar_y + 6)], fill=(r, g, b))
    # rounded ends
    draw.ellipse([(bar_x0 - 6, bar_y - 6), (bar_x0 + 6, bar_y + 6)], fill=CORAL)
    draw.ellipse([(bar_x1 - 6, bar_y - 6), (bar_x1 + 6, bar_y + 6)], fill=PINK)

    # 4 markers
    moments = [
        (0.05, "6 AM", "Coffee run", "★★★★★", CORAL_DEEP),
        (0.36, "12 PM", "Lunch break", "★★★★★", CORAL),
        (0.68, "6 PM", "Dinner date", "★★★★☆", PINK),
        (0.95, "10 PM", "Last spritz still on", "★★★★☆", "#FF8FB0"),
    ]
    for t, time, moment, intensity, color in moments:
        cx = bar_x0 + int(bar_w * t)
        # marker dot
        draw.ellipse([(cx - 14, bar_y - 14), (cx + 14, bar_y + 14)], fill=color, outline=WHITE, width=3)
        # time above
        tw = text_w(draw, time, f_n)
        draw.text((cx - tw // 2, bar_y - 80), time, font=f_n, fill=INK)
        # moment below
        mw = text_w(draw, moment, f_l)
        draw.text((cx - mw // 2, bar_y + 30), moment, font=f_l, fill="#4b5563")
        iw = text_w(draw, intensity, f_t)
        draw.text((cx - iw // 2, bar_y + 56), intensity, font=f_t, fill="#FFB800")

    # bottom note
    f_foot = font("regular", 16)
    foot = "Hyaluronic-bound fragrance molecules cling to skin instead of evaporating with alcohol."
    fw = text_w(draw, foot, f_foot)
    draw.text((W // 2 - fw // 2, H - 80), foot, font=f_foot, fill="#6b7280")
    f_mark = font("bold", 18)
    draw.text((50, H - 40), "everymood", font=f_mark, fill=INDIGO)

    canvas.save(out_path, quality=92)
    print("✓", os.path.relpath(out_path, ROOT))


# C3. ZERO PERCENT DENATURED ALCOHOL STAMP
def zero_alcohol_stamp(out_path: str):
    W, H = 1080, 1080
    canvas = Image.new("RGB", (W, H), CREAM)
    draw = ImageDraw.Draw(canvas)

    # Big stamp circle
    cx, cy = W // 2, H // 2 - 30
    r = 320
    # outer ring
    draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=CORAL)
    draw.ellipse([(cx - r + 10, cy - r + 10), (cx + r - 10, cy + r - 10)], outline=WHITE, width=4)
    # inner content
    f_pct = font("bold", 220)
    f_lbl = font("medium", 28)
    f_brand = font("bold", 22)

    pw = text_w(draw, "0%", f_pct)
    draw.text((cx - pw // 2, cy - 150), "0%", font=f_pct, fill=WHITE)
    lbl1 = "DENATURED"
    lbl2 = "ALCOHOL"
    l1w = text_w(draw, lbl1, f_lbl)
    l2w = text_w(draw, lbl2, f_lbl)
    draw.text((cx - l1w // 2, cy + 70), lbl1, font=f_lbl, fill=WHITE)
    draw.text((cx - l2w // 2, cy + 110), lbl2, font=f_lbl, fill=WHITE)
    # tiny ring of dots around perimeter
    import math
    for i in range(36):
        a = i * 10 * math.pi / 180
        dx = cx + int((r - 30) * math.cos(a))
        dy = cy + int((r - 30) * math.sin(a))
        draw.ellipse([(dx - 3, dy - 3), (dx + 3, dy + 3)], fill=WHITE)

    # supporting copy
    f_h = font("medium", 36)
    f_s = font("regular", 22)
    h1 = "Fragrance, not solvent."
    hw = text_w(draw, h1, f_h)
    draw.text((W // 2 - hw // 2, 60), h1, font=f_h, fill=INK)
    s1 = "Hydrates skin instead of stripping it."
    sw = text_w(draw, s1, f_s)
    draw.text((W // 2 - sw // 2, 110), s1, font=f_s, fill="#6b7280")
    bw = text_w(draw, "everymood", f_brand)
    draw.text((W // 2 - bw // 2, H - 60), "everymood", font=f_brand, fill=INDIGO)

    canvas.save(out_path, quality=92)
    print("✓", os.path.relpath(out_path, ROOT))


# C4. SWITCHED-FROM CAROUSEL CARD (single card; can render multiple)
def switched_from_card(out_path: str, was_brand="Designer floral", was_price=148,
                       was_size="50mL", saved=126, persona="Switched after 3 bottles"):
    W, H = 1080, 1080
    canvas = Image.new("RGB", (W, H), CREAM)
    draw = ImageDraw.Draw(canvas)
    # Header
    f_eyebrow = font("bold", 16)
    draw.text((50, 50), "SWITCHED FROM", font=f_eyebrow, fill="#9CA3AF")
    f_h = font("medium", 56)
    draw.text((50, 78), was_brand, font=f_h, fill=INK)
    f_meta = font("regular", 18)
    draw.text((50, 152), f"${was_price} / {was_size} · 70-90% alcohol",
              font=f_meta, fill="#6b7280")

    # Arrow down divider
    f_arrow = font("bold", 36)
    draw.text((50, 200), "↓", font=f_arrow, fill=CORAL)

    # NOW SECTION
    f_eyebrow2 = font("bold", 16)
    draw.text((50, 264), "NOW WEARING", font=f_eyebrow2, fill=CORAL_DEEP)
    f_h2 = font("medium", 56)
    draw.text((50, 292), "Berry Obsessed", font=f_h2, fill=INK)
    draw.text((50, 366), "$22 / 100mL · 0% denatured alcohol",
              font=f_meta, fill=CORAL)

    # Bottle photo right side
    bottle = load("berry-hero.png")
    bh = 360
    bw = int(bottle.width * bh / bottle.height)
    bottle = bottle.resize((bw, bh))
    canvas.paste(bottle, (W - bw - 60, 200), bottle)

    # Big saved stat
    f_save_lbl = font("bold", 18)
    f_save_pct = font("bold", 130)
    f_save_sub = font("regular", 22)
    draw.text((50, 480), "SAVED PER BOTTLE", font=f_save_lbl, fill="#9CA3AF")
    draw.text((50, 510), f"${saved}", font=f_save_pct, fill=CORAL)
    draw.text((50, 660), persona, font=f_save_sub, fill="#4b5563")

    # Bottom stripe with breakdown
    rounded_rect(draw, [(40, 740), (W - 40, 880)], 16, "#FFE9F1")
    f_b = font("bold", 22)
    f_bs = font("regular", 16)
    bullets = [
        ("Same designer-grade scent profile.", "Strawberry / cream / vanilla — gourmand."),
        ("Skincare-first formula.", "HA + coconut + Vitamin E."),
        ("Hair-safe.", "Won't fry your strands."),
    ]
    by = 760
    for h_, s_ in bullets:
        draw.ellipse([(60, by + 6), (76, by + 22)], fill=CORAL)
        draw.text((90, by), h_, font=f_b, fill=INK)
        draw.text((90, by + 28), s_, font=f_bs, fill="#4b5563")
        by += 12

    f_brand = font("bold", 22)
    draw.text((50, H - 40), "everymood", font=f_brand, fill=INDIGO)
    canvas.save(out_path, quality=92)
    print("✓", os.path.relpath(out_path, ROOT))


# C5. HAIR-SAFE BEFORE/AFTER (illustrated)
def hair_safe_demo(out_path: str):
    W, H = 1300, 900
    canvas = Image.new("RGB", (W, H), CREAM)
    draw = ImageDraw.Draw(canvas)

    # Header
    f_h = font("medium", 50)
    draw.text((40, 50), "Your hair on perfume vs.", font=f_h, fill=INK)
    draw.text((40, 110), "your hair on EveryMood.", font=f_h, fill=CORAL)

    gap = 40
    cell_w = (W - gap - 80) // 2
    top_y = 220
    cell_h = H - top_y - 100

    def draw_strands(x0, y0, w, h, frizzy=False, color="#3D2818"):
        """Illustrate hair strands with optional frizz/split ends."""
        import random
        random.seed(7 if frizzy else 13)
        n = 18
        for i in range(n):
            sx = x0 + 30 + (i * (w - 60) // (n - 1))
            for branch in range(2 if not frizzy else 4):
                ex = sx + (random.randint(-30, 30) if frizzy else random.randint(-4, 4))
                wave = random.randint(-12, 12) if frizzy else 0
                draw.line([(sx, y0 + 20),
                           (sx + wave // 2, y0 + h // 3),
                           (ex + wave, y0 + 2 * h // 3),
                           (ex + (random.randint(-15, 15) if frizzy else random.randint(-2, 2)),
                            y0 + h - 20)],
                          fill=color, width=2 if frizzy else 3, joint='curve')
                if frizzy:
                    # split ends fork
                    draw.line([(ex + wave + random.randint(-4, 4), y0 + h - 30),
                               (ex + wave + random.randint(8, 20), y0 + h - 4)],
                              fill=color, width=1)
                    draw.line([(ex + wave + random.randint(-4, 4), y0 + h - 30),
                               (ex + wave + random.randint(-20, -8), y0 + h - 4)],
                              fill=color, width=1)

    # LEFT cell (perfume)
    lx, ly = 40, top_y
    draw.rectangle([(lx, ly), (lx + cell_w, ly + cell_h)], fill="#E8DFD9")
    draw_strands(lx, ly, cell_w, cell_h, frizzy=True)
    # label pill
    f_pill = font("bold", 26)
    pw = text_w(draw, "On perfume", f_pill) + 50
    rounded_rect(draw, [(lx + 30, ly + cell_h - 80), (lx + 30 + pw, ly + cell_h - 32)], 24, INK)
    draw.text((lx + 55, ly + cell_h - 71), "On perfume", font=f_pill, fill=CREAM)
    f_d = font("regular", 16)
    draw.text((lx + 30, ly + 30), "Split ends · brittle · color fade", font=f_d, fill="#4b5563")

    # RIGHT cell (everymood)
    rx, ry = lx + cell_w + gap, top_y
    draw.rectangle([(rx, ry), (rx + cell_w, ry + cell_h)], fill=PINK_BLUSH)
    draw_strands(rx, ry, cell_w, cell_h, frizzy=False, color="#2D1B0F")
    pw2 = text_w(draw, "On EveryMood", f_pill) + 50
    rounded_rect(draw, [(rx + 30, ry + cell_h - 80), (rx + 30 + pw2, ry + cell_h - 32)],
                 24, CORAL)
    draw.text((rx + 55, ry + cell_h - 71), "On EveryMood", font=f_pill, fill=WHITE)
    draw.text((rx + 30, ry + 30), "Smooth · nourished · safe to spritz", font=f_d, fill=CORAL_DEEP)

    f_foot = font("regular", 18)
    foot = "Vitamin E + Aloe nourish the cuticle while the scent locks in."
    fw = text_w(draw, foot, f_foot)
    draw.text((W // 2 - fw // 2, H - 60), foot, font=f_foot, fill="#6b7280")

    canvas.save(out_path, quality=92)
    print("✓", os.path.relpath(out_path, ROOT))


# C6. SCENT NOTES PYRAMID — standalone clean infographic
def scent_pyramid_standalone(out_path: str):
    W, H = 1080, 1080
    canvas = Image.new("RGB", (W, H), CREAM)
    draw = ImageDraw.Draw(canvas)
    f_eye = font("bold", 14)
    f_h = font("medium", 56)
    f_lbl = font("bold", 24)
    f_n = font("medium", 22)
    f_d = font("regular", 16)

    draw.text((50, 50), "FRAGRANCE PYRAMID", font=f_eye, fill="#9CA3AF")
    draw.text((50, 80), "How Berry Obsessed", font=f_h, fill=INK)
    draw.text((50, 138), "actually unfolds.", font=f_h, fill=CORAL)

    # Triangle pyramid centered
    cx = W // 2
    base_y = H - 160
    apex_y = 280
    base_half = 380
    pyr_h = base_y - apex_y

    # Three horizontal bands inside the pyramid
    bands = [
        (apex_y, apex_y + pyr_h // 3, "TOP", "First 5 min", "Wild strawberry · Citrus zest", PINK_PALE),
        (apex_y + pyr_h // 3, apex_y + 2 * pyr_h // 3, "HEART", "5 min → 1 hr", "Sweet cream · Pink peony", PINK),
        (apex_y + 2 * pyr_h // 3, base_y, "BASE", "1 hr → 12 hr", "Vanilla · Soft musk", CORAL),
    ]
    # Draw the pyramid by filling triangle band by band
    for y0, y1, label, time_, notes, color in bands:
        # band trapezoid
        t0 = (y0 - apex_y) / pyr_h  # 0..1
        t1 = (y1 - apex_y) / pyr_h
        x0_l = cx - int(base_half * t0)
        x0_r = cx + int(base_half * t0)
        x1_l = cx - int(base_half * t1)
        x1_r = cx + int(base_half * t1)
        draw.polygon([(x0_l, y0), (x0_r, y0), (x1_r, y1), (x1_l, y1)], fill=color)
        # text inside
        cy_b = (y0 + y1) // 2
        f_inner = font("bold", 28)
        f_inner_t = font("regular", 16)
        f_inner_n = font("medium", 18)
        lw = text_w(draw, label, f_inner)
        draw.text((cx - lw // 2, cy_b - 30), label, font=f_inner,
                  fill=INK if color == PINK_PALE else WHITE)
        tw = text_w(draw, time_, f_inner_t)
        draw.text((cx - tw // 2, cy_b + 4), time_, font=f_inner_t,
                  fill=(0,0,0,180) if color == PINK_PALE else (255,255,255,200))
        nw = text_w(draw, notes, f_inner_n)
        draw.text((cx - nw // 2, cy_b + 28), notes, font=f_inner_n,
                  fill=INK if color == PINK_PALE else WHITE)

    # Brand mark
    f_mark = font("bold", 22)
    mw = text_w(draw, "everymood · Juicy & Vibrant Mood", f_mark)
    draw.text((W // 2 - mw // 2, H - 50), "everymood · Juicy & Vibrant Mood", font=f_mark, fill=INDIGO)

    canvas.save(out_path, quality=92)
    print("✓", os.path.relpath(out_path, ROOT))


# C7-C9. INGREDIENT HERO TRIO
def _ingredient_card(out_path, title, sub, big_stat, stat_label, accent_color, icon_draw_fn):
    W, H = 1080, 1080
    canvas = Image.new("RGB", (W, H), CREAM)
    draw = ImageDraw.Draw(canvas)
    f_eye = font("bold", 14)
    f_h = font("medium", 64)
    f_sub = font("regular", 22)
    f_pct = font("bold", 110)
    f_pct_lbl = font("medium", 22)
    f_brand = font("bold", 22)

    # accent block left half
    block = Image.new("RGB", (W // 2, H), accent_color)
    canvas.paste(block, (0, 0))

    draw.text((50, 60), "MADE WITH", font=f_eye, fill=(255,255,255,200))
    draw.text((50, 92), title, font=f_h, fill=WHITE)
    sub_lines = sub.split("\n")
    sy = 200
    for line in sub_lines:
        draw.text((50, sy), line, font=f_sub, fill=(255,255,255,230))
        sy += 32

    # icon on left lower
    icon_draw_fn(draw, 90, 460)

    # Right side: hero stat
    rx = W // 2 + 60
    draw.text((rx, 200), big_stat, font=f_pct, fill=accent_color)
    draw.text((rx, 340), stat_label, font=f_pct_lbl, fill=INK)

    # Right side bottom: 3 micro-bullets
    f_b = font("medium", 18)
    bullets = [
        "Replaces alcohol as the carrier",
        "Binds scent to moisture",
        "Plumps fine lines on contact",
    ]
    by = 480
    for b in bullets:
        draw.ellipse([(rx, by + 6), (rx + 14, by + 20)], fill=accent_color)
        draw.text((rx + 28, by), b, font=f_b, fill="#4b5563")
        by += 36

    # brand
    draw.text((50, H - 60), "everymood", font=f_brand, fill=WHITE)
    canvas.save(out_path, quality=92)
    print("✓", os.path.relpath(out_path, ROOT))


def ingredient_ha(out_path: str):
    def icon(draw, x, y):
        # water-drop cluster
        for cx, cy, sz in [(x + 60, y + 60, 90), (x + 150, y + 90, 60), (x + 30, y + 140, 50)]:
            draw.polygon([(cx, cy - sz), (cx - sz * 0.7, cy + sz * 0.4),
                          (cx, cy + sz * 0.7), (cx + sz * 0.7, cy + sz * 0.4)], fill=WHITE)
    _ingredient_card(out_path, "Hyaluronic Acid",
                     "The hydration molecule\nthat replaces alcohol\nas the scent carrier.",
                     "+137%", "moisture retained vs. perfume",
                     INDIGO, icon)


def ingredient_coconut(out_path: str):
    def icon(draw, x, y):
        # coconut: brown circle with spotted texture
        cx, cy = x + 100, y + 80
        draw.ellipse([(cx - 80, cy - 80), (cx + 80, cy + 80)], fill="#8B5A3C")
        draw.ellipse([(cx - 60, cy - 60), (cx + 60, cy + 60)], fill="#FFFAF0")
        # coconut "eyes"
        for ex, ey in [(cx - 25, cy - 15), (cx + 25, cy - 15), (cx, cy + 25)]:
            draw.ellipse([(ex - 8, ey - 8), (ex + 8, ey + 8)], fill="#5C3A24")
    _ingredient_card(out_path, "Coconut Extract",
                     "Cold-pressed lipid base.\nGentle hydration.\nNo greasy residue.",
                     "0%", "stripping (vs. ethanol carriers)",
                     CORAL, icon)


def ingredient_vitamin_e(out_path: str):
    def icon(draw, x, y):
        # E in a circle with sparkles
        cx, cy = x + 100, y + 80
        draw.ellipse([(cx - 80, cy - 80), (cx + 80, cy + 80)], fill=WHITE,
                     outline=PINK, width=4)
        f_e = font("bold", 96)
        ew = 32
        draw.text((cx - 28, cy - 60), "E", font=f_e, fill=PINK)
        # sparkles
        for sx, sy in [(cx + 70, cy - 60), (cx - 70, cy - 60), (cx + 70, cy + 60), (cx - 70, cy + 60)]:
            draw.polygon([(sx, sy - 10), (sx + 4, sy - 4), (sx + 10, sy),
                          (sx + 4, sy + 4), (sx, sy + 10), (sx - 4, sy + 4),
                          (sx - 10, sy), (sx - 4, sy - 4)], fill=LIME_ACCENT)
    _ingredient_card(out_path, "Vitamin E",
                     "Antioxidant + cuticle\nshield. Hair-safe.\nProtects, never strips.",
                     "3×", "less hair breakage",
                     PINK, icon)


# C10. FREE-FROM / MADE-WITH PANEL
def free_from_panel(out_path: str):
    W, H = 1080, 1080
    canvas = Image.new("RGB", (W, H), CREAM)
    draw = ImageDraw.Draw(canvas)
    f_h = font("medium", 56)
    f_eye = font("bold", 16)
    f_lbl = font("bold", 22)
    f_b = font("medium", 22)
    f_brand = font("bold", 22)

    draw.text((50, 50), "What's in.", font=f_h, fill=INK)
    draw.text((50, 116), "What's not.", font=f_h, fill=CORAL)

    # Left col: Made with
    lx = 60
    ly = 230
    draw.text((lx, ly), "MADE WITH", font=f_eye, fill=CORAL_DEEP)
    made = ["Hyaluronic Acid", "Coconut Extract", "Vitamin E", "Aloe Vera",
            "Strawberry Cream notes", "Plant glycerin", "Distilled water"]
    yy = ly + 36
    for item in made:
        # checkmark coral circle
        draw.ellipse([(lx, yy + 6), (lx + 24, yy + 30)], fill=CORAL)
        draw.text((lx + 6, yy + 5), "✓", font=font("bold", 18), fill=WHITE)
        draw.text((lx + 40, yy + 4), item, font=f_b, fill=INK)
        yy += 44

    # Right col: Free from
    rx = W // 2 + 30
    draw.text((rx, ly), "FREE FROM", font=f_eye, fill="#6b7280")
    free = ["Denatured alcohol", "Parabens", "Phthalates",
            "Sulfates", "Synthetic dyes", "Mineral oil", "Animal testing"]
    yy = ly + 36
    for item in free:
        # X mark grey circle
        draw.ellipse([(rx, yy + 6), (rx + 24, yy + 30)], fill="#D9CFCB")
        draw.text((rx + 7, yy + 5), "✗", font=font("bold", 18), fill="#6b7280")
        draw.text((rx + 40, yy + 4), item, font=f_b, fill="#4b5563")
        yy += 44

    # Footer band
    rounded_rect(draw, [(50, H - 180), (W - 50, H - 80)], 16, INDIGO)
    f_f = font("medium", 22)
    foot = "Vegan · Cruelty-free · Dermatologist tested · Made in small batches"
    fw = text_w(draw, foot, f_f)
    draw.text((W // 2 - fw // 2, H - 145), foot, font=f_f, fill=WHITE)

    draw.text((50, H - 50), "everymood", font=f_brand, fill=INDIGO)
    canvas.save(out_path, quality=92)
    print("✓", os.path.relpath(out_path, ROOT))


# C11. PRICING LADDER
def pricing_ladder(out_path: str):
    W, H = 1080, 1080
    canvas = Image.new("RGB", (W, H), CREAM)
    draw = ImageDraw.Draw(canvas)
    f_h = font("medium", 50)
    f_eye = font("bold", 14)
    f_brand = font("bold", 26)
    f_price = font("bold", 32)
    f_lbl = font("medium", 22)
    f_meta = font("regular", 14)

    draw.text((50, 50), "EVERYMOOD VS. THE LADDER", font=f_eye, fill="#9CA3AF")
    draw.text((50, 80), "The fragrance value", font=f_h, fill=INK)
    draw.text((50, 138), "ladder, end to end.", font=f_h, fill=CORAL)

    # Ladder rows
    rows = [
        ("Designer luxury",  148, 50,  "≈ $2.96/mL", "#A8966C"),
        ("Niche / indie",    98,  50,  "≈ $1.96/mL", "#C7B486"),
        ("Skincare-fragrance hybrid", 58, 100, "≈ $0.58/mL", "#D9CFCB"),
        ("Body mist (BBW tier)",      28, 240, "≈ $0.12/mL", "#E5DDD9"),
        ("EveryMood",                  22, 100, "≈ $0.22/mL", CORAL),
    ]
    rx0 = 80
    rx_max = W - 100
    bar_h = 64
    gap = 18
    by = 250
    max_price = 148
    for label, price, size, per_ml, color in rows:
        bar_len = int((rx_max - rx0) * (price / max_price))
        # background track
        draw.rectangle([(rx0, by), (rx_max, by + bar_h)], fill="#FFEEE0")
        # filled bar
        draw.rectangle([(rx0, by), (rx0 + bar_len, by + bar_h)], fill=color)
        # label inside
        is_em = label == "EveryMood"
        draw.text((rx0 + 14, by + 10), label, font=f_lbl,
                  fill=WHITE if is_em or color == "#A8966C" else INK)
        draw.text((rx0 + 14, by + 36), per_ml, font=f_meta,
                  fill=(255,255,255,200) if is_em or color == "#A8966C" else "#4b5563")
        # price right
        ptxt = f"${price} / {size}mL"
        pw = text_w(draw, ptxt, f_price)
        draw.text((rx_max - pw - 4, by + 12), ptxt, font=f_price,
                  fill=CORAL if is_em else INK)
        # arrow if EveryMood
        if is_em:
            ax = rx0 + bar_len + 8
            draw.polygon([(ax, by + bar_h // 2 - 8), (ax + 12, by + bar_h // 2),
                          (ax, by + bar_h // 2 + 8)], fill=CORAL)
            draw.text((ax + 18, by + bar_h // 2 - 12), "you are here", font=font("bold", 16),
                      fill=CORAL_DEEP)
        by += bar_h + gap

    # bottom note
    f_foot = font("regular", 16)
    foot = "Same designer-grade scent. None of the markup."
    fw = text_w(draw, foot, f_foot)
    draw.text((W // 2 - fw // 2, H - 90), foot, font=f_foot, fill="#6b7280")
    draw.text((50, H - 50), "everymood", font=f_brand, fill=INDIGO)
    canvas.save(out_path, quality=92)
    print("✓", os.path.relpath(out_path, ROOT))


# C12. COMPLIMENT WALL — high-density quote grid
def compliment_wall(out_path: str):
    W, H = 1080, 1080
    canvas = Image.new("RGB", (W, H), CREAM)
    draw = ImageDraw.Draw(canvas)
    f_h = font("medium", 50)
    f_brand = font("bold", 26)
    f_q = font("medium", 18)
    f_attr = font("regular", 13)

    draw.text((50, 50), "12,483 compliments", font=f_h, fill=INK)
    draw.text((50, 110), "and counting.", font=f_h, fill=CORAL)

    # Compliments grid (synthesized buyer voice — generic, not from any single review)
    comps = [
        ("Got 4 compliments at brunch.", "JESS T."),
        ("My boyfriend asked what I'm wearing.", "KATIE M."),
        ("8 hours later still smelling like dessert.", "ALEX P."),
        ("Smooth ends for the first time in years.", "MIRA S."),
        ("My skin feels like silk after.", "NORA W."),
        ("Coffee shop barista asked the brand.", "SAM L."),
        ("Replaced my $130 perfume.", "JOY T."),
        ("Lasted from gym to dinner.", "RIA K."),
        ("No more dry chest skin.", "DEV M."),
        ("My partner keeps stealing it.", "EM R."),
        ("Strangers stop me on the street.", "TAY P."),
        ("Made me feel put-together in 3 sec.", "BRI N."),
    ]
    cols = 3
    rows = 4
    pad = 30
    grid_top = 230
    cell_w = (W - pad * 2 - (cols - 1) * 14) // cols
    cell_h = (H - grid_top - 100 - (rows - 1) * 14) // rows
    for i, (q, n) in enumerate(comps):
        cx = i % cols
        cy = i // cols
        x = pad + cx * (cell_w + 14)
        y = grid_top + cy * (cell_h + 14)
        bg = [PINK_BLUSH, "#FFE3DC", "#FFF0F4", PINK_PALE][(cx + cy) % 4]
        rounded_rect(draw, [(x, y), (x + cell_w, y + cell_h)], 14, bg)
        # quote
        # line wrap manually
        words = q.split(" ")
        line = ""
        ty = y + 14
        for w in words:
            test = (line + " " + w).strip()
            if text_w(draw, test, f_q) > cell_w - 24:
                draw.text((x + 14, ty), line, font=f_q, fill=INK)
                ty += 22
                line = w
            else:
                line = test
        if line:
            draw.text((x + 14, ty), line, font=f_q, fill=INK)
        # attribution bottom
        draw.text((x + 14, y + cell_h - 22), n, font=f_attr, fill=CORAL_DEEP)

    draw.text((50, H - 50), "everymood", font=f_brand, fill=INDIGO)
    canvas.save(out_path, quality=92)
    print("✓", os.path.relpath(out_path, ROOT))


# C13. MOTHER'S DAY GIFT FRAME
def mothers_day_frame(out_path: str):
    W, H = 1080, 1080
    canvas = Image.new("RGB", (W, H), PINK_PALE)
    draw = ImageDraw.Draw(canvas)
    # Soft top gradient
    band = gradient_band_fast(W, H // 2, (255,255,255,80), (255,255,255,0))
    canvas_rgba = canvas.convert("RGBA")
    canvas_rgba.paste(band, (0, 0), band)
    canvas = canvas_rgba.convert("RGB")
    draw = ImageDraw.Draw(canvas)

    # Big bottle hero
    bottle = load("berry-frame276.png")
    bh = int(H * 0.55)
    bw = int(bottle.width * bh / bottle.height)
    bottle = bottle.resize((bw, bh))
    canvas.paste(bottle, ((W - bw) // 2, 280), bottle)

    # ribbon overlay decorative
    f_eye = font("bold", 16)
    draw.text((50, 50), "MOTHER'S DAY · LIMITED-TIME", font=f_eye, fill=CORAL_DEEP)
    f_h = font("medium", 64)
    draw.text((50, 80), "Mom doesn't want", font=f_h, fill=INK)
    draw.text((50, 148), "another candle.", font=f_h, fill=CORAL)
    f_sub = font("regular", 22)
    draw.text((50, 224), "Gift the scent that doubles as skincare.", font=f_sub, fill="#4b5563")

    # Bottom bar
    rounded_rect(draw, [(40, H - 200), (W - 40, H - 80)], 16, INDIGO)
    f_b = font("bold", 28)
    f_bs = font("regular", 18)
    label = "Order by Tue · Ships in time for May 11"
    lw = text_w(draw, label, f_b)
    draw.text((W // 2 - lw // 2, H - 180), label, font=f_b, fill=WHITE)
    sub2 = "Free gift wrap on 2x and 3x bundles"
    sw = text_w(draw, sub2, f_bs)
    draw.text((W // 2 - sw // 2, H - 130), sub2, font=f_bs, fill=(255,255,255,220))

    f_brand = font("bold", 22)
    draw.text((50, H - 50), "everymood", font=f_brand, fill=INDIGO)
    canvas.save(out_path, quality=92)
    print("✓", os.path.relpath(out_path, ROOT))


# C14. GIFT BUNDLE VISUAL
def gift_bundle_visual(out_path: str):
    W, H = 1080, 1080
    canvas = Image.new("RGB", (W, H), CREAM)
    draw = ImageDraw.Draw(canvas)
    f_eye = font("bold", 14)
    f_h = font("medium", 60)
    f_sub = font("regular", 22)
    f_brand = font("bold", 22)

    draw.text((50, 60), "THE 3-PACK GIFT SET", font=f_eye, fill=CORAL_DEEP)
    draw.text((50, 90), "One for you.", font=f_h, fill=INK)
    draw.text((50, 154), "Two for them.", font=f_h, fill=CORAL)

    # 3 bottles in a row
    bottle = load("berry-hero.png")
    bh = 380
    bw = int(bottle.width * bh / bottle.height)
    bottle = bottle.resize((bw, bh))
    spacing = 80
    total = bw * 3 + spacing * 2
    sx = (W - total) // 2
    by = 320
    for i in range(3):
        canvas.paste(bottle, (sx + i * (bw + spacing), by), bottle)
    # Ribbon decoration above bottles
    rounded_rect(draw, [(sx - 30, by + bh + 30), (sx + total + 30, by + bh + 80)], 24, CORAL)
    f_r = font("bold", 22)
    rt = "Comes with kraft box · ribbon · scent guide"
    rw = text_w(draw, rt, f_r)
    draw.text((W // 2 - rw // 2, by + bh + 42), rt, font=f_r, fill=WHITE)

    # Bottom: 3 bullets
    f_b = font("medium", 20)
    bullets = [
        "FREE shipping on 3x bundles",
        "FREE Mystery Mini included",
        "FREE digital scent guide",
    ]
    by2 = H - 180
    for i, b in enumerate(bullets):
        x = 80 + i * ((W - 160) // 3)
        draw.ellipse([(x, by2 + 6), (x + 16, by2 + 22)], fill=LIME_ACCENT)
        draw.text((x + 26, by2 + 4), b, font=f_b, fill=INK)

    draw.text((50, H - 50), "everymood", font=f_brand, fill=INDIGO)
    canvas.save(out_path, quality=92)
    print("✓", os.path.relpath(out_path, ROOT))


# C15. TSA / TRAVEL-FRIENDLY BADGE
def tsa_badge(out_path: str):
    W, H = 1080, 720
    canvas = Image.new("RGB", (W, H), CREAM)
    draw = ImageDraw.Draw(canvas)
    f_eye = font("bold", 14)
    f_h = font("medium", 56)
    f_brand = font("bold", 22)
    f_b = font("medium", 22)

    draw.text((50, 50), "100mL · TSA-FRIENDLY", font=f_eye, fill=CORAL_DEEP)
    draw.text((50, 80), "Travels everywhere.", font=f_h, fill=INK)
    draw.text((50, 148), "Smells like home.", font=f_h, fill=CORAL)

    # bottle on left lower
    bottle = load("berry-hero.png")
    bh = 320
    bw = int(bottle.width * bh / bottle.height)
    bottle = bottle.resize((bw, bh))
    canvas.paste(bottle, (80, H - bh - 60), bottle)

    # Right: 4 use cases
    rx = W // 2
    cases = [
        ("✈", "Carry-on approved"),
        ("🏨", "Refresh after the flight"),
        ("🏖", "Beach to dinner switch"),
        ("💼", "Toss in any tote"),
    ]
    f_em = font("regular", 32)
    cy = 240
    for emoji, txt in cases:
        draw.text((rx, cy), emoji, font=f_em, fill=INK)
        draw.text((rx + 60, cy + 6), txt, font=f_b, fill="#4b5563")
        cy += 56

    draw.text((50, H - 40), "everymood", font=f_brand, fill=INDIGO)
    canvas.save(out_path, quality=92)
    print("✓", os.path.relpath(out_path, ROOT))


if __name__ == "__main__":
    print("Generating EveryMood imagery → out/")
    # A-series — standalone composites
    stats_infographic(os.path.join(OUT, "01-stats-infographic.jpg"))
    mood_color_block(os.path.join(OUT, "02-adapts-to-mood.jpg"))
    before_after_frame(os.path.join(OUT, "03-before-after-hair.jpg"),
                       caption="Hair on traditional alcohol-based perfume vs. EveryMood")
    before_after_frame(os.path.join(OUT, "04-before-after-skin.jpg"),
                       label_pair=("Day 1", "Day 14"),
                       caption="Skin hydration on Day 1 vs. Day 14 of daily EveryMood use")
    loved_by_grid(os.path.join(OUT, "05-loved-by-grid.jpg"))
    comparison_shot(os.path.join(OUT, "06-comparison-shot.jpg"))
    mood_swatch_row(os.path.join(OUT, "07-mood-swatches.jpg"))
    press_strip(os.path.join(OUT, "08-press-strip.jpg"))

    # B-series — overlays on real EveryMood gallery photos
    print("\n— Photo-overlay variations (frame189: lifestyle) —")
    lifestyle_v1_clean(os.path.join(OUT, "B1-lifestyle-clean.jpg"))
    lifestyle_v2_stat_overlay(os.path.join(OUT, "B2-lifestyle-stat.jpg"))
    lifestyle_v3_quote(os.path.join(OUT, "B3-lifestyle-quote.jpg"))

    print("\n— Photo-overlay variations (frame190: ingredients flatlay) —")
    ingredients_v1_callouts(os.path.join(OUT, "B4-ingredients-callouts.jpg"))
    ingredients_v2_zero_alcohol_badge(os.path.join(OUT, "B5-ingredients-zero-alcohol.jpg"))
    ingredients_v3_clean_label(os.path.join(OUT, "B6-ingredients-clean-label.jpg"))

    print("\n— Photo-overlay variations (frame276: strawberry hero) —")
    strawberry_v1_scent_pyramid(os.path.join(OUT, "B7-strawberry-pyramid.jpg"))
    strawberry_v2_dupe_callout(os.path.join(OUT, "B8-strawberry-dupe.jpg"))
    strawberry_v3_specs_strip(os.path.join(OUT, "B9-strawberry-specs.jpg"))

    print("\n— Photo-overlay variations (frame288: red drama) —")
    red_v1_hero_headline(os.path.join(OUT, "B10-red-headline.jpg"))
    red_v2_offer_badge(os.path.join(OUT, "B11-red-offer.jpg"))
    red_v3_review_quote(os.path.join(OUT, "B12-red-quote.jpg"))

    print("\n— Photo-overlay variations (frame193: clean bottle) —")
    clean_v1_specs(os.path.join(OUT, "B13-clean-specs.jpg"))
    clean_v2_compliment_promise(os.path.join(OUT, "B14-clean-guarantee.jpg"))

    print("\n— C-series — fragrance-specific conversion assets —")
    dupe_comparison(os.path.join(OUT, "C1-dupe-comparison.jpg"))
    day_to_night_timeline(os.path.join(OUT, "C2-day-to-night-timeline.jpg"))
    zero_alcohol_stamp(os.path.join(OUT, "C3-zero-alcohol-stamp.jpg"))
    switched_from_card(os.path.join(OUT, "C4-switched-from-designer.jpg"),
                       was_brand="Designer floral", was_price=148, saved=126)
    switched_from_card(os.path.join(OUT, "C4b-switched-from-niche.jpg"),
                       was_brand="Niche oud", was_price=98, saved=76,
                       persona="Switched after first sniff")
    hair_safe_demo(os.path.join(OUT, "C5-hair-safe-demo.jpg"))
    scent_pyramid_standalone(os.path.join(OUT, "C6-scent-pyramid.jpg"))
    ingredient_ha(os.path.join(OUT, "C7-ingredient-ha.jpg"))
    ingredient_coconut(os.path.join(OUT, "C8-ingredient-coconut.jpg"))
    ingredient_vitamin_e(os.path.join(OUT, "C9-ingredient-vitamin-e.jpg"))
    free_from_panel(os.path.join(OUT, "C10-free-from-panel.jpg"))
    pricing_ladder(os.path.join(OUT, "C11-pricing-ladder.jpg"))
    compliment_wall(os.path.join(OUT, "C12-compliment-wall.jpg"))
    mothers_day_frame(os.path.join(OUT, "C13-mothers-day.jpg"))
    gift_bundle_visual(os.path.join(OUT, "C14-gift-bundle.jpg"))
    tsa_badge(os.path.join(OUT, "C15-tsa-badge.jpg"))

    print("\nDone.")
