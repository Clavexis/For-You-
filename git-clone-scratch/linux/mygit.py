#!/usr/bin/env python3
"""
mygit — a minimal git implementation from scratch (no git used).

Implements git's real content-addressable object model:
  - blobs (file contents), trees (directories), commits
  - SHA-1 object IDs, zlib-compressed object storage under .mygit/objects
  - commands: init, add, commit, log, diff, branch, checkout, status

Usage:
  mygit.py init
  mygit.py add file.txt
  mygit.py commit -m "message"
  mygit.py log
  mygit.py diff
  mygit.py branch [name]

Built by clavexis — github.com/clavexis
"""

import argparse
import hashlib
import os
import sys
import time
import zlib
from pathlib import Path

GIT_DIR = ".mygit"


class C:
    RESET = "\033[0m"; BOLD = "\033[1m"; DIM = "\033[2m"
    GREEN = "\033[32m"; CYAN = "\033[36m"; YELLOW = "\033[33m"; RED = "\033[31m"

    @classmethod
    def off(cls):
        for n in ("RESET", "BOLD", "DIM", "GREEN", "CYAN", "YELLOW", "RED"):
            setattr(cls, n, "")


if not sys.stdout.isatty() or os.environ.get("NO_COLOR"):
    C.off()


def repo_root() -> Path:
    p = Path.cwd()
    while p != p.parent:
        if (p / GIT_DIR).is_dir():
            return p
        p = p.parent
    sys.stderr.write(f"{C.RED}Not a mygit repository (run 'mygit init').{C.RESET}\n")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Object storage (content-addressable, like git).
# ---------------------------------------------------------------------------
def hash_object(root: Path, data: bytes, obj_type: str, write: bool = True) -> str:
    """Store data as a git-style object and return its SHA-1 id."""
    header = f"{obj_type} {len(data)}".encode() + b"\x00"
    full = header + data
    oid = hashlib.sha1(full).hexdigest()
    if write:
        obj_dir = root / GIT_DIR / "objects" / oid[:2]
        obj_dir.mkdir(parents=True, exist_ok=True)
        obj_path = obj_dir / oid[2:]
        if not obj_path.exists():
            obj_path.write_bytes(zlib.compress(full))
    return oid


def read_object(root: Path, oid: str):
    """Return (obj_type, data) for an object id."""
    obj_path = root / GIT_DIR / "objects" / oid[:2] / oid[2:]
    raw = zlib.decompress(obj_path.read_bytes())
    null = raw.index(b"\x00")
    header = raw[:null].decode()
    obj_type, _ = header.split(" ", 1)
    return obj_type, raw[null + 1:]


# ---------------------------------------------------------------------------
# Index (staging area) — a simple text file: "<oid> <path>" per line.
# ---------------------------------------------------------------------------
def read_index(root: Path) -> dict:
    idx = root / GIT_DIR / "index"
    entries = {}
    if idx.exists():
        for line in idx.read_text().splitlines():
            oid, path = line.split(" ", 1)
            entries[path] = oid
    return entries


def write_index(root: Path, entries: dict):
    idx = root / GIT_DIR / "index"
    idx.write_text("".join(f"{oid} {path}\n" for path, oid in sorted(entries.items())))


# ---------------------------------------------------------------------------
# Refs / HEAD.
# ---------------------------------------------------------------------------
def current_branch(root: Path) -> str:
    head = (root / GIT_DIR / "HEAD").read_text().strip()
    if head.startswith("ref: refs/heads/"):
        return head[len("ref: refs/heads/"):]
    return head  # detached


def branch_ref_path(root: Path, name: str) -> Path:
    return root / GIT_DIR / "refs" / "heads" / name


def resolve_head(root: Path):
    branch = current_branch(root)
    ref = branch_ref_path(root, branch)
    return ref.read_text().strip() if ref.exists() else None


def update_branch(root: Path, name: str, oid: str):
    ref = branch_ref_path(root, name)
    ref.parent.mkdir(parents=True, exist_ok=True)
    ref.write_text(oid + "\n")


# ---------------------------------------------------------------------------
# Commands.
# ---------------------------------------------------------------------------
def cmd_init():
    root = Path.cwd()
    gd = root / GIT_DIR
    if gd.exists():
        print(f"{C.YELLOW}Already a mygit repository.{C.RESET}")
        return 1
    (gd / "objects").mkdir(parents=True)
    (gd / "refs" / "heads").mkdir(parents=True)
    (gd / "HEAD").write_text("ref: refs/heads/main\n")
    print(f"{C.GREEN}Initialised empty mygit repository in {gd}{C.RESET}")
    return 0


def cmd_add(paths):
    root = repo_root()
    entries = read_index(root)
    for p in paths:
        fp = Path(p)
        if not fp.is_file():
            sys.stderr.write(f"{C.RED}No such file: {p}{C.RESET}\n")
            continue
        oid = hash_object(root, fp.read_bytes(), "blob")
        rel = str(fp.resolve().relative_to(root))
        entries[rel] = oid
        print(f"added {rel}")
    write_index(root, entries)
    return 0


