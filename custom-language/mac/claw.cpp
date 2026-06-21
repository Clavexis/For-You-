// Claw — a minimal interpreted programming language.
//
//   Lexer + recursive-descent parser + tree-walking interpreter.
//   Features: numbers, strings, booleans, nil; variables; arithmetic,
//   comparison and logical operators; if/else; while loops; functions with
//   parameters and return; a built-in print; clear errors with line numbers.
//
// Build:  g++ -O2 -std=c++17 -o claw claw.cpp
// Run :   ./claw program.claw      (run a file)
//         ./claw                   (interactive REPL)
//
// Built by clavexis — github.com/clavexis

#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <memory>
#include <unordered_map>
#include <functional>
#include <stdexcept>

// ===========================================================================
// Tokens
// ===========================================================================
enum class Tok {
    LPAREN, RPAREN, LBRACE, RBRACE, COMMA, SEMICOLON,
    PLUS, MINUS, STAR, SLASH, PERCENT,
    BANG, BANG_EQ, EQ, EQ_EQ, GT, GE, LT, LE,
    AND, OR,
    IDENT, NUMBER, STRING,
    LET, FN, IF, ELSE, WHILE, RETURN, PRINT, TRUE, FALSE, NIL,
    END
};

struct Token {
    Tok type;
    std::string lexeme;
    double number = 0;
    int line = 1;
};

// A parse/runtime error carrying a line number for friendly messages.
struct ClawError : std::runtime_error {
    int line;
    ClawError(int ln, const std::string& msg)
        : std::runtime_error(msg), line(ln) {}
};

// ===========================================================================
// Lexer
// ===========================================================================
class Lexer {
public:
    explicit Lexer(std::string src) : src_(std::move(src)) {}

    std::vector<Token> scan() {
        std::vector<Token> out;
        while (!atEnd()) {
            skipWhitespace();
            if (atEnd()) break;
            char c = peek();
            if (std::isdigit((unsigned char)c)) out.push_back(number());
            else if (std::isalpha((unsigned char)c) || c == '_') out.push_back(identifier());
            else if (c == '"') out.push_back(string());
            else out.push_back(symbol());
        }
        out.push_back({Tok::END, "", 0, line_});
        return out;
    }

private:
    std::string src_;
    size_t pos_ = 0;
    int line_ = 1;

    bool atEnd() { return pos_ >= src_.size(); }
    char peek() { return atEnd() ? '\0' : src_[pos_]; }
    char peekNext() { return pos_ + 1 < src_.size() ? src_[pos_ + 1] : '\0'; }
    char advance() { return src_[pos_++]; }
    bool match(char c) { if (peek() == c) { pos_++; return true; } return false; }

    void skipWhitespace() {
        while (!atEnd()) {
            char c = peek();
            if (c == '\n') { line_++; pos_++; }
            else if (c == ' ' || c == '\t' || c == '\r') pos_++;
            else if (c == '#') { while (!atEnd() && peek() != '\n') pos_++; } // comment
            else break;
        }
    }

    Token number() {
        std::string s;
        while (std::isdigit((unsigned char)peek())) s += advance();
        if (peek() == '.' && std::isdigit((unsigned char)peekNext())) {
            s += advance();
            while (std::isdigit((unsigned char)peek())) s += advance();
        }
        return {Tok::NUMBER, s, std::stod(s), line_};
    }

    Token identifier() {
        std::string s;
        while (std::isalnum((unsigned char)peek()) || peek() == '_') s += advance();
        static const std::unordered_map<std::string, Tok> kw = {
            {"let", Tok::LET}, {"fn", Tok::FN}, {"if", Tok::IF}, {"else", Tok::ELSE},
            {"while", Tok::WHILE}, {"return", Tok::RETURN}, {"print", Tok::PRINT},
            {"true", Tok::TRUE}, {"false", Tok::FALSE}, {"nil", Tok::NIL},
            {"and", Tok::AND}, {"or", Tok::OR},
        };
        auto it = kw.find(s);
        return {it == kw.end() ? Tok::IDENT : it->second, s, 0, line_};
    }

