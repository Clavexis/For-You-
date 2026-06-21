# AI Thumbnail Generator

Type a video title, get a ready-to-upload **1280×720 YouTube thumbnail** — with an AI-generated background (DALL-E) or a clean styled gradient that works fully offline.

## Demo

A title like *"10 Python Tricks You Didn't Know"* in the `tech` style produces:

```text
┌──────────────────────────────────────────┐
│                                          │
│        10 PYTHON TRICKS YOU              │  ← bold, outlined, auto-wrapped
│            DIDN'T KNOW                   │     white text on a blue gradient
│                                          │
│▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔│  ← cyan accent bar
└──────────────────────────────────────────┘
```

(See the generated PNG — high-contrast text with a black outline, readable on any background.)

## Features

- **1280×720 PNG** output — exactly YouTube's thumbnail spec.
- **AI backgrounds** via OpenAI DALL-E when `OPENAI_API_KEY` is set.
- **Offline gradient backgrounds** with a subtle glow — no API key needed, works out of the box.
- **Smart text overlay** — auto font-sizing, word wrap, bold outline for readability, accent bar.
- **Style presets:** `tech`, `gaming`, `minimal`, `warm`, `nature`.
- **Batch mode** — generate a folder of thumbnails from a list of titles.

## Installation

Requires **Python 3.8+** and **Pillow** (installed by the script). An OpenAI key is optional, for AI backgrounds.

### Linux
```bash
cd linux && ./install.sh
thumbgen "My Video Title" --style gaming
```

### macOS (Apple Silicon & Intel)
```bash
cd mac && ./install.sh
thumbgen "My Video Title" --style minimal
```

### Windows
```powershell
cd windows
install.bat
python thumbnail.py "My Video Title" --style tech
```

## Usage

```bash
# Single thumbnail
thumbgen "How to Build a Website" --style tech -o website.png

# Force the offline gradient (no API call)
thumbgen "My Gaming Highlights" --style gaming --no-ai

# Batch: one title per line -> thumbnails/thumb_01.png, thumb_02.png, ...
thumbgen --batch sample-titles.txt --style warm
```

### Enabling AI backgrounds
```bash
export OPENAI_API_KEY=sk-...
thumbgen "The Future of AI" --style tech     # DALL-E background + your title overlay
```
If the API call fails or no key is set, it falls back to the gradient automatically.

## Tech stack

- **Python 3** + **Pillow** (PIL) for image generation and text overlay
- Optional **OpenAI** SDK (DALL-E 3) for AI backgrounds

---

Built by clavexis — [github.com/clavexis](https://github.com/clavexis)
