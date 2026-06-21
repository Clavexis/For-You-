#!/usr/bin/env python3
"""
clawfmt — a language-agnostic code formatter and style linter.

Checks (and optionally fixes) common whitespace and style problems across
Python, JavaScript, C/C++ and other text source files. Rules are configurable
via a JSON file, it has an auto-fix mode, and it returns CI-friendly exit codes.
Pure Python standard library — no third-party dependencies.

    clawfmt check  file ...            report issues (exit 1 if any are found)
    clawfmt fix    file ...            rewrite files, fixing what can be fixed
    clawfmt diff   file ...            show what fix would change, without writing
    clawfmt test                       run the built-in self-tests

Configuration is read from --config PATH or a ".clawfmt.json" found by walking
up from the file. See DEFAULT_CONFIG below for all options.

Built by clavexis — github.com/clavexis
"""

import sys
import os
import json
import argparse
import difflib

# ---------------------------------------------------------------------------
# Configuration.
# ---------------------------------------------------------------------------

DEFAULT_CONFIG = {
    "indent_size": 4,          # spaces per indent level when expanding tabs
    "use_tabs": False,         # if true, indentation should use tabs, not spaces
    "max_line_length": 100,    # flag lines longer than this (0 disables)
    "max_blank_lines": 2,      # collapse runs of blank lines down to this many
    "trim_trailing_whitespace": True,
    "insert_final_newline": True,
    "normalize_line_endings": True,   # convert CRLF/CR to LF
    "trim_trailing_blank_lines": True,
}

# Per-extension overrides — sensible defaults for each language.
LANGUAGE_DEFAULTS = {
    ".py": {"indent_size": 4, "max_line_length": 88},
    ".js": {"indent_size": 2, "max_line_length": 100},
    ".ts": {"indent_size": 2, "max_line_length": 100},
    ".jsx": {"indent_size": 2, "max_line_length": 100},
    ".c": {"indent_size": 4, "max_line_length": 100},
    ".h": {"indent_size": 4, "max_line_length": 100},
    ".cpp": {"indent_size": 4, "max_line_length": 100},
    ".hpp": {"indent_size": 4, "max_line_length": 100},
    ".go": {"use_tabs": True, "max_line_length": 120},
    ".md": {"max_line_length": 0, "trim_trailing_whitespace": False},
}


def load_config(path, explicit=None):
    """Build the effective config for ``path``.

    Precedence (low → high): DEFAULT_CONFIG, language defaults for the file's
    extension, a discovered/explicit .clawfmt.json file.
    """
    config = dict(DEFAULT_CONFIG)
    ext = os.path.splitext(path)[1].lower()
    config.update(LANGUAGE_DEFAULTS.get(ext, {}))

    config_file = explicit or _find_config_file(path)
    if config_file and os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as fh:
                user = json.load(fh)
            # Apply a top-level block and any per-extension block it defines.
            config.update({k: v for k, v in user.items() if not k.startswith(".")})
            if ext in user:
                config.update(user[ext])
        except (OSError, json.JSONDecodeError) as exc:
            print("warning: could not read config %s: %s" % (config_file, exc),
                  file=sys.stderr)
    return config


def _find_config_file(start_path):
    """Walk up the directory tree looking for a .clawfmt.json."""
    directory = os.path.dirname(os.path.abspath(start_path))
    while True:
        candidate = os.path.join(directory, ".clawfmt.json")
        if os.path.exists(candidate):
            return candidate
        parent = os.path.dirname(directory)
        if parent == directory:
            return None
        directory = parent


# ---------------------------------------------------------------------------
# Linting — report problems without changing anything.
# ---------------------------------------------------------------------------


class Issue:
    """A single style problem at a specific line."""

    def __init__(self, line, code, message):
        self.line = line
        self.code = code
        self.message = message

    def __repr__(self):
        return "Issue(%d, %r, %r)" % (self.line, self.code, self.message)


