#!/usr/bin/env python3
"""
Voice to Code — speak an idea, get working code back.

Pipeline:
  1. Capture speech  — record from the microphone, or pass an existing audio
     file with --audio, or skip straight to text with --text "your idea".
  2. Transcribe      — using a local Whisper model if `openai-whisper` is
     installed, otherwise the OpenAI Whisper API (needs OPENAI_API_KEY).
  3. Generate code   — Claude turns the transcript into a complete program.
  4. Save            — write the code to a file (extension inferred from the
     requested language).

Heavy dependencies (sounddevice, whisper) are optional and only needed for the
record/transcribe steps. `--text` works with just the `anthropic` package.

Built by clavexis — github.com/clavexis
"""

import argparse
import os
import re
import sys
import tempfile
import wave
from pathlib import Path

try:
    import anthropic
except ImportError:
    sys.stderr.write("Error: 'anthropic' is required.  pip install anthropic\n")
    sys.exit(1)

DEFAULT_MODEL = "claude-opus-4-8"
SAMPLE_RATE = 16000

LANG_EXT = {
    "python": ".py", "javascript": ".js", "typescript": ".ts", "java": ".java",
    "c": ".c", "c++": ".cpp", "cpp": ".cpp", "go": ".go", "rust": ".rs",
    "ruby": ".rb", "php": ".php", "bash": ".sh", "shell": ".sh", "html": ".html",
    "c#": ".cs", "csharp": ".cs", "swift": ".swift", "kotlin": ".kt",
}


class C:
    RESET = "\033[0m"; BOLD = "\033[1m"; DIM = "\033[2m"
    CYAN = "\033[36m"; GREEN = "\033[32m"; YELLOW = "\033[33m"; RED = "\033[31m"

    @classmethod
    def off(cls):
        for n in ("RESET", "BOLD", "DIM", "CYAN", "GREEN", "YELLOW", "RED"):
            setattr(cls, n, "")


if not sys.stdout.isatty() or os.environ.get("NO_COLOR"):
    C.off()


