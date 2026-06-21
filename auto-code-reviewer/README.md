# Auto Code Reviewer

Point it at a file (or pipe code in) and get a full AI code review — bugs, security, performance, and style — with line references and diff-style fixes.

## Demo

```text
── Reviewing payment.py (Python) ──

## Summary
Solid structure, but one critical rounding bug and a missing input check.

## Critical
- **Line 42:** Float arithmetic on currency loses precision.
  ```diff
  - total = price * 1.0825
  + total = (Decimal(price) * Decimal("1.0825")).quantize(Decimal("0.01"))
  ```

## Warnings
- **Line 17:** `user_id` is used in an f-string SQL query → SQL injection risk.

## Suggestions
- **Line 8:** Rename `d` to `discount` for readability.
```

## Features

- **Flexible input** — a file path, multiple files / globs, or code piped on stdin.
- **Four review dimensions** — correctness/bugs, security, performance, style.
- **Line-referenced findings** grouped by severity (Critical / Warnings / Suggestions).
- **Diff-style fixes** in fenced ```diff blocks where useful.
- **Auto language detection** for Python, JS/TS, C/C++, Java, Go, Rust, Ruby, PHP, C#, and more (`--lang` to override).
- **Focus mode** — `--focus security` to bias the review.
- **Save reports** — append Markdown reviews to a file with `--save`.

## Installation

Requires **Python 3.10+** and an Anthropic API key ([get one](https://console.anthropic.com/)).

### Linux
```bash
cd linux && ./install.sh
export ANTHROPIC_API_KEY=sk-ant-...
code-review yourfile.py
```

### macOS (Apple Silicon & Intel)
```bash
cd mac && ./install.sh
export ANTHROPIC_API_KEY=sk-ant-...
code-review yourfile.py
```

### Windows
```powershell
cd windows
install.bat
set ANTHROPIC_API_KEY=sk-ant-...
python review.py yourfile.py
```

## Usage

```bash
# Review a single file
code-review app.py

# Review several files
code-review src/handler.js src/db.js

# Pipe code in and name the language
cat snippet.cpp | code-review --lang "C++"

# Focus the review and save it
code-review auth.py --focus security --save review.md
```

## Tech stack

- **Python 3** + the official [`anthropic`](https://pypi.org/project/anthropic/) SDK
- Streaming output, model `claude-opus-4-8`
- Line-numbered prompting so findings cite exact lines

---

Built by clavexis — [github.com/clavexis](https://github.com/clavexis)
