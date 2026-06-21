# Real-Time Multiplayer Game (C++)

A LAN multiplayer game with a **client-server architecture** — player movement synced in real time over **UDP**, up to **4 players**, rendered with **SDL2**.

## Demo

```text
$ ./server
Game server listening on UDP 9999 (max 4 players).
Player 0 joined.
Player 1 joined.

# each player runs:
$ ./client 192.168.1.20
Joined as player 1
# move with arrow keys / WASD — everyone sees everyone move in real time
```

Each player is a coloured square; your own player has a white outline.

## Architecture

```text
        ┌──────── authoritative UDP server ────────┐
        │  receives input, runs the simulation,     │
        │  broadcasts game state ~30 Hz             │
        └───────────────────────────────────────────┘
             ▲          ▲          ▲          ▲
          client 0   client 1   client 2   client 3   (SDL2 rendering)
```

The **server** owns the truth: it receives each client's input, moves the players, and broadcasts the full state to everyone. Clients just send input and draw whatever the server reports — so no client can cheat the positions.

## Features

- **Client-server over UDP** — low-latency, connectionless.
- **Up to 4 players**, each assigned a slot/colour on join.
- **Real-time movement sync** — input → server simulation → broadcast → render.
- **Authoritative server** (headless, no graphics) — fully testable on its own.
- **SDL2 client** with keyboard movement (arrows / WASD).
- A compact binary wire protocol (see `protocol.h`).

## Build & run

The **server** needs only a C++17 compiler. The **client** also needs **SDL2**.

### Linux
```bash
cd linux
make                          # builds server (+ client if SDL2 is installed)
# install SDL2 if needed:  sudo apt install libsdl2-dev
./server                      # on the host machine
./client 127.0.0.1            # one per player (give the server's IP)
```

### macOS (Apple Silicon & Intel)
```bash
cd mac
brew install sdl2
./build.sh
./server
./client 127.0.0.1
```

### Windows
Build under **WSL** (Ubuntu) with the `linux/` Makefile, or with MinGW + SDL2:
```bash
# inside WSL:
sudo apt install build-essential libsdl2-dev
cd linux && make
```

## How to play

1. Start the **server** on one machine.
2. Each player runs the **client** with the server's IP: `./client <server-ip>`.
3. Move with the **arrow keys** or **WASD** — everyone moves in real time.

## Protocol

A tiny binary UDP protocol (`protocol.h`):
- Client → Server: `JOIN`, `INPUT` (id, dx, dy, shoot), `LEAVE`
- Server → Client: `WELCOME` (assigned id), `STATE` (all players' positions)

Verified end-to-end: two clients join with distinct IDs, one client's input moves its player on the server, and the new position is broadcast to the other client.

## Tech stack

- **C++17** — BSD sockets (UDP), fixed-tick simulation
- **SDL2** for the client window/rendering
- Custom binary wire protocol

---

Built by clavexis — [github.com/clavexis](https://github.com/clavexis)
