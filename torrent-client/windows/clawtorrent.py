#!/usr/bin/env python3
"""
clawtorrent — a minimal BitTorrent client written from scratch in pure Python.

No third-party libraries: the bencode parser, tracker protocol (HTTP + UDP), the
peer wire protocol and SHA-1 piece verification are all implemented here using
only the standard library.

Commands:
    clawtorrent info  <file.torrent>                 show metadata about a torrent
    clawtorrent peers <file.torrent>                 ask the tracker for a peer list
    clawtorrent get   <file.torrent> [-o DIR]        download the torrent
    clawtorrent test                                 run the built-in self-tests

Built by clavexis — github.com/clavexis
"""

import sys
import os
import socket
import struct
import hashlib
import random
import time
import argparse
import urllib.request
import urllib.parse
from collections import OrderedDict

# ---------------------------------------------------------------------------
# Bencode — the encoding used by .torrent files and HTTP trackers.
# Grammar:  integers  i<n>e   strings  <len>:<bytes>   lists  l...e   dicts d...e
# ---------------------------------------------------------------------------


def bdecode(data):
    """Decode a bencoded byte string into Python objects.

    Returns the decoded value. Raises ValueError on malformed input.
    """
    value, index = _bdecode(data, 0)
    if index != len(data):
        raise ValueError("trailing data after bencoded value")
    return value


def _bdecode(data, i):
    """Decode the single bencoded value starting at offset ``i``.

    Returns a (value, next_index) tuple so callers can keep parsing.
    """
    if i >= len(data):
        raise ValueError("unexpected end of data")
    c = data[i : i + 1]

    if c == b"i":  # integer:  i<number>e
        end = data.index(b"e", i)
        num = int(data[i + 1 : end])
        return num, end + 1

    if c == b"l":  # list:  l<item><item>...e
        i += 1
        items = []
        while data[i : i + 1] != b"e":
            value, i = _bdecode(data, i)
            items.append(value)
        return items, i + 1

    if c == b"d":  # dict:  d<key><value>...e  (keys are byte strings, sorted)
        i += 1
        result = OrderedDict()
        while data[i : i + 1] != b"e":
            key, i = _bdecode(data, i)
            value, i = _bdecode(data, i)
            result[key] = value
        return result, i + 1

    if c.isdigit():  # byte string:  <length>:<bytes>
        colon = data.index(b":", i)
        length = int(data[i:colon])
        start = colon + 1
        return data[start : start + length], start + length

    raise ValueError("invalid bencode token at offset %d" % i)


def bencode(value):
    """Encode a Python object (int, bytes, str, list, dict) back to bencode."""
    if isinstance(value, int):
        return b"i" + str(value).encode() + b"e"
    if isinstance(value, bytes):
        return str(len(value)).encode() + b":" + value
    if isinstance(value, str):
        encoded = value.encode()
        return str(len(encoded)).encode() + b":" + encoded
    if isinstance(value, (list, tuple)):
        return b"l" + b"".join(bencode(v) for v in value) + b"e"
    if isinstance(value, dict):
        # Bencode requires dictionary keys to be sorted lexicographically.
        out = b"d"
        for key in sorted(value.keys()):
            out += bencode(key) + bencode(value[key])
        return out + b"e"
    raise TypeError("cannot bencode value of type %s" % type(value).__name__)


# ---------------------------------------------------------------------------
# Torrent — parsed view of a .torrent file.
# ---------------------------------------------------------------------------


class TorrentFile:
    """A single file inside a (possibly multi-file) torrent."""

    def __init__(self, path, length, offset):
        self.path = path        # relative path on disk
        self.length = length    # size in bytes
        self.offset = offset    # absolute byte offset within the whole torrent


