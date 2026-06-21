#!/usr/bin/env python3
"""
Real-Time Code Collaboration — edit the same file together over the network.

  - WebSocket-based sync (server broadcasts edits to everyone in a room)
  - Multiple users edit the same document live
  - Shows each user's cursor position
  - Simple terminal editor (curses)
  - No accounts — just share a room code

Subcommands:
  collab.py server [--host H] [--port P]      start the sync server
  collab.py join <room> [--url ws://...]      open the editor and join a room
  collab.py bot  <room> [ops...] [--url ...]   scripted client (for testing)

Built by clavexis — github.com/clavexis
"""

import argparse
import asyncio
import json
import os
import sys
import threading
import queue

try:
    import websockets
except ImportError:
    sys.stderr.write("This tool needs the 'websockets' package.  pip install websockets\n")
    sys.exit(1)

DEFAULT_URL = "ws://localhost:8765"


# ===========================================================================
# Server — keeps an authoritative document per room and broadcasts changes.
# ===========================================================================
class Room:
    def __init__(self):
        self.doc = [""]                 # list of lines (authoritative)
        self.clients = {}               # websocket -> {"name":..., "line":0, "col":0}

    def apply(self, op):
        t = op.get("type")
        line = op.get("line", 0)
        if t == "set_line" and 0 <= line < len(self.doc):
            self.doc[line] = op.get("text", "")
        elif t == "insert_line" and 0 <= line <= len(self.doc):
            self.doc.insert(line, op.get("text", ""))
        elif t == "delete_line" and 0 <= line < len(self.doc) and len(self.doc) > 1:
            self.doc.pop(line)


def make_server():
    rooms = {}

    async def handler(ws):
        room_code = None
        name = None
        try:
            async for raw in ws:
                msg = json.loads(raw)
                mtype = msg.get("type")

                if mtype == "join":
                    room_code = msg.get("room", "default")
                    name = msg.get("name", "anon")
                    room = rooms.setdefault(room_code, Room())
                    room.clients[ws] = {"name": name, "line": 0, "col": 0}
                    # Send the current document snapshot to the newcomer.
                    await ws.send(json.dumps({"type": "snapshot", "doc": room.doc,
                                              "users": [c["name"] for c in room.clients.values()]}))
                    await broadcast(room, {"type": "presence",
                                           "users": [c["name"] for c in room.clients.values()]}, exclude=ws)
                    continue

                if room_code is None:
                    continue
                room = rooms.get(room_code)
                if not room:
                    continue

                if mtype in ("set_line", "insert_line", "delete_line"):
                    room.apply(msg)
                    await broadcast(room, msg, exclude=ws)
                elif mtype == "cursor":
                    if ws in room.clients:
                        room.clients[ws]["line"] = msg.get("line", 0)
                        room.clients[ws]["col"] = msg.get("col", 0)
                    await broadcast(room, {"type": "cursor", "name": name,
                                           "line": msg.get("line", 0), "col": msg.get("col", 0)}, exclude=ws)
        except websockets.ConnectionClosed:
            pass
        finally:
            if room_code and room_code in rooms:
                room = rooms[room_code]
                room.clients.pop(ws, None)
                await broadcast(room, {"type": "presence",
                                       "users": [c["name"] for c in room.clients.values()]})

    async def broadcast(room, msg, exclude=None):
        data = json.dumps(msg)
        dead = []
        for client in list(room.clients):
            if client is exclude:
                continue
            try:
                await client.send(data)
            except websockets.ConnectionClosed:
                dead.append(client)
        for d in dead:
            room.clients.pop(d, None)

    return handler


async def run_server(host, port):
    handler = make_server()
    async with websockets.serve(handler, host, port):
        print(f"Collab server listening on ws://{host}:{port}")
        await asyncio.Future()  # run forever


# ===========================================================================
# Bot client — scripted, for testing the sync protocol without a terminal.
# ===========================================================================
async def run_bot(url, room, name, ops, wait):
    async with websockets.connect(url) as ws:
        await ws.send(json.dumps({"type": "join", "room": room, "name": name}))
        doc = [""]

        async def reader():
            nonlocal doc
            try:
                async for raw in ws:
                    msg = json.loads(raw)
                    if msg["type"] == "snapshot":
                        doc = msg["doc"]
                    elif msg["type"] == "set_line" and 0 <= msg["line"] < len(doc):
                        doc[msg["line"]] = msg["text"]
                    elif msg["type"] == "insert_line":
                        doc.insert(msg["line"], msg.get("text", ""))
                    elif msg["type"] == "delete_line" and 0 <= msg["line"] < len(doc):
                        doc.pop(msg["line"])
            except websockets.ConnectionClosed:
                pass

        task = asyncio.create_task(reader())
        await asyncio.sleep(0.2)
        for op in ops:
            await ws.send(json.dumps(op))
            await asyncio.sleep(0.05)
        await asyncio.sleep(wait)
        task.cancel()
        print(json.dumps({"name": name, "doc": doc}))