    Token string() {
        advance(); // opening quote
        std::string s;
        while (!atEnd() && peek() != '"') {
            char c = advance();
            if (c == '\\' && !atEnd()) {               // simple escapes
                char e = advance();
                if (e == 'n') c = '\n';
                else if (e == 't') c = '\t';
                else c = e;
            }
            if (c == '\n') line_++;
            s += c;
        }
        if (atEnd()) throw ClawError(line_, "unterminated string");
        advance(); // closing quote
        return {Tok::STRING, s, 0, line_};
    }

    Token symbol() {
        int ln = line_;
        char c = advance();
        switch (c) {
            case '(': return {Tok::LPAREN, "(", 0, ln};
            case ')': return {Tok::RPAREN, ")", 0, ln};
            case '{': return {Tok::LBRACE, "{", 0, ln};
            case '}': return {Tok::RBRACE, "}", 0, ln};
            case ',': return {Tok::COMMA, ",", 0, ln};
            case ';': return {Tok::SEMICOLON, ";", 0, ln};
            case '+': return {Tok::PLUS, "+", 0, ln};
            case '-': return {Tok::MINUS, "-", 0, ln};
            case '*': return {Tok::STAR, "*", 0, ln};
            case '/': return {Tok::SLASH, "/", 0, ln};
            case '%': return {Tok::PERCENT, "%", 0, ln};
            case '!': return {match('=') ? Tok::BANG_EQ : Tok::BANG, "!", 0, ln};
            case '=': return {match('=') ? Tok::EQ_EQ : Tok::EQ, "=", 0, ln};
            case '>': return {match('=') ? Tok::GE : Tok::GT, ">", 0, ln};
            case '<': return {match('=') ? Tok::LE : Tok::LT, "<", 0, ln};
        }
        throw ClawError(ln, std::string("unexpected character '") + c + "'");
    }
};

// ===========================================================================
// AST
// ===========================================================================
struct Interpreter;
struct Value;
struct Environment;

struct Expr { int line = 0; virtual ~Expr() = default; virtual Value eval(Interpreter&) = 0; };
struct Stmt : std::enable_shared_from_this<Stmt> {
    int line = 0; virtual ~Stmt() = default; virtual void exec(Interpreter&) = 0;
};
using ExprP = std::shared_ptr<Expr>;
using StmtP = std::shared_ptr<Stmt>;

struct FunctionStmt; // fwd

// Runtime value.
struct Value {
    enum Type { NIL, NUMBER, BOOL, STRING, FUNCTION } type = NIL;
    double num = 0;
    bool boolean = false;
    std::string str;
    std::shared_ptr<FunctionStmt> fn;
    std::shared_ptr<Environment> closure;

    static Value nil() { return {}; }
    static Value number(double d) { Value v; v.type = NUMBER; v.num = d; return v; }
    static Value bul(bool b) { Value v; v.type = BOOL; v.boolean = b; return v; }
    static Value string_(std::string s) { Value v; v.type = STRING; v.str = std::move(s); return v; }

    bool truthy() const {
        if (type == NIL) return false;
        if (type == BOOL) return boolean;
        if (type == NUMBER) return num != 0;
        return true;
    }
    std::string toString() const {
        switch (type) {
            case NIL: return "nil";
            case BOOL: return boolean ? "true" : "false";
            case STRING: return str;
            case FUNCTION: return "<fn>";
            case NUMBER: {
                if (num == (long long)num) return std::to_string((long long)num);
                std::ostringstream os; os << num; return os.str();
            }
        }
        return "nil";
    }
};

// Expression nodes
struct Literal : Expr { Value value; Value eval(Interpreter&) override { return value; } };
struct Variable : Expr { std::string name; Value eval(Interpreter&) override; };
struct Assign : Expr { std::string name; ExprP value; Value eval(Interpreter&) override; };
struct Unary : Expr { Tok op; ExprP right; Value eval(Interpreter&) override; };
struct Binary : Expr { Tok op; ExprP left, right; Value eval(Interpreter&) override; };
struct Logical : Expr { Tok op; ExprP left, right; Value eval(Interpreter&) override; };
struct Call : Expr { ExprP callee; std::vector<ExprP> args; Value eval(Interpreter&) override; };

