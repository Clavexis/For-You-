# Voice to Code

Speak your idea out loud — or pass an audio file, or just type it — and get complete, working code back, saved to a file.

## Demo

```text
$ voice-to-code --record 5 --lang python
Recording for 5s — speak now...
Done recording.
Transcribing with local Whisper...

Idea: make a command line tool that flips a coin a hundred times and counts heads

Generating Python code:
```python
import random
heads = sum(random.choice([0, 1]) for _ in range(100))
print(f"Heads: {heads}, Tails: {100 - heads}")
```
Run with: python generated.py

Saved code to generated.py
```

## Pipeline

1. **Capture** — record from the mic (`--record N`), use an audio file (`--audio f.wav`), or skip straight to text (`--text "..."`).
2. **Transcribe** — local [Whisper](https://github.com/openai/whisper) if installed (offline), otherwise the OpenAI Whisper API.
3. **Generate** — Claude turns the transcript into a complete program.
4. **Save** — code is written to a file with the right extension for the language.

## Features

- Three input modes (mic / audio file / text) — the `--text` mode needs **no audio dependencies**.
- Offline-first transcription (local Whisper) with an OpenAI API fallback.
- Target any language with `--lang` (Python, JS, C++, Go, Rust, …).
- Extracts the code from Claude's response and saves a clean source file.

## Installation

Requires **Python 3.10+** and an Anthropic API key.

### Linux
```bash
cd linux && ./install.sh
export ANTHROPIC_API_KEY=sk-ant-...
voice-to-code --text "a CLI to-do list" --lang python
```

### macOS (Apple Silicon & Intel)
```bash
cd mac && ./install.sh
export ANTHROPIC_API_KEY=sk-ant-...
voice-to-code --text "a CLI to-do list" --lang python
```

### Windows
```powershell
cd windows
install.bat
set ANTHROPIC_API_KEY=sk-ant-...
python voice_to_code.py --text "a CLI to-do list" --lang python
```

### Optional audio dependencies
For microphone recording and offline transcription:
```bash
pip install sounddevice numpy openai-whisper
```
For the OpenAI Whisper API path instead: `pip install openai` and `export OPENAI_API_KEY=sk-...`.

## Usage

```bash
voice-to-code --record 8 --lang javascript        # record 8s from the mic
voice-to-code --audio idea.wav --lang go           # transcribe a file
voice-to-code --text "binary search in C++" --lang c++ -o search.cpp
```

## Tech stack

- **Python 3** + [`anthropic`](https://pypi.org/project/anthropic/) SDK (`claude-opus-4-8`)
- Optional: `sounddevice` (recording), `openai-whisper` / OpenAI API (transcription)

---

Built by clavexis — [github.com/clavexis](https://github.com/clavexis)