def lint_text(text, config):
    """Return a list of Issue objects for ``text`` under ``config``."""
    issues = []

    # Line-ending check operates on the raw text before splitting.
    if config["normalize_line_endings"] and ("\r\n" in text or "\r" in text):
        issues.append(Issue(0, "CRLF", "file uses non-LF line endings"))

    lines = text.split("\n")
    max_len = config["max_line_length"]

    for i, line in enumerate(lines, 1):
        stripped_eol = line.rstrip("\r")

        if config["trim_trailing_whitespace"] and stripped_eol != stripped_eol.rstrip():
            issues.append(Issue(i, "TRAIL", "trailing whitespace"))

        if max_len and len(stripped_eol.expandtabs(config["indent_size"])) > max_len:
            issues.append(Issue(
                i, "LONG", "line exceeds %d columns (%d)"
                % (max_len, len(stripped_eol.expandtabs(config["indent_size"])))))

        # Indentation consistency: flag the style we are NOT configured for.
        indent = stripped_eol[: len(stripped_eol) - len(stripped_eol.lstrip())]
        if config["use_tabs"] and " " in indent and "\t" in indent:
            issues.append(Issue(i, "MIXIND", "mixed tabs and spaces in indentation"))
        elif not config["use_tabs"] and "\t" in indent:
            issues.append(Issue(i, "TABIND", "tab used for indentation (expected spaces)"))

    # Whole-file checks.
    if config["insert_final_newline"] and text and not text.endswith("\n"):
        issues.append(Issue(len(lines), "EOFNL", "no newline at end of file"))

    if config["trim_trailing_blank_lines"]:
        trailing = _count_trailing_blanks(lines)
        if trailing > 0:
            issues.append(Issue(len(lines), "EOFBLANK",
                                "%d blank line(s) at end of file" % trailing))

    if config["max_blank_lines"] >= 0:
        for start, run in _blank_runs(lines):
            if run > config["max_blank_lines"]:
                issues.append(Issue(start + 1, "BLANKS",
                                    "%d consecutive blank lines (max %d)"
                                    % (run, config["max_blank_lines"])))

    issues.sort(key=lambda it: (it.line, it.code))
    return issues


def _count_trailing_blanks(lines):
    """How many blank lines sit at the end (ignoring the final newline slot)."""
    # A trailing "\n" produces an empty final element; don't count that one.
    end = len(lines) - 1 if lines and lines[-1] == "" else len(lines)
    count = 0
    i = end - 1
    while i >= 0 and lines[i].strip() == "":
        count += 1
        i -= 1
    return count


def _blank_runs(lines):
    """Yield (start_index, length) for each maximal run of blank lines."""
    i = 0
    n = len(lines)
    while i < n:
        if lines[i].strip() == "":
            start = i
            while i < n and lines[i].strip() == "":
                i += 1
            yield start, i - start
        else:
            i += 1


# ---------------------------------------------------------------------------
# Formatting — produce a corrected version of the text.
# ---------------------------------------------------------------------------


def format_text(text, config):
    """Return a fixed copy of ``text`` applying every enabled rule."""
    # 1. Normalise line endings first so everything downstream sees plain "\n".
    if config["normalize_line_endings"]:
        text = text.replace("\r\n", "\n").replace("\r", "\n")

    lines = text.split("\n")
    had_final_newline = text.endswith("\n")
    if had_final_newline:
        lines = lines[:-1]  # drop the empty element the trailing \n creates

    fixed = []
    for line in lines:
        # 2. Convert leading tabs/spaces to the configured indentation style.
        line = _fix_indentation(line, config)
        # 3. Strip trailing whitespace.
        if config["trim_trailing_whitespace"]:
            line = line.rstrip()
        fixed.append(line)

    # 4. Collapse over-long runs of blank lines.
    if config["max_blank_lines"] >= 0:
        fixed = _collapse_blanks(fixed, config["max_blank_lines"])

    # 5. Trim trailing blank lines.
    if config["trim_trailing_blank_lines"]:
        while fixed and fixed[-1].strip() == "":
            fixed.pop()

    result = "\n".join(fixed)

    # 6. Ensure exactly one final newline (if the file had any content).
    if config["insert_final_newline"]:
        if result:
            result += "\n"
    elif had_final_newline:
        result += "\n"

    return result