// Statement nodes
struct ExpressionStmt : Stmt { ExprP expr; void exec(Interpreter&) override; };
struct PrintStmt : Stmt { ExprP expr; void exec(Interpreter&) override; };
struct LetStmt : Stmt { std::string name; ExprP init; void exec(Interpreter&) override; };
struct BlockStmt : Stmt { std::vector<StmtP> stmts; void exec(Interpreter&) override; };
struct IfStmt : Stmt { ExprP cond; StmtP thenB, elseB; void exec(Interpreter&) override; };
struct WhileStmt : Stmt { ExprP cond; StmtP body; void exec(Interpreter&) override; };
struct FunctionStmt : Stmt {
    std::string name; std::vector<std::string> params; std::vector<StmtP> body;
    void exec(Interpreter&) override;
};
struct ReturnStmt : Stmt { ExprP value; void exec(Interpreter&) override; };

// ===========================================================================
// Parser (recursive descent)
// ===========================================================================
class Parser {
public:
    explicit Parser(std::vector<Token> toks) : toks_(std::move(toks)) {}

    std::vector<StmtP> parse() {
        std::vector<StmtP> stmts;
        while (!check(Tok::END)) stmts.push_back(statement());
        return stmts;
    }

private:
    std::vector<Token> toks_;
    size_t pos_ = 0;

    const Token& peek() { return toks_[pos_]; }
    const Token& prev() { return toks_[pos_ - 1]; }
    bool check(Tok t) { return peek().type == t; }
    bool match(Tok t) { if (check(t)) { pos_++; return true; } return false; }
    const Token& advance() { return toks_[pos_++]; }
    const Token& expect(Tok t, const std::string& msg) {
        if (check(t)) return advance();
        throw ClawError(peek().line, msg);
    }

    StmtP statement() {
        if (match(Tok::LET)) return letStmt();
        if (match(Tok::PRINT)) return printStmt();
        if (match(Tok::IF)) return ifStmt();
        if (match(Tok::WHILE)) return whileStmt();
        if (match(Tok::FN)) return funcStmt();
        if (match(Tok::RETURN)) return returnStmt();
        if (match(Tok::LBRACE)) return block();
        return exprStmt();
    }

    StmtP letStmt() {
        auto s = std::make_shared<LetStmt>();
        s->line = prev().line;
        s->name = expect(Tok::IDENT, "expected variable name after 'let'").lexeme;
        if (match(Tok::EQ)) s->init = expression();
        expect(Tok::SEMICOLON, "expected ';' after let statement");
        return s;
    }
    StmtP printStmt() {
        auto s = std::make_shared<PrintStmt>();
        s->line = prev().line;
        s->expr = expression();
        expect(Tok::SEMICOLON, "expected ';' after print");
        return s;
    }
    StmtP ifStmt() {
        auto s = std::make_shared<IfStmt>();
        s->line = prev().line;
        expect(Tok::LPAREN, "expected '(' after 'if'");
        s->cond = expression();
        expect(Tok::RPAREN, "expected ')' after condition");
        s->thenB = statement();
        if (match(Tok::ELSE)) s->elseB = statement();
        return s;
    }
    StmtP whileStmt() {
        auto s = std::make_shared<WhileStmt>();
        s->line = prev().line;
        expect(Tok::LPAREN, "expected '(' after 'while'");
        s->cond = expression();
        expect(Tok::RPAREN, "expected ')' after condition");
        s->body = statement();
        return s;
    }
    StmtP funcStmt() {
        auto s = std::make_shared<FunctionStmt>();
        s->line = prev().line;
        s->name = expect(Tok::IDENT, "expected function name").lexeme;
        expect(Tok::LPAREN, "expected '(' after function name");
        if (!check(Tok::RPAREN)) {
            do { s->params.push_back(expect(Tok::IDENT, "expected parameter name").lexeme); }
            while (match(Tok::COMMA));
        }
        expect(Tok::RPAREN, "expected ')' after parameters");
        expect(Tok::LBRACE, "expected '{' before function body");
        while (!check(Tok::RBRACE) && !check(Tok::END)) s->body.push_back(statement());
        expect(Tok::RBRACE, "expected '}' after function body");
        return s;
    }
    StmtP returnStmt() {
        auto s = std::make_shared<ReturnStmt>();
        s->line = prev().line;
        if (!check(Tok::SEMICOLON)) s->value = expression();
        expect(Tok::SEMICOLON, "expected ';' after return");
        return s;
    }
    StmtP block() {
        auto s = std::make_shared<BlockStmt>();
        s->line = prev().line;
        while (!check(Tok::RBRACE) && !check(Tok::END)) s->stmts.push_back(statement());
        expect(Tok::RBRACE, "expected '}' to close block");
        return s;
    }
    StmtP exprStmt() {
        auto s = std::make_shared<ExpressionStmt>();
        s->line = peek().line;
        s->expr = expression();
        expect(Tok::SEMICOLON, "expected ';' after expression");
        return s;
    }

