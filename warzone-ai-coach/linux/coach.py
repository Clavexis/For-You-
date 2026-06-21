#!/usr/bin/env python3
"""
Warzone AI Coach — analyse your Call of Duty: Warzone stats and get
AI-powered improvement tips.

Two modes of getting stats:
  1. Manual input  — answer a few prompts, or pass a JSON file with --stats.
  2. Warzone API   — optional; requires credentials in the config file. The
                     public Warzone API is unofficial and rate-limited, so the
                     manual/JSON path is the recommended default.

Analysis:
  - Always runs a fast offline heuristic breakdown (no API key needed).
  - If an Anthropic API key is available, Claude writes a tailored coaching
    report on top of the heuristics.

Reports can be saved to a file with --save.

Built by clavexis — github.com/clavexis
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Anthropic SDK is optional — the offline coach works without it.
try:
    import anthropic
    HAVE_ANTHROPIC = True
except ImportError:
    HAVE_ANTHROPIC = False

DEFAULT_MODEL = "claude-opus-4-8"


class C:
    RESET = "\033[0m"; BOLD = "\033[1m"; DIM = "\033[2m"
    CYAN = "\033[36m"; GREEN = "\033[32m"; YELLOW = "\033[33m"; RED = "\033[31m"

    @classmethod
    def off(cls):
        for n in ("RESET", "BOLD", "DIM", "CYAN", "GREEN", "YELLOW", "RED"):
            setattr(cls, n, "")


if not sys.stdout.isatty() or os.environ.get("NO_COLOR"):
    C.off()


# ---------------------------------------------------------------------------
# Config (shared key storage, mirrors the other clawtornix AI tools).
# ---------------------------------------------------------------------------
def config_path() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(Path.home(), ".config")
    return Path(base) / "warzone-ai-coach" / "config.json"


def load_config() -> dict:
    p = config_path()
    if p.exists():
        try:
            return json.loads(p.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def resolve_api_key(cfg: dict):
    return os.environ.get("ANTHROPIC_API_KEY") or cfg.get("api_key")


# ---------------------------------------------------------------------------
# Stats input.
# ---------------------------------------------------------------------------
STAT_FIELDS = [
    ("kd", "K/D ratio (e.g. 1.05)", float),
    ("win_rate", "Win rate % (e.g. 4.5)", float),
    ("accuracy", "Accuracy % (e.g. 22)", float),
    ("avg_kills", "Average kills per match (e.g. 4.2)", float),
    ("matches", "Matches played (e.g. 800)", int),
    ("headshot_pct", "Headshot % (e.g. 18)", float),
]


def prompt_stats() -> dict:
    print(f"{C.CYAN}{C.BOLD}Enter your Warzone stats{C.RESET} "
          f"{C.DIM}(press Enter to skip a field){C.RESET}")
    stats: dict = {}
    for key, label, cast in STAT_FIELDS:
        while True:
            raw = input(f"  {label}: ").strip()
            if not raw:
                break
            try:
                stats[key] = cast(raw)
                break
            except ValueError:
                print(f"  {C.RED}Not a valid number, try again.{C.RESET}")
    weapons = input("  Most-used weapons (comma separated): ").strip()
    if weapons:
        stats["weapons"] = [w.strip() for w in weapons.split(",") if w.strip()]
    return stats


def load_stats_file(path: str) -> dict:
    data = json.loads(Path(path).read_text())
    if not isinstance(data, dict):
        raise ValueError("stats file must contain a JSON object")
    return data


def fetch_from_api(cfg: dict, gamertag: str, platform: str) -> dict:
    """Optional Warzone API path.

    The public Warzone API is unofficial (commonly via the `callofduty.py`
    project) and needs an authenticated session cookie that Activision rotates
    frequently. Rather than ship a brittle scraper, we read the credentials
    from config and surface a clear message. Drop your own fetch logic here.
    """
    creds = cfg.get("warzone_api", {})
    if not creds.get("sso_token"):
        raise RuntimeError(
            "Warzone API not configured. Add credentials to the config file:\n"
            f"  {config_path()}\n"
            '  {"warzone_api": {"sso_token": "<ACT_SSO_COOKIE>"}}\n'
            "Or just use manual input / --stats <file.json>."
        )
    raise RuntimeError(
        "Live API fetching is a placeholder (Activision tokens rotate often). "
        "Use --stats <file.json> or manual input for now."
    )


# ---------------------------------------------------------------------------
# Offline heuristic analysis — works with zero dependencies / no API key.
# ---------------------------------------------------------------------------
def heuristic_report(stats: dict) -> list[str]:
    tips: list[str] = []

    kd = stats.get("kd")
    if kd is not None:
        if kd < 0.8:
            tips.append("Your K/D is below 0.8 — focus on survival: land in quieter "
                        "POIs, fight with your team, and avoid mid-range pushes you "
                        "can't win.")
        elif kd < 1.2:
            tips.append("K/D is around average. To climb, pre-aim common angles and "
                        "practise centring crosshair placement at head height.")
        else:
            tips.append("Strong K/D — your gunfights are paying off. Next gains come "
                        "from positioning and rotations, not raw aim.")

    wr = stats.get("win_rate")
    if wr is not None and kd is not None:
        if wr < 3 and kd >= 1.2:
            tips.append("High K/D but low win rate: you're winning fights but losing "
                        "games. Work on end-game positioning and zone rotations.")
        elif wr < 2:
            tips.append("Low win rate — play the circle earlier and prioritise good "
                        "compound/high-ground positions in the final zones.")

    acc = stats.get("accuracy")
    if acc is not None:
        if acc < 18:
            tips.append("Accuracy under 18% — tighten bursts at range and don't spray "
                        "full-auto past 30m. Recoil control drills help here.")
        elif acc > 25:
            tips.append("Excellent accuracy — lean into ARs/tactical rifles that reward "
                        "your precision.")

    hs = stats.get("headshot_pct")
    if hs is not None and hs < 15:
        tips.append("Headshot % is low — raise your default aim height to neck/head "
                    "level; it boosts both damage and accuracy.")

    weapons = stats.get("weapons")
    if weapons:
        tips.append(f"You favour {', '.join(weapons)}. Make sure your loadout pairs a "
                    "close-range option with a ranged one so no engagement catches you out.")

    if not tips:
        tips.append("Not enough stats to analyse — provide at least your K/D and win rate.")
    return tips


# ---------------------------------------------------------------------------
# AI coaching layer.
# ---------------------------------------------------------------------------
def ai_report(api_key: str, model: str, stats: dict) -> str:
    client = anthropic.Anthropic(api_key=api_key)
    system = (
        "You are an elite Call of Duty: Warzone coach. Given a player's stats, "
        "write a concise, encouraging coaching report with concrete, actionable "
        "tips. Use short sections: Strengths, Weaknesses, and a 3-step practice "
        "plan. Be specific to the numbers provided."
    )
    user = "Here are my Warzone stats as JSON:\n" + json.dumps(stats, indent=2)
    chunks: list[str] = []
    with client.messages.stream(
        model=model, max_tokens=1500, system=system,
        messages=[{"role": "user", "content": user}],
    ) as stream:
        for text in stream.text_stream:
            chunks.append(text)
    return "".join(chunks)


# ---------------------------------------------------------------------------
def build_report(stats: dict, ai_text: str | None) -> str:
    lines = []
    lines.append("=" * 60)
    lines.append("WARZONE AI COACH — REPORT")
    lines.append(datetime.now().strftime("Generated %Y-%m-%d %H:%M"))
    lines.append("=" * 60)
    lines.append("")
    lines.append("Stats provided:")
    for k, v in stats.items():
        lines.append(f"  - {k}: {v}")
    lines.append("")
    lines.append("Quick analysis:")
    for tip in heuristic_report(stats):
        lines.append(f"  • {tip}")
    if ai_text:
        lines.append("")
        lines.append("AI Coaching Report:")
        lines.append("")
        lines.append(ai_text.strip())
    lines.append("")
    lines.append("Built by clavexis — github.com/clavexis")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Analyse Warzone stats and get coaching tips.")
    ap.add_argument("--stats", help="Path to a JSON file with your stats.")
    ap.add_argument("--api", action="store_true", help="Fetch stats from the Warzone API (needs config).")
    ap.add_argument("--gamertag", help="Gamertag for --api mode.")
    ap.add_argument("--platform", default="battle", help="Platform for --api mode (battle/psn/xbl).")
    ap.add_argument("--no-ai", action="store_true", help="Skip the AI report (heuristics only).")
    ap.add_argument("-m", "--model", default=DEFAULT_MODEL, help="Anthropic model ID.")
    ap.add_argument("--save", metavar="FILE", help="Save the report to a file.")
    args = ap.parse_args()

    cfg = load_config()

    # Gather stats.
    try:
        if args.stats:
            stats = load_stats_file(args.stats)
        elif args.api:
            stats = fetch_from_api(cfg, args.gamertag or "", args.platform)
        else:
            stats = prompt_stats()
    except (OSError, ValueError, RuntimeError) as exc:
        sys.stderr.write(f"{C.RED}Error: {exc}{C.RESET}\n")
        return 1

    if not stats:
        sys.stderr.write(f"{C.RED}No stats provided — nothing to analyse.{C.RESET}\n")
        return 1

    # AI layer (optional).
    ai_text = None
    api_key = resolve_api_key(cfg)
    if not args.no_ai and HAVE_ANTHROPIC and api_key:
        try:
            print(f"{C.DIM}Generating AI coaching report...{C.RESET}\n")
            ai_text = ai_report(api_key, args.model, stats)
        except Exception as exc:  # noqa: BLE001 — surface any API issue, keep heuristics
            sys.stderr.write(f"{C.YELLOW}AI report unavailable ({exc}); showing heuristics only.{C.RESET}\n")
    elif not args.no_ai and not (HAVE_ANTHROPIC and api_key):
        print(f"{C.DIM}(No API key / SDK — showing offline heuristic report. "
              f"Set ANTHROPIC_API_KEY for AI coaching.){C.RESET}\n")

    report = build_report(stats, ai_text)
    print(report)

    if args.save:
        try:
            Path(args.save).write_text(report)
            print(f"\n{C.GREEN}Saved report to {args.save}{C.RESET}")
        except OSError as exc:
            sys.stderr.write(f"{C.RED}Could not save report: {exc}{C.RESET}\n")
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
