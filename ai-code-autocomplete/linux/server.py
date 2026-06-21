#!/usr/bin/env python3
"""
Local Code Autocomplete bridge — a tiny HTTP server that turns a local LLM
(Ollama or llama.cpp) into a code-completion endpoint for the VS Code extension.

Everything runs on your machine — no code is ever sent to a cloud service.

  POST /complete  { "prefix": "...", "suffix": "...", "language": "python" }
    -> { "completion": "..." }

It talks to Ollama's local API (http://localhost:11434) by default, using a
fill-in-the-middle (FIM) prompt so completions fit between your cursor's
prefix and suffix.

Usage:
  ollama pull qwen2.5-coder:1.5b      # one-time: get a small code model
  server.py --model qwen2.5-coder:1.5b --port 11500

Built by clavexis — github.com/clavexis
"""

import argparse
import json
import os
import sys
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")


# ---------------------------------------------------------------------------
# Prompt building (pure / testable).
# ---------------------------------------------------------------------------
# Many code models support fill-in-the-middle with special tokens. We use the
# common StarCoder/Qwen-style markers and fall back to a plain prefix prompt.
def build_fim_prompt(prefix: str, suffix: str) -> str:
    if suffix.strip():
        return f"<|fim_prefix|>{prefix}<|fim_suffix|>{suffix}<|fim_middle|>"
    return prefix


def clean_completion(text: str) -> str:
    """Trim a model completion to something safe to insert inline."""
    # Stop at FIM/EOT markers if the model echoes them.
    for marker in ("<|fim", "<|endoftext|>", "<|eot", "```"):
        idx = text.find(marker)
        if idx != -1:
            text = text[:idx]
    return text


def call_ollama(model: str, prompt: str, max_tokens: int) -> str:
    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"num_predict": max_tokens, "temperature": 0.2, "stop": ["\n\n"]},
    }).encode()
    req = urllib.request.Request(f"{OLLAMA_URL}/api/generate", data=payload,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
    return data.get("response", "")


# ---------------------------------------------------------------------------
# HTTP server.
# ---------------------------------------------------------------------------
def make_handler(model: str, max_tokens: int):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):  # quiet by default
            pass

        def _json(self, code, obj):
            body = json.dumps(obj).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == "/health":
                self._json(200, {"status": "ok", "model": model})
            else:
                self._json(404, {"error": "not found"})

        def do_POST(self):
            if self.path != "/complete":
                self._json(404, {"error": "not found"})
                return
            try:
                length = int(self.headers.get("Content-Length", 0))
                req = json.loads(self.rfile.read(length) or b"{}")
            except (ValueError, json.JSONDecodeError):
                self._json(400, {"error": "invalid JSON"})
                return

            prefix = req.get("prefix", "")
            suffix = req.get("suffix", "")
            prompt = build_fim_prompt(prefix, suffix)
            try:
                raw = call_ollama(model, prompt, max_tokens)
                self._json(200, {"completion": clean_completion(raw)})
            except urllib.error.URLError:
                self._json(503, {
                    "error": "Could not reach Ollama. Is it running?",
                    "hint": "Start Ollama and `ollama pull " + model + "`.",
                })
            except Exception as exc:  # noqa: BLE001
                self._json(500, {"error": str(exc)})

    return Handler


def main() -> int:
    ap = argparse.ArgumentParser(description="Local code-completion bridge for the VS Code extension.")
    ap.add_argument("--model", default="qwen2.5-coder:1.5b", help="Ollama model name.")
    ap.add_argument("--port", type=int, default=11500, help="Port to listen on.")
    ap.add_argument("--max-tokens", type=int, default=64, help="Max tokens per completion.")
    args = ap.parse_args()

    handler = make_handler(args.model, args.max_tokens)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    print(f"Local autocomplete bridge on http://127.0.0.1:{args.port} "
          f"(model: {args.model})")
    print("Point the VS Code extension at this port. Ctrl-C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
