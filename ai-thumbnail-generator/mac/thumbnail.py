#!/usr/bin/env python3
"""
AI Thumbnail Generator — turn a video title into a 1280x720 YouTube thumbnail.

  - Generates a background image:
      * with OpenAI DALL-E if OPENAI_API_KEY is set, OR
      * a styled gradient rendered locally with PIL (works fully offline).
  - Overlays the title text with a bold, high-contrast outline for readability.
  - Outputs a ready-to-upload 1280x720 PNG.
  - Batch mode: generate many thumbnails from a file of titles.

Usage:
  thumbnail.py "10 Python Tricks You Didn't Know" --style tech -o out.png
  thumbnail.py "My Gaming Highlights" --style gaming
  thumbnail.py --batch titles.txt --style minimal

Built by clavexis — github.com/clavexis
"""

import argparse
import os
import sys
import math
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
except ImportError:
    sys.stderr.write("Pillow is required.  pip install Pillow\n")
    sys.exit(1)

WIDTH, HEIGHT = 1280, 720

# Colour presets: (top gradient RGB, bottom gradient RGB, text RGB, accent RGB)
STYLES = {
    "tech":    ((20, 30, 60),   (10, 10, 25),   (255, 255, 255), (0, 200, 255)),
    "gaming":  ((90, 0, 90),    (20, 0, 40),    (255, 255, 255), (255, 60, 120)),
    "minimal": ((245, 245, 245),(220, 220, 220),(20, 20, 20),    (255, 90, 60)),
    "warm":    ((250, 180, 90), (200, 60, 40),  (255, 255, 255), (255, 230, 120)),
    "nature":  ((60, 140, 90),  (20, 60, 40),   (255, 255, 255), (200, 255, 150)),
}


def gradient_background(top, bottom) -> Image.Image:
    """Render a smooth vertical gradient with a subtle diagonal vignette."""
    img = Image.new("RGB", (WIDTH, HEIGHT))
    px = img.load()
    for y in range(HEIGHT):
        t = y / (HEIGHT - 1)
        r = int(top[0] + (bottom[0] - top[0]) * t)
        g = int(top[1] + (bottom[1] - top[1]) * t)
        b = int(top[2] + (bottom[2] - top[2]) * t)
        for x in range(WIDTH):
            px[x, y] = (r, g, b)
    # Soft accent glow in the top-left for visual interest.
    glow = Image.new("L", (WIDTH, HEIGHT), 0)
    gd = ImageDraw.Draw(glow)
    gd.ellipse([-200, -200, 500, 500], fill=90)
    glow = glow.filter(ImageFilter.GaussianBlur(120))
    accent = Image.new("RGB", (WIDTH, HEIGHT), (255, 255, 255))
    img = Image.composite(accent, img, glow.point(lambda v: int(v * 0.25)))
    return img


def ai_background(prompt: str) -> Image.Image:
    """Generate a background with DALL-E and resize to 1280x720."""
    from openai import OpenAI
    import urllib.request
    import io
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    result = client.images.generate(model="dall-e-3", prompt=prompt, n=1, size="1792x1024")
    url = result.data[0].url
    data = urllib.request.urlopen(url, timeout=30).read()
    img = Image.open(io.BytesIO(data)).convert("RGB")
    return img.resize((WIDTH, HEIGHT))


def load_font(size: int):
    """Try a few common bold fonts; fall back to PIL's default."""
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def wrap_text(draw, text, font, max_width):
    """Greedy word-wrap so the title fits the thumbnail width."""
    words = text.split()
    lines, line = [], ""
    for w in words:
        trial = (line + " " + w).strip()
        if draw.textlength(trial, font=font) <= max_width:
            line = trial
        else:
            if line:
                lines.append(line)
            line = w
    if line:
        lines.append(line)
    return lines


def draw_title(img, title, text_color, accent):
    draw = ImageDraw.Draw(img)
    # Pick a font size that fits in at most 4 lines.
    size = 110
    while size > 40:
        font = load_font(size)
        lines = wrap_text(draw, title.upper(), font, WIDTH - 160)
        if len(lines) <= 4:
            break
        size -= 10
    font = load_font(size)
    lines = wrap_text(draw, title.upper(), font, WIDTH - 160)

    # Vertically centre the block.
    line_h = size + 18
    total_h = line_h * len(lines)
    y = (HEIGHT - total_h) // 2

    for line in lines:
        w = draw.textlength(line, font=font)
        x = (WIDTH - w) // 2
        # Outline for readability against any background.
        draw.text((x, y), line, font=font, fill=text_color,
                  stroke_width=max(3, size // 20), stroke_fill=(0, 0, 0))
        y += line_h

    # Accent bar along the bottom.
    draw.rectangle([0, HEIGHT - 14, WIDTH, HEIGHT], fill=accent)


def make_thumbnail(title: str, style: str, out: str, use_ai: bool) -> str:
    top, bottom, text_color, accent = STYLES.get(style, STYLES["tech"])

    if use_ai and os.environ.get("OPENAI_API_KEY"):
        try:
            print(f"  generating AI background for '{title}'...")
            img = ai_background(f"YouTube thumbnail background, {style} style, "
                                f"theme: {title}, no text, vibrant, high contrast")
        except Exception as exc:  # noqa: BLE001 — fall back to a local gradient
            print(f"  AI background unavailable ({exc}); using gradient.")
            img = gradient_background(top, bottom)
    else:
        img = gradient_background(top, bottom)

    draw_title(img, title, text_color, accent)
    img.save(out, "PNG")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate a 1280x720 YouTube thumbnail.")
    ap.add_argument("title", nargs="?", help="Video title (text overlay).")
    ap.add_argument("--style", default="tech", choices=list(STYLES.keys()), help="Visual style.")
    ap.add_argument("-o", "--out", default="thumbnail.png", help="Output PNG path.")
    ap.add_argument("--batch", metavar="FILE", help="File with one title per line.")
    ap.add_argument("--no-ai", action="store_true", help="Force the local gradient background.")
    args = ap.parse_args()

    use_ai = not args.no_ai

    if args.batch:
        titles = [t.strip() for t in Path(args.batch).read_text().splitlines() if t.strip()]
        outdir = Path("thumbnails")
        outdir.mkdir(exist_ok=True)
        for i, title in enumerate(titles, 1):
            out = outdir / f"thumb_{i:02d}.png"
            make_thumbnail(title, args.style, str(out), use_ai)
            print(f"  saved {out}")
        print(f"Generated {len(titles)} thumbnails in {outdir}/")
        return 0

    if not args.title:
        sys.stderr.write("Provide a title, or use --batch FILE.\n")
        return 1

    out = make_thumbnail(args.title, args.style, args.out, use_ai)
    print(f"Saved {out} (1280x720)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
