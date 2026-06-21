#!/usr/bin/env python3
"""
clawbrowse — browse the web from your terminal.

Fetches pages over HTTP/HTTPS, renders the HTML as clean readable text with
ANSI formatting, numbers every link so you can follow them by typing a number,
and keeps a bookmark list and back/forward history. Pure Python standard
library — no third-party dependencies.

Interactive:
    clawbrowse                       start at a blank prompt
    clawbrowse https://example.com   open a page and drop into the browser

One-shot:
    clawbrowse --dump https://example.com   render once to stdout and exit

Built by clavexis — github.com/clavexis
"""

import sys
import os
import re
import json
import argparse
import textwrap
import urllib.request
import urllib.parse
from html.parser import HTMLParser
from html import unescape

# ---------------------------------------------------------------------------
# ANSI styling helpers. A tiny "CSS" layer: we map HTML structure to colours.
# ---------------------------------------------------------------------------

ANSI = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "dim": "\033[2m",
    "italic": "\033[3m",
    "underline": "\033[4m",
    "heading": "\033[1;36m",   # bold cyan
    "link": "\033[4;34m",      # underlined blue
    "code": "\033[33m",        # yellow
    "quote": "\033[2;37m",     # dim grey
}

_USE_COLOR = sys.stdout.isatty()


def style(text, *names):
    """Wrap ``text`` in the given ANSI styles, unless colour is disabled."""
    if not _USE_COLOR or not names:
        return text
    codes = "".join(ANSI[n] for n in names)
    return codes + text + ANSI["reset"]


# ---------------------------------------------------------------------------
# HTML → readable text renderer.
# ---------------------------------------------------------------------------

# Block-level tags introduce line breaks; inline tags don't.
BLOCK_TAGS = {
    "p", "div", "section", "article", "header", "footer", "main", "nav",
    "ul", "ol", "table", "tr", "br", "hr", "blockquote", "pre", "form",
    "h1", "h2", "h3", "h4", "h5", "h6",
}
SKIP_TAGS = {"script", "style", "noscript", "svg", "template"}


