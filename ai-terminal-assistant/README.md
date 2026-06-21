# AI Terminal Assistant

Chat with Claude (Anthropic's LLM) directly from your shell — with streaming responses, memory, and colour.

## Demo

```text
AI Terminal Assistant (model: claude-opus-4-8)
Type your message and press Enter. Commands: /reset, /exit (or Ctrl-D).

You: explain a closure in one sentence
Claude: A closure is a function that remembers the variables from the scope
where it was created, even after that scope has finished executing.

You: now show me one in Python
Claude: def make_counter():
            count = 0
            def increment():
                nonlocal count
                count += 1
                return count
            return increment   # `increment` closes over `count`
```

## Features

- **Streaming responses** — tokens appear in real time, no waiting for the full reply.
- **Conversation memory** — the assistant remembers context for the whole session.
- **System prompts** — steer behaviour with `--system "You are a terse Rust expert"`.
- **Coloured output** — clear, readable formatting (auto-disabled when piped or `NO_COLOR` is set).
- **One-shot & piped modes** — `ai-assistant "question"` or `echo "data" | ai-assistant "summarise"`.
- **Config file** — store your API key once in `~/.config/ai-terminal-assistant/config.json` (chmod 600).

## Installation

You need **Python 3.10+** and an Anthropic API key ([get one here](https://console.anthropic.com/)).

### Linux

```bash
cd linux
./install.sh
ai-assistant --set-key sk-ant-...
```

### macOS (Apple Silicon & Intel)

```bash
cd mac
./install.sh        # uses Homebrew Python if present
ai-assistant --set-key sk-ant-...
```

### Windows

```powershell
cd windows
install.bat
python assistant.py --set-key sk-ant-...
```

Alternatively, on any platform: `pip install -r requirements.txt` then `python assistant.py`.

## Usage

```bash
# Interactive chat (remembers context)
ai-assistant

# One-shot question
ai-assistant "What's the difference between TCP and UDP?"

# With a system prompt
ai-assistant --system "Answer only in haiku" "Describe the ocean"

# Pick a different model / token limit
ai-assistant -m claude-sonnet-4-6 --max-tokens 1024 "Hello"

# Pipe data in
git diff | ai-assistant "Write a commit message for this diff"
```

Inside interactive mode: `/reset` clears history, `/exit` quits.

The API key is read from `ANTHROPIC_API_KEY` (environment) or the config file — the environment variable wins.

## Tech stack

- **Python 3** + the official [`anthropic`](https://pypi.org/project/anthropic/) SDK
- ANSI escape codes for colour (no extra dependencies)
- Model: `claude-opus-4-8` (configurable)

---

Built by clavexis — [github.com/clavexis](https://github.com/clavexis)
