#!/usr/bin/env python3
"""
AI Terminal Assistant — chat with Claude directly from your shell.

Features:
  - Real-time streaming responses
  - Persistent conversation history (remembers context within a session)
  - Custom system prompts
  - Coloured, formatted terminal output
  - Config file for API key storage (~/.config/ai-terminal-assistant/config.json)

Built by clavexis — github.com/clavexis
"""

import argparse
import json
import os
import sys
from pathlib import Path

try:
    import anthropic
except ImportError:
    sys.stderr.write(
        "Error: the 'anthropic' package is not installed.\n"
        "Install it with:  pip install anthropic\n"
    )
    sys.exit(1)

# Default model. Opus 4.8 is Anthropic's most capable Opus-tier model.
DEFAULT_MODEL = "claude-opus-4-8"
DEFAULT_MAX_TOKENS = 4096

# ---------------------------------------------------------------------------
# Terminal colours. We only emit ANSI codes when writing to a real terminal,
# so piping the output to a file stays clean.
# ---------------------------------------------------------------------------
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    BLUE = "\033[34m"

    @classmethod
    def disable(cls):
        for name in ("RESET", "BOLD", "DIM", "CYAN", "GREEN", "YELLOW", "RED", "BLUE"):
            setattr(cls, name, "")


if not sys.stdout.isatty() or os.environ.get("NO_COLOR"):
    Colors.disable()


# ---------------------------------------------------------------------------
# Config handling. The API key can come from the config file or the
# ANTHROPIC_API_KEY environment variable (env var wins).
# ---------------------------------------------------------------------------
def config_dir() -> Path:
    """Return the per-user config directory, respecting XDG on Linux/mac."""
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(Path.home(), ".config")
    return Path(base) / "ai-terminal-assistant"


def config_path() -> Path:
    return config_dir() / "config.json"


def load_config() -> dict:
    path = config_path()
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError) as exc:
            sys.stderr.write(f"{Colors.YELLOW}Warning: could not read config ({exc}).{Colors.RESET}\n")
    return {}


def save_config(cfg: dict) -> None:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cfg, indent=2))
    # Lock the file down — it may contain an API key.
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    print(f"{Colors.GREEN}Saved config to {path}{Colors.RESET}")


def resolve_api_key(cfg: dict) -> str | None:
    return os.environ.get("ANTHROPIC_API_KEY") or cfg.get("api_key")


# ---------------------------------------------------------------------------
# Core chat logic.
# ---------------------------------------------------------------------------
def stream_reply(client, model, system, messages, max_tokens) -> str:
    """Stream one assistant turn to the terminal and return the full text."""
    parts: list[str] = []
    kwargs = dict(model=model, max_tokens=max_tokens, messages=messages)
    if system:
        kwargs["system"] = system

    print(f"{Colors.GREEN}{Colors.BOLD}Claude:{Colors.RESET} ", end="", flush=True)
    try:
        with client.messages.stream(**kwargs) as stream:
            for text in stream.text_stream:
                parts.append(text)
                print(text, end="", flush=True)
    except anthropic.APIStatusError as exc:
        print()  # finish the line
        raise RuntimeError(f"API error {exc.status_code}: {exc.message}") from exc
    except anthropic.APIConnectionError as exc:
        print()
        raise RuntimeError(f"Connection error: {exc}") from exc
    print("\n")
    return "".join(parts)


def interactive_session(client, model, system, max_tokens) -> None:
    """Run a back-and-forth REPL that remembers context."""
    messages: list[dict] = []
    print(f"{Colors.CYAN}{Colors.BOLD}AI Terminal Assistant{Colors.RESET} "
          f"{Colors.DIM}(model: {model}){Colors.RESET}")
    print(f"{Colors.DIM}Type your message and press Enter. "
          f"Commands: /reset, /exit (or Ctrl-D).{Colors.RESET}\n")

    while True:
        try:
            user = input(f"{Colors.BLUE}{Colors.BOLD}You:{Colors.RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n{Colors.DIM}Goodbye.{Colors.RESET}")
            return

        if not user:
            continue
        if user in ("/exit", "/quit"):
            print(f"{Colors.DIM}Goodbye.{Colors.RESET}")
            return
        if user == "/reset":
            messages.clear()
            print(f"{Colors.YELLOW}Conversation history cleared.{Colors.RESET}\n")
            continue

        messages.append({"role": "user", "content": user})
        try:
            reply = stream_reply(client, model, system, messages, max_tokens)
        except RuntimeError as exc:
            sys.stderr.write(f"{Colors.RED}{exc}{Colors.RESET}\n")
            messages.pop()  # drop the unanswered turn so history stays valid
            continue
        messages.append({"role": "assistant", "content": reply})


def one_shot(client, model, system, max_tokens, prompt) -> None:
    """Answer a single prompt (useful for piping / scripting)."""
    messages = [{"role": "user", "content": prompt}]
    stream_reply(client, model, system, messages, max_tokens)


# ---------------------------------------------------------------------------
# CLI entry point.
# ---------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(
        description="Chat with Claude from your terminal.",
    )
    parser.add_argument("prompt", nargs="*", help="Prompt for one-shot mode. Omit for interactive chat.")
    parser.add_argument("-s", "--system", help="System prompt to steer the assistant.")
    parser.add_argument("-m", "--model", default=None, help=f"Model ID (default: {DEFAULT_MODEL}).")
    parser.add_argument("--max-tokens", type=int, default=None, help="Max output tokens per reply.")
    parser.add_argument("--set-key", metavar="KEY", help="Store an API key in the config file and exit.")
    args = parser.parse_args()

    cfg = load_config()

    if args.set_key:
        cfg["api_key"] = args.set_key
        save_config(cfg)
        return 0

    api_key = resolve_api_key(cfg)
    if not api_key:
        sys.stderr.write(
            f"{Colors.RED}No API key found.{Colors.RESET}\n"
            "Set one with:  ai-assistant --set-key sk-ant-...\n"
            "or export ANTHROPIC_API_KEY in your shell.\n"
        )
        return 1

    model = args.model or cfg.get("model") or DEFAULT_MODEL
    max_tokens = args.max_tokens or cfg.get("max_tokens") or DEFAULT_MAX_TOKENS
    system = args.system or cfg.get("system")

    client = anthropic.Anthropic(api_key=api_key)

    # Accept a prompt piped in via stdin (e.g. `echo "hi" | ai-assistant`).
    piped = ""
    if not sys.stdin.isatty():
        piped = sys.stdin.read().strip()

    prompt = " ".join(args.prompt).strip()
    if piped:
        prompt = f"{prompt}\n\n{piped}".strip()

    try:
        if prompt:
            one_shot(client, model, system, max_tokens, prompt)
        else:
            interactive_session(client, model, system, max_tokens)
    except RuntimeError as exc:
        sys.stderr.write(f"{Colors.RED}{exc}{Colors.RESET}\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
