#!/usr/bin/env python3
"""
Discord AI Bot — a full-featured Discord bot powered by Claude.

Commands & behaviour:
  - Mention the bot (or DM it) to chat with Claude, with short per-channel memory.
  - /ask <prompt>        — ask Claude anything
  - /review <code>       — AI code review
  - /imagine <prompt>    — generate an image with OpenAI DALL-E
  - /summarise <url>     — fetch a page and summarise it
  - Moderation           — auto-delete messages containing banned words
  - Per-server config    — banned words & toggles stored per guild

Configuration (config.json or environment variables):
  {
    "discord_token": "...",      # or env DISCORD_TOKEN
    "anthropic_api_key": "...",  # or env ANTHROPIC_API_KEY
    "openai_api_key": "..."      # or env OPENAI_API_KEY  (for /imagine)
  }

Run as a service:  python bot.py   (see README for systemd / pm2 setup)

Built by clavexis — github.com/clavexis
"""

import json
import os
import re
import sys
from pathlib import Path

MODEL = "claude-opus-4-8"
CONFIG_FILE = Path(__file__).with_name("config.json")
GUILD_CONFIG_FILE = Path(__file__).with_name("guild_config.json")


# ---------------------------------------------------------------------------
# Pure helpers (unit-testable without a Discord connection).
# ---------------------------------------------------------------------------
def load_config() -> dict:
    cfg = {}
    if CONFIG_FILE.exists():
        try:
            cfg = json.loads(CONFIG_FILE.read_text())
        except json.JSONDecodeError:
            pass
    # Environment variables override the file.
    cfg.setdefault("discord_token", os.environ.get("DISCORD_TOKEN", cfg.get("discord_token", "")))
    cfg.setdefault("anthropic_api_key", os.environ.get("ANTHROPIC_API_KEY", cfg.get("anthropic_api_key", "")))
    cfg.setdefault("openai_api_key", os.environ.get("OPENAI_API_KEY", cfg.get("openai_api_key", "")))
    return cfg


def load_guild_config() -> dict:
    if GUILD_CONFIG_FILE.exists():
        try:
            return json.loads(GUILD_CONFIG_FILE.read_text())
        except json.JSONDecodeError:
            pass
    return {}


def save_guild_config(data: dict) -> None:
    GUILD_CONFIG_FILE.write_text(json.dumps(data, indent=2))


def banned_words_for(guild_cfg: dict, guild_id: str) -> list:
    return guild_cfg.get(str(guild_id), {}).get("banned_words", [])


def message_violates(content: str, banned_words: list) -> bool:
    """Return True if the message contains any banned word (whole-word, case-insensitive)."""
    if not banned_words:
        return False
    text = content.lower()
    for word in banned_words:
        if re.search(rf"\b{re.escape(word.lower())}\b", text):
            return True
    return False


