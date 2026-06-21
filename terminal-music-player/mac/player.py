#!/usr/bin/env python3
"""
Terminal Music Player — control Spotify from your terminal.

  - Play, pause, next, previous, set volume
  - Show the current track with a live progress bar
  - Search songs and playlists
  - Live "now playing" mode that refreshes in place

Requires a Spotify account (Premium for playback control) and a Spotify app:
https://developer.spotify.com/dashboard — set client id/secret/redirect in the
config file (or environment variables).

Usage:
  player.py now              # show current track
  player.py live             # live now-playing view (refreshes)
  player.py play|pause|next|prev
  player.py volume 60
  player.py search "daft punk"

Built by clavexis — github.com/clavexis
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path


class C:
    RESET = "\033[0m"; BOLD = "\033[1m"; DIM = "\033[2m"
    GREEN = "\033[32m"; CYAN = "\033[36m"; YELLOW = "\033[33m"; RED = "\033[31m"

    @classmethod
    def off(cls):
        for n in ("RESET", "BOLD", "DIM", "GREEN", "CYAN", "YELLOW", "RED"):
            setattr(cls, n, "")


if not sys.stdout.isatty() or os.environ.get("NO_COLOR"):
    C.off()


# ---------------------------------------------------------------------------
# Pure helpers (unit-testable without Spotify).
# ---------------------------------------------------------------------------
def format_ms(ms: int) -> str:
    """Format milliseconds as M:SS."""
    seconds = max(0, ms // 1000)
    return f"{seconds // 60}:{seconds % 60:02d}"


def progress_bar(pos_ms: int, total_ms: int, width: int = 30) -> str:
    """Render a text progress bar with elapsed/total times."""
    if total_ms <= 0:
        ratio = 0.0
    else:
        ratio = min(1.0, max(0.0, pos_ms / total_ms))
    filled = int(ratio * width)
    bar = "█" * filled + "─" * (width - filled)
    return f"{format_ms(pos_ms)} {bar} {format_ms(total_ms)}"


def config_path() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(Path.home(), ".config")
    return Path(base) / "terminal-music-player" / "config.json"


def load_config() -> dict:
    cfg = {}
    p = config_path()
    if p.exists():
        try:
            cfg = json.loads(p.read_text())
        except json.JSONDecodeError:
            pass
    cfg.setdefault("client_id", os.environ.get("SPOTIFY_CLIENT_ID", cfg.get("client_id", "")))
    cfg.setdefault("client_secret", os.environ.get("SPOTIFY_CLIENT_SECRET", cfg.get("client_secret", "")))
    cfg.setdefault("redirect_uri", os.environ.get("SPOTIFY_REDIRECT_URI",
                                                  cfg.get("redirect_uri", "http://localhost:8888/callback")))
    return cfg


# ---------------------------------------------------------------------------
# Spotify client (requires spotipy + credentials).
# ---------------------------------------------------------------------------
def get_spotify(cfg: dict):
    try:
        import spotipy
        from spotipy.oauth2 import SpotifyOAuth
    except ImportError:
        sys.stderr.write("Spotify control needs spotipy.  pip install spotipy\n")
        return None
    if not cfg["client_id"] or not cfg["client_secret"]:
        sys.stderr.write(
            "Spotify credentials not set. Create an app at\n"
            "  https://developer.spotify.com/dashboard\n"
            f"and add client_id/client_secret to {config_path()} "
            "(or SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET).\n")
        return None
    scope = ("user-read-playback-state user-modify-playback-state "
             "user-read-currently-playing")
    auth = SpotifyOAuth(client_id=cfg["client_id"], client_secret=cfg["client_secret"],
                        redirect_uri=cfg["redirect_uri"], scope=scope,
                        cache_path=str(config_path().parent / ".cache"))
    return spotipy.Spotify(auth_manager=auth)


def show_now(sp) -> None:
    current = sp.current_playback()
    if not current or not current.get("item"):
        print(f"{C.DIM}Nothing playing.{C.RESET}")
        return
    item = current["item"]
    name = item["name"]
    artists = ", ".join(a["name"] for a in item["artists"])
    pos = current.get("progress_ms", 0)
    total = item.get("duration_ms", 0)
    playing = current.get("is_playing", False)
    icon = "▶" if playing else "⏸"
    print(f"{C.GREEN}{icon} {C.BOLD}{name}{C.RESET} {C.DIM}—{C.RESET} {C.CYAN}{artists}{C.RESET}")
    print(f"  {progress_bar(pos, total)}")
    vol = current.get("device", {}).get("volume_percent")
    if vol is not None:
        print(f"  {C.DIM}volume: {vol}%{C.RESET}")


def live_view(sp) -> None:
    print(f"{C.DIM}Live now-playing — Ctrl-C to exit.{C.RESET}")
    try:
        while True:
            current = sp.current_playback()
            sys.stdout.write("\033[2J\033[H")  # clear screen
            print(f"{C.DIM}Live now-playing — Ctrl-C to exit.{C.RESET}\n")
            if current and current.get("item"):
                show_now(sp)
            else:
                print(f"{C.DIM}Nothing playing.{C.RESET}")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopped.")


def search(sp, query: str) -> None:
    results = sp.search(q=query, type="track,playlist", limit=5)
    tracks = results.get("tracks", {}).get("items", [])
    print(f"{C.BOLD}Tracks:{C.RESET}")
    for i, t in enumerate(tracks, 1):
        artists = ", ".join(a["name"] for a in t["artists"])
        print(f"  {i}. {t['name']} — {C.CYAN}{artists}{C.RESET}  {C.DIM}{t['uri']}{C.RESET}")
    playlists = results.get("playlists", {}).get("items", [])
    if playlists:
        print(f"{C.BOLD}Playlists:{C.RESET}")
        for i, p in enumerate(playlists, 1):
            print(f"  {i}. {p['name']}  {C.DIM}{p['uri']}{C.RESET}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Control Spotify from the terminal.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("now", help="Show the current track.")
    sub.add_parser("live", help="Live now-playing view.")
    sub.add_parser("play", help="Resume playback.")
    sub.add_parser("pause", help="Pause playback.")
    sub.add_parser("next", help="Next track.")
    sub.add_parser("prev", help="Previous track.")
    vol = sub.add_parser("volume", help="Set volume (0-100).")
    vol.add_argument("level", type=int)
    s = sub.add_parser("search", help="Search tracks/playlists.")
    s.add_argument("query", nargs="+")
    args = ap.parse_args()

    cfg = load_config()
    sp = get_spotify(cfg)
    if not sp:
        return 1

    try:
        if args.cmd == "now":
            show_now(sp)
        elif args.cmd == "live":
            live_view(sp)
        elif args.cmd == "play":
            sp.start_playback(); print("▶ Playing.")
        elif args.cmd == "pause":
            sp.pause_playback(); print("⏸ Paused.")
        elif args.cmd == "next":
            sp.next_track(); print("⏭ Next."); time.sleep(0.3); show_now(sp)
        elif args.cmd == "prev":
            sp.previous_track(); print("⏮ Previous."); time.sleep(0.3); show_now(sp)
        elif args.cmd == "volume":
            level = max(0, min(100, args.level))
            sp.volume(level); print(f"🔊 Volume set to {level}%.")
        elif args.cmd == "search":
            search(sp, " ".join(args.query))
    except Exception as exc:  # noqa: BLE001 — surface Spotify/auth errors cleanly
        sys.stderr.write(f"{C.RED}Spotify error: {exc}{C.RESET}\n")
        sys.stderr.write(f"{C.DIM}(Playback control needs Spotify Premium and an active device.){C.RESET}\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
