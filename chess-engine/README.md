# Chess Engine from Scratch

A complete chess engine written in C++ with **no chess libraries** — legal move generation, a negamax + alpha-beta search, and a terminal board to play against the AI.

## Demo

```text
  +------------------------+
8 | r  n  b  q  k  b  n  r |
7 | p  p  p  p  .  p  p  p |
6 | .  .  .  .  .  .  .  . |
5 | .  .  .  .  p  .  .  . |
4 | .  .  .  .  P  .  .  . |
3 | .  .  .  .  .  .  .  . |
2 | P  P  P  P  .  P  P  P |
1 | R  N  B  Q  K  B  N  R |
  +------------------------+
    a  b  c  d  e  f  g  h
  Black to move.

AI plays b8c6  (0.005s)
Your move: g1f3
```

## Features

- **Full legal move generation** — including castling, en passant, and pawn promotion. Verified correct with [perft](https://www.chessprogramming.org/Perft): matches the canonical node counts for the start position, Kiwipete, and en-passant test positions exactly.
- **Negamax search with alpha-beta pruning** — adjustable strength via search depth.
- **Evaluation** — material values plus piece-square tables for central play.
- **Check / checkmate / stalemate detection.**
- **FEN support** — load any position with `--fen`.
- **Play either colour** against the AI in the terminal.
- **Built-in `--perft` self-test** for verifying move generation.

## Build & run

Requires a C++17 compiler (g++ / clang++ / MSVC).

### Linux
```bash
cd linux
make            # or ./build.sh
./chess         # you play White
./chess --depth 5
```

### macOS (Apple Silicon & Intel)
```bash
cd mac
./build.sh      # uses clang++
./chess
```

### Windows
```powershell
cd windows
build.bat       # uses g++ (MinGW) or cl (MSVC), whichever is on PATH
chess.exe
```

## Usage

```bash
./chess                 # default depth 4, you are White
./chess --depth 5       # stronger (slower) AI
./chess --black         # you play Black
./chess --fen "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
./chess --perft 4       # verify move generation (prints node counts)
```

Enter moves in coordinate notation: `e2e4`, captures `e4d5`, promotions `e7e8q`. Type `quit` to exit.

### Verifying correctness

```bash
$ ./chess --perft 4
perft(1) = 20
perft(2) = 400
perft(3) = 8902
perft(4) = 197281      # exactly the known reference values
```

## Tech stack

- **C++17**, single self-contained file (`chess.cpp`), zero dependencies
- 8×8 mailbox board, negamax + alpha-beta, piece-square evaluation

---

Built by clavexis — [github.com/clavexis](https://github.com/clavexis)