# ===========================================================================
# Interactive editor (curses) — joins a room and syncs in real time.
# ===========================================================================
def run_editor(url, room, name):
    import curses

    shared = {"doc": [""], "users": [], "cursors": {}, "lock": threading.Lock()}
    out_q: "queue.Queue" = queue.Queue()
    stop = threading.Event()

    def net_thread():
        async def main():
            try:
                async with websockets.connect(url) as ws:
                    await ws.send(json.dumps({"type": "join", "room": room, "name": name}))

                    async def sender():
                        while not stop.is_set():
                            try:
                                op = out_q.get_nowait()
                                await ws.send(json.dumps(op))
                            except queue.Empty:
                                await asyncio.sleep(0.02)

                    async def receiver():
                        async for raw in ws:
                            msg = json.loads(raw)
                            with shared["lock"]:
                                if msg["type"] == "snapshot":
                                    shared["doc"] = msg["doc"] or [""]
                                    shared["users"] = msg.get("users", [])
                                elif msg["type"] == "presence":
                                    shared["users"] = msg.get("users", [])
                                elif msg["type"] == "set_line" and 0 <= msg["line"] < len(shared["doc"]):
                                    shared["doc"][msg["line"]] = msg["text"]
                                elif msg["type"] == "insert_line":
                                    shared["doc"].insert(msg["line"], msg.get("text", ""))
                                elif msg["type"] == "delete_line" and 0 <= msg["line"] < len(shared["doc"]):
                                    shared["doc"].pop(msg["line"])
                                elif msg["type"] == "cursor":
                                    shared["cursors"][msg["name"]] = (msg["line"], msg["col"])
                    await asyncio.gather(sender(), receiver())
            except Exception:  # noqa: BLE001 — connection issues end the editor
                stop.set()
        asyncio.run(main())

    threading.Thread(target=net_thread, daemon=True).start()

    def editor(stdscr):
        curses.curs_set(1)
        stdscr.nodelay(True)
        stdscr.timeout(50)
        cy, cx = 0, 0
        while not stop.is_set():
            with shared["lock"]:
                doc = shared["doc"]
                users = list(shared["users"])
                cursors = dict(shared["cursors"])
            cy = max(0, min(cy, len(doc) - 1))
            cx = max(0, min(cx, len(doc[cy])))

            stdscr.erase()
            h, w = stdscr.getmaxyx()
            stdscr.addnstr(0, 0, f" Room: {room}  Users: {', '.join(users)}  (Ctrl-Q quit)".ljust(w - 1),
                           w - 1, curses.A_REVERSE)
            for i, line in enumerate(doc[:h - 2]):
                stdscr.addnstr(i + 1, 0, f"{i+1:>3} {line}", w - 1)
            # Other users' cursors as markers in the status area.
            others = "  ".join(f"{n}@L{l+1}" for n, (l, c) in cursors.items() if n != name)
            if others:
                stdscr.addnstr(h - 1, 0, f" cursors: {others}".ljust(w - 1), w - 1, curses.A_DIM)
            stdscr.move(min(cy + 1, h - 2), min(cx + 4, w - 1))
            stdscr.refresh()

            try:
                ch = stdscr.getch()
            except KeyboardInterrupt:
                break
            if ch == -1:
                continue
            if ch == 17:  # Ctrl-Q
                break
            with shared["lock"]:
                doc = shared["doc"]
                if ch in (curses.KEY_UP,):
                    cy = max(0, cy - 1)
                elif ch in (curses.KEY_DOWN,):
                    cy = min(len(doc) - 1, cy + 1)
                elif ch == curses.KEY_LEFT:
                    cx = max(0, cx - 1)
                elif ch == curses.KEY_RIGHT:
                    cx = min(len(doc[cy]), cx + 1)
                elif ch in (curses.KEY_BACKSPACE, 127, 8):
                    if cx > 0:
                        doc[cy] = doc[cy][:cx - 1] + doc[cy][cx:]
                        cx -= 1
                        out_q.put({"type": "set_line", "line": cy, "text": doc[cy]})
                elif ch in (10, 13):  # Enter
                    rest = doc[cy][cx:]
                    doc[cy] = doc[cy][:cx]
                    out_q.put({"type": "set_line", "line": cy, "text": doc[cy]})
                    doc.insert(cy + 1, rest)
                    out_q.put({"type": "insert_line", "line": cy + 1, "text": rest})
                    cy += 1
                    cx = 0
                elif 32 <= ch < 127:
                    doc[cy] = doc[cy][:cx] + chr(ch) + doc[cy][cx:]
                    cx += 1
                    out_q.put({"type": "set_line", "line": cy, "text": doc[cy]})
            out_q.put({"type": "cursor", "line": cy, "col": cx})
        stop.set()

    curses.wrapper(editor)


def main():
    ap = argparse.ArgumentParser(description="Real-time collaborative code editor.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("server", help="Run the sync server.")
    sp.add_argument("--host", default="0.0.0.0")
    sp.add_argument("--port", type=int, default=8765)

    jp = sub.add_parser("join", help="Open the editor and join a room.")
    jp.add_argument("room")
    jp.add_argument("--url", default=DEFAULT_URL)
    jp.add_argument("--name", default=os.environ.get("USER", "anon"))

    bp = sub.add_parser("bot", help="Scripted client (for testing).")
    bp.add_argument("room")
    bp.add_argument("--url", default=DEFAULT_URL)
    bp.add_argument("--name", default="bot")
    bp.add_argument("--op", action="append", default=[], help="JSON op to send.")
    bp.add_argument("--wait", type=float, default=0.5)

    args = ap.parse_args()

    if args.cmd == "server":
        asyncio.run(run_server(args.host, args.port))
    elif args.cmd == "join":
        run_editor(args.url, args.room, args.name)
    elif args.cmd == "bot":
        ops = [json.loads(o) for o in args.op]
        asyncio.run(run_bot(args.url, args.room, args.name, ops, args.wait))


if __name__ == "__main__":
    main()
