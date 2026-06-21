# Warzone AI Coach

Analyse your Call of Duty: Warzone stats and get AI-powered, actionable improvement tips — right in your terminal.

## Demo

```text
============================================================
WARZONE AI COACH — REPORT
Generated 2026-06-20 19:24
============================================================

Stats provided:
  - kd: 0.74
  - win_rate: 1.8
  - accuracy: 16.5
  - weapons: ['MCW', 'Renetti']

Quick analysis:
  • Your K/D is below 0.8 — focus on survival: land in quieter POIs...
  • Low win rate — play the circle earlier and prioritise high ground...
  • Accuracy under 18% — tighten bursts at range, recoil drills help...

AI Coaching Report:
  Strengths: ...
  Weaknesses: ...
  3-step practice plan: ...
```

## Features

- **Two input modes** — answer interactive prompts, or pass a JSON stats file with `--stats`.
- **Offline heuristic coach** — sensible, specific tips with **no API key required**.
- **AI coaching layer** — when an Anthropic API key is present, Claude writes a tailored report (Strengths / Weaknesses / 3-step practice plan).
- **Analyses** K/D, win rate, accuracy, headshot %, average kills, and most-used weapons.
- **Save reports** to a text file with `--save report.txt`.
- **Optional Warzone API hook** — credentials read from config (the public API is unofficial; manual/JSON input is the recommended default).

## Installation

Requires **Python 3.10+**. The `anthropic` package is optional (only needed for the AI report).

### Linux
```bash
cd linux && ./install.sh
warzone-coach --stats sample-stats.json
```

### macOS (Apple Silicon & Intel)
```bash
cd mac && ./install.sh
warzone-coach --stats sample-stats.json
```

### Windows
```powershell
cd windows
install.bat
python coach.py --stats sample-stats.json
```

## Usage

```bash
# Interactive: answer a few prompts
warzone-coach

# From a JSON file (see sample-stats.json)
warzone-coach --stats my-stats.json

# Save the report
warzone-coach --stats my-stats.json --save coaching.txt

# Heuristics only (no API call)
warzone-coach --stats my-stats.json --no-ai
```

### Enabling AI coaching
Set your Anthropic API key (one of):
```bash
export ANTHROPIC_API_KEY=sk-ant-...
```
or add it to `~/.config/warzone-ai-coach/config.json`:
```json
{ "api_key": "sk-ant-..." }
```

### Stats file format
```json
{
  "kd": 0.74,
  "win_rate": 1.8,
  "accuracy": 16.5,
  "avg_kills": 3.1,
  "matches": 640,
  "headshot_pct": 12,
  "weapons": ["MCW", "Renetti"]
}
```

## Tech stack

- **Python 3** — heuristic analysis engine (no dependencies)
- Optional [`anthropic`](https://pypi.org/project/anthropic/) SDK + `claude-opus-4-8` for AI coaching
- JSON for stats input/config

---

Built by clavexis — [github.com/clavexis](https://github.com/clavexis)