class Torrent:
    """Parsed metadata of a .torrent file."""

    def __init__(self, path):
        with open(path, "rb") as fh:
            self.meta = bdecode(fh.read())

        info = self.meta[b"info"]

        # The info-hash uniquely identifies the torrent. It is the SHA-1 of the
        # *bencoded* info dictionary, exactly as it appeared in the file.
        self.info_hash = hashlib.sha1(bencode(info)).digest()

        self.name = info[b"name"].decode("utf-8", "replace")
        self.piece_length = info[b"piece length"]

        # "pieces" is a flat concatenation of 20-byte SHA-1 hashes, one per piece.
        raw = info[b"pieces"]
        self.piece_hashes = [raw[i : i + 20] for i in range(0, len(raw), 20)]

        # A torrent is either single-file (has "length") or multi-file ("files").
        self.files = []
        if b"length" in info:
            self.total_length = info[b"length"]
            self.files.append(TorrentFile(self.name, self.total_length, 0))
        else:
            offset = 0
            for entry in info[b"files"]:
                parts = [p.decode("utf-8", "replace") for p in entry[b"path"]]
                length = entry[b"length"]
                rel = os.path.join(self.name, *parts)
                self.files.append(TorrentFile(rel, length, offset))
                offset += length
            self.total_length = offset

        self.num_pieces = len(self.piece_hashes)

        # Collect every announce URL (the main tracker plus any backups).
        self.trackers = []
        if b"announce" in self.meta:
            self.trackers.append(self.meta[b"announce"].decode())
        for tier in self.meta.get(b"announce-list", []):
            for url in tier:
                u = url.decode()
                if u not in self.trackers:
                    self.trackers.append(u)

    def piece_size(self, index):
        """Length of a given piece (the last piece is usually shorter)."""
        if index == self.num_pieces - 1:
            remainder = self.total_length - self.piece_length * (self.num_pieces - 1)
            return remainder
        return self.piece_length


def make_peer_id():
    """Generate a 20-byte peer id with an Azureus-style client prefix."""
    return b"-CT0001-" + bytes(random.randint(0, 255) for _ in range(12))


# ---------------------------------------------------------------------------
# Trackers — where we discover peers. Supports both HTTP(S) and UDP trackers.
# ---------------------------------------------------------------------------


def parse_compact_peers(blob):
    """Parse the compact peer list (6 bytes each: 4 IP + 2 port)."""
    peers = []
    for i in range(0, len(blob) - 5, 6):
        ip = ".".join(str(b) for b in blob[i : i + 4])
        port = struct.unpack(">H", blob[i + 4 : i + 6])[0]
        peers.append((ip, port))
    return peers


def http_tracker(url, torrent, peer_id, port=6881):
    """Announce to an HTTP/HTTPS tracker and return a list of (ip, port) peers."""
    params = {
        "info_hash": torrent.info_hash,
        "peer_id": peer_id,
        "port": port,
        "uploaded": 0,
        "downloaded": 0,
        "left": torrent.total_length,
        "compact": 1,
        "event": "started",
    }
    query = urllib.parse.urlencode(params)
    request = urllib.request.Request(url + ("&" if "?" in url else "?") + query)
    with urllib.request.urlopen(request, timeout=15) as resp:
        body = bdecode(resp.read())

    if b"failure reason" in body:
        raise RuntimeError(body[b"failure reason"].decode("utf-8", "replace"))

    peers = body.get(b"peers", b"")
    if isinstance(peers, bytes):  # compact format
        return parse_compact_peers(peers)
    # Dictionary format: a list of {ip, port} dicts.
    return [(p[b"ip"].decode(), p[b"port"]) for p in peers]


def udp_tracker(url, torrent, peer_id, port=6881):
    """Announce to a UDP tracker (BEP 15) and return a list of peers."""
    parsed = urllib.parse.urlparse(url)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(10)
    try:
        addr = (socket.gethostbyname(parsed.hostname), parsed.port or 80)

        # Step 1: connect request — exchange a connection id with the tracker.
        transaction_id = random.randint(0, 0xFFFFFFFF)
        connect = struct.pack(">QII", 0x41727101980, 0, transaction_id)
        sock.sendto(connect, addr)
        resp = sock.recv(16)
        action, txn, connection_id = struct.unpack(">IIQ", resp)
        if action != 0 or txn != transaction_id:
            raise RuntimeError("bad UDP connect response")

        # Step 2: announce request — ask for peers using that connection id.
        transaction_id = random.randint(0, 0xFFFFFFFF)
        announce = struct.pack(
            ">QII20s20sQQQIIIiH",
            connection_id, 1, transaction_id,
            torrent.info_hash, peer_id,
            0, torrent.total_length, 0,   # downloaded, left, uploaded
            2, 0, 0, -1, port,            # event=started, ip, key, num_want, port
        )
        sock.sendto(announce, addr)
        resp = sock.recv(4096)
        action, txn = struct.unpack(">II", resp[:8])
        if action != 1:
            raise RuntimeError("bad UDP announce response")
        return parse_compact_peers(resp[20:])
    finally:
        sock.close()


def get_peers(torrent, peer_id):
    """Try every tracker in turn and return the first peer list we obtain."""
    for url in torrent.trackers:
        try:
            if url.startswith("udp"):
                peers = udp_tracker(url, torrent, peer_id)
            else:
                peers = http_tracker(url, torrent, peer_id)
            if peers:
                print("  tracker %s -> %d peers" % (url, len(peers)))
                return peers
        except Exception as exc:  # noqa: BLE001 - report and try the next tracker
            print("  tracker %s failed: %s" % (url, exc))
    return []


