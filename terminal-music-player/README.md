# Terminal Music Player

Control Spotify from your terminal — play, pause, skip, set volume, search, and watch the current track with a live progress bar.

## Demo

```text
$ spotify-cli now
▶ Get Lucky — Daft Punk, Pharrell Williams
  1:40 ██████████──────────────────── 3:20
  volume: 70%

$ spotify-cli next
⏭ Next.
▶ Instant Crush — Daft Punk, Julian Casablancas
  0:03 ─────────────────────────────── 5:37
```

## Features

- **Playback control** — `play`, `pause`, `next`, `prev`, `volume`.
- **Now playing** — current track, artists, and a text **progress bar**.
- **Live view** — `live` refreshes the now-playing display in place.
- **Search** — songs and playlists, with their Spotify URIs.
- Clean, colourful terminal output.

## Setup

1. Install (needs **Python 3.8+** and [`spotipy`](https://pypi.org/project/spotipy/)).
2. Create a Spotify app at [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard).
   - Add `http://localhost:8888/callback` as a Redirect URI.
3. Add your credentials — either environment variables:
   ```bash
   export SPOTIFY_CLIENT_ID=...
   export SPOTIFY_CLIENT_SECRET=...
   ```
   or copy `config.json.example` to `~/.config/terminal-music-player/config.json`.

> Playback control (play/pause/skip/volume) requires **Spotify Premium** and an active device (the desktop/phone app open).

### Linux
```bash
cd linux && ./install.sh
spotify-cli now
```

### macOS (Apple Silicon & Intel)
```bash
cd mac && ./install.sh
spotify-cli now
```

### Windows
```powershell
cd windows
install.bat
python player.py now
```

## Usage

```bash
spotify-cli now              # current track + progress bar
spotify-cli live             # live updating view
spotify-cli play             # resume
spotify-cli pause            # pause
spotify-cli next             # next track
spotify-cli prev             # previous track
spotify-cli volume 60        # set volume to 60%
spotify-cli search "daft punk"
```

The first run opens a browser to authorise the app (OAuth); the token is cached for later runs.

## Tech stack

- **Python 3** + [`spotipy`](https://pypi.org/project/spotipy/) (Spotify Web API)
- OAuth via `SpotifyOAuth`; standard-library rendering for the progress bar

---

Built by clavexis — [github.com/clavexis](https://github.com/clavexis)
