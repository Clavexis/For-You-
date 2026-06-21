# Discord AI Bot

A full-featured Discord bot powered by Claude — chat, code review, web summaries, image generation, and word moderation, all configurable per server.

## Demo

```text
@clawbot what's the time complexity of quicksort?
clawbot: Average case O(n log n), worst case O(n²) when the pivot is poorly chosen...

/review code: def add(a,b): return a-b
clawbot: ⚠️ Line 1 — the function is named `add` but subtracts. Likely a bug...

/imagine prompt: a neon city at dusk, synthwave
clawbot: https://...generated-image.png
```

## Features

- **Chat** — mention the bot (or DM it) to talk to Claude, with short per-channel memory.
- **`/ask`** — ask Claude anything.
- **`/review`** — get an AI code review.
- **`/summarise <url>`** — fetch a web page and summarise it.
- **`/imagine <prompt>`** — generate an image with OpenAI DALL-E.
- **Moderation** — auto-deletes messages containing banned words (whole-word, case-insensitive).
- **`/ban_word`** — add a banned word, stored **per server**.

## Installation

Requires **Python 3.10+**. You need a [Discord bot token](https://discord.com/developers/applications) and an Anthropic API key. (An OpenAI key is optional, for `/imagine`.)

### Linux
```bash
cd linux && ./install.sh
cp config.json.example config.json   # fill in your tokens
python3 bot.py
```

### macOS (Apple Silicon & Intel)
```bash
cd mac && ./install.sh
cp config.json.example config.json
python3 bot.py
```

### Windows
```powershell
cd windows
install.bat
copy config.json.example config.json
python bot.py
```

## Configuration

Either set environment variables (`DISCORD_TOKEN`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`) or fill in `config.json`:

```json
{
  "discord_token": "YOUR_DISCORD_BOT_TOKEN",
  "anthropic_api_key": "sk-ant-...",
  "openai_api_key": "sk-... (optional)"
}
```

Enable the **Message Content Intent** for your bot in the Discord developer portal so it can read messages for chat and moderation.

## Running as a service

A `systemd` unit is provided (`linux/clawbot.service`):
```bash
sudo cp linux/clawbot.service /etc/systemd/system/
sudo systemctl enable --now clawbot
```
On any platform you can also use a process manager (pm2, supervisor) pointed at `python bot.py`.

## Tech stack

- **Python 3** + [`discord.py`](https://pypi.org/project/discord.py/) 2.x (slash commands via `app_commands`)
- [`anthropic`](https://pypi.org/project/anthropic/) SDK (`claude-opus-4-8`) for chat / review / summaries
- Optional `openai` for DALL-E image generation
- Per-server config persisted to `guild_config.json`

---

Built by clavexis — [github.com/clavexis](https://github.com/clavexis)