# ---------------------------------------------------------------------------
# Peer wire protocol — connect to a peer and exchange pieces. (BEP 3)
# ---------------------------------------------------------------------------

# Message ids in the peer protocol.
CHOKE, UNCHOKE, INTERESTED, NOT_INTERESTED = 0, 1, 2, 3
HAVE, BITFIELD, REQUEST, PIECE, CANCEL = 4, 5, 6, 7, 8

BLOCK_SIZE = 16384  # 16 KiB — the standard request block size.


class Peer:
    """A live TCP connection to one peer, speaking the BitTorrent wire protocol."""

    def __init__(self, ip, port, torrent, peer_id):
        self.ip = ip
        self.port = port
        self.torrent = torrent
        self.peer_id = peer_id
        self.sock = None
        self.choked = True
        self.has_pieces = set()

    def connect(self):
        """Open the TCP connection and perform the BitTorrent handshake."""
        self.sock = socket.create_connection((self.ip, self.port), timeout=8)
        self.sock.settimeout(8)

        # Handshake: <pstrlen=19><"BitTorrent protocol"><8 reserved><info_hash><peer_id>
        pstr = b"BitTorrent protocol"
        handshake = bytes([len(pstr)]) + pstr + b"\x00" * 8
        handshake += self.torrent.info_hash + self.peer_id
        self.sock.sendall(handshake)

        response = self._recv_exact(68)
        if response[28:48] != self.torrent.info_hash:
            raise RuntimeError("info hash mismatch in handshake")

    def _recv_exact(self, n):
        """Read exactly ``n`` bytes from the socket or raise on disconnect."""
        buf = b""
        while len(buf) < n:
            chunk = self.sock.recv(n - len(buf))
            if not chunk:
                raise RuntimeError("peer closed the connection")
            buf += chunk
        return buf

    def _send_message(self, msg_id, payload=b""):
        """Send a length-prefixed peer message."""
        body = bytes([msg_id]) + payload
        self.sock.sendall(struct.pack(">I", len(body)) + body)

    def _read_message(self):
        """Read one peer message. Returns (id, payload); id is None for keep-alive."""
        length = struct.unpack(">I", self._recv_exact(4))[0]
        if length == 0:
            return None, b""  # keep-alive
        data = self._recv_exact(length)
        return data[0], data[1:]

    def handle_bitfield_and_unchoke(self):
        """Tell the peer we're interested and wait until it unchokes us."""
        self._send_message(INTERESTED)
        deadline = time.time() + 15
        while time.time() < deadline:
            msg_id, payload = self._read_message()
            if msg_id == BITFIELD:
                self._parse_bitfield(payload)
            elif msg_id == HAVE:
                self.has_pieces.add(struct.unpack(">I", payload)[0])
            elif msg_id == UNCHOKE:
                self.choked = False
                return True
            elif msg_id == CHOKE:
                self.choked = True
        return not self.choked

    def _parse_bitfield(self, payload):
        """Record which piece indices the peer advertises in its bitfield."""
        for i, byte in enumerate(payload):
            for bit in range(8):
                if byte & (1 << (7 - bit)):
                    self.has_pieces.add(i * 8 + bit)

    def download_piece(self, index):
        """Request every block of a piece and return the assembled bytes."""
        size = self.torrent.piece_size(index)
        data = bytearray(size)
        offset = 0
        while offset < size:
            block = min(BLOCK_SIZE, size - offset)
            self._send_message(REQUEST, struct.pack(">III", index, offset, block))
            # Wait for the matching PIECE response (ignore unrelated traffic).
            while True:
                msg_id, payload = self._read_message()
                if msg_id == PIECE:
                    p_index, p_begin = struct.unpack(">II", payload[:8])
                    if p_index == index and p_begin == offset:
                        data[offset : offset + block] = payload[8:]
                        break
                elif msg_id == CHOKE:
                    raise RuntimeError("peer choked us mid-piece")
            offset += block
        return bytes(data)

    def close(self):
        if self.sock:
            try:
                self.sock.close()
            except OSError:
                pass


# ---------------------------------------------------------------------------
# Piece manager — verifies pieces and writes them to the correct files on disk.
# ---------------------------------------------------------------------------


