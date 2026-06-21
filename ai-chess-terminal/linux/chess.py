#!/usr/bin/env python3
"""
AI Chess in Terminal — play chess against a minimax AI, entirely in the terminal.

  - Unicode chess board display
  - Full legal move validation (castling, en passant, promotion)
  - AI opponent using minimax with alpha-beta pruning
  - Adjustable difficulty (search depth)
  - Move history display
  - Built-in --perft self-test to verify move generation

Usage:
  chess.py                 # you play White vs a depth-3 AI
  chess.py --depth 4       # stronger AI
  chess.py --black         # you play Black
  chess.py --perft 4       # verify move generation against known counts

Built by clavexis — github.com/clavexis
"""

import argparse
import sys

# Board: list of 64, index = rank*8 + file (rank 0 = rank 1, file 0 = 'a').
# Uppercase = White, lowercase = black, '.' = empty.

START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

UNICODE = {
    'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
    'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟',
    '.': '·',
}

KNIGHT_DELTAS = [(1, 2), (2, 1), (-1, 2), (-2, 1), (1, -2), (2, -1), (-1, -2), (-2, -1)]
ROOK_DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]
BISHOP_DIRS = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
KING_DIRS = ROOK_DIRS + BISHOP_DIRS

PIECE_VALUE = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}


class Move:
    __slots__ = ("frm", "to", "promo", "ep", "castle", "double")

    def __init__(self, frm, to, promo=None, ep=False, castle=False, double=False):
        self.frm = frm
        self.to = to
        self.promo = promo      # uppercase promo piece or None
        self.ep = ep
        self.castle = castle
        self.double = double


class Position:
    def __init__(self):
        self.board = ['.'] * 64
        self.white = True
        self.wK = self.wQ = self.bK = self.bQ = True
        self.ep = -1            # en-passant target square or -1

    def copy(self):
        p = Position.__new__(Position)
        p.board = self.board[:]
        p.white = self.white
        p.wK, p.wQ, p.bK, p.bQ = self.wK, self.wQ, self.bK, self.bQ
        p.ep = self.ep
        return p


def rank_of(sq): return sq // 8
def file_of(sq): return sq % 8
def on_board(r, f): return 0 <= r < 8 and 0 <= f < 8
def is_white(c): return c != '.' and c.isupper()


def square_name(sq):
    return chr(ord('a') + file_of(sq)) + chr(ord('1') + rank_of(sq))


def from_fen(fen):
    p = Position()
    parts = fen.split()
    placement = parts[0]
    rank, file = 7, 0
    for c in placement:
        if c == '/':
            rank -= 1
            file = 0
        elif c.isdigit():
            file += int(c)
        else:
            p.board[rank * 8 + file] = c
            file += 1
    p.white = (len(parts) < 2 or parts[1] != 'b')
    castle = parts[2] if len(parts) > 2 else "KQkq"
    p.wK, p.wQ = 'K' in castle, 'Q' in castle
    p.bK, p.bQ = 'k' in castle, 'q' in castle
    if len(parts) > 3 and parts[3] != '-':
        p.ep = (int(parts[3][1]) - 1) * 8 + (ord(parts[3][0]) - ord('a'))
    return p


def is_attacked(p, sq, by_white):
    r, f = rank_of(sq), file_of(sq)
    b = p.board
    # Pawns
    pr = r - 1 if by_white else r + 1
    for df in (-1, 1):
        if on_board(pr, f + df):
            c = b[pr * 8 + (f + df)]
            if (by_white and c == 'P') or (not by_white and c == 'p'):
                return True
    # Knights
    for dr, df in KNIGHT_DELTAS:
        nr, nf = r + dr, f + df
        if on_board(nr, nf):
            c = b[nr * 8 + nf]
            if (by_white and c == 'N') or (not by_white and c == 'n'):
                return True
    # King
    for dr, df in KING_DIRS:
        nr, nf = r + dr, f + df
        if on_board(nr, nf):
            c = b[nr * 8 + nf]
            if (by_white and c == 'K') or (not by_white and c == 'k'):
                return True
    # Sliders
    for dr, df in ROOK_DIRS:
        nr, nf = r + dr, f + df
        while on_board(nr, nf):
            c = b[nr * 8 + nf]
            if c != '.':
                if (by_white and c in 'RQ') or (not by_white and c in 'rq'):
                    return True
                break
            nr += dr; nf += df
    for dr, df in BISHOP_DIRS:
        nr, nf = r + dr, f + df
        while on_board(nr, nf):
            c = b[nr * 8 + nf]
            if c != '.':
                if (by_white and c in 'BQ') or (not by_white and c in 'bq'):
                    return True
                break
            nr += dr; nf += df
    return False