    // Expression precedence ladder.
    ExprP expression() { return assignment(); }

    ExprP assignment() {
        ExprP expr = logicOr();
        if (match(Tok::EQ)) {
            int ln = prev().line;
            ExprP value = assignment();
            if (auto var = std::dynamic_pointer_cast<Variable>(expr)) {
                auto a = std::make_shared<Assign>();
                a->line = ln; a->name = var->name; a->value = value;
                return a;
            }
            throw ClawError(ln, "invalid assignment target");
        }
        return expr;
    }
    ExprP logicOr() {
        ExprP expr = logicAnd();
        while (match(Tok::OR)) { auto l = std::make_shared<Logical>(); l->op = Tok::OR; l->line = prev().line; l->left = expr; l->right = logicAnd(); expr = l; }
        return expr;
    }
    ExprP logicAnd() {
        ExprP expr = equality();
        while (match(Tok::AND)) { auto l = std::make_shared<Logical>(); l->op = Tok::AND; l->line = prev().line; l->left = expr; l->right = equality(); expr = l; }
        return expr;
    }
    ExprP equality() {
        ExprP expr = comparison();
        while (check(Tok::EQ_EQ) || check(Tok::BANG_EQ)) {
            Tok op = advance().type; auto b = std::make_shared<Binary>();
            b->op = op; b->line = prev().line; b->left = expr; b->right = comparison(); expr = b;
        }
        return expr;
    }
    ExprP comparison() {
        ExprP expr = term();
        while (check(Tok::GT) || check(Tok::GE) || check(Tok::LT) || check(Tok::LE)) {
            Tok op = advance().type; auto b = std::make_shared<Binary>();
            b->op = op; b->line = prev().line; b->left = expr; b->right = term(); expr = b;
        }
        return expr;
    }
    ExprP term() {
        ExprP expr = factor();
        while (check(Tok::PLUS) || check(Tok::MINUS)) {
            Tok op = advance().type; auto b = std::make_shared<Binary>();
            b->op = op; b->line = prev().line; b->left = expr; b->right = factor(); expr = b;
        }
        return expr;
    }
    ExprP factor() {
        ExprP expr = unary();
        while (check(Tok::STAR) || check(Tok::SLASH) || check(Tok::PERCENT)) {
            Tok op = advance().type; auto b = std::make_shared<Binary>();
            b->op = op; b->line = prev().line; b->left = expr; b->right = unary(); expr = b;
        }
        return expr;
    }
    ExprP unary() {
        if (check(Tok::BANG) || check(Tok::MINUS)) {
            Tok op = advance().type; auto u = std::make_shared<Unary>();
            u->op = op; u->line = prev().line; u->right = unary(); return u;
        }
        return call();
    }
    ExprP call() {
        ExprP expr = primary();
        while (match(Tok::LPAREN)) {
            auto c = std::make_shared<Call>(); c->line = prev().line; c->callee = expr;
            if (!check(Tok::RPAREN)) {
                do { c->args.push_back(expression()); } while (match(Tok::COMMA));
            }
            expect(Tok::RPAREN, "expected ')' after arguments");
            expr = c;
        }
        return expr;
    }
    ExprP primary() {
        const Token& t = peek();
        if (match(Tok::NUMBER)) { auto l = std::make_shared<Literal>(); l->line = t.line; l->value = Value::number(t.number); return l; }
        if (match(Tok::STRING)) { auto l = std::make_shared<Literal>(); l->line = t.line; l->value = Value::string_(t.lexeme); return l; }
        if (match(Tok::TRUE))  { auto l = std::make_shared<Literal>(); l->line = t.line; l->value = Value::bul(true); return l; }
        if (match(Tok::FALSE)) { auto l = std::make_shared<Literal>(); l->line = t.line; l->value = Value::bul(false); return l; }
        if (match(Tok::NIL))   { auto l = std::make_shared<Literal>(); l->line = t.line; l->value = Value::nil(); return l; }
        if (match(Tok::IDENT)) { auto v = std::make_shared<Variable>(); v->line = t.line; v->name = t.lexeme; return v; }
        if (match(Tok::LPAREN)) { ExprP e = expression(); expect(Tok::RPAREN, "expected ')'"); return e; }
        throw ClawError(t.line, "expected an expression");
    }
};