class PieceManager:
    """Tracks download progress and lays bytes down across the torrent's files."""

    def __init__(self, torrent, output_dir):
        self.torrent = torrent
        self.output_dir = output_dir
        self.completed = set()
        self._prepare_files()

    def _prepare_files(self):
        """Pre-create every output file at its final size (sparse where possible)."""
        for f in self.torrent.files:
            full = os.path.join(self.output_dir, f.path)
            os.makedirs(os.path.dirname(full) or ".", exist_ok=True)
            if not os.path.exists(full) or os.path.getsize(full) != f.length:
                with open(full, "wb") as fh:
                    fh.truncate(f.length)

    def verify(self, index, data):
        """Check a downloaded piece against its expected SHA-1 hash."""
        return hashlib.sha1(data).digest() == self.torrent.piece_hashes[index]

    def write(self, index, data):
        """Write a verified piece, splitting it across file boundaries as needed."""
        piece_start = index * self.torrent.piece_length
        for f in self.torrent.files:
            file_start, file_end = f.offset, f.offset + f.length
            piece_end = piece_start + len(data)
            # Does this piece overlap this file?
            if piece_start < file_end and piece_end > file_start:
                overlap_start = max(piece_start, file_start)
                overlap_end = min(piece_end, file_end)
                full = os.path.join(self.output_dir, f.path)
                with open(full, "r+b") as fh:
                    fh.seek(overlap_start - file_start)
                    fh.write(data[overlap_start - piece_start : overlap_end - piece_start])
        self.completed.add(index)


def progress_bar(done, total, width=40):
    """Render a textual progress bar like  [#####-----]  42%."""
    filled = int(width * done / total) if total else width
    bar = "#" * filled + "-" * (width - filled)
    pct = (100 * done / total) if total else 100
    return "[%s] %5.1f%% (%d/%d pieces)" % (bar, pct, done, total)


# ---------------------------------------------------------------------------
# Download orchestration.
# ---------------------------------------------------------------------------


def download(torrent, output_dir):
    """Discover peers, then download and verify every piece of the torrent."""
    peer_id = make_peer_id()
    os.makedirs(output_dir, exist_ok=True)

    print("Announcing to trackers...")
    peer_list = get_peers(torrent, peer_id)
    if not peer_list:
        print("No peers available — the torrent may be dead or trackers unreachable.")
        return False

    manager = PieceManager(torrent, output_dir)
    needed = list(range(torrent.num_pieces))
    print("Downloading %d pieces from %d peers...\n" % (len(needed), len(peer_list)))

    for ip, port in peer_list:
        if not needed:
            break
        peer = Peer(ip, port, torrent, peer_id)
        try:
            peer.connect()
            if not peer.handle_bitfield_and_unchoke():
                continue
            # Pull every piece this peer has and we still need.
            for index in list(needed):
                if index not in peer.has_pieces:
                    continue
                try:
                    data = peer.download_piece(index)
                except (RuntimeError, OSError):
                    break  # peer broke; move on to the next one
                if manager.verify(index, data):
                    manager.write(index, data)
                    needed.remove(index)
                    done = torrent.num_pieces - len(needed)
                    sys.stdout.write("\r" + progress_bar(done, torrent.num_pieces))
                    sys.stdout.flush()
        except (OSError, RuntimeError):
            continue  # could not reach this peer
        finally:
            peer.close()

    print()
    if not needed:
        print("\nDownload complete — all pieces verified. Saved to %s" % output_dir)
        return True
    print("\nFinished with %d/%d pieces (could not source the rest from available peers)."
          % (torrent.num_pieces - len(needed), torrent.num_pieces))
    return False


# ---------------------------------------------------------------------------
# CLI commands.
# ---------------------------------------------------------------------------


def cmd_info(args):
    """Print human-readable metadata about a torrent."""
    t = Torrent(args.torrent)
    print("Name:         %s" % t.name)
    print("Info hash:    %s" % t.info_hash.hex())
    print("Total size:   %s" % human_size(t.total_length))
    print("Piece length: %s" % human_size(t.piece_length))
    print("Pieces:       %d" % t.num_pieces)
    print("Files:")
    for f in t.files:
        print("  %12s  %s" % (human_size(f.length), f.path))
    print("Trackers:")
    for url in t.trackers:
        print("  %s" % url)


def cmd_peers(args):
    """Query trackers and print the peers they return."""
    t = Torrent(args.torrent)
    peer_id = make_peer_id()
    print("Announcing to %d tracker(s)..." % len(t.trackers))
    peers = get_peers(t, peer_id)
    print("\n%d peer(s):" % len(peers))
    for ip, port in peers:
        print("  %s:%d" % (ip, port))


