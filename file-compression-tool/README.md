# File Compression Tool (Huffman)

A file compressor built from scratch using **Huffman coding** — no zlib, no compression libraries. Compress and decompress any file (text or binary), losslessly, and see the compression ratio.

## Demo

```text
$ ./huff -c book.txt book.huf
Compressed book.txt (22500 bytes) -> book.huf (14623 bytes)
Compression ratio: 35.0% smaller

$ ./huff -d book.huf restored.txt
Decompressed book.huf -> restored.txt (22500 bytes)

$ cmp book.txt restored.txt && echo "identical"
identical
```

## Features

- **Huffman coding from scratch** — builds the Huffman tree from byte frequencies and assigns optimal prefix codes.
- **Lossless & binary-safe** — round-trips any file (verified on text *and* random binary) to byte-identical output.
- **Compression ratio** reported after compressing.
- **Self-describing format** — the header stores the frequency table, so the decompressor rebuilds the exact same tree. No external metadata needed.
- Handles edge cases: empty files and single-symbol files.

## Build & run

Requires a C++17 compiler.

### Linux
```bash
cd linux
make                          # or ./build.sh
./huff -c input.txt out.huf   # compress
./huff -d out.huf restored    # decompress
```

### macOS (Apple Silicon & Intel)
```bash
cd mac
./build.sh                    # uses clang++
./huff -c input.txt out.huf
```

### Windows
```powershell
cd windows
build.bat
huff.exe -c input.txt out.huf
```

## Usage

```bash
huff -c <input> <output.huf>     # compress
huff -d <output.huf> <restored>  # decompress
```

## How it works

```text
COMPRESS:
  count byte frequencies ──▶ build Huffman tree (min-heap)
  ──▶ assign prefix codes ──▶ write header (freq table + size)
  ──▶ pack each byte's code into a bitstream

DECOMPRESS:
  read header ──▶ rebuild the identical tree
  ──▶ walk the tree bit by bit, emitting a byte at each leaf
```

The file format is:
```text
[ "HUF1" ][ original size : 8 bytes ][ frequency table : 256×8 bytes ][ bitstream ]
```

Storing the frequency table makes the file self-contained — for large files the ~2 KB header is negligible; tiny files may not shrink because of it.

## Tech stack

- **C++17**, single file, standard library only (`<queue>` for the min-heap)
- Huffman tree, prefix codes, manual bit packing/unpacking

---

Built by clavexis — [github.com/clavexis](https://github.com/clavexis)
