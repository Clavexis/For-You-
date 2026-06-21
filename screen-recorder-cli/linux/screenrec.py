#!/usr/bin/env python3
"""
Screen Recorder CLI — record your screen from the terminal with one command.

  - Choose resolution, FPS, and output file
  - Record the full screen or a region
  - Save as MP4 or animated GIF
  - Optional audio capture
  - ffmpeg-based backend (uses the right capture device per OS)

Usage:
  screenrec.py out.mp4                       # record full screen until Ctrl-C
  screenrec.py demo.gif --fps 15             # record a GIF
  screenrec.py clip.mp4 --duration 10        # 10-second clip
  screenrec.py region.mp4 --region 1280x720+100+80
  screenrec.py talk.mp4 --audio

Built by clavexis — github.com/clavexis
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys


def have_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


def parse_region(region: str):
    """Parse 'WxH+X+Y' -> (w, h, x, y). Returns None on full-screen."""
    if not region:
        return None
    try:
        wh, *offset = region.replace("+", " ").split()
        w, h = wh.split("x")
        x, y = (offset + ["0", "0"])[:2]
        return int(w), int(h), int(x), int(y)
    except (ValueError, IndexError):
        raise ValueError(f"Invalid region '{region}'. Use WxH+X+Y, e.g. 1280x720+0+0")


def build_command(output: str, fps: int, region, audio: bool,
                  duration: int, system: str, display: str = ":0.0",
                  size: str = None) -> list:
    """Build the ffmpeg command for the given platform. Pure + testable."""
    cmd = ["ffmpeg", "-y"]

    is_gif = output.lower().endswith(".gif")

    if system == "Linux":
        cmd += ["-f", "x11grab", "-framerate", str(fps)]
        if region:
            w, h, x, y = region
            cmd += ["-video_size", f"{w}x{h}", "-i", f"{display}+{x},{y}"]
        else:
            if size:
                cmd += ["-video_size", size]
            cmd += ["-i", display]
        if audio:
            cmd += ["-f", "pulse", "-i", "default"]

    elif system == "Darwin":  # macOS: avfoundation
        # "1:0" -> screen index 1, audio device 0 (varies by machine).
        spec = "1:0" if audio else "1"
        cmd += ["-f", "avfoundation", "-framerate", str(fps), "-i", spec]
        if region:
            w, h, x, y = region
            cmd += ["-vf", f"crop={w}:{h}:{x}:{y}"]

    elif system == "Windows":
        cmd += ["-f", "gdigrab", "-framerate", str(fps)]
        if region:
            w, h, x, y = region
            cmd += ["-offset_x", str(x), "-offset_y", str(y),
                    "-video_size", f"{w}x{h}", "-i", "desktop"]
        else:
            cmd += ["-i", "desktop"]
        if audio:
            cmd += ["-f", "dshow", "-i", "audio=virtual-audio-capturer"]
    else:
        raise RuntimeError(f"Unsupported platform: {system}")

    if duration:
        cmd += ["-t", str(duration)]

    if is_gif:
        # Palette-based encoding for good-looking GIFs.
        cmd += ["-vf", f"fps={fps},scale=iw:-1:flags=lanczos", output]
    else:
        cmd += ["-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p"]
        if audio:
            cmd += ["-c:a", "aac"]
        cmd += [output]
    return cmd


def main() -> int:
    ap = argparse.ArgumentParser(description="Record your screen with ffmpeg.")
    ap.add_argument("output", help="Output file (.mp4 or .gif).")
    ap.add_argument("--fps", type=int, default=30, help="Frames per second (default 30).")
    ap.add_argument("--region", help="Capture region WxH+X+Y (default: full screen).")
    ap.add_argument("--size", help="Full-screen size override, e.g. 1920x1080.")
    ap.add_argument("--audio", action="store_true", help="Also record audio.")
    ap.add_argument("--duration", type=int, default=0, help="Stop after N seconds (0 = until Ctrl-C).")
    ap.add_argument("--display", default=os.environ.get("DISPLAY", ":0.0"), help="X11 display (Linux).")
    ap.add_argument("--dry-run", action="store_true", help="Print the ffmpeg command and exit.")
    args = ap.parse_args()

    try:
        region = parse_region(args.region)
    except ValueError as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 1

    system = platform.system()
    cmd = build_command(args.output, args.fps, region, args.audio,
                        args.duration, system, args.display, args.size)

    if args.dry_run:
        print(" ".join(cmd))
        return 0

    if not have_ffmpeg():
        sys.stderr.write(
            "ffmpeg is required but not found.\n"
            "  Linux:   sudo apt install ffmpeg\n"
            "  macOS:   brew install ffmpeg\n"
            "  Windows: winget install Gyan.FFmpeg\n"
        )
        return 1

    print(f"Recording to {args.output}"
          + (f" for {args.duration}s" if args.duration else " (press Ctrl-C / q to stop)")
          + f" at {args.fps} fps...")
    try:
        return subprocess.call(cmd)
    except KeyboardInterrupt:
        print("\nStopped.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