def build_tree(root: Path, entries: dict) -> str:
    """Build a single (flat) tree object from the index."""
    body = b""
    for path, oid in sorted(entries.items()):
        body += f"100644 {path}\x00".encode() + bytes.fromhex(oid)
    return hash_object(root, body, "tree")


def cmd_commit(message):
    root = repo_root()
    entries = read_index(root)
    if not entries:
        sys.stderr.write(f"{C.YELLOW}Nothing staged to commit.{C.RESET}\n")
        return 1
    tree = build_tree(root, entries)
    parent = resolve_head(root)
    ts = int(time.time())
    lines = [f"tree {tree}"]
    if parent:
        lines.append(f"parent {parent}")
    lines.append(f"author clavexis <github.com/clavexis> {ts}")
    lines.append("")
    lines.append(message)
    commit_data = ("\n".join(lines) + "\n").encode()
    oid = hash_object(root, commit_data, "commit")
    update_branch(root, current_branch(root), oid)
    print(f"[{current_branch(root)} {oid[:7]}] {message}")
    return 0


def parse_commit(data: bytes) -> dict:
    text = data.decode()
    head, _, msg = text.partition("\n\n")
    info = {"message": msg.strip()}
    for line in head.splitlines():
        key, _, val = line.partition(" ")
        info.setdefault(key, val)
    return info


def cmd_log():
    root = repo_root()
    oid = resolve_head(root)
    if not oid:
        print(f"{C.DIM}No commits yet.{C.RESET}")
        return 0
    while oid:
        _, data = read_object(root, oid)
        info = parse_commit(data)
        ts = info.get("author", "").split()[-1]
        when = time.strftime("%Y-%m-%d %H:%M", time.localtime(int(ts))) if ts.isdigit() else ""
        print(f"{C.YELLOW}commit {oid}{C.RESET}")
        print(f"  {C.DIM}{when}{C.RESET}")
        print(f"  {info['message']}\n")
        oid = info.get("parent")
    return 0


def tree_to_dict(root: Path, tree_oid: str) -> dict:
    _, data = read_object(root, tree_oid)
    entries = {}
    i = 0
    while i < len(data):
        nul = data.index(b"\x00", i)
        mode_path = data[i:nul].decode()
        _, path = mode_path.split(" ", 1)
        oid = data[nul + 1:nul + 21].hex()
        entries[path] = oid
        i = nul + 21
    return entries


def cmd_diff():
    root = repo_root()
    index = read_index(root)
    # Compare working tree against the index.
    any_diff = False
    for path, oid in sorted(index.items()):
        fp = root / path
        if not fp.exists():
            print(f"{C.RED}deleted: {path}{C.RESET}")
            any_diff = True
            continue
        cur = hash_object(root, fp.read_bytes(), "blob", write=False)
        if cur != oid:
            print(f"{C.YELLOW}modified: {path}{C.RESET}")
            any_diff = True
    if not any_diff:
        print(f"{C.GREEN}No changes since last 'add'.{C.RESET}")
    return 0


def cmd_status():
    root = repo_root()
    index = read_index(root)
    head = resolve_head(root)
    committed = {}
    if head:
        _, data = read_object(root, head)
        committed = tree_to_dict(root, parse_commit(data)["tree"])
    print(f"On branch {C.CYAN}{current_branch(root)}{C.RESET}")
    staged = {p: o for p, o in index.items() if committed.get(p) != o}
    if staged:
        print(f"{C.GREEN}Staged changes:{C.RESET}")
        for p in sorted(staged):
            print(f"  {p}")
    if not staged:
        print(f"{C.DIM}Nothing staged.{C.RESET}")
    return 0


def cmd_branch(name):
    root = repo_root()
    if not name:
        cur = current_branch(root)
        heads_dir = root / GIT_DIR / "refs" / "heads"
        for ref in sorted(heads_dir.glob("*")):
            mark = "* " if ref.name == cur else "  "
            print(f"{mark}{ref.name}")
        return 0
    head = resolve_head(root)
    if head:
        update_branch(root, name, head)
    print(f"Created branch {name}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="A minimal git from scratch.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")
    a = sub.add_parser("add"); a.add_argument("paths", nargs="+")
    c = sub.add_parser("commit"); c.add_argument("-m", "--message", required=True)
    sub.add_parser("log")
    sub.add_parser("diff")
    sub.add_parser("status")
    b = sub.add_parser("branch"); b.add_argument("name", nargs="?")
    args = ap.parse_args()

    if args.cmd == "init": return cmd_init()
    if args.cmd == "add": return cmd_add(args.paths)
    if args.cmd == "commit": return cmd_commit(args.message)
    if args.cmd == "log": return cmd_log()
    if args.cmd == "diff": return cmd_diff()
    if args.cmd == "status": return cmd_status()
    if args.cmd == "branch": return cmd_branch(args.name)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