def _fix_indentation(line, config):
    """Rewrite the leading whitespace of a line to the configured style."""
    stripped = line.lstrip(" \t")
    indent = line[: len(line) - len(stripped)]
    if not indent:
        return line

    if config["use_tabs"]:
        # Convert leading spaces (in indent_size chunks) to tabs.
        spaces = indent.replace("\t", " " * config["indent_size"])
        tabs = "\t" * (len(spaces) // config["indent_size"])
        remainder = " " * (len(spaces) % config["indent_size"])
        return tabs + remainder + stripped
    # Spaces mode: expand any tabs to spaces.
    return indent.expandtabs(config["indent_size"]) + stripped


def _collapse_blanks(lines, max_blank):
    """Reduce any run of more than ``max_blank`` blank lines to ``max_blank``."""
    result = []
    blanks = 0
    for line in lines:
        if line.strip() == "":
            blanks += 1
            if blanks <= max_blank:
                result.append(line)
        else:
            blanks = 0
            result.append(line)
    return result


# ---------------------------------------------------------------------------
# File handling and commands.
# ---------------------------------------------------------------------------


def _read(path):
    with open(path, "r", encoding="utf-8", newline="") as fh:
        return fh.read()


def _expand_paths(paths):
    """Expand directories into the files within them, recursively."""
    out = []
    for p in paths:
        if os.path.isdir(p):
            for root, _dirs, files in os.walk(p):
                if ".git" in root.split(os.sep):
                    continue
                for name in files:
                    out.append(os.path.join(root, name))
        else:
            out.append(p)
    return out


# Colour helpers (auto-disabled when output is not a terminal).
_C = sys.stdout.isatty()


def _red(s):
    return "\033[31m" + s + "\033[0m" if _C else s


def _green(s):
    return "\033[32m" + s + "\033[0m" if _C else s


def _yellow(s):
    return "\033[33m" + s + "\033[0m" if _C else s


def cmd_check(paths, explicit_config):
    """Report issues. Exit code 1 if any file has issues (CI-friendly)."""
    total = 0
    for path in _expand_paths(paths):
        try:
            text = _read(path)
        except (OSError, UnicodeDecodeError):
            continue  # skip binaries / unreadable files
        config = load_config(path, explicit_config)
        issues = lint_text(text, config)
        if issues:
            total += len(issues)
            print(_yellow(path))
            for it in issues:
                loc = "%s:%d" % (path, it.line)
                print("  %s  %s  %s" % (loc, _red(it.code), it.message))
    if total:
        print("\n%s" % _red("%d issue(s) found." % total))
        return 1
    print(_green("All clean."))
    return 0


def cmd_fix(paths, explicit_config):
    """Rewrite files in place, fixing every fixable issue."""
    changed = 0
    for path in _expand_paths(paths):
        try:
            text = _read(path)
        except (OSError, UnicodeDecodeError):
            continue
        config = load_config(path, explicit_config)
        fixed = format_text(text, config)
        if fixed != text:
            with open(path, "w", encoding="utf-8", newline="") as fh:
                fh.write(fixed)
            print("%s %s" % (_green("fixed"), path))
            changed += 1
    print("\n%d file(s) changed." % changed)
    return 0


def cmd_diff(paths, explicit_config):
    """Show a unified diff of what fix would change, without writing."""
    any_diff = False
    for path in _expand_paths(paths):
        try:
            text = _read(path)
        except (OSError, UnicodeDecodeError):
            continue
        config = load_config(path, explicit_config)
        fixed = format_text(text, config)
        if fixed != text:
            any_diff = True
            diff = difflib.unified_diff(
                text.splitlines(keepends=True), fixed.splitlines(keepends=True),
                fromfile=path, tofile=path + " (formatted)",
            )
            for line in diff:
                if line.startswith("+") and not line.startswith("+++"):
                    sys.stdout.write(_green(line))
                elif line.startswith("-") and not line.startswith("---"):
                    sys.stdout.write(_red(line))
                else:
                    sys.stdout.write(line)
    return 1 if any_diff else 0


# ---------------------------------------------------------------------------
# Self-tests.
# ---------------------------------------------------------------------------


def run_tests():
    failures = 0

    def check(name, condition):
        nonlocal failures
        if not condition:
            failures += 1
        print("  [%s] %s" % ("ok" if condition else "FAIL", name))

    print("Running self-tests...")
    cfg = dict(DEFAULT_CONFIG)

    # Trailing whitespace is detected and fixed.
    issues = lint_text("foo  \nbar\n", cfg)
    check("detect trailing whitespace", any(i.code == "TRAIL" for i in issues))
    check("fix trailing whitespace", format_text("foo  \nbar\n", cfg) == "foo\nbar\n")

    # Missing final newline.
    check("detect missing EOF newline",
          any(i.code == "EOFNL" for i in lint_text("x", cfg)))
    check("insert final newline", format_text("x", cfg) == "x\n")

    # Blank line collapsing (max 2).
    src = "a\n\n\n\n\nb\n"
    check("detect too many blanks", any(i.code == "BLANKS" for i in lint_text(src, cfg)))
    check("collapse blank lines", format_text(src, cfg) == "a\n\n\nb\n")

    # Trailing blank lines trimmed.
    check("trim trailing blanks", format_text("a\n\n\n", cfg) == "a\n")

    # CRLF normalisation.
    check("detect CRLF", any(i.code == "CRLF" for i in lint_text("a\r\nb\r\n", cfg)))
    check("normalize CRLF", format_text("a\r\nb\r\n", cfg) == "a\nb\n")

    # Tab indentation flagged in spaces mode, and expanded to spaces on fix.
    check("detect tab indent", any(i.code == "TABIND" for i in lint_text("\tx\n", cfg)))
    check("expand tab indent", format_text("\tx\n", cfg) == "    x\n")

    # Long line detection (default max for plain config is 100).
    long_line = "x" * 120 + "\n"
    check("detect long line", any(i.code == "LONG" for i in lint_text(long_line, cfg)))

    # Tabs mode: spaces are converted back to a tab.
    tab_cfg = dict(DEFAULT_CONFIG, use_tabs=True, indent_size=4)
    check("convert spaces to tab", format_text("    x\n", tab_cfg) == "\tx\n")

    # Language defaults: .py picks up 88-column limit.
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as tf:
        py_path = tf.name
    try:
        py_cfg = load_config(py_path)
        check("python uses 88-col default", py_cfg["max_line_length"] == 88)
    finally:
        os.unlink(py_path)

    # Idempotence: formatting an already-clean file changes nothing.
    clean = "def f():\n    return 1\n"
    check("format is idempotent", format_text(clean, cfg) == clean)

    # A clean file yields no issues.
    check("clean file has no issues", lint_text(clean, cfg) == [])

    print()
    if failures:
        print("%d test(s) FAILED" % failures)
        sys.exit(1)
    print("All tests passed.")


# ---------------------------------------------------------------------------
# Entry point.
# ---------------------------------------------------------------------------


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="clawfmt",
        description="A language-agnostic code formatter and style linter.",
    )
    parser.add_argument("--config", help="path to a .clawfmt.json config file")
    sub = parser.add_subparsers(dest="command")

    for name, help_text in (
        ("check", "report issues (exit 1 if any found)"),
        ("fix", "rewrite files, fixing what can be fixed"),
        ("diff", "show what fix would change, without writing"),
    ):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("paths", nargs="+", help="files or directories")

    sub.add_parser("test", help="run built-in self-tests")

    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 1

    if args.command == "test":
        run_tests()
        return 0

    handlers = {"check": cmd_check, "fix": cmd_fix, "diff": cmd_diff}
    return handlers[args.command](args.paths, args.config)


if __name__ == "__main__":
    sys.exit(main())

# Built by clavexis — github.com/clavexis
