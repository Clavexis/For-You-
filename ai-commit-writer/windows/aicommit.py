#!/usr/bin/env python3
"""
AI Commit Message Writer — generate a great commit message from your git diff.

  - Reads the git diff automatically from the current repo
  - Sends it to Claude and gets back a Conventional Commits message
  - One command: run it in any git repo
  - Optionally commits with the generated message (--commit)

Usage:
  aicommit.py                # staged changes -> suggested message
  aicommit.py --all          # include unstaged changes
  aicommit.py --commit       # generate and commit in one step
  aicommit.py --type fix     # hint the commit type

Built by clavexis — github.com/clavexis
"""

import argparse
import os
import subprocess
import sys

DEFAULT_MODEL = "claude-opus-4-8"
MAX_DIFF_CHARS = 12000


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
# Git helpers (testable in any repo).
# ---------------------------------------------------------------------------
def git(*args) -> str:
    return subprocess.check_output(["git", *args], text=True, stderr=subprocess.DEVNULL)


def in_git_repo() -> bool:
    try:
        git("rev-parse", "--is-inside-work-tree")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_diff(include_unstaged: bool) -> str:
    """Return the diff to summarise: staged by default, or all changes."""
    if include_unstaged:
        diff = git("diff", "HEAD")  # staged + unstaged vs HEAD
    else:
        diff = git("diff", "--cached")  # staged only
    return diff


def changed_files(include_unstaged: bool) -> list:
    args = ["diff", "--name-only"] + (["HEAD"] if include_unstaged else ["--cached"])
    out = git(*args).strip()
    return out.splitlines() if out else []


SYSTEM_PROMPT = (
    "You are an expert at writing git commit messages in the Conventional Commits "
    "style. Given a git diff, produce ONE commit message:\n"
    "- First line: `type(scope): summary` (≤ 72 chars). type ∈ feat, fix, docs, "
    "style, refactor, perf, test, build, ci, chore.\n"
    "- Then a blank line and 1-4 bullet points describing the key changes, if "
    "warranted.\n"
    "Output ONLY the commit message — no preamble, no code fences."
)


def build_prompt(diff: str, files: list, type_hint: str) -> str:
    prompt = ""
    if files:
        prompt += "Changed files:\n" + "\n".join(f"  {f}" for f in files) + "\n\n"
    if type_hint:
        prompt += f"Preferred commit type: {type_hint}\n\n"
    prompt += "Diff:\n" + diff[:MAX_DIFF_CHARS]
    if len(diff) > MAX_DIFF_CHARS:
        prompt += "\n... (diff truncated)"
    return prompt


def generate_message(diff: str, files: list, type_hint: str, model: str) -> str:
    try:
        import anthropic
    except ImportError:
        raise RuntimeError("This needs the 'anthropic' package.  pip install anthropic")
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError("Set ANTHROPIC_API_KEY to generate messages.")
    client = anthropic.Anthropic(api_key=key)
    msg = client.messages.create(
        model=model, max_tokens=400, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_prompt(diff, files, type_hint)}],
    )
    return "".join(b.text for b in msg.content if b.type == "text").strip()


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate a commit message from your git diff.")
    ap.add_argument("--all", action="store_true", help="Include unstaged changes.")
    ap.add_argument("--commit", action="store_true", help="Commit with the generated message.")
    ap.add_argument("--type", dest="type_hint", help="Preferred commit type (feat, fix, ...).")
    ap.add_argument("-m", "--model", default=DEFAULT_MODEL, help="Anthropic model.")
    args = ap.parse_args()

    if not in_git_repo():
        sys.stderr.write(f"{C.RED}Not inside a git repository.{C.RESET}\n")
        return 1

    diff = get_diff(args.all)
    if not diff.strip():
        hint = "" if args.all else " (try --all, or `git add` your changes first)"
        sys.stderr.write(f"{C.YELLOW}No changes to summarise{hint}.{C.RESET}\n")
        return 1

    files = changed_files(args.all)
    try:
        message = generate_message(diff, files, args.type_hint, args.model)
    except RuntimeError as exc:
        sys.stderr.write(f"{C.RED}{exc}{C.RESET}\n")
        return 1
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(f"{C.RED}API error: {exc}{C.RESET}\n")
        return 1

    print(f"\n{C.CYAN}{C.BOLD}Suggested commit message:{C.RESET}\n")
    print(message)
    print()

    if args.commit:
        if args.all:
            git("add", "-A")
        try:
            subprocess.run(["git", "commit", "-m", message], check=True)
            print(f"{C.GREEN}Committed.{C.RESET}")
        except subprocess.CalledProcessError:
            sys.stderr.write(f"{C.RED}git commit failed.{C.RESET}\n")
            return 1
    else:
        print(f"{C.DIM}Run again with --commit to use this message, or copy it manually.{C.RESET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
