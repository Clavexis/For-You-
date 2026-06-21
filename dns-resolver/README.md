# DNS Resolver from Scratch

A working DNS resolver built on raw UDP sockets — it constructs DNS query packets by hand, parses the binary responses (compression and all), and supports A, AAAA, CNAME, MX, and NS records. No DNS libraries.

## Demo

```text
$ ./dns example.com
Resolving via 8.8.8.8:
NAME                           TYPE   TTL    VALUE
example.com                    A      240    172.66.147.243
example.com                    A      240    104.20.23.154

$ ./dns google.com MX
google.com                     MX     207    10 smtp.google.com

$ ./dns google.com AAAA
google.com                     AAAA   118    2404:6800:4000:100e::66

$ ./dns cloudflare.com cloudflare.com     # second lookup is a cache hit
cloudflare.com                 A      300    104.16.132.229
cloudflare.com A     104.16.132.229  (from cache)
```

## Features

- **Hand-built DNS packets** — header + question encoded byte by byte.
- **Full response parsing**, including **compressed names** (the `0xC0` pointer scheme).
- **Record types** — A, AAAA, CNAME, MX (with preference), NS.
- **Recursion-desired** queries via a recursive resolver (default `8.8.8.8`, `--server` to change).
- **In-memory cache** with TTLs — repeated lookups in a run are served from cache.
- TTLs shown for every record.

## Build & run

Requires a C compiler.

### Linux
```bash
cd linux
make                 # or ./build.sh
./dns example.com
./dns google.com MX
./dns example.com --server 1.1.1.1
```

### macOS (Apple Silicon & Intel)
```bash
cd mac
./build.sh           # uses clang
./dns example.com AAAA
```

### Windows
The resolver uses BSD sockets; build under **WSL** with the `linux/` Makefile (or adapt to Winsock).

## Usage

```bash
./dns <name>...                 # one or more names (A records)
./dns example.com MX            # a specific record type (A|AAAA|CNAME|MX|NS)
./dns example.com --server 9.9.9.9
./dns a.com b.com a.com         # repeated names hit the cache
```

## How it works

```text
build query (id, RD flag, encoded name, qtype) ──UDP──▶ resolver:53
response ──▶ parse header ──▶ skip question ──▶ for each answer:
              decode name (follow 0xC0 pointers) ──▶ read type/TTL/rdata
              A→IPv4  AAAA→IPv6  CNAME/NS→name  MX→pref+name
```

The trickiest part — and the thing most tutorials skip — is **name compression**: DNS reuses earlier names via two-byte pointers, so the parser follows them while tracking where to resume in the original stream.

## Tech stack

- **C** — raw UDP sockets, manual packet construction and parsing
- Custom DNS message encoder/decoder with compression support

---

Built by clavexis — [github.com/clavexis](https://github.com/clavexis)
