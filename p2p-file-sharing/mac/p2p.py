#!/usr/bin/env python3
"""
P2P File Sharing — send a file directly between two computers, no server.

  - Direct peer-to-peer TCP connection
  - Encrypted transfer (AES via Fernet, key derived from a shared code)
  - Progress bar during transfer
  - Resume interrupted transfers (the receiver asks to continue from its offset)
  - QR code for easy connection on a LAN (optional)

Usage:
  # On the sending machine:
  p2p.py send myfile.zip
      -> prints  host, port, and a CODE (and a QR if 'qrcode' is installed)

  # On the receiving machine:
  p2p.py recv <host> <port> <code> [-o output_name]

Built by clavexis — github.com/clavexis
"""

import argparse
import base64
import hashlib
import hmac
import os
import secrets
import socket
import struct
import sys
from pathlib import Path

try:
    from cryptography.fernet import Fernet
except ImportError:
    sys.stderr.write("This tool needs the 'cryptography' package.  pip install cryptography\n")
    sys.exit(1)

APP_SALT = b"clawtornix-p2p-v1"
CHUNK = 64 * 1024


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
# Crypto / helpers (unit-testable).
# ---------------------------------------------------------------------------
def gen_code() -> str:
    words = ["fox", "moon", "echo", "iris", "jade", "kilo", "lime", "nova",
             "opal", "puma", "ruby", "sage", "tiger", "vega", "wave", "zeta"]
    return "-".join(secrets.choice(words) for _ in range(3))


def derive_key(code: str) -> bytes:
    raw = hashlib.pbkdf2_hmac("sha256", code.encode(), APP_SALT, 100_000)
    return base64.urlsafe_b64encode(raw)


def auth_token(code: str) -> bytes:
    return hmac.new(code.encode(), b"p2p-auth", hashlib.sha256).digest()


def progress_bar(done: int, total: int, width: int = 30) -> str:
    ratio = (done / total) if total else 0.0
    ratio = min(1.0, max(0.0, ratio))
    filled = int(ratio * width)
    bar = "█" * filled + "─" * (width - filled)
    return f"[{bar}] {ratio*100:5.1f}%  {human(done)}/{human(total)}"


def human(n: float) -> str:
    size = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.0f}{unit}" if unit == "B" else f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}GB"


# Length-prefixed framing for sending whole encrypted messages.
def send_frame(sock, data: bytes):
    sock.sendall(struct.pack("!I", len(data)) + data)


def recv_exact(sock, n: int) -> bytes:
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("connection closed")
        buf += chunk
    return buf


def recv_frame(sock) -> bytes:
    (length,) = struct.unpack("!I", recv_exact(sock, 4))
    return recv_exact(sock, length)


def local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "127.0.0.1"