def king_square(p, white):
    target = 'K' if white else 'k'
    return p.board.index(target) if target in p.board else -1


def in_check(p, white):
    ks = king_square(p, white)
    return ks >= 0 and is_attacked(p, ks, not white)


def make_move(p, m):
    piece = p.board[m.frm]
    white = is_white(piece)
    p.ep = -1
    p.board[m.frm] = '.'
    if m.ep:
        cap = m.to - 8 if white else m.to + 8
        p.board[cap] = '.'
    if m.promo:
        p.board[m.to] = m.promo if white else m.promo.lower()
    else:
        p.board[m.to] = piece
    if m.double:
        p.ep = m.frm + 8 if white else m.frm - 8
    if m.castle:
        if m.to == m.frm + 2:        # king-side
            p.board[m.frm + 1] = p.board[m.frm + 3]
            p.board[m.frm + 3] = '.'
        else:                        # queen-side
            p.board[m.frm - 1] = p.board[m.frm - 4]
            p.board[m.frm - 4] = '.'
    if piece == 'K': p.wK = p.wQ = False
    if piece == 'k': p.bK = p.bQ = False
    for sq in (m.frm, m.to):
        if sq == 0: p.wQ = False
        elif sq == 7: p.wK = False
        elif sq == 56: p.bQ = False
        elif sq == 63: p.bK = False
    p.white = not p.white


def gen_pseudo(p):
    moves = []
    white = p.white
    b = p.board
    for sq in range(64):
        c = b[sq]
        if c == '.' or is_white(c) != white:
            continue
        up = c.upper()
        r, f = rank_of(sq), file_of(sq)
        if up == 'P':
            _pawn_moves(p, sq, moves)
        elif up == 'N':
            for dr, df in KNIGHT_DELTAS:
                nr, nf = r + dr, f + df
                if on_board(nr, nf):
                    t = b[nr * 8 + nf]
                    if t == '.' or is_white(t) != white:
                        moves.append(Move(sq, nr * 8 + nf))
        elif up in ('B', 'R', 'Q'):
            dirs = BISHOP_DIRS if up == 'B' else ROOK_DIRS if up == 'R' else KING_DIRS
            for dr, df in dirs:
                nr, nf = r + dr, f + df
                while on_board(nr, nf):
                    t = b[nr * 8 + nf]
                    if t == '.':
                        moves.append(Move(sq, nr * 8 + nf))
                    else:
                        if is_white(t) != white:
                            moves.append(Move(sq, nr * 8 + nf))
                        break
                    nr += dr; nf += df
        elif up == 'K':
            for dr, df in KING_DIRS:
                nr, nf = r + dr, f + df
                if on_board(nr, nf):
                    t = b[nr * 8 + nf]
                    if t == '.' or is_white(t) != white:
                        moves.append(Move(sq, nr * 8 + nf))
            _castle_moves(p, sq, white, moves)
    return moves


def _pawn_moves(p, sq, moves):
    b = p.board
    white = is_white(b[sq])
    direction = 1 if white else -1
    r, f = rank_of(sq), file_of(sq)
    start = 1 if white else 6
    promo_rank = 7 if white else 0

    def push(frm, to, ep=False, double=False):
        if rank_of(to) == promo_rank:
            for promo in ('Q', 'R', 'B', 'N'):
                moves.append(Move(frm, to, promo=promo))
        else:
            moves.append(Move(frm, to, ep=ep, double=double))

    one = r + direction
    if on_board(one, f) and b[one * 8 + f] == '.':
        push(sq, one * 8 + f)
        if r == start and b[(r + 2 * direction) * 8 + f] == '.':
            push(sq, (r + 2 * direction) * 8 + f, double=True)
    for df in (-1, 1):
        nr, nf = r + direction, f + df
        if not on_board(nr, nf):
            continue
        to = nr * 8 + nf
        t = b[to]
        if t != '.' and is_white(t) != white:
            push(sq, to)
        elif to == p.ep:
            push(sq, to, ep=True)


def _castle_moves(p, sq, white, moves):
    home = 4 if white else 60
    if sq != home or in_check(p, white):
        return
    b = p.board
    k_side = p.wK if white else p.bK
    q_side = p.wQ if white else p.bQ
    if (k_side and b[home + 1] == '.' and b[home + 2] == '.' and
            not is_attacked(p, home + 1, not white) and not is_attacked(p, home + 2, not white)):
        moves.append(Move(home, home + 2, castle=True))
    if (q_side and b[home - 1] == '.' and b[home - 2] == '.' and b[home - 3] == '.' and
            not is_attacked(p, home - 1, not white) and not is_attacked(p, home - 2, not white)):
        moves.append(Move(home, home - 2, castle=True))


