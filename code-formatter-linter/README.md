# clawfmt — code formatter & linter

A **language-agnostic** code formatter and style linter. It checks (and optionally fixes) the whitespace and style problems that plague every codebase — trailing whitespace, tabs vs spaces, missing final newlines, runaway blank lines, over-long lines, CRLF endings — across **Python, JavaScript, C/C++, Go** and any other text source. Rules are configurable via JSON, it has an auto-fix mode, and it returns **CI-friendly exit codes**. Pure Python standard library, **no dependencies**.

## Demo

```text
$ clawfmt check src/messy.py
src/messy.py
  src/messy.py:1   TRAIL     trailing whitespace
  src/messy.py:2   TABIND    tab used for indentation (expected spaces)
  src/messy.py:3   BLANKS    4 consecutive blank lines (max 2)
  src/messy.py:10  EOFBLANK  2 blank line(s) at end of file

4 issue(s) found.      # exit code 1 — fails CI

$ clawfmt fix src/messy.py
fixed src/messy.py

1 file(s) changed.

$ clawfmt check src/messy.py
All clean.             # exit code 0
```

## Features

- **One tool, many languages** — picks sensible defaults per file extension (`.py` → 88 cols, `.js`/`.ts` → 2-space indent, `.go` → tabs, `.md` → no line limit, …).
- **Checks**: trailing whitespace, tab/space indentation mismatches, lines over the column limit, too many consecutive blank lines, trailing blank lines, missing final newline, non-LF line endings.
- **Auto-fix** (`fix`) rewrites files; **`diff`** shows the changes without touching disk.
- **Configurable** via a `.clawfmt.json` discovered by walking up the tree, or `--config PATH`. Top-level options plus per-extension overrides.
- **CI-friendly**: `check` and `diff` exit non-zero when there's anything to fix, so they drop straight into a pipeline.
- **Idempotent** — running `fix` twice produces the same result.
- **Reports with `file:line` and a short rule code** for every issue.
- **Recurses directories** (skipping `.git`) and ignores binary/unreadable files.
- **Offline self-test suite** (`clawfmt test`).

## Installation

Requires only **Python 3.6+** — nothing to install.

### Linux
```bash
cd linux && ./install.sh
clawfmt test
```

### macOS (Apple Silicon & Intel)
```bash
cd mac && ./install.sh
clawfmt test
```

### Windows
```powershell
cd windows
.\install.bat
python "%USERPROFILE%\bin\clawfmt.py" test
```

Or run in place: `python3 clawfmt.py check .`

## Usage

```bash
clawfmt check file.py src/ docs/      # report issues (exit 1 if any)
clawfmt diff  file.py                 # preview fixes as a coloured diff
clawfmt fix   src/                    # rewrite files in place
clawfmt --config team.json check .    # use a specific config
```

### Configuration (`.clawfmt.json`)

```json
{
  "max_line_length": 100,
  "indent_size": 4,
  "use_tabs": false,
  "max_blank_lines": 2,
  "trim_trailing_whitespace": true,
  "insert_final_newline": true,
  "normalize_line_endings": true,
  "trim_trailing_blank_lines": true,

  ".py": { "max_line_length": 88 },
  ".js": { "indent_size": 2 }
}
```

Precedence (low → high): built-in defaults → per-extension language defaults → your `.clawfmt.json` top-level block → your per-extension block.

### Rule codes

| Code       | Meaning                                       |
|------------|-----------------------------------------------|
| `TRAIL`    | trailing whitespace on a line                 |
| `TABIND`   | tab used for indentation (spaces expected)    |
| `MIXIND`   | mixed tabs and spaces in indentation          |
| `LONG`     | line exceeds the column limit                 |
| `BLANKS`   | too many consecutive blank lines              |
| `EOFNL`    | no newline at end of file                     |
| `EOFBLANK` | blank line(s) at end of file                  |
| `CRLF`     | non-LF line endings                           |

## Tech stack

- **Python 3** standard library only — `argparse`, `json`, `difflib`, `os`
- A small rules engine: each rule is a pure function over the file text, so checking and fixing share the same logic

---

Built by clavexis — [github.com/clavexis](https://github.com/clavexis)