class Renderer(HTMLParser):
    """Turns an HTML document into terminal text plus an indexed link table.

    The result is available as ``.text`` (the rendered page) and ``.links``
    (a list of absolute URLs, where link [n] in the text is ``links[n-1]``).
    """

    def __init__(self, base_url=""):
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.out = []           # accumulated output fragments
        self.links = []         # absolute hrefs in encounter order
        self._skip_depth = 0    # >0 while inside script/style/etc.
        self._pre_depth = 0     # >0 while inside <pre> (preserve whitespace)
        self._list_stack = []   # tracks ol/ul nesting and ordered counters
        self._pending_link = None
        self._heading = None
        self._title = None
        self._in_title = False

    # -- helpers ------------------------------------------------------------

    def _emit(self, text):
        self.out.append(text)

    def _newline(self, count=1):
        """Emit up to ``count`` blank-ish line breaks without piling them up."""
        # Collapse trailing whitespace so we never produce huge vertical gaps.
        while self.out and self.out[-1].strip() == "" and self.out[-1].count("\n") >= count:
            return
        self._emit("\n" * count)

    # -- tag handlers -------------------------------------------------------

    def handle_starttag(self, tag, attrs):
        if tag in SKIP_TAGS:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        attr = dict(attrs)

        if tag == "title":
            self._in_title = True
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._newline(2)
            self._heading = tag
        elif tag == "p":
            self._newline(2)
        elif tag == "br":
            self._emit("\n")
        elif tag == "hr":
            self._newline(2)
            self._emit(style("─" * 60, "dim"))
            self._newline(2)
        elif tag == "li":
            self._newline(1)
            if self._list_stack and self._list_stack[-1][0] == "ol":
                self._list_stack[-1][1] += 1
                self._emit("  %d. " % self._list_stack[-1][1])
            else:
                self._emit("  • ")
        elif tag in ("ul", "ol"):
            self._newline(1)
            self._list_stack.append([tag, 0])
        elif tag == "blockquote":
            self._newline(2)
            self._emit(style("> ", "quote"))
        elif tag == "pre":
            self._newline(2)
            self._pre_depth += 1
        elif tag in ("b", "strong"):
            self._emit(ANSI["bold"] if _USE_COLOR else "")
        elif tag in ("i", "em"):
            self._emit(ANSI["italic"] if _USE_COLOR else "")
        elif tag == "code" and not self._pre_depth:
            self._emit(ANSI["code"] if _USE_COLOR else "`")
        elif tag == "a":
            href = attr.get("href")
            if href and not href.startswith("javascript:"):
                absolute = urllib.parse.urljoin(self.base_url, href)
                self.links.append(absolute)
                self._pending_link = len(self.links)
                self._emit(ANSI["link"] if _USE_COLOR else "")
        elif tag == "img":
            alt = attr.get("alt", "").strip()
            self._emit(style("[img: %s]" % (alt or "image"), "dim"))

    def handle_endtag(self, tag):
        if tag in SKIP_TAGS:
            if self._skip_depth:
                self._skip_depth -= 1
            return
        if self._skip_depth:
            return

        if tag == "title":
            self._in_title = False
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._heading = None
            self._newline(2)
        elif tag in ("p", "blockquote"):
            self._newline(2)
        elif tag in ("ul", "ol"):
            if self._list_stack:
                self._list_stack.pop()
            self._newline(1)
        elif tag == "pre":
            if self._pre_depth:
                self._pre_depth -= 1
            self._newline(2)
        elif tag in ("b", "strong", "i", "em"):
            self._emit(ANSI["reset"] if _USE_COLOR else "")
        elif tag == "code" and not self._pre_depth:
            self._emit(ANSI["reset"] if _USE_COLOR else "`")
        elif tag == "a":
            if self._pending_link is not None:
                self._emit((ANSI["reset"] if _USE_COLOR else "")
                           + style("[%d]" % self._pending_link, "dim"))
                self._pending_link = None

    def handle_data(self, data):
        if self._skip_depth:
            return
        if self._in_title:
            self._title = (self._title or "") + data
            return
        if self._pre_depth:
            self._emit(data)  # preserve whitespace inside <pre>
            return
        # Collapse runs of whitespace for normal flow text.
        text = re.sub(r"\s+", " ", data)
        if not text.strip() and (not self.out or self.out[-1].endswith((" ", "\n"))):
            return
        if self._heading:
            self._emit(style(text, "heading"))
        else:
            self._emit(text)

    # -- finalisation -------------------------------------------------------

    @property
    def title(self):
        return (self._title or "").strip()

    @property
    def text(self):
        """Assemble fragments, then wrap paragraphs to the terminal width."""
        raw = "".join(self.out)
        # Squeeze 3+ newlines down to a clean paragraph break.
        raw = re.sub(r"\n{3,}", "\n\n", raw).strip()
        width = min(_terminal_width(), 100)
        wrapped = []
        for line in raw.split("\n"):
            if not line.strip():
                wrapped.append("")
            elif line.startswith(("  •", "  ")) and line.strip()[:1].isdigit() is False:
                wrapped.append(line)  # don't re-wrap list items / preformatted
            else:
                wrapped.append(_wrap_visible(line, width))
        return "\n".join(wrapped)


def _terminal_width():
    try:
        return os.get_terminal_size().columns
    except OSError:
        return 80


# Matches ANSI escape sequences so we can wrap on *visible* width.
_ANSI_RE = re.compile(r"\033\[[0-9;]*m")


def _wrap_visible(line, width):
    """Word-wrap a line to ``width`` visible columns, ignoring ANSI codes."""
    if len(_ANSI_RE.sub("", line)) <= width:
        return line
    # textwrap can't see past escape codes, so wrap the stripped text and
    # accept that wrapped links lose colour at the break — readability first.
    plain = _ANSI_RE.sub("", line)
    return textwrap.fill(plain, width=width)


def render_html(html, base_url=""):
    """Convenience wrapper: return (title, text, links) for an HTML string."""
    parser = Renderer(base_url)
    parser.feed(html)
    return parser.title, parser.text, parser.links


# ---------------------------------------------------------------------------
# Networking.
# ---------------------------------------------------------------------------