# ---------------------------------------------------------------------------
# Sender
# ---------------------------------------------------------------------------
def send_file(path: str, port: int):
    file = Path(path)
    if not file.is_file():
        sys.stderr.write(f"{C.RED}No such file: {path}{C.RESET}\n")
        return 1
    size = file.stat().st_size
    code = gen_code()
    fernet = Fernet(derive_key(code))

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", port))
    srv.listen(1)
    actual_port = srv.getsockname()[1]
    ip = local_ip()

    print(f"{C.CYAN}{C.BOLD}Ready to send {file.name} ({human(size)}){C.RESET}")
    print(f"  Host: {C.BOLD}{ip}{C.RESET}   Port: {C.BOLD}{actual_port}{C.RESET}")
    print(f"  Code: {C.GREEN}{C.BOLD}{code}{C.RESET}")
    print(f"\n  On the other machine run:")
    print(f"    {C.DIM}p2p.py recv {ip} {actual_port} {code}{C.RESET}")
    show_qr(f"{ip}:{actual_port}:{code}")
    print(f"\n{C.DIM}Waiting for the receiver...{C.RESET}")

    conn, addr = srv.accept()
    print(f"{C.GREEN}Connected to {addr[0]}.{C.RESET}")
    try:
        # Authenticate the receiver.
        token = recv_frame(conn)
        if not hmac.compare_digest(token, auth_token(code)):
            send_frame(conn, b"DENY")
            print(f"{C.RED}Receiver supplied the wrong code — refused.{C.RESET}")
            return 1
        send_frame(conn, b"OK")

        # Send metadata (encrypted): filename + size.
        meta = f"{file.name}\n{size}".encode()
        send_frame(conn, fernet.encrypt(meta))

        # Receiver tells us where to resume from.
        offset = struct.unpack("!Q", recv_frame(conn))[0]
        if offset:
            print(f"{C.YELLOW}Resuming from {human(offset)}.{C.RESET}")

        with open(file, "rb") as f:
            f.seek(offset)
            sent = offset
            while True:
                chunk = f.read(CHUNK)
                if not chunk:
                    break
                send_frame(conn, fernet.encrypt(chunk))
                sent += len(chunk)
                print(f"\r  {progress_bar(sent, size)}", end="", flush=True)
        send_frame(conn, b"")  # empty frame signals EOF
        print(f"\n{C.GREEN}Done — sent {file.name}.{C.RESET}")
    finally:
        conn.close()
        srv.close()
    return 0


# ---------------------------------------------------------------------------
# Receiver
# ---------------------------------------------------------------------------
def recv_file(host: str, port: int, code: str, out: str = None):
    fernet = Fernet(derive_key(code))
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((host, port))
    except OSError as exc:
        sys.stderr.write(f"{C.RED}Could not connect to {host}:{port} — {exc}{C.RESET}\n")
        return 1

    try:
        send_frame(sock, auth_token(code))
        if recv_frame(sock) != b"OK":
            print(f"{C.RED}Authentication failed (wrong code?).{C.RESET}")
            return 1

        meta = fernet.decrypt(recv_frame(sock)).decode()
        filename, size_s = meta.split("\n")
        size = int(size_s)
        target = out or filename
        partial = Path(target + ".part")

        # Resume if a partial download exists.
        offset = partial.stat().st_size if partial.exists() else 0
        send_frame(sock, struct.pack("!Q", offset))
        if offset:
            print(f"{C.YELLOW}Resuming {target} from {human(offset)}.{C.RESET}")

        print(f"{C.CYAN}Receiving {filename} ({human(size)})...{C.RESET}")
        got = offset
        with open(partial, "ab") as f:
            while True:
                frame = recv_frame(sock)
                if frame == b"":
                    break
                data = fernet.decrypt(frame)
                f.write(data)
                got += len(data)
                print(f"\r  {progress_bar(got, size)}", end="", flush=True)
        partial.rename(target)
        print(f"\n{C.GREEN}Saved {target} ({human(got)}).{C.RESET}")
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(f"\n{C.RED}Transfer failed: {exc}{C.RESET}\n")
        sys.stderr.write(f"{C.DIM}(Re-run the same command to resume.){C.RESET}\n")
        return 1
    finally:
        sock.close()
    return 0


def show_qr(text: str):
    try:
        import qrcode
        qr = qrcode.QRCode(border=1)
        qr.add_data(text)
        qr.make()
        qr.print_ascii(invert=True)
    except ImportError:
        pass  # QR is optional


def main():
    ap = argparse.ArgumentParser(description="Peer-to-peer encrypted file transfer.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("send", help="Send a file.")
    s.add_argument("file")
    s.add_argument("--port", type=int, default=0, help="Port (0 = auto).")
    r = sub.add_parser("recv", help="Receive a file.")
    r.add_argument("host")
    r.add_argument("port", type=int)
    r.add_argument("code")
    r.add_argument("-o", "--out", help="Output filename.")
    args = ap.parse_args()

    if args.cmd == "send":
        return send_file(args.file, args.port)
    return recv_file(args.host, args.port, args.code, args.out)


if __name__ == "__main__":
    raise SystemExit(main())
