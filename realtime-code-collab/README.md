# Real-Time Code Collaboration

Edit the same file together over the network — a WebSocket-synced collaborative code editor in your terminal. No accounts, just share a room code.

## Demo

```text
 Room: team  Users: alice, bob  (Ctrl-Q quit)
  1 def hello():
  2     print("hi from alice")
  3     print("...and bob")_
 cursors: alice@L2
```

Two people open the same room and type — edits appear on both screens instantly, and you can see where the other person's cursor is.

## How it works

```text
   alice ──┐                         ┌── bob
           ├──▶ WebSocket server ◀──┤
   carol ──┘   (rooms, broadcast)   └── dave
```

The server keeps the authoritative document per room. When you join, it sends a snapshot; as anyone edits, the change is broadcast to everyone else in the room.

## Features

- **WebSocket sync** — low-latency, broadcast to all peers in a room.
- **Multiple users** editing the same document live.
- **Cursor presence** — see each user's line position.
- **Room codes** — no login; share a code to collaborate.
- **Terminal editor** (curses) with arrow keys, typing, Enter/Backspace.
- **Scriptable `bot` client** for automation and testing.

## Installation

Requires **Python 3.8+** and the `websockets` package (installed by the script).

### Linux
```bash
cd linux && ./install.sh
```

### macOS (Apple Silicon & Intel)
```bash
cd mac && ./install.sh
```

### Windows
```powershell
cd windows
install.bat        # also installs windows-curses for the editor UI
```

## Usage

**1. Start a server** (one machine — or a small VPS so others can reach it):
```bash
collab server                 # listens on ws://0.0.0.0:8765
```

**2. Everyone joins the same room:**
```bash
collab join team                                  # connect to localhost
collab join team --url ws://your-server:8765 --name alice
```

Edit away — arrow keys to move, type to insert, Enter for a new line, **Ctrl-Q** to quit.

**Scripted client (testing / bots):**
```bash
collab bot team --op '{"type":"set_line","line":0,"text":"hello"}'
```

## Protocol

JSON messages over WebSocket: `join`, `snapshot`, `set_line`, `insert_line`, `delete_line`, `cursor`, `presence`. The server applies edits to the authoritative document and rebroadcasts them (last-writer-wins per line).

## Tech stack

- **Python 3** + [`websockets`](https://pypi.org/project/websockets/) (asyncio)
- `curses` terminal UI; threads bridge the editor loop and the async network client

---

Built by clavexis — [github.com/clavexis](https://github.com/clavexis)