def extract_text_from_html(html: str, limit: int = 6000) -> str:
    """Strip tags/scripts and collapse whitespace to get readable page text."""
    html = re.sub(r"(?is)<(script|style).*?</\1>", " ", html)
    text = re.sub(r"(?s)<[^>]+>", " ", html)
    text = re.sub(r"&[a-zA-Z#0-9]+;", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def chunk_message(text: str, size: int = 1900) -> list:
    """Split a long reply into Discord-sized chunks (2000-char limit)."""
    return [text[i:i + size] for i in range(0, len(text), size)] or [""]


# ---------------------------------------------------------------------------
# Bot wiring (requires discord.py + anthropic at runtime).
# ---------------------------------------------------------------------------
def run_bot():
    try:
        import discord
        from discord import app_commands
    except ImportError:
        sys.stderr.write(
            "discord.py is required to run the bot.\n"
            "Install it with:  pip install -U discord.py anthropic\n"
        )
        return 1

    try:
        import anthropic
    except ImportError:
        sys.stderr.write("anthropic is required.  pip install anthropic\n")
        return 1

    cfg = load_config()
    if not cfg["discord_token"]:
        sys.stderr.write(
            "No Discord token. Set DISCORD_TOKEN or add 'discord_token' to config.json.\n"
        )
        return 1

    claude = anthropic.Anthropic(api_key=cfg["anthropic_api_key"]) if cfg["anthropic_api_key"] else None
    guild_cfg = load_guild_config()
    channel_history: dict = {}   # channel_id -> [messages]

    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)
    tree = app_commands.CommandTree(client)

    async def ask_claude(system: str, messages: list, max_tokens: int = 1024) -> str:
        if not claude:
            return "(Claude is not configured — set ANTHROPIC_API_KEY.)"
        msg = await client.loop.run_in_executor(
            None,
            lambda: claude.messages.create(
                model=MODEL, max_tokens=max_tokens, system=system, messages=messages
            ),
        )
        return "".join(b.text for b in msg.content if b.type == "text")

    @client.event
    async def on_ready():
        await tree.sync()
        print(f"Logged in as {client.user} — serving {len(client.guilds)} guild(s).")

    @client.event
    async def on_message(message):
        if message.author == client.user:
            return
        # Moderation: delete banned-word messages.
        if message.guild:
            banned = banned_words_for(guild_cfg, message.guild.id)
            if message_violates(message.content, banned):
                try:
                    await message.delete()
                    await message.channel.send(
                        f"{message.author.mention}, that message was removed by moderation.",
                        delete_after=5,
                    )
                except discord.Forbidden:
                    pass
                return
        # Chat when mentioned or in a DM.
        mentioned = client.user in message.mentions
        is_dm = message.guild is None
        if mentioned or is_dm:
            prompt = message.content.replace(f"<@{client.user.id}>", "").strip()
            if not prompt:
                return
            hist = channel_history.setdefault(message.channel.id, [])
            hist.append({"role": "user", "content": prompt})
            hist[:] = hist[-10:]  # keep last 10 turns
            async with message.channel.typing():
                reply = await ask_claude("You are a helpful, friendly Discord assistant.", hist)
            hist.append({"role": "assistant", "content": reply})
            for chunk in chunk_message(reply):
                await message.channel.send(chunk)

    @tree.command(name="ask", description="Ask Claude anything.")
    async def ask_cmd(interaction, prompt: str):
        await interaction.response.defer()
        reply = await ask_claude("You are a concise, helpful assistant.",
                                 [{"role": "user", "content": prompt}])
        for chunk in chunk_message(reply):
            await interaction.followup.send(chunk)

    @tree.command(name="review", description="Get an AI code review.")
    async def review_cmd(interaction, code: str):
        await interaction.response.defer()
        reply = await ask_claude(
            "You are a senior engineer. Review the code for bugs, security, and style. Be concise.",
            [{"role": "user", "content": f"Review this code:\n```\n{code}\n```"}],
            max_tokens=1500,
        )
        for chunk in chunk_message(reply):
            await interaction.followup.send(chunk)

    @tree.command(name="summarise", description="Summarise a web page.")
    async def summarise_cmd(interaction, url: str):
        await interaction.response.defer()
        try:
            import urllib.request
            req = urllib.request.Request(url, headers={"User-Agent": "clawbot/1.0"})
            html = await client.loop.run_in_executor(
                None, lambda: urllib.request.urlopen(req, timeout=15).read().decode("utf-8", "ignore"))
        except Exception as exc:  # noqa: BLE001
            await interaction.followup.send(f"Could not fetch the page: {exc}")
            return
        text = extract_text_from_html(html)
        reply = await ask_claude(
            "Summarise the following web page content in 4-6 bullet points.",
            [{"role": "user", "content": text}], max_tokens=800)
        for chunk in chunk_message(reply):
            await interaction.followup.send(chunk)

    @tree.command(name="imagine", description="Generate an image with DALL-E.")
    async def imagine_cmd(interaction, prompt: str):
        await interaction.response.defer()
        if not cfg["openai_api_key"]:
            await interaction.followup.send("Image generation needs an OpenAI API key (set OPENAI_API_KEY).")
            return
        try:
            from openai import OpenAI
            oai = OpenAI(api_key=cfg["openai_api_key"])
            result = await client.loop.run_in_executor(
                None, lambda: oai.images.generate(model="dall-e-3", prompt=prompt, n=1, size="1024x1024"))
            await interaction.followup.send(result.data[0].url)
        except ImportError:
            await interaction.followup.send("Install the OpenAI SDK:  pip install openai")
        except Exception as exc:  # noqa: BLE001
            await interaction.followup.send(f"Image generation failed: {exc}")

    @tree.command(name="ban_word", description="Add a banned word for this server (admins).")
    async def ban_word_cmd(interaction, word: str):
        if not interaction.guild:
            await interaction.response.send_message("Server-only command.", ephemeral=True)
            return
        gid = str(interaction.guild.id)
        guild_cfg.setdefault(gid, {}).setdefault("banned_words", [])
        if word.lower() not in [w.lower() for w in guild_cfg[gid]["banned_words"]]:
            guild_cfg[gid]["banned_words"].append(word)
            save_guild_config(guild_cfg)
        await interaction.response.send_message(f"Banned word added: '{word}'", ephemeral=True)

    client.run(cfg["discord_token"])
    return 0


if __name__ == "__main__":
    raise SystemExit(run_bot())
