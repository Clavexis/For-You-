#!/usr/bin/env python3
"""
Auto Code Reviewer — get a full AI code review for any file or piped input.

  - Accepts a file path, multiple files, or code piped on stdin.
  - Reviews for bugs, style, performance, and security.
  - Prints findings grouped by severity, with line references and suggested
    fixes (diff-style where useful).
  - Auto-detects the language from the file extension.

Usage:
  review.py myfile.py
  review.py src/*.js
  cat snippet.cpp | review.py --lang cpp
  review.py myfile.py --focus security --save review.md

Built by clavexis — github.com/clavexis
"""

import argparse
import os
import sys
from pathlib import Path

try:
    import anthropic
except ImportError:
    sys.stderr.write(
        "Error: the 'anthropic' package is required.\n"
        "Install it with:  pip install anthropic\n"
    )
    sys.exit(1)

DEFAULT_MODEL = "claude-opus-4-8"

# Map common extensions to human-readable language names for the prompt.
EXT_LANG = {
    ".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript (React)",
    ".ts": "TypeScript", ".tsx": "TypeScript (React)", ".java": "Java",
    ".c": "C", ".h": "C header", ".cpp": "C++", ".cc": "C++", ".cxx": "C++",
    ".hpp": "C++ header", ".go": "Go", ".rs": "Rust", ".rb": "Ruby",
    ".php": "PHP", ".cs": "C#", ".swift": "Swift", ".kt": "Kotlin",
    ".sh": "Bash", ".sql": "SQL", ".html": "HTML", ".css": "CSS",
}


class C:
    RESET = "\033[0m"; BOLD = "\033[1m"; DIM = "\033[2m"
    CYAN = "\033[36m"; GREEN = "\033[32m"; YELLOW = "\033[33m"; RED = "\033[31m"

    @classmethod
    def off(cls):
        for n in ("RESET", "BOLD", "DIM", "CYAN", "GREEN", "YELLOW", "RED"):
            setattr(cls, n, "")


if not sys.stdout.isatty() or os.environ.get("NO_COLOR"):
    C.off()


def detect_language(path: str | None, override: str | None) -> str:
    if override:
        return override
    if path:
        return EXT_LANG.get(Path(path).suffix.lower(), "the source language")
    return "the source language"


def add_line_numbers(code: str) -> str:
    """Prefix each line with its number so the model can reference lines."""
    return "\n".join(f"{i:>4} | {line}" for i, line in enumerate(code.splitlines(), 1))


SYSTEM_PROMPT = (
    "You are a meticulous senior software engineer doing a code review. "
    "Review the provided code for: (1) Bugs and correctness issues, "
    "(2) Security vulnerabilities, (3) Performance problems, (4) Style and "
    "readability. The code is shown with line numbers in a 'NNN | code' format.\n\n"
    "Output a Markdown report with these sections, omitting any that are empty:\n"
    "## Summary  — one or two sentences.\n"
    "## Critical  — bugs/security issues that must be fixed.\n"
    "## Warnings  — likely problems or risky patterns.\n"
    "## Suggestions  — style, readability, minor improvements.\n\n"
    "For each finding cite the line number(s) and, when helpful, show a short "
    "before/after diff using ```diff fenced blocks with - and + lines. "
    "Be specific and concise. If the code is solid, say so."
)


def review_code(client, model, language, code, focus, max_tokens) -> str:
    numbered = add_line_numbers(code)
    instruction = f"Please review this {language} code"
    if focus:
        instruction += f", focusing especially on {focus}"
    instruction += ":\n\n```\n" + numbered + "\n```"

    chunks: list[str] = []
    with client.messages.stream(
        model=model, max_tokens=max_tokens, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": instruction}],
    ) as stream:
        for text in stream.text_stream:
            chunks.append(text)
            print(text, end="", flush=True)
    print()
    return "".join(chunks)


def read_inputs(args) -> list[tuple[str, str]]:
    """Return a list of (label, code) pairs from files and/or stdin."""
    inputs: list[tuple[str, str]] = []
    for path in args.files:
        try:
            inputs.append((path, Path(path).read_text()))
        except OSError as exc:
            sys.stderr.write(f"{C.RED}Could not read {path}: {exc}{C.RESET}\n")
    if not args.files and not sys.stdin.isatty():
        piped = sys.stdin.read()
        if piped.strip():
            inputs.append(("<stdin>", piped))
    return inputs


def main() -> int:
    ap = argparse.ArgumentParser(description="AI code reviewer for any source file.")
    ap.add_argument("files", nargs="*", help="Source file(s) to review. Omit to read stdin.")
    ap.add_argument("--lang", help="Override detected language (e.g. 'Python', 'C++').")
    ap.add_argument("--focus", help="Focus area: bugs | security | performance | style.")
    ap.add_argument("-m", "--model", default=DEFAULT_MODEL, help="Anthropic model ID.")
    ap.add_argument("--max-tokens", type=int, default=2500, help="Max output tokens.")
    ap.add_argument("--save", metavar="FILE", help="Append the review to a Markdown file.")
    args = ap.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.stderr.write(
            f"{C.RED}No API key found.{C.RESET}\n"
            "Set one with:  export ANTHROPIC_API_KEY=sk-ant-...\n"
        )
        return 1

    inputs = read_inputs(args)
    if not inputs:
        sys.stderr.write(f"{C.RED}No input. Pass a file path or pipe code on stdin.{C.RESET}\n")
        return 1

    client = anthropic.Anthropic(api_key=api_key)
    all_reports: list[str] = []

    for label, code in inputs:
        if not code.strip():
            continue
        language = detect_language(label if label != "<stdin>" else None, args.lang)
        print(f"{C.CYAN}{C.BOLD}── Reviewing {label} ({language}) ──{C.RESET}\n")
        try:
            report = review_code(client, args.model, language, code, args.focus, args.max_tokens)
        except anthropic.APIStatusError as exc:
            sys.stderr.write(f"\n{C.RED}API error {exc.status_code}: {exc.message}{C.RESET}\n")
            return 1
        except anthropic.APIConnectionError as exc:
            sys.stderr.write(f"\n{C.RED}Connection error: {exc}{C.RESET}\n")
            return 1
        all_reports.append(f"# Review: {label} ({language})\n\n{report}\n")
        print()

    if args.save and all_reports:
        try:
            with open(args.save, "a") as fh:
                fh.write("\n\n".join(all_reports))
                fh.write("\n\n_Generated by Auto Code Reviewer — clavexis_\n")
            print(f"{C.GREEN}Saved review to {args.save}{C.RESET}")
        except OSError as exc:
            sys.stderr.write(f"{C.RED}Could not save: {exc}{C.RESET}\n")
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