def fetch(url):
    """Download a URL and return (final_url, html_text). Follows redirects."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    request = urllib.request.Request(
        url, headers={"User-Agent": "clawbrowse/1.0 (+github.com/clavexis)"}
    )
    with urllib.request.urlopen(request, timeout=20) as resp:
        final_url = resp.geturl()
        charset = resp.headers.get_content_charset() or "utf-8"
        body = resp.read()
    return final_url, body.decode(charset, errors="replace")


# ---------------------------------------------------------------------------
# Bookmarks (persisted as JSON in the user's config directory).
# ---------------------------------------------------------------------------


def _config_path():
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(
        os.path.expanduser("~"), ".config"
    )
    directory = os.path.join(base, "clawbrowse")
    os.makedirs(directory, exist_ok=True)
    return os.path.join(directory, "bookmarks.json")


def load_bookmarks():
    path = _config_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, json.JSONDecodeError):
            return []
    return []


def save_bookmarks(bookmarks):
    with open(_config_path(), "w", encoding="utf-8") as fh:
        json.dump(bookmarks, fh, indent=2)


# ---------------------------------------------------------------------------
# Interactive browser loop.
# ---------------------------------------------------------------------------

HELP = """\
Commands:
  <number>      follow link number N on the current page
  o <url>       open a URL
  b / f         go back / forward in history
  r             reload the current page
  links         list all links on the current page
  book          bookmark the current page
  bookmarks     list bookmarks (open with: o <number-from-list>)
  help          show this help
  q             quit\
