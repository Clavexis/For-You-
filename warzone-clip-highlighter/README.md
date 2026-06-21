# Warzone Clip Auto-Highlighter

Drop in a gameplay recording and get a highlight reel of the best moments — automatically detected from the audio (gunfire, explosions, and callouts spike the volume).

## Demo

```text
$ wz-highlight match.mp4 -o highlights.mp4
Analysing audio for high-action moments...
Found 6 highlight window(s):
  1.   42.3s -   50.3s  (8.0s)
  2.  118.7s -  126.7s  (8.0s)
  3.  205.1s -  213.1s  (8.0s)
  ...
  cutting clip 1/6...
Stitching the reel...
Done -> highlights.mp4
```

## How it works

```text
video ──▶ ffmpeg ebur128 (audio loudness over time)
       ──▶ find loudest moments, drop ones too close together
       ──▶ pad each into an 8s window, cut clips
       ──▶ concat into a reel (+ optional intro/outro)
```

Loud moments in Warzone almost always mean action — gunfights, kills, finishes — so audio energy is a cheap, effective highlight detector.

## Features

- **Automatic highlight detection** from audio energy (no manual scrubbing).
- **Tunable** — number of clips (`--clips`), context padding (`--pad`).
- **Merges nearby peaks** so a single fight isn't cut into pieces.
- **Intro / outro** clips (`--intro`, `--outro`).
- **`--dry-run`** to preview the detected moments before rendering.
- ffmpeg-based — fast cutting and stream-copy concatenation.

## Installation

Requires **Python 3.6+** and **ffmpeg** (with `ffprobe`).

| OS | Install ffmpeg |
|----|----------------|
| Linux | `sudo apt install ffmpeg` |
| macOS | `brew install ffmpeg` |
| Windows | `winget install Gyan.FFmpeg` |

### Linux
```bash
cd linux && ./install.sh
wz-highlight gameplay.mp4 -o highlights.mp4
```

### macOS (Apple Silicon & Intel)
```bash
cd mac && ./install.sh
wz-highlight gameplay.mp4 -o highlights.mp4
```

### Windows
```powershell
cd windows
python highlighter.py gameplay.mp4 -o highlights.mp4
```

## Usage

```bash
wz-highlight match.mp4                       # 6 highlights -> highlights.mp4
wz-highlight match.mp4 --clips 10 --pad 5    # 10 longer clips
wz-highlight match.mp4 --intro intro.mp4 --outro outro.mp4
wz-highlight match.mp4 --dry-run             # just show detected moments
```

## Tech stack

- **Python 3** standard library — peak detection, clip planning
- **ffmpeg / ffprobe** — `ebur128` loudness analysis, cutting, concat

---

Built by clavexis — [github.com/clavexis](https://github.com/clavexis)