def cmd_get(args):
    """Download a torrent to disk."""
    t = Torrent(args.torrent)
    print("Torrent: %s (%s, %d pieces)\n" % (t.name, human_size(t.total_length), t.num_pieces))
    ok = download(t, args.output)
    sys.exit(0 if ok else 1)


def human_size(n):
    """Format a byte count as a human-friendly string."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return "%.1f %s" % (n, unit) if unit != "B" else "%d B" % n
        n /= 1024


def cmd_test(args):
    """Run built-in self-tests for the parts that don't need a network."""
    failures = 0

    def check(name, condition):
        nonlocal failures
        status = "ok" if condition else "FAIL"
        if not condition:
            failures += 1
        print("  [%s] %s" % (status, name))

    print("Running self-tests...")

    # Bencode round-trips.
    check("bdecode integer", bdecode(b"i42e") == 42)
    check("bdecode string", bdecode(b"4:spam") == b"spam")
    check("bdecode list", bdecode(b"l4:spam4:eggse") == [b"spam", b"eggs"])
    check("bdecode dict", bdecode(b"d3:cow3:moo4:spam4:eggse")
          == {b"cow": b"moo", b"spam": b"eggs"})
    check("bencode integer", bencode(42) == b"i42e")
    check("bencode string", bencode(b"spam") == b"4:spam")
    check("bencode dict is sorted",
          bencode({b"spam": b"eggs", b"cow": b"moo"}) == b"d3:cow3:moo4:spam4:eggse")

    # Round-trip a nested structure.
    original = {b"a": 1, b"b": [b"x", 2, {b"c": b"d"}]}
    check("bencode/bdecode round-trip", bdecode(bencode(original)) == original)

    # Info-hash + piece verification on a tiny synthetic torrent.
    payload = b"hello clawtorrent" * 100  # 1700 bytes
    piece_len = 512
    pieces = b"".join(
        hashlib.sha1(payload[i : i + piece_len]).digest()
        for i in range(0, len(payload), piece_len)
    )
    info = {
        b"name": b"test.bin",
        b"length": len(payload),
        b"piece length": piece_len,
        b"pieces": pieces,
    }
    meta = {b"announce": b"http://tracker.example/announce", b"info": info}

    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".torrent", delete=False) as tf:
        tf.write(bencode(meta))
        torrent_path = tf.name
    try:
        t = Torrent(torrent_path)
        check("parsed total length", t.total_length == len(payload))
        check("parsed piece count", t.num_pieces == 4)
        check("info hash matches", t.info_hash == hashlib.sha1(bencode(info)).digest())
        check("last piece size", t.piece_size(3) == len(payload) - 512 * 3)

        # Simulate downloading + verifying + writing the payload, then read it back.
        outdir = tempfile.mkdtemp()
        manager = PieceManager(t, outdir)
        for idx in range(t.num_pieces):
            start = idx * piece_len
            chunk = payload[start : start + t.piece_size(idx)]
            ok = manager.verify(idx, chunk)
            check("verify piece %d" % idx, ok)
            manager.write(idx, chunk)
        with open(os.path.join(outdir, "test.bin"), "rb") as fh:
            written = fh.read()
        check("reassembled file matches", written == payload)

        # A corrupted piece must fail verification.
        check("corrupt piece rejected", not manager.verify(0, b"x" * t.piece_size(0)))
    finally:
        os.unlink(torrent_path)

    print()
    if failures:
        print("%d test(s) FAILED" % failures)
        sys.exit(1)
    print("All tests passed.")


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="clawtorrent",
        description="A minimal BitTorrent client written from scratch in pure Python.",
    )
    sub = parser.add_subparsers(dest="command")

    p_info = sub.add_parser("info", help="show torrent metadata")
    p_info.add_argument("torrent")
    p_info.set_defaults(func=cmd_info)

    p_peers = sub.add_parser("peers", help="list peers from the tracker")
    p_peers.add_argument("torrent")
    p_peers.set_defaults(func=cmd_peers)

    p_get = sub.add_parser("get", help="download a torrent")
    p_get.add_argument("torrent")
    p_get.add_argument("-o", "--output", default=".", help="output directory")
    p_get.set_defaults(func=cmd_get)

    p_test = sub.add_parser("test", help="run built-in self-tests")
    p_test.set_defaults(func=cmd_test)

    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        sys.exit(1)
    try:
        args.func(args)
    except FileNotFoundError as exc:
        print("Error: file not found — %s" % exc.filename, file=sys.stderr)
        sys.exit(1)
    except (ValueError, RuntimeError) as exc:
        print("Error: %s" % exc, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

# Built by clavexis — github.com/clavexis