# ---------------------------------------------------------------------------
# 1. Recording (optional — needs sounddevice + numpy).
# ---------------------------------------------------------------------------
def record_audio(seconds: int) -> str:
    try:
        import sounddevice as sd
        import numpy as np
    except ImportError as exc:
        raise RuntimeError(
            "Recording needs extra packages:  pip install sounddevice numpy\n"
            "Or supply audio with --audio file.wav, or skip with --text."
        ) from exc

    print(f"{C.YELLOW}Recording for {seconds}s — speak now...{C.RESET}")
    frames = sd.rec(int(seconds * SAMPLE_RATE), samplerate=SAMPLE_RATE,
                    channels=1, dtype="int16")
    sd.wait()
    print(f"{C.GREEN}Done recording.{C.RESET}")

    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    with wave.open(tmp.name, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(frames.tobytes())
    return tmp.name


# ---------------------------------------------------------------------------
# 2. Transcription (local whisper preferred, OpenAI API fallback).
# ---------------------------------------------------------------------------
def transcribe(audio_path: str) -> str:
    # Try local whisper first (fully offline, no API key).
    try:
        import whisper  # type: ignore
        print(f"{C.DIM}Transcribing with local Whisper...{C.RESET}")
        model = whisper.load_model("base")
        result = model.transcribe(audio_path)
        return str(result.get("text", "")).strip()
    except ImportError:
        pass

    # Fall back to the OpenAI Whisper API.
    openai_key = os.environ.get("OPENAI_API_KEY")
    if not openai_key:
        raise RuntimeError(
            "No transcription backend available.\n"
            "  Option A (offline):  pip install openai-whisper\n"
            "  Option B (API):      export OPENAI_API_KEY=sk-...\n"
            "Or skip transcription entirely with --text \"your idea\"."
        )
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("OpenAI API path needs:  pip install openai") from exc

    print(f"{C.DIM}Transcribing with OpenAI Whisper API...{C.RESET}")
    client = OpenAI(api_key=openai_key)
    with open(audio_path, "rb") as fh:
        result = client.audio.transcriptions.create(model="whisper-1", file=fh)
    return result.text.strip()


# ---------------------------------------------------------------------------
# 3. Code generation with Claude.
# ---------------------------------------------------------------------------
def generate_code(api_key: str, model: str, idea: str, language: str) -> str:
    client = anthropic.Anthropic(api_key=api_key)
    system = (
        "You are an expert programmer. The user describes what they want in "
        "plain language (transcribed from speech, so it may be informal). "
        f"Write complete, working {language} code that fulfils the request. "
        "Output the code in a single fenced code block, with brief inline "
        "comments. After the code block, add one short line on how to run it."
    )
    chunks: list[str] = []
    with client.messages.stream(
        model=model, max_tokens=2500, system=system,
        messages=[{"role": "user", "content": idea}],
    ) as stream:
        for text in stream.text_stream:
            chunks.append(text)
            print(text, end="", flush=True)
    print()
    return "".join(chunks)


def extract_code_block(text: str) -> str:
    """Pull the first fenced code block out of the model's response."""
    m = re.search(r"```[a-zA-Z0-9+#]*\n(.*?)```", text, re.DOTALL)
    return m.group(1).rstrip() if m else text.strip()


def main() -> int:
    ap = argparse.ArgumentParser(description="Speak (or type) an idea, get code back.")
    src = ap.add_argument_group("input (choose one)")
    src.add_argument("--text", help="Skip audio; use this text as the idea.")
    src.add_argument("--audio", help="Path to an existing audio file to transcribe.")
    src.add_argument("--record", type=int, metavar="SECONDS",
                     help="Record from the microphone for N seconds.")
    ap.add_argument("--lang", default="Python", help="Target language (default: Python).")
    ap.add_argument("-m", "--model", default=DEFAULT_MODEL, help="Anthropic model ID.")
    ap.add_argument("-o", "--out", help="File to save the generated code to.")
    args = ap.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.stderr.write(f"{C.RED}Set ANTHROPIC_API_KEY first.{C.RESET}\n")
        return 1

    # Resolve the idea text.
    try:
        if args.text:
            idea = args.text
        elif args.audio:
            idea = transcribe(args.audio)
        elif args.record:
            wav = record_audio(args.record)
            idea = transcribe(wav)
        else:
            sys.stderr.write(f"{C.RED}Provide --text, --audio, or --record.{C.RESET}\n")
            return 1
    except (RuntimeError, OSError) as exc:
        sys.stderr.write(f"{C.RED}{exc}{C.RESET}\n")
        return 1

    if not idea.strip():
        sys.stderr.write(f"{C.RED}Empty transcript — nothing to build.{C.RESET}\n")
        return 1

    print(f"{C.CYAN}{C.BOLD}Idea:{C.RESET} {idea}\n")
    print(f"{C.CYAN}{C.BOLD}Generating {args.lang} code:{C.RESET}\n")

    try:
        response = generate_code(api_key, args.model, idea, args.lang)
    except anthropic.APIStatusError as exc:
        sys.stderr.write(f"\n{C.RED}API error {exc.status_code}: {exc.message}{C.RESET}\n")
        return 1
    except anthropic.APIConnectionError as exc:
        sys.stderr.write(f"\n{C.RED}Connection error: {exc}{C.RESET}\n")
        return 1

    out = args.out
    if not out:
        ext = LANG_EXT.get(args.lang.lower(), ".txt")
        out = f"generated{ext}"
    code = extract_code_block(response)
    try:
        Path(out).write_text(code + "\n")
        print(f"\n{C.GREEN}Saved code to {out}{C.RESET}")
    except OSError as exc:
        sys.stderr.write(f"{C.RED}Could not save: {exc}{C.RESET}\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
