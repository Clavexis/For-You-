#!/usr/bin/env python3
"""
Warzone Clip Auto-Highlighter — find the best moments in a gameplay recording
and export a highlight reel.

How it works:
  - Measures audio loudness across the video (gunfire, explosions, and callouts
    spike the volume — a strong proxy for action).
  - Finds the loudest peaks, merges nearby ones into highlight windows.
  - Cuts a clip around each highlight and concatenates them into a reel.
  - Optionally bolts on an intro/outro clip.

ffmpeg does the heavy lifting (audio analysis + cutting + concat).

Usage:
  highlighter.py gameplay.mp4 -o highlights.mp4
  highlighter.py gameplay.mp4 --clips 8 --pad 4 --intro intro.mp4
  highlighter.py gameplay.mp4 --dry-run

Built by clavexis — github.com/clavexis
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile


def have_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


# ---------------------------------------------------------------------------
# Pure logic (unit-testable).
# ---------------------------------------------------------------------------
def find_highlights(loudness, window_sec, top_n, pad, video_len, min_gap=8.0):
    """Given per-window loudness values, return merged highlight (start, end) ranges.

    loudness: list of (time_sec, level) — higher level = louder = more action.
    Returns up to `top_n` ranges, each padded by `pad` seconds, non-overlapping.
    """
    if not loudness:
        return []
    # Sort windows by loudness, take the loudest.
    ranked = sorted(loudness, key=lambda x: x[1], reverse=True)
    chosen_times = []
    for t, _level in ranked:
        # Skip if too close to an already-chosen moment.
        if all(abs(t - c) >= min_gap for c in chosen_times):
            chosen_times.append(t)
        if len(chosen_times) >= top_n:
            break

    chosen_times.sort()
    # Build padded ranges, clamped to the video.
    ranges = []
    for t in chosen_times:
        start = max(0.0, t - pad)
        end = min(video_len, t + pad)
        ranges.append((start, end))

    # Merge overlapping/adjacent ranges.
    merged = []
    for start, end in ranges:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def parse_loudness_log(text):
    """Parse ffmpeg ebur128 stderr lines into (time_sec, momentary_loudness)."""
    out = []
    # Lines look like: [Parsed_ebur128 ...] t: 12.34  M: -18.2 S: ...
    for m in re.finditer(r"t:\s*([\d.]+)\s+M:\s*(-?[\d.]+|-?inf)", text):
        t = float(m.group(1))
        level_s = m.group(2)
        level = -120.0 if "inf" in level_s else float(level_s)
        out.append((t, level))
    return out


def build_concat_command(clip_files, output):
    """ffmpeg concat-demuxer command. clip_files: list of file paths."""
    # The list file is created by the caller; here we just build the command.
    return ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "LIST",
            "-c", "copy", output]


# ---------------------------------------------------------------------------
# ffmpeg operations.
# ---------------------------------------------------------------------------
def video_duration(path):
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", path])
    return float(out.strip())


def measure_loudness(path):
    """Run ffmpeg ebur128 over the audio and parse momentary loudness."""
    proc = subprocess.run(
        ["ffmpeg", "-i", path, "-af", "ebur128", "-f", "null", "-"],
        stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True)
    return parse_loudness_log(proc.stderr)


def cut_clip(src, start, end, dst):
    subprocess.run(
        ["ffmpeg", "-y", "-ss", f"{start:.2f}", "-to", f"{end:.2f}",
         "-i", src, "-c:v", "libx264", "-preset", "fast", "-c:a", "aac", dst],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


def concat_clips(clips, output, intro=None, outro=None):
    files = []
    if intro:
        files.append(intro)
    files += clips
    if outro:
        files.append(outro)
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as lf:
        for f in files:
            lf.write(f"file '{os.path.abspath(f)}'\n")
        list_path = lf.name
    cmd = build_concat_command(files, output)
    cmd[cmd.index("LIST")] = list_path
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    os.unlink(list_path)


def main() -> int:
    ap = argparse.ArgumentParser(description="Auto-generate a Warzone highlight reel.")
    ap.add_argument("video", help="Input gameplay video.")
    ap.add_argument("-o", "--output", default="highlights.mp4", help="Output reel.")
    ap.add_argument("--clips", type=int, default=6, help="Number of highlight moments.")
    ap.add_argument("--pad", type=float, default=4.0, help="Seconds of context around each peak.")
    ap.add_argument("--intro", help="Optional intro clip to prepend.")
    ap.add_argument("--outro", help="Optional outro clip to append.")
    ap.add_argument("--dry-run", action="store_true", help="Analyse and print highlights only.")
    args = ap.parse_args()

    if not os.path.isfile(args.video):
        sys.stderr.write(f"No such file: {args.video}\n")
        return 1
    if not have_ffmpeg():
        sys.stderr.write("ffmpeg and ffprobe are required.\n"
                         "  Linux: sudo apt install ffmpeg | macOS: brew install ffmpeg | "
                         "Windows: winget install Gyan.FFmpeg\n")
        return 1

    print("Analysing audio for high-action moments...")
    length = video_duration(args.video)
    loud = measure_loudness(args.video)
    highlights = find_highlights(loud, 1.0, args.clips, args.pad, length)

    if not highlights:
        sys.stderr.write("No clear highlights found (is there audio?).\n")
        return 1

    print(f"Found {len(highlights)} highlight window(s):")
    for i, (s, e) in enumerate(highlights, 1):
        print(f"  {i}. {s:6.1f}s - {e:6.1f}s  ({e-s:.1f}s)")

    if args.dry_run:
        return 0

    tmpdir = tempfile.mkdtemp(prefix="wz_highlights_")
    clips = []
    for i, (s, e) in enumerate(highlights):
        clip = os.path.join(tmpdir, f"clip_{i:02d}.mp4")
        print(f"  cutting clip {i+1}/{len(highlights)}...")
        cut_clip(args.video, s, e, clip)
        clips.append(clip)

    print("Stitching the reel...")
    concat_clips(clips, args.output, args.intro, args.outro)
    shutil.rmtree(tmpdir, ignore_errors=True)
    print(f"Done -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
