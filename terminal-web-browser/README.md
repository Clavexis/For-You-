# clawbrowse — a terminal web browser

Browse the web from your terminal. **clawbrowse** fetches pages over HTTP/HTTPS, renders the HTML as clean, readable text with light colour formatting, numbers every link so you can follow it by typing a number, and keeps a back/forward history and a bookmark list. Pure Python standard library — **no third-party dependencies**.

## Demo

```text
clawbrowse> o example.com

Example Domain
https://example.com/
────────────────────────────────────────────────────────
Example Domain

This domain is for use in illustrative examples in documents. You may
use this domain in literature without prior coordination or asking for
permission.

More information...[1]
────────────────────────────────────────────────────────
1 link(s). Type a number to follow, or 'help'.

clawbrowse> 1          # follows link [1]
```

## Features

- **Fetches HTTP & HTTPS** pages, follows redirects, respects the page charset.
- **Renders HTML to readable text** — headings, paragraphs, lists (bulleted *and* numbered), blockquotes, `<pre>` code blocks, bold/italic/code spans, and `[img: alt]` placeholders.
- **Numbered links** — every `<a>` becomes `text[N]`; type `N` to follow it. Relative links are resolved against the page URL.
- **Back / forward history** like a real browser (`b` / `f`).
- **Bookmarks** saved to `~/.config/clawbrowse/bookmarks.json`, openable by number.
- **Basic "CSS"**: ANSI colour for headings, links, code and quotes (auto-disabled when piped).
- **One-shot `--dump` mode** to render a page to stdout (great for scripts/pipes).
- **Skips `<script>` and `<style>`** so you get content, not code.
- **Offline self-test suite** (`--test`) covering the renderer end to end.

## Installation

Requires only **Python 3.6+** — nothing to `pip install`.

### Linux
```bash
cd linux && ./install.sh
clawbrowse https://example.com
```

### macOS (Apple Silicon & Intel)
```bash
cd mac && ./install.sh
clawbrowse https://example.com
```

### Windows
```powershell
cd windows
.\install.bat
python "%USERPROFILE%\bin\clawbrowse.py" https://example.com
```

Or run in place anywhere: `python3 clawbrowse.py https://example.com`.

## Usage

Start interactive, optionally at a page:
```bash
clawbrowse                       # blank prompt
clawbrowse https://example.com   # open and browse
```

Commands inside the browser:

| Command       | Action                                             |
|---------------|----------------------------------------------------|
| `<number>`    | follow link number N on the current page           |
| `o <url>`     | open a URL                                          |
| `b` / `f`     | go back / forward in history                       |
| `r`           | reload the current page                            |
| `links`       | list every link on the page                        |
| `book`        | bookmark the current page                          |
| `bookmarks`   | list bookmarks (open with `o <n>`)                 |
| `help`        | show command help                                  |
| `q`           | quit                                               |

One-shot render to stdout:
```bash
clawbrowse --dump https://example.com
clawbrowse --dump https://example.com | less -R
```

## How it works

```text
URL ──urllib──▶ HTML ──html.parser──▶ structural events
                                          │
   headings/lists/links/code  ──▶  text fragments + ANSI styling
                                          │
              collapse whitespace, wrap to terminal width
                                          │
                          rendered page + numbered link table
```

clawbrowse subclasses Python's built-in `html.parser.HTMLParser`. As the parser walks the document it emits text for content tags, records every `<a href>` into an indexed table, and applies ANSI styling based on tag type — a tiny stylesheet expressed in code. The output is then whitespace-collapsed and word-wrapped to your terminal width.

## Tech stack

- **Python 3** standard library only — `urllib` (fetch), `html.parser` (parse), `textwrap` (layout), `json` (bookmarks)
- ANSI escape codes for colour and formatting

---

Built by clavexis — [github.com/clavexis](https://github.com/clavexis)
