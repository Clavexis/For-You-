# clawtorrent — a BitTorrent client from scratch

A minimal but real **BitTorrent client written in pure Python**, with **no third-party libraries**. The bencode parser, the tracker protocol (both **HTTP** and **UDP**), the **peer wire protocol** and **SHA-1 piece verification** are all implemented here from the spec — only the Python standard library is used.

## Demo

```text
$ clawtorrent info ubuntu.torrent
Name:         ubuntu-24.04-desktop-amd64.iso
Info hash:    a5a684e9341c6e39cebfdeeae9979fa556f3ad72
Total size:   5.7 GB
Piece length: 256.0 KB
Pieces:       23456
Files:
       5.7 GB  ubuntu-24.04-desktop-amd64.iso
Trackers:
  https://torrent.ubuntu.com/announce
  udp://tracker.opentrackr.org:1337/announce

$ clawtorrent get ubuntu.torrent -o ~/Downloads
Torrent: ubuntu-24.04-desktop-amd64.iso (5.7 GB, 23456 pieces)

Announcing to trackers...
  tracker udp://tracker.opentrackr.org:1337/announce -> 50 peers
Downloading 23456 pieces from 50 peers...

[##########------------------------------]  24.3% (5700/23456 pieces)
```

## Features

- **Parses `.torrent` files** — full bencode decoder/encoder, single- and multi-file torrents.
- **Computes the info-hash** the real way: SHA-1 of the bencoded `info` dictionary (byte-for-byte compatible with every other client).
- **Talks to trackers** over both **HTTP/HTTPS** and **UDP** (BEP 15), with automatic fallback across the announce list.
- **Peer wire protocol** — handshake, bitfield/have parsing, interested/unchoke handshake, and block-by-block piece requests (BEP 3).
- **Verifies every piece** against its SHA-1 hash before writing — corrupt data is rejected.
- **Writes pieces across file boundaries** correctly for multi-file torrents.
- **Live progress bar** in the terminal.
- **Built-in self-test suite** (`clawtorrent test`) covering bencode, parsing, info-hash, and piece verification — no network needed.

## Installation

Requires only **Python 3.6+** — there are no dependencies to install.

### Linux
```bash
cd linux && ./install.sh
clawtorrent test
```

### macOS (Apple Silicon & Intel)
```bash
cd mac && ./install.sh
clawtorrent test
```

### Windows
```powershell
cd windows
.\install.bat
python "%USERPROFILE%\bin\clawtorrent.py" test
```

Or just run it in place on any platform: `python3 clawtorrent.py test`.

## Usage

```bash
clawtorrent info  file.torrent          # show name, size, pieces, files, trackers
clawtorrent peers file.torrent          # ask the tracker(s) for a peer list
clawtorrent get   file.torrent -o DIR   # download into DIR (default: current dir)
clawtorrent test                        # run the offline self-tests
```

## How it works

```text
.torrent file ──bdecode──▶ info dict ──SHA-1──▶ info-hash
                                  │
        tracker (HTTP/UDP) ◀──────┘  announce(info_hash) ──▶ peer list
                                                                  │
        per peer:  TCP handshake ──▶ interested ──▶ unchoke ──▶ request blocks
                                                                  │
        each 16 KiB block ──assemble piece──▶ SHA-1 check ──▶ write to disk
```

A torrent is a list of fixed-size **pieces**, each with a known SHA-1 hash. clawtorrent discovers peers from the tracker, connects to them over TCP, asks which pieces they have, downloads each piece in 16 KiB blocks, checks the hash, and writes verified bytes to the right offset in the right file. The hash check is what makes BitTorrent tamper-proof — a piece that doesn't match is thrown away.

> Note: downloading needs a live swarm with reachable seeders. The `info`, `peers`, and `test` commands work entirely offline.

## Tech stack

- **Python 3** standard library only — `socket` (TCP/UDP), `hashlib` (SHA-1), `struct` (binary framing), `urllib` (HTTP tracker)
- The BitTorrent protocol (BEP 3) and UDP tracker protocol (BEP 15), implemented from scratch

---

Built by clavexis — [github.com/clavexis](https://github.com/clavexis)
