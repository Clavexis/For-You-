# Screen Recorder CLI

Record your screen from the terminal with one command — full screen or a region, to MP4 or animated GIF, with optional audio. An ffmpeg front-end that picks the right capture backend for your OS.

## Demo

```text
$ screenrec demo.mp4 --duration 10 --fps 30
Recording to demo.mp4 for 10s at 30 fps...

$ screenrec tutorial.gif --fps 15 --region 1280x720+0+0
Recording to tutorial.gif (press Ctrl-C / q to stop) at 15 fps...
```

## Features

- **One-command capture** — `screenrec out.mp4` and you're recording.
- **Full screen or a region** — `--region WxH+X+Y`.
- **MP4 or GIF** — chosen by the output extension; GIFs use lanczos scaling.
- **Configurable FPS** and a fixed `--duration` or record until Ctrl-C.
- **Optional audio** — `--audio`.
- **Per-OS backend** — Linux `x11grab`, macOS `avfoundation`, Windows `gdigrab`.
- **`--dry-run`** prints the exact ffmpeg command without recording.

## Installation

Requires **Python 3.6+** and **ffmpeg**.

| OS | Install ffmpeg |
|----|----------------|
| Linux | `sudo apt install ffmpeg` |
| macOS | `brew install ffmpeg` |
| Windows | `winget install Gyan.FFmpeg` |

### Linux
```bash
cd linux && ./install.sh
screenrec out.mp4 --duration 10
```

### macOS (Apple Silicon & Intel)
```bash
cd mac && ./install.sh
screenrec out.mp4 --duration 10
# Grant your terminal "Screen Recording" permission in System Settings → Privacy.
```

### Windows
```powershell
cd windows
python screenrec.py out.mp4 --duration 10
```

## Usage

```bash
screenrec out.mp4                          # full screen until Ctrl-C
screenrec clip.mp4 --duration 15 --fps 60  # 15-second 60fps clip
screenrec demo.gif --fps 15                # animated GIF
screenrec region.mp4 --region 1280x720+100+80   # a 1280x720 area at (100,80)
screenrec talk.mp4 --audio                 # with audio
screenrec out.mp4 --dry-run                # just print the ffmpeg command
```

## How it works

The tool builds the correct ffmpeg command for your platform — for example, on Linux:
```bash
ffmpeg -y -f x11grab -framerate 30 -video_size 1920x1080 -i :0.0 \
       -c:v libx264 -preset ultrafast -pix_fmt yuv420p out.mp4
```
Use `--dry-run` to see exactly what will run.

## Tech stack

- **Python 3** standard library (subprocess) wrapping **ffmpeg**
- Capture backends: `x11grab` (Linux), `avfoundation` (macOS), `gdigrab` (Windows)

---

Built by clavexis — [github.com/clavexis](https://github.com/clavexis)
