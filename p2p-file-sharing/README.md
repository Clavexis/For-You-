# P2P File Sharing

Send a file **directly** between two computers — no cloud, no server. The transfer is encrypted, resumable, and as easy as sharing a short code.

## Demo

**Sender:**
```text
$ p2p send holiday-photos.zip
Ready to send holiday-photos.zip (240.5MB)
  Host: 192.168.1.20   Port: 49213
  Code: nova-kilo-puma

  On the other machine run:
    p2p.py recv 192.168.1.20 49213 nova-kilo-puma

  █▀▀▀▀▀█ ▀▄ █ █▀▀▀▀▀█
  █ ███ █ ▀█▀  █ ███ █     ← scan on a phone / LAN device
  ...
Waiting for the receiver...
```

**Receiver:**
```text
$ p2p recv 192.168.1.20 49213 nova-kilo-puma
Receiving holiday-photos.zip (240.5MB)...
  [████████████████──────────────]  53.2%  128.0MB/240.5MB
Saved holiday-photos.zip (240.5MB).
```

## Features

- **Direct peer-to-peer** TCP connection — one machine sends, the other receives, no middleman.
- **Encrypted transfer** — AES (via Fernet) with a key derived from the shared code (PBKDF2, 100k iterations). The wrong code is rejected before any data flows.
- **Progress bar** with live transfer speed feedback.
- **Resume interrupted transfers** — re-run the receive command and it continues from where it stopped (`.part` file + offset negotiation).
- **QR code** of the connection details for easy LAN pairing (optional, needs `qrcode`).

## Installation

Requires **Python 3.7+** and `cryptography` (`qrcode` is optional).

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
install.bat
```

## Usage

```bash
# Sender
p2p send myfile.zip               # auto-picks a port and prints a code
p2p send myfile.zip --port 5000   # fixed port

# Receiver (uses the host/port/code the sender printed)
p2p recv 192.168.1.20 49213 nova-kilo-puma
p2p recv 192.168.1.20 49213 nova-kilo-puma -o renamed.zip
```

If the transfer is interrupted, just run the same `recv` command again — it resumes.

## How it works

```text
sender: listen ──▶ accept ──▶ verify HMAC(code) ──▶ send metadata
                                                  ──▶ stream Fernet-encrypted chunks
receiver: connect ──▶ send HMAC(code) ──▶ recv metadata ──▶ ask resume offset
                                                          ──▶ decrypt + write chunks
```

Both peers derive the same encryption key from the shared code, so the code authenticates the receiver *and* keys the encryption — nothing readable crosses the wire.

> The code is a shared secret — read it to the other person or have them scan the QR. Anyone who knows the host, port, and code can receive the file.

## Tech stack

- **Python 3** — raw TCP sockets, length-prefixed framing
- [`cryptography`](https://pypi.org/project/cryptography/) (Fernet / AES, PBKDF2)
- Optional [`qrcode`](https://pypi.org/project/qrcode/) for LAN pairing

---

Built by clavexis — [github.com/clavexis](https://github.com/clavexis)