// ===========================================================================
// Environment & Interpreter
// ===========================================================================
struct Environment {
    std::unordered_map<std::string, Value> values;
    std::shared_ptr<Environment> parent;

    void define(const std::string& n, const Value& v) { values[n] = v; }

    Value get(const std::string& n, int line) {
        auto it = values.find(n);
        if (it != values.end()) return it->second;
        if (parent) return parent->get(n, line);
        throw ClawError(line, "undefined variable '" + n + "'");
    }
    void assign(const std::string& n, const Value& v, int line) {
        if (values.count(n)) { values[n] = v; return; }
        if (parent) { parent->assign(n, v, line); return; }
        throw ClawError(line, "assignment to undefined variable '" + n + "'");
    }
};

struct ReturnException { Value value; };

struct Interpreter {
    std::shared_ptr<Environment> globals = std::make_shared<Environment>();
    std::shared_ptr<Environment> env = globals;

    void run(const std::vector<StmtP>& stmts) {
        for (const auto& s : stmts) s->exec(*this);
    }

    void executeBlock(const std::vector<StmtP>& stmts, std::shared_ptr<Environment> e) {
        auto previous = env;
        env = std::move(e);
        try { for (const auto& s : stmts) s->exec(*this); }
        catch (...) { env = previous; throw; }
        env = previous;
    }
};

// ---- expression evaluation ----
Value Variable::eval(Interpreter& it) { return it.env->get(name, line); }

Value Assign::eval(Interpreter& it) {
    Value v = value->eval(it);
    it.env->assign(name, v, line);
    return v;
}

Value Unary::eval(Interpreter& it) {
    Value r = right->eval(it);
    if (op == Tok::MINUS) {
        if (r.type != Value::NUMBER) throw ClawError(line, "unary '-' needs a number");
        return Value::number(-r.num);
    }
    return Value::bul(!r.truthy()); // BANG
}

static void requireNumbers(int line, const Value& a, const Value& b, const char* op) {
    if (a.type != Value::NUMBER || b.type != Value::NUMBER)
        throw ClawError(line, std::string("operator '") + op + "' needs numbers");
}

Value Binary::eval(Interpreter& it) {
    Value a = left->eval(it), b = right->eval(it);
    switch (op) {
        case Tok::PLUS:
            if (a.type == Value::STRING || b.type == Value::STRING)
                return Value::string_(a.toString() + b.toString());
            requireNumbers(line, a, b, "+"); return Value::number(a.num + b.num);
        case Tok::MINUS: requireNumbers(line, a, b, "-"); return Value::number(a.num - b.num);
        case Tok::STAR:  requireNumbers(line, a, b, "*"); return Value::number(a.num * b.num);
        case Tok::SLASH:
            requireNumbers(line, a, b, "/");
            if (b.num == 0) throw ClawError(line, "division by zero");
            return Value::number(a.num / b.num);
        case Tok::PERCENT:
            requireNumbers(line, a, b, "%");
            if (b.num == 0) throw ClawError(line, "modulo by zero");
            return Value::number((double)((long long)a.num % (long long)b.num));
        case Tok::GT: requireNumbers(line, a, b, ">"); return Value::bul(a.num > b.num);
        case Tok::GE: requireNumbers(line, a, b, ">="); return Value::bul(a.num >= b.num);
        case Tok::LT: requireNumbers(line, a, b, "<"); return Value::bul(a.num < b.num);
        case Tok::LE: requireNumbers(line, a, b, "<="); return Value::bul(a.num <= b.num);
        case Tok::EQ_EQ: case Tok::BANG_EQ: {
            bool eq;
            if (a.type != b.type) eq = false;
            else if (a.type == Value::NUMBER) eq = a.num == b.num;
            else if (a.type == Value::BOOL) eq = a.boolean == b.boolean;
            else if (a.type == Value::STRING) eq = a.str == b.str;
            else eq = a.type == Value::NIL; // nil == nil
            return Value::bul(op == Tok::EQ_EQ ? eq : !eq);
        }
        default: throw ClawError(line, "unknown binary operator");
    }
}

