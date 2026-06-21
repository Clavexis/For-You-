// Chess Engine from Scratch — no chess libraries.
//
//   - Full legal move generation (castling, en passant, promotion)
//   - Negamax search with alpha-beta pruning
//   - Material + piece-square-table evaluation
//   - Adjustable difficulty (search depth)
//   - FEN load/print, terminal play against the AI
//
// Build:  g++ -O2 -std=c++17 -o chess chess.cpp
// Play :  ./chess            (you are White)
//         ./chess --depth 5  (stronger AI)
//         ./chess --fen "<FEN>"
//
// Built by clavexis — github.com/clavexis

#include <array>
#include <cctype>
#include <chrono>
#include <climits>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

// Squares are 0..63, square = rank*8 + file, rank 0 == rank 1 (White's home),
// file 0 == 'a'. White pieces are uppercase, black lowercase, '.' is empty.

struct Move {
    int from, to;
    char promo = 0;          // 'Q','R','B','N' (uppercase) if a promotion
    bool isEnPassant = false;
    bool isCastle = false;
    bool isDoublePush = false;
};

struct Position {
    std::array<char, 64> board{};
    bool whiteToMove = true;
    // Castling rights: K Q k q
    bool wK = true, wQ = true, bK = true, bQ = true;
    int enPassant = -1;      // target square behind a double push, or -1
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
static inline int rankOf(int sq) { return sq / 8; }
static inline int fileOf(int sq) { return sq % 8; }
static inline bool onBoard(int r, int f) { return r >= 0 && r < 8 && f >= 0 && f < 8; }
static inline bool isWhitePiece(char c) { return c != '.' && std::isupper((unsigned char)c); }
static inline bool isBlackPiece(char c) { return c != '.' && std::islower((unsigned char)c); }

static std::string squareName(int sq) {
    std::string s;
    s += char('a' + fileOf(sq));
    s += char('1' + rankOf(sq));
    return s;
}

// ---------------------------------------------------------------------------
// FEN
// ---------------------------------------------------------------------------
static Position fromFEN(const std::string& fen) {
    Position p;
    p.board.fill('.');
    std::istringstream iss(fen);
    std::string placement, side, castle, ep;
    iss >> placement >> side >> castle >> ep;

    int rank = 7, file = 0;
    for (char c : placement) {
        if (c == '/') { rank--; file = 0; }
        else if (std::isdigit((unsigned char)c)) { file += c - '0'; }
        else { p.board[rank * 8 + file] = c; file++; }
    }
    p.whiteToMove = (side != "b");
    p.wK = castle.find('K') != std::string::npos;
    p.wQ = castle.find('Q') != std::string::npos;
    p.bK = castle.find('k') != std::string::npos;
    p.bQ = castle.find('q') != std::string::npos;
    if (ep.size() == 2 && ep != "-")
        p.enPassant = (ep[1] - '1') * 8 + (ep[0] - 'a');
    return p;
}

static const std::string START_FEN =
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";

// ---------------------------------------------------------------------------
// Attack detection
// ---------------------------------------------------------------------------
// Is `sq` attacked by the side given by `byWhite`?
static bool isAttacked(const Position& p, int sq, bool byWhite) {
    int r = rankOf(sq), f = fileOf(sq);

    // Pawns: a white pawn on (r-1, f±1) attacks (r,f).
    int pr = byWhite ? r - 1 : r + 1;
    for (int df : {-1, 1}) {
        if (onBoard(pr, f + df)) {
            char c = p.board[pr * 8 + (f + df)];
            if (byWhite && c == 'P') return true;
            if (!byWhite && c == 'p') return true;
        }
    }
    // Knights
    static const int kn[8][2] = {{1,2},{2,1},{-1,2},{-2,1},{1,-2},{2,-1},{-1,-2},{-2,-1}};
    for (auto& d : kn) {
        int nr = r + d[0], nf = f + d[1];
        if (onBoard(nr, nf)) {
            char c = p.board[nr * 8 + nf];
            if (byWhite && c == 'N') return true;
            if (!byWhite && c == 'n') return true;
        }
    }
    // King
    for (int dr = -1; dr <= 1; dr++)
        for (int dfk = -1; dfk <= 1; dfk++) {
            if (!dr && !dfk) continue;
            int nr = r + dr, nf = f + dfk;
            if (onBoard(nr, nf)) {
                char c = p.board[nr * 8 + nf];
                if (byWhite && c == 'K') return true;
                if (!byWhite && c == 'k') return true;
            }
        }
    // Sliding: rook/queen (orthogonal), bishop/queen (diagonal)
    static const int rookDir[4][2] = {{1,0},{-1,0},{0,1},{0,-1}};
    static const int bishDir[4][2] = {{1,1},{1,-1},{-1,1},{-1,-1}};
    for (auto& d : rookDir) {
        int nr = r + d[0], nf = f + d[1];
        while (onBoard(nr, nf)) {
            char c = p.board[nr * 8 + nf];
            if (c != '.') {
                if (byWhite && (c == 'R' || c == 'Q')) return true;
                if (!byWhite && (c == 'r' || c == 'q')) return true;
                break;
            }
            nr += d[0]; nf += d[1];
        }
    }
    for (auto& d : bishDir) {
        int nr = r + d[0], nf = f + d[1];
        while (onBoard(nr, nf)) {
            char c = p.board[nr * 8 + nf];
            if (c != '.') {
                if (byWhite && (c == 'B' || c == 'Q')) return true;
                if (!byWhite && (c == 'b' || c == 'q')) return true;
                break;
            }
            nr += d[0]; nf += d[1];
        }
    }
    return false;
}

static int kingSquare(const Position& p, bool white) {
    char k = white ? 'K' : 'k';
    for (int i = 0; i < 64; i++) if (p.board[i] == k) return i;
    return -1;
}

static bool inCheck(const Position& p, bool white) {
    int ks = kingSquare(p, white);
    return ks >= 0 && isAttacked(p, ks, !white);
}

// ---------------------------------------------------------------------------
// Make / unmake
// ---------------------------------------------------------------------------
static void makeMove(Position& p, const Move& m) {
    char piece = p.board[m.from];
    bool white = isWhitePiece(piece);

    p.enPassant = -1;
    p.board[m.from] = '.';

    if (m.isEnPassant) {
        // Captured pawn sits beside the destination, on the mover's rank.
        int capSq = white ? m.to - 8 : m.to + 8;
        p.board[capSq] = '.';
    }

    if (m.promo)
        p.board[m.to] = white ? m.promo : char(std::tolower(m.promo));
    else
        p.board[m.to] = piece;

    if (m.isDoublePush)
        p.enPassant = white ? m.from + 8 : m.from - 8;

    if (m.isCastle) {
        // Move the rook to the other side of the king.
        if (m.to == m.from + 2) {                 // king-side
            p.board[m.from + 1] = p.board[m.from + 3];
            p.board[m.from + 3] = '.';
        } else {                                  // queen-side
            p.board[m.from - 1] = p.board[m.from - 4];
            p.board[m.from - 4] = '.';
        }
    }

    // Update castling rights when king/rook moves or a rook is captured.
    if (piece == 'K') { p.wK = p.wQ = false; }
    if (piece == 'k') { p.bK = p.bQ = false; }
    if (m.from == 0 || m.to == 0) p.wQ = false;
    if (m.from == 7 || m.to == 7) p.wK = false;
    if (m.from == 56 || m.to == 56) p.bQ = false;
    if (m.from == 63 || m.to == 63) p.bK = false;

    p.whiteToMove = !p.whiteToMove;
}

// ---------------------------------------------------------------------------
// Pseudo-legal move generation
// ---------------------------------------------------------------------------
static void addPawnMoves(const Position& p, int sq, std::vector<Move>& out) {
    bool white = isWhitePiece(p.board[sq]);
    int dir = white ? 1 : -1;
    int r = rankOf(sq), f = fileOf(sq);
    int startRank = white ? 1 : 6;
    int promoRank = white ? 7 : 0;

    auto pushPromo = [&](int from, int to, bool ep, bool dbl) {
        if (rankOf(to) == promoRank) {
            for (char pr : {'Q', 'R', 'B', 'N'}) {
                Move m; m.from = from; m.to = to; m.promo = pr; out.push_back(m);
            }
        } else {
            Move m; m.from = from; m.to = to; m.isEnPassant = ep; m.isDoublePush = dbl;
            out.push_back(m);
        }
    };

    int oneR = r + dir;
    if (onBoard(oneR, f) && p.board[oneR * 8 + f] == '.') {
        pushPromo(sq, oneR * 8 + f, false, false);
        if (r == startRank && p.board[(r + 2 * dir) * 8 + f] == '.')
            pushPromo(sq, (r + 2 * dir) * 8 + f, false, true);
    }
    for (int df : {-1, 1}) {
        int nr = r + dir, nf = f + df;
        if (!onBoard(nr, nf)) continue;
        int to = nr * 8 + nf;
        char c = p.board[to];
        if (c != '.' && isWhitePiece(c) != white)
            pushPromo(sq, to, false, false);
        else if (to == p.enPassant)
            pushPromo(sq, to, true, false);
    }
}

static void addStepMoves(const Position& p, int sq, const int dirs[][2], int n,
                         bool white, std::vector<Move>& out) {
    int r = rankOf(sq), f = fileOf(sq);
    for (int i = 0; i < n; i++) {
        int nr = r + dirs[i][0], nf = f + dirs[i][1];
        if (!onBoard(nr, nf)) continue;
        char c = p.board[nr * 8 + nf];
        if (c == '.' || isWhitePiece(c) != white) {
            Move m; m.from = sq; m.to = nr * 8 + nf; out.push_back(m);
        }
    }
}

static void addSlideMoves(const Position& p, int sq, const int dirs[][2], int n,
                          bool white, std::vector<Move>& out) {
    int r = rankOf(sq), f = fileOf(sq);
    for (int i = 0; i < n; i++) {
        int nr = r + dirs[i][0], nf = f + dirs[i][1];
        while (onBoard(nr, nf)) {
            char c = p.board[nr * 8 + nf];
            if (c == '.') {
                Move m; m.from = sq; m.to = nr * 8 + nf; out.push_back(m);
            } else {
                if (isWhitePiece(c) != white) {
                    Move m; m.from = sq; m.to = nr * 8 + nf; out.push_back(m);
                }
                break;
            }
            nr += dirs[i][0]; nf += dirs[i][1];
        }
    }
}

static void generatePseudoLegal(const Position& p, std::vector<Move>& out) {
    bool white = p.whiteToMove;
    static const int rookD[4][2] = {{1,0},{-1,0},{0,1},{0,-1}};
    static const int bishD[4][2] = {{1,1},{1,-1},{-1,1},{-1,-1}};
    static const int allD[8][2]  = {{1,0},{-1,0},{0,1},{0,-1},{1,1},{1,-1},{-1,1},{-1,-1}};
    static const int knD[8][2]   = {{1,2},{2,1},{-1,2},{-2,1},{1,-2},{2,-1},{-1,-2},{-2,-1}};

    for (int sq = 0; sq < 64; sq++) {
        char c = p.board[sq];
        if (c == '.') continue;
        if (isWhitePiece(c) != white) continue;
        char up = std::toupper((unsigned char)c);
        switch (up) {
            case 'P': addPawnMoves(p, sq, out); break;
            case 'N': addStepMoves(p, sq, knD, 8, white, out); break;
            case 'B': addSlideMoves(p, sq, bishD, 4, white, out); break;
            case 'R': addSlideMoves(p, sq, rookD, 4, white, out); break;
            case 'Q': addSlideMoves(p, sq, allD, 8, white, out); break;
            case 'K': {
                addStepMoves(p, sq, allD, 8, white, out);
                // Castling — squares empty and not passing through check.
                int home = white ? 4 : 60;
                if (sq == home && !inCheck(p, white)) {
                    bool kSide = white ? p.wK : p.bK;
                    bool qSide = white ? p.wQ : p.bQ;
                    if (kSide && p.board[home+1]=='.' && p.board[home+2]=='.' &&
                        !isAttacked(p, home+1, !white) && !isAttacked(p, home+2, !white)) {
                        Move m; m.from = home; m.to = home + 2; m.isCastle = true; out.push_back(m);
                    }
                    if (qSide && p.board[home-1]=='.' && p.board[home-2]=='.' &&
                        p.board[home-3]=='.' &&
                        !isAttacked(p, home-1, !white) && !isAttacked(p, home-2, !white)) {
                        Move m; m.from = home; m.to = home - 2; m.isCastle = true; out.push_back(m);
                    }
                }
                break;
            }
        }
    }
}

// Legal moves = pseudo-legal moves that don't leave our king in check.
static std::vector<Move> generateLegal(const Position& p) {
    std::vector<Move> pseudo, legal;
    generatePseudoLegal(p, pseudo);
    bool white = p.whiteToMove;
    for (const Move& m : pseudo) {
        Position copy = p;
        makeMove(copy, m);
        if (!inCheck(copy, white)) legal.push_back(m);
    }
    return legal;
}

// ---------------------------------------------------------------------------
// Evaluation
// ---------------------------------------------------------------------------
static int pieceValue(char up) {
    switch (up) {
        case 'P': return 100; case 'N': return 320; case 'B': return 330;
        case 'R': return 500; case 'Q': return 900; case 'K': return 20000;
    }
    return 0;
}

// A single pawn piece-square table; mirrored for black. Encourages central play.
static const int pawnPST[64] = {
     0,  0,  0,  0,  0,  0,  0,  0,
     5, 10, 10,-20,-20, 10, 10,  5,
     5, -5,-10,  0,  0,-10, -5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5,  5, 10, 25, 25, 10,  5,  5,
    10, 10, 20, 30, 30, 20, 10, 10,
    50, 50, 50, 50, 50, 50, 50, 50,
     0,  0,  0,  0,  0,  0,  0,  0
};
static const int knightPST[64] = {
   -50,-40,-30,-30,-30,-30,-40,-50,
   -40,-20,  0,  5,  5,  0,-20,-40,
   -30,  5, 10, 15, 15, 10,  5,-30,
   -30,  0, 15, 20, 20, 15,  0,-30,
   -30,  5, 15, 20, 20, 15,  5,-30,
   -30,  0, 10, 15, 15, 10,  0,-30,
   -40,-20,  0,  0,  0,  0,-20,-40,
   -50,-40,-30,-30,-30,-30,-40,-50
};

// Evaluation from the side-to-move's perspective (for negamax).
static int evaluate(const Position& p) {
    int score = 0;
    for (int sq = 0; sq < 64; sq++) {
        char c = p.board[sq];
        if (c == '.') continue;
        bool white = isWhitePiece(c);
        char up = std::toupper((unsigned char)c);
        int v = pieceValue(up);
        int pstSq = white ? sq : (56 - (sq / 8) * 8 + (sq % 8)); // mirror rank for black
        if (up == 'P') v += pawnPST[pstSq];
        else if (up == 'N') v += knightPST[pstSq];
        score += white ? v : -v;
    }
    return p.whiteToMove ? score : -score;
}

// ---------------------------------------------------------------------------
// Negamax + alpha-beta
// ---------------------------------------------------------------------------
static int negamax(const Position& p, int depth, int alpha, int beta) {
    if (depth == 0) return evaluate(p);

    std::vector<Move> moves = generateLegal(p);
    if (moves.empty()) {
        // Checkmate (bad for side to move) or stalemate (draw).
        if (inCheck(p, p.whiteToMove)) return -100000 + (10 - depth); // prefer slower mates
        return 0;
    }

    int best = INT_MIN;
    for (const Move& m : moves) {
        Position copy = p;
        makeMove(copy, m);
        int score = -negamax(copy, depth - 1, -beta, -alpha);
        if (score > best) best = score;
        if (best > alpha) alpha = best;
        if (alpha >= beta) break; // beta cutoff
    }
    return best;
}

// Perft — counts leaf nodes at a given depth. Used to verify that legal move
// generation is correct against known reference values.
static long long perft(const Position& p, int depth) {
    if (depth == 0) return 1;
    long long nodes = 0;
    for (const Move& m : generateLegal(p)) {
        Position copy = p;
        makeMove(copy, m);
        nodes += perft(copy, depth - 1);
    }
    return nodes;
}

static Move searchBestMove(const Position& p, int depth) {
    std::vector<Move> moves = generateLegal(p);
    Move best = moves.empty() ? Move{} : moves[0];
    int bestScore = INT_MIN, alpha = -1000000, beta = 1000000;
    for (const Move& m : moves) {
        Position copy = p;
        makeMove(copy, m);
        int score = -negamax(copy, depth - 1, -beta, -alpha);
        if (score > bestScore) { bestScore = score; best = m; }
        if (score > alpha) alpha = score;
    }
    return best;
}

// ---------------------------------------------------------------------------
// Terminal I/O
// ---------------------------------------------------------------------------
static void printBoard(const Position& p) {
    std::cout << "\n  +------------------------+\n";
    for (int r = 7; r >= 0; r--) {
        std::cout << (r + 1) << " |";
        for (int f = 0; f < 8; f++) {
            char c = p.board[r * 8 + f];
            std::cout << ' ' << (c == '.' ? '.' : c) << ' ';
        }
        std::cout << "|\n";
    }
    std::cout << "  +------------------------+\n";
    std::cout << "    a  b  c  d  e  f  g  h\n";
    std::cout << "  " << (p.whiteToMove ? "White" : "Black") << " to move.\n\n";
}

// Parse "e2e4" / "e7e8q" into a legal Move (matched against the legal list).
static bool parseMove(const Position& p, const std::string& in, Move& out) {
    if (in.size() < 4) return false;
    int from = (in[1] - '1') * 8 + (in[0] - 'a');
    int to   = (in[3] - '1') * 8 + (in[2] - 'a');
    char promo = in.size() >= 5 ? std::toupper((unsigned char)in[4]) : 0;
    for (const Move& m : generateLegal(p)) {
        if (m.from == from && m.to == to) {
            if (m.promo) { if (m.promo == (promo ? promo : 'Q')) { out = m; return true; } }
            else { out = m; return true; }
        }
    }
    return false;
}

static bool gameOver(const Position& p) {
    if (!generateLegal(p).empty()) return false;
    if (inCheck(p, p.whiteToMove))
        std::cout << "Checkmate! " << (p.whiteToMove ? "Black" : "White") << " wins.\n";
    else
        std::cout << "Stalemate — draw.\n";
    return true;
}

int main(int argc, char** argv) {
    int depth = 4;
    std::string fen = START_FEN;
    bool whiteIsHuman = true;

    for (int i = 1; i < argc; i++) {
        std::string a = argv[i];
        if (a == "--depth" && i + 1 < argc) depth = std::stoi(argv[++i]);
        else if (a == "--fen" && i + 1 < argc) fen = argv[++i];
        else if (a == "--black") whiteIsHuman = false; // human plays Black
        else if (a == "--perft" && i + 1 < argc) {
            int d = std::stoi(argv[++i]);
            Position pp = fromFEN(fen);
            for (int k = 1; k <= d; k++)
                std::cout << "perft(" << k << ") = " << perft(pp, k) << "\n";
            return 0;
        }
        else if (a == "--help") {
            std::cout << "Usage: chess [--depth N] [--fen \"FEN\"] [--black] [--perft D]\n";
            return 0;
        }
    }

    Position pos = fromFEN(fen);
    std::cout << "Chess Engine from Scratch — by clavexis\n";
    std::cout << "Enter moves like 'e2e4' (promotions: 'e7e8q'). Type 'quit' to exit.\n";
    std::cout << "AI search depth: " << depth << "\n";

    while (true) {
        printBoard(pos);
        if (gameOver(pos)) break;

        bool humanTurn = (pos.whiteToMove == whiteIsHuman);
        if (humanTurn) {
            std::cout << "Your move: ";
            std::string in;
            if (!std::getline(std::cin, in)) break;
            if (in == "quit" || in == "exit") break;
            Move m;
            if (!parseMove(pos, in, m)) {
                std::cout << "Illegal or malformed move. Try again.\n";
                continue;
            }
            makeMove(pos, m);
        } else {
            std::cout << "AI thinking...\n";
            auto t0 = std::chrono::steady_clock::now();
            Move m = searchBestMove(pos, depth);
            auto t1 = std::chrono::steady_clock::now();
            double secs = std::chrono::duration<double>(t1 - t0).count();
            std::cout << "AI plays " << squareName(m.from) << squareName(m.to);
            if (m.promo) std::cout << char(std::tolower(m.promo));
            std::cout << "  (" << secs << "s)\n";
            makeMove(pos, m);
        }
    }
    std::cout << "Thanks for playing!\n";
    return 0;
}