def legal_moves(p):
    out = []
    white = p.white
    for m in gen_pseudo(p):
        c = p.copy()
        make_move(c, m)
        if not in_check(c, white):
            out.append(m)
    return out


def perft(p, depth):
    if depth == 0:
        return 1
    nodes = 0
    for m in legal_moves(p):
        c = p.copy()
        make_move(c, m)
        nodes += perft(c, depth - 1)
    return nodes


# Mirror a square's rank for black piece-square lookup.
PAWN_PST = [
     0,  0,  0,  0,  0,  0,  0,  0,
     5, 10, 10,-20,-20, 10, 10,  5,
     5, -5,-10,  0,  0,-10, -5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5,  5, 10, 25, 25, 10,  5,  5,
    10, 10, 20, 30, 30, 20, 10, 10,
    50, 50, 50, 50, 50, 50, 50, 50,
     0,  0,  0,  0,  0,  0,  0,  0,
]


def evaluate(p):
    score = 0
    for sq in range(64):
        c = p.board[sq]
        if c == '.':
            continue
        white = is_white(c)
        up = c.upper()
        v = PIECE_VALUE[up]
        if up == 'P':
            pst_sq = sq if white else (56 - (sq // 8) * 8 + sq % 8)
            v += PAWN_PST[pst_sq]
        score += v if white else -v
    return score if p.white else -score


def negamax(p, depth, alpha, beta):
    if depth == 0:
        return evaluate(p)
    moves = legal_moves(p)
    if not moves:
        return -100000 + (10 - depth) if in_check(p, p.white) else 0
    best = -10 ** 9
    for m in moves:
        c = p.copy()
        make_move(c, m)
        score = -negamax(c, depth - 1, -beta, -alpha)
        if score > best:
            best = score
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best


def search_best(p, depth):
    best, best_score, alpha = None, -10 ** 9, -10 ** 9
    for m in legal_moves(p):
        c = p.copy()
        make_move(c, m)
        score = -negamax(c, depth - 1, -10 ** 9, -alpha)
        if score > best_score:
            best_score, best = score, m
        if score > alpha:
            alpha = score
    return best


def print_board(p, history):
    print()
    for r in range(7, -1, -1):
        row = f"{r + 1} |"
        for f in range(8):
            row += " " + UNICODE[p.board[r * 8 + f]]
        print(row + " |")
    print("   a b c d e f g h")
    print(f"  {'White' if p.white else 'Black'} to move.")
    if history:
        print("  Moves: " + " ".join(history))
    print()


def parse_move(p, s):
    if len(s) < 4:
        return None
    frm = (int(s[1]) - 1) * 8 + (ord(s[0]) - ord('a'))
    to = (int(s[3]) - 1) * 8 + (ord(s[2]) - ord('a'))
    promo = s[4].upper() if len(s) >= 5 else None
    for m in legal_moves(p):
        if m.frm == frm and m.to == to:
            if m.promo:
                if m.promo == (promo or 'Q'):
                    return m
            else:
                return m
    return None


def main():
    ap = argparse.ArgumentParser(description="Play chess against an AI in the terminal.")
    ap.add_argument("--depth", type=int, default=3, help="AI search depth (difficulty).")
    ap.add_argument("--fen", default=START_FEN, help="Starting position (FEN).")
    ap.add_argument("--black", action="store_true", help="You play Black.")
    ap.add_argument("--perft", type=int, metavar="D", help="Run a perft self-test and exit.")
    args = ap.parse_args()

    pos = from_fen(args.fen)

    if args.perft:
        for d in range(1, args.perft + 1):
            print(f"perft({d}) = {perft(pos, d)}")
        return 0

    human_white = not args.black
    history = []

    print("AI Chess in Terminal — by clavexis")
    print("Enter moves like 'e2e4' (promotions 'e7e8q'). Type 'quit' to exit.")
    print(f"AI depth: {args.depth}")

    while True:
        print_board(pos, history)
        moves = legal_moves(pos)
        if not moves:
            if in_check(pos, pos.white):
                print(f"Checkmate! {'Black' if pos.white else 'White'} wins.")
            else:
                print("Stalemate — draw.")
            break

        if pos.white == human_white:
            try:
                s = input("Your move: ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if s in ("quit", "exit"):
                break
            m = parse_move(pos, s)
            if not m:
                print("Illegal or malformed move. Try again.")
                continue
            history.append(square_name(m.frm) + square_name(m.to))
            make_move(pos, m)
        else:
            print("AI thinking...")
            m = search_best(pos, args.depth)
            mv = square_name(m.frm) + square_name(m.to) + (m.promo.lower() if m.promo else "")
            print(f"AI plays {mv}")
            history.append(mv)
            make_move(pos, m)

    print("Thanks for playing!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
