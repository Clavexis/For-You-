# AI Chess in Terminal

Play chess against a minimax AI entirely inside your terminal — pure Python, **no dependencies**, no chess libraries.

## Demo

```text
8 | ♜ ♞ ♝ ♛ ♚ ♝ ♞ ♜ |
7 | ♟ ♟ ♟ ♟ · ♟ ♟ ♟ |
6 | · · · · · · · · |
5 | · · · · ♟ · · · |
4 | · · · · ♙ · · · |
3 | · · · · · · · · |
2 | ♙ ♙ ♙ ♙ · ♙ ♙ ♙ |
1 | ♖ ♘ ♗ ♕ ♔ ♗ ♘ ♖ |
   a b c d e f g h
  White to move.
  Moves: e2e4 e7e5

Your move: g1f3
```

## Features

- **Unicode chess board** rendered in the terminal.
- **Full legal move validation** — castling, en passant, and promotion. Verified with [perft](https://www.chessprogramming.org/Perft) against the canonical node counts.
- **Minimax AI with alpha-beta pruning** and a material + piece-square evaluation.
- **Adjustable difficulty** via search depth (`--depth`).
- **Move history** shown under the board.
- **Play either colour**, load any position with `--fen`.
- **`--perft` self-test** to verify move generation.

## Installation

Requires only **Python 3.8+** — no packages to install.

### Linux
```bash
cd linux && ./install.sh
ai-chess
```

### macOS (Apple Silicon & Intel)
```bash
cd mac && ./install.sh
ai-chess
```

### Windows
```powershell
cd windows
python chess.py
```

## Usage

```bash
python chess.py                 # you play White vs a depth-3 AI
python chess.py --depth 4       # stronger (slower) AI
python chess.py --black         # you play Black
python chess.py --perft 4       # verify move generation
```

Enter moves in coordinate notation: `e2e4`, `e4d5` (capture), `e7e8q` (promotion). Type `quit` to exit.

### Verifying correctness
```bash
$ python chess.py --perft 3
perft(1) = 20
perft(2) = 400
perft(3) = 8902      # exact reference values
```

## Tech stack

- **Python 3**, single file, standard library only
- Negamax + alpha-beta search, piece-square evaluation, FEN support

---

Built by clavexis — [github.com/clavexis](https://github.com/clavexis)