Value Logical::eval(Interpreter& it) {
    Value a = left->eval(it);
    if (op == Tok::OR) return a.truthy() ? a : right->eval(it);
    return a.truthy() ? right->eval(it) : a; // AND
}

Value Call::eval(Interpreter& it) {
    Value callee = this->callee->eval(it);
    if (callee.type != Value::FUNCTION)
        throw ClawError(line, "can only call functions");
    std::vector<Value> argv;
    for (auto& a : args) argv.push_back(a->eval(it));
    auto fn = callee.fn;
    if (argv.size() != fn->params.size())
        throw ClawError(line, "expected " + std::to_string(fn->params.size()) +
                              " argument(s) but got " + std::to_string(argv.size()));
    auto local = std::make_shared<Environment>();
    local->parent = callee.closure ? callee.closure : it.globals;
    for (size_t i = 0; i < fn->params.size(); i++)
        local->define(fn->params[i], argv[i]);
    try {
        it.executeBlock(fn->body, local);
    } catch (ReturnException& r) {
        return r.value;
    }
    return Value::nil();
}

// ---- statement execution ----
void ExpressionStmt::exec(Interpreter& it) { expr->eval(it); }

void PrintStmt::exec(Interpreter& it) {
    std::cout << expr->eval(it).toString() << "\n";
}

void LetStmt::exec(Interpreter& it) {
    Value v = init ? init->eval(it) : Value::nil();
    it.env->define(name, v);
}

void BlockStmt::exec(Interpreter& it) {
    auto local = std::make_shared<Environment>();
    local->parent = it.env;
    it.executeBlock(stmts, local);
}

void IfStmt::exec(Interpreter& it) {
    if (cond->eval(it).truthy()) thenB->exec(it);
    else if (elseB) elseB->exec(it);
}

void WhileStmt::exec(Interpreter& it) {
    while (cond->eval(it).truthy()) body->exec(it);
}

void FunctionStmt::exec(Interpreter& it) {
    Value v; v.type = Value::FUNCTION;
    // shared_ptr to this node, kept alive by the AST; closure is the defining env.
    v.fn = std::static_pointer_cast<FunctionStmt>(shared_from_this());
    v.closure = it.env;
    it.env->define(name, v);
}

void ReturnStmt::exec(Interpreter& it) {
    throw ReturnException{value ? value->eval(it) : Value::nil()};
}

// ===========================================================================
// main
// ===========================================================================
static int runSource(const std::string& src) {
    try {
        Lexer lexer(src);
        Parser parser(lexer.scan());
        auto program = parser.parse();
        Interpreter interp;
        interp.run(program);
        return 0;
    } catch (const ClawError& e) {
        std::cerr << "Error [line " << e.line << "]: " << e.what() << "\n";
        return 1;
    }
}

int main(int argc, char** argv) {
    if (argc >= 2) {
        std::ifstream f(argv[1]);
        if (!f) { std::cerr << "Could not open file: " << argv[1] << "\n"; return 1; }
        std::stringstream ss; ss << f.rdbuf();
        return runSource(ss.str());
    }
    // REPL
    std::cout << "Claw REPL — by clavexis. Type statements; Ctrl-D to exit.\n";
    Interpreter interp;
    std::string line;
    std::cout << "> " << std::flush;
    while (std::getline(std::cin, line)) {
        try {
            Lexer lexer(line);
            Parser parser(lexer.scan());
            auto program = parser.parse();
            interp.run(program);
        } catch (const ClawError& e) {
            std::cerr << "Error [line " << e.line << "]: " << e.what() << "\n";
        }
        std::cout << "> " << std::flush;
    }
    std::cout << "\n";
    return 0;
}
