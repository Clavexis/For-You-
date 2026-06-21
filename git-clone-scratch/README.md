# mygit — Git from Scratch

A minimal reimplementation of git's core, in Python, **using no git at all**. It builds the same content-addressable object model — blobs, trees, and commits identified by SHA-1 — so its object hashes are **byte-for-byte compatible with real git**.

## Demo

```text
$ mygit init
Initialised empty mygit repository in /project/.mygit

$ echo "hello world" > a.txt
$ mygit add a.txt
added a.txt
$ mygit commit -m "first commit"
[main 4b40e6b] first commit

$ mygit log
commit 4b40e6b801d8b8c41a162e8b100e3f354529f241
  2026-06-21 17:45
  first commit
```

## It's actually git-compatible

The blob for `"hello world\n"` hashes to `3b18e512dba79e4c8300dd08aeb37f8e728b8dad` — **exactly** what `git hash-object` produces, because mygit uses git's real object format (`"<type> <len>\0<content>"`, zlib-compressed, SHA-1 addressed).

## Features

- **`init`** — create a repository (`.mygit/` with `objects/`, `refs/`, `HEAD`).
- **`add`** — hash files into **blob** objects and stage them in the index.
- **`commit`** — build a **tree** from the index and a **commit** object linked to its parent.
- **`log`** — walk the commit chain (newest first).
- **`diff`** — show files modified since the last `add`.
- **`status`** — show staged changes on the current branch.
- **`branch`** — create and list branches.
- **SHA-1 object IDs**, **zlib-compressed object storage** — just like git.

## Installation

Pure **Python 3.6+** — no dependencies.

### Linux
```bash
cd linux && ./install.sh
mygit init
```

### macOS (Apple Silicon & Intel)
```bash
cd mac && ./install.sh
mygit init
```

### Windows
```powershell
cd windows
python mygit.py init
```

## Usage

```bash
mygit init
mygit add file1.txt file2.txt
mygit commit -m "your message"
mygit log
mygit diff
mygit status
mygit branch              # list branches
mygit branch feature      # create a branch
```

## The object model

```text
add file ──▶ blob object  (SHA-1 of "blob <len>\0<content>")
commit   ──▶ tree object   (lists staged blobs)
         ──▶ commit object (tree + parent + author + message)
HEAD ──▶ refs/heads/<branch> ──▶ latest commit id
```

Every object is stored, zlib-compressed, at `.mygit/objects/<first2>/<rest>` — the same fan-out layout git uses.

## Tech stack

- **Python 3** standard library — `hashlib` (SHA-1), `zlib` (compression)
- git's content-addressable object model, reimplemented from scratch

---

Built by clavexis — [github.com/clavexis](https://github.com/clavexis)