"""


class Browser:
    def __init__(self):
        self.history = []     # list of (url, title, text, links)
        self.position = -1    # index into history (for back/forward)
        self.bookmarks = load_bookmarks()

    @property
    def current(self):
        return self.history[self.position] if self.position >= 0 else None

    def open(self, url):
        """Fetch and display ``url``, truncating any forward history."""
        try:
            final_url, html = fetch(url)
        except Exception as exc:  # noqa: BLE001 - report any network/parse error
            print(style("Could not open %s: %s" % (url, exc), "dim"))
            return
        title, text, links = render_html(html, final_url)
        # Drop forward history when navigating to a new page.
        self.history = self.history[: self.position + 1]
        self.history.append((final_url, title, text, links))
        self.position = len(self.history) - 1
        self._display()

    def _display(self):
        url, title, text, links = self.current
        print()
        print(style(title or url, "heading"))
        print(style(url, "dim"))
        print(style("─" * min(_terminal_width(), 100), "dim"))
        print(text)
        print(style("─" * min(_terminal_width(), 100), "dim"))
        print(style("%d link(s). Type a number to follow, or 'help'." % len(links), "dim"))

    def follow(self, n):
        url, title, text, links = self.current
        if 1 <= n <= len(links):
            self.open(links[n - 1])
        else:
            print(style("No link number %d (page has %d)." % (n, len(links)), "dim"))

    def back(self):
        if self.position > 0:
            self.position -= 1
            self._display()
        else:
            print(style("Already at the start of history.", "dim"))

    def forward(self):
        if self.position < len(self.history) - 1:
            self.position += 1
            self._display()
        else:
            print(style("Already at the most recent page.", "dim"))

    def list_links(self):
        if not self.current:
            return
        for i, link in enumerate(self.current[3], 1):
            print("  [%d] %s" % (i, link))

    def bookmark(self):
        if not self.current:
            print(style("Open a page first.", "dim"))
            return
        url, title = self.current[0], self.current[1]
        if any(b["url"] == url for b in self.bookmarks):
            print(style("Already bookmarked.", "dim"))
            return
        self.bookmarks.append({"url": url, "title": title or url})
        save_bookmarks(self.bookmarks)
        print(style("Bookmarked: %s" % (title or url), "dim"))

    def list_bookmarks(self):
        if not self.bookmarks:
            print(style("No bookmarks yet.", "dim"))
            return
        for i, b in enumerate(self.bookmarks, 1):
            print("  [%d] %s — %s" % (i, b["title"], style(b["url"], "dim")))

    def run(self, start_url=None):
        print(style("clawbrowse — terminal web browser. Type 'help' for commands.", "dim"))
        if start_url:
            self.open(start_url)
        while True:
            try:
                line = input(style("\nclawbrowse> ", "bold")).strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not line:
                continue
            self.dispatch(line)

    def dispatch(self, line):
        """Route one command line typed by the user."""
        if line in ("q", "quit", "exit"):
            sys.exit(0)
        elif line in ("help", "h", "?"):
            print(HELP)
        elif line.isdigit():
            # A bare number follows a link, OR opens a bookmark if no page is loaded.
            if self.current:
                self.follow(int(line))
            else:
                self._open_bookmark(int(line))
        elif line in ("b", "back"):
            self.back()
        elif line in ("f", "forward"):
            self.forward()
        elif line in ("r", "reload"):
            if self.current:
                self.open(self.current[0])
        elif line == "links":
            self.list_links()
        elif line in ("book", "bookmark"):
            self.bookmark()
        elif line == "bookmarks":
            self.list_bookmarks()
        elif line.startswith("o ") or line.startswith("open "):
            arg = line.split(None, 1)[1].strip()
            if arg.isdigit():
                self._open_bookmark(int(arg))
            else:
                self.open(arg)
        else:
            # Bare URL or search term: treat anything with a dot as a URL.
            if "." in line and " " not in line:
                self.open(line)
            else:
                print(style("Unknown command. Type 'help'.", "dim"))

    def _open_bookmark(self, n):
        if 1 <= n <= len(self.bookmarks):
            self.open(self.bookmarks[n - 1]["url"])
        else:
            print(style("No bookmark number %d." % n, "dim"))


# ---------------------------------------------------------------------------
# Self-tests (offline — exercise the renderer without any network).
# ---------------------------------------------------------------------------


def run_tests():
    global _USE_COLOR
    _USE_COLOR = False  # deterministic, colour-free output for assertions
    failures = 0

    def check(name, condition):
        nonlocal failures
        if not condition:
            failures += 1
        print("  [%s] %s" % ("ok" if condition else "FAIL", name))

    print("Running self-tests...")

    html = """
    <html><head><title>Test Page</title><style>p{color:red}</style></head>
    <body>
      <h1>Hello</h1>
      <p>This is a <b>bold</b> paragraph with a
         <a href="/about">link</a> and another
         <a href="https://example.org">external link</a>.</p>
      <ul><li>first</li><li>second</li></ul>
      <script>alert('should be skipped')</script>
      <blockquote>a quote</blockquote>
    </body></html>
    """
    title, text, links = render_html(html, "https://example.com/page")

    check("title parsed", title == "Test Page")
    check("heading text present", "Hello" in text)
    check("paragraph text present", "bold paragraph" in text)
    check("script content skipped", "should be skipped" not in text)
    check("style content skipped", "color:red" not in text)
    check("two links found", len(links) == 2)
    check("relative link resolved", links[0] == "https://example.com/about")
    check("absolute link preserved", links[1] == "https://example.org")
    check("link numbered in text", "[1]" in text and "[2]" in text)
    check("list bullets rendered", "•" in text)
    check("blockquote marker", ">" in text)

    # Entity decoding.
    _, t2, _ = render_html("<p>5 &lt; 10 &amp; 3 &gt; 1</p>")
    check("entities decoded", "5 < 10 & 3 > 1" in t2)

    # Empty / malformed input shouldn't crash.
    _, t3, l3 = render_html("<p>unclosed paragraph <b>bold")
    check("malformed html handled", "unclosed paragraph" in t3 and l3 == [])

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
        prog="clawbrowse",
        description="Browse the web from your terminal (pure Python, no deps).",
    )
    parser.add_argument("url", nargs="?", help="URL to open")
    parser.add_argument("--dump", action="store_true",
                        help="render the URL once to stdout and exit")
    parser.add_argument("--test", action="store_true", help="run self-tests")
    args = parser.parse_args(argv)

    if args.test:
        run_tests()
        return

    if args.dump:
        if not args.url:
            parser.error("--dump requires a URL")
        final_url, html = fetch(args.url)
        title, text, links = render_html(html, final_url)
        if title:
            print(style(title, "heading"))
        print(text)
        return

    Browser().run(args.url)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        sys.exit(130)

# Built by clavexis — github.com/clavexis
