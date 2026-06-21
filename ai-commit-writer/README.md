# AI Commit Message Writer

Stop agonising over commit messages. Run one command in any git repo and get a clean **Conventional Commits** message generated from your diff — optionally committing it for you.

## Demo

```text
$ git add .
$ aicommit

Suggested commit message:

feat(auth): add JWT refresh-token rotation

- Issue a new refresh token on every access-token renewal
- Invalidate the previous token to prevent replay
- Add expiry checks in the auth middleware

Run again with --commit to use this message, or copy it manually.
```

## Features

- **Reads your git diff automatically** — staged changes by default, or everything with `--all`.
- **Conventional Commits** format: `type(scope): summary` + bullet points.
- **One-command commit** — `aicommit --commit` generates *and* commits.
- **Type hints** — `--type fix` nudges the commit type.
- Works in **any git repository**.

## Installation

Requires **Python 3.6+**, **git**, and an Anthropic API key.

### Linux
```bash
cd linux && ./install.sh
export ANTHROPIC_API_KEY=sk-ant-...
```

### macOS (Apple Silicon & Intel)
```bash
cd mac && ./install.sh
export ANTHROPIC_API_KEY=sk-ant-...
```

### Windows
```powershell
cd windows
install.bat
set ANTHROPIC_API_KEY=sk-ant-...
```

## Usage

```bash
git add .                  # stage your changes
aicommit                   # suggest a message for staged changes
aicommit --all             # include unstaged changes too
aicommit --commit          # generate and commit in one step
aicommit --type fix        # hint the commit type
```

A handy git alias:
```bash
git config --global alias.ai '!aicommit --commit'
# then:  git add .  &&  git ai
```

## How it works

```text
git diff (staged) ──▶ build prompt (files + diff) ──▶ Claude
                  ──▶ Conventional Commits message ──▶ print / git commit -m
```

The diff is truncated to a sane size before sending, and the prompt asks for a single, well-formed message — no preamble, no code fences.

## Tech stack

- **Python 3** standard library (subprocess + git)
- [`anthropic`](https://pypi.org/project/anthropic/) SDK (`claude-opus-4-8`)

---

Built by clavexis — [github.com/clavexis](https://github.com/clavexis)
