# AI Code Autocomplete — Local & Offline

Inline code suggestions powered by a **local** LLM (via Ollama). No internet, no cloud, **no data ever leaves your machine**. A small Python bridge connects VS Code to a local model.

## Demo

```python
def fibonacci(n):
    if n < 2:
        return n
    return ▏        # ← grey suggestion: fibonacci(n-1) + fibonacci(n-2)  [Tab to accept]
```

## Architecture

```text
VS Code extension ──HTTP──▶ server.py (bridge) ──▶ Ollama (local LLM)
   (inline suggestions)      (FIM prompt)            qwen2.5-coder, etc.
```

The extension sends the text around your cursor to a local bridge; the bridge wraps it in a fill-in-the-middle prompt and asks your local model. Everything stays on `localhost`.

## Features

- **100% offline** — runs on Ollama / llama.cpp locally; nothing is sent to a server.
- **Fill-in-the-middle** completions that respect the code *after* the cursor too.
- **Tab to accept** (VS Code's native inline suggestions).
- **Multi-language** — Python, JavaScript, TypeScript, C, C++ (configurable).
- **Configurable** model, endpoint, languages, and debounce.

## Setup

Requires **Python 3.6+**, **VS Code**, and **[Ollama](https://ollama.com)**.

### 1. Install Ollama and a code model
```bash
# Linux:   curl -fsSL https://ollama.com/install.sh | sh
# macOS:   brew install ollama   (or download from ollama.com)
# Windows: download from https://ollama.com/download
ollama pull qwen2.5-coder:1.5b      # a small, fast code model
```

### 2. Run the bridge
```bash
cd linux        # or mac / windows
python3 server.py --model qwen2.5-coder:1.5b
# -> Local autocomplete bridge on http://127.0.0.1:11500
```

### 3. Install the VS Code extension
The extension lives in `linux/extension` (identical in `mac/` and `windows/`).
```bash
cd linux/extension
# Option A — load it directly: open this folder in VS Code and press F5 (Extension Dev Host).
# Option B — package and install:
npm install -g @vscode/vsce
vsce package
code --install-extension local-ai-autocomplete-1.0.0.vsix
```

Then just start typing — grey inline suggestions appear; press **Tab** to accept.

## Configuration (VS Code settings)

| Setting | Default | Meaning |
|---------|---------|---------|
| `localAiAutocomplete.endpoint` | `http://127.0.0.1:11500/complete` | Bridge URL |
| `localAiAutocomplete.languages` | `["python","javascript","typescript","cpp","c"]` | Where it's active |
| `localAiAutocomplete.debounceMs` | `300` | Delay before requesting |

## API

The bridge exposes a simple HTTP API you can use from any editor:
```bash
curl http://127.0.0.1:11500/health
curl -X POST http://127.0.0.1:11500/complete \
  -d '{"prefix":"def add(a,b):\n    return ","suffix":"","language":"python"}'
# -> {"completion": "a + b"}
```

## Tech stack

- **Python 3** standard-library HTTP bridge (FIM prompting, Ollama API)
- **JavaScript** VS Code extension (Inline Completion API)
- Local LLM via **Ollama** (e.g. `qwen2.5-coder`) — fully offline

---

Built by clavexis — [github.com/clavexis](https://github.com/clavexis)
