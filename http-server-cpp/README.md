# HTTP Server from Scratch (C++)

A working **HTTP/1.1 server written from scratch in C++** — raw sockets, no web frameworks or libraries. Serves static files, handles GET and POST, and runs one thread per connection.

## Demo

```text
$ ./server --port 8080 --root ../www
clawserver listening on http://localhost:8080  (root: ../www)
[2026-06-20 21:08:39] 127.0.0.1 "GET /" 200
[2026-06-20 21:08:39] 127.0.0.1 "GET /style.css" 200
[2026-06-20 21:08:39] 127.0.0.1 "POST /submit" 200
[2026-06-20 21:08:39] 127.0.0.1 "GET /../../etc/passwd" 403
```

## Features

- **HTTP/1.1** request parsing — method, path, query string, headers, body.
- **GET** — serves static files from the document root with correct `Content-Type` (HTML, CSS, JS, JSON, images, …) and a directory `index.html`.
- **POST** — reads the request body and echoes it back.
- **Multi-threaded** — a detached `std::thread` per connection (verified with concurrent requests).
- **Path-traversal protection** — `..` segments are rejected with `403` (verified against `/../../etc/passwd`).
- **Access logging** to stdout: timestamp, client IP, method, path, status.
- **Configurable** port (`--port`) and document root (`--root`).
- **Cross-platform sockets** — POSIX on Linux/macOS, Winsock on Windows (single source file, `#ifdef`).

## Build & run

Requires a C++17 compiler.

### Linux
```bash
cd linux
make            # or ./build.sh
./server --port 8080 --root ../www
# then visit http://localhost:8080
```

### macOS (Apple Silicon & Intel)
```bash
cd mac
./build.sh      # uses clang++
./server --port 8080 --root ../www
```

### Windows
```powershell
cd windows
build.bat       # MinGW g++ (-lws2_32) or MSVC cl
server.exe --port 8080 --root ..\www
```

## Usage

```bash
./server                              # defaults: port 8080, root "."
./server --port 3000 --root ./public  # custom port and root

# Test it:
curl http://localhost:8080/                       # serves index.html
curl -X POST -d "name=clavexis" localhost:8080/x  # echoes the body
curl --path-as-is localhost:8080/../secret        # -> 403 Forbidden
```

A sample site lives in `www/` (served by the examples above).

## How it works

```text
accept() ──▶ std::thread(handleClient) ──▶ parse request line + headers
                                            ├── GET  → read file from root → 200 / 404
                                            ├── POST → echo body → 200
                                            └── reject ".." → 403
```

Responses are built with proper status lines, `Content-Length`, and `Connection: close`.

## Tech stack

- **C++17**, single source file (`server.cpp`), `std::thread`
- BSD sockets (POSIX) / Winsock2 (Windows) — no external libraries

---

Built by clavexis — [github.com/clavexis](https://github.com/clavexis)
