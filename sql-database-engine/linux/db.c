#define _GNU_SOURCE
// SQL Database Engine from Scratch — a tiny relational database in C.
//
//   - CREATE TABLE, INSERT, SELECT (with WHERE), DELETE
//   - Persistent storage to disk (one file per table)
//   - In-memory B-tree index on the primary key for O(log n) lookups
//   - A simple SQL parser and an interactive REPL
//
// Build:  gcc -O2 -o db db.c
// Run  :  ./db mydata          (REPL; data persists in ./mydata/)
//         echo "SELECT * FROM users;" | ./db mydata
//
// Built by clavexis — github.com/clavexis

#include <ctype.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

#define MAX_COLS 8
#define TEXT_LEN 32
#define MAX_NAME 32

enum ColType { COL_INT, COL_TEXT };

struct Column { char name[MAX_NAME]; enum ColType type; };

struct Schema {
    char table[MAX_NAME];
    int ncols;
    struct Column cols[MAX_COLS];
};

// A row value: int or fixed-length text.
struct Value { long ival; char text[TEXT_LEN]; };
struct Row { struct Value vals[MAX_COLS]; int deleted; };

static char db_dir[256] = "data";

// ---------------------------------------------------------------------------
// B-tree index (in-memory) on the integer primary key (column 0).
// Maps key -> row offset (index in the table file). Order-5 B-tree.
// ---------------------------------------------------------------------------
#define BT_ORDER 5
struct BNode {
    int n;
    int leaf;
    long keys[BT_ORDER];
    long vals[BT_ORDER];        // row index
    struct BNode* child[BT_ORDER + 1];
};
struct BTree { struct BNode* root; };

static struct BNode* bnode_new(int leaf) {
    struct BNode* x = calloc(1, sizeof(struct BNode));
    x->leaf = leaf;
    return x;
}
static long bt_search(struct BNode* x, long key) {
    if (!x) return -1;
    int i = 0;
    while (i < x->n && key > x->keys[i]) i++;
    if (i < x->n && key == x->keys[i]) return x->vals[i];
    if (x->leaf) return -1;
    return bt_search(x->child[i], key);
}
static void bt_split_child(struct BNode* x, int i) {
    struct BNode* y = x->child[i];
    struct BNode* z = bnode_new(y->leaf);
    int mid = BT_ORDER / 2;
    z->n = y->n - mid - 1;
    for (int j = 0; j < z->n; j++) { z->keys[j] = y->keys[mid + 1 + j]; z->vals[j] = y->vals[mid + 1 + j]; }
    if (!y->leaf) for (int j = 0; j <= z->n; j++) z->child[j] = y->child[mid + 1 + j];
    y->n = mid;
    for (int j = x->n; j > i; j--) x->child[j + 1] = x->child[j];
    x->child[i + 1] = z;
    for (int j = x->n - 1; j >= i; j--) { x->keys[j + 1] = x->keys[j]; x->vals[j + 1] = x->vals[j]; }
    x->keys[i] = y->keys[mid]; x->vals[i] = y->vals[mid];
    x->n++;
}
static void bt_insert_nonfull(struct BNode* x, long key, long val) {
    int i = x->n - 1;
    if (x->leaf) {
        while (i >= 0 && key < x->keys[i]) { x->keys[i + 1] = x->keys[i]; x->vals[i + 1] = x->vals[i]; i--; }
        x->keys[i + 1] = key; x->vals[i + 1] = val; x->n++;
    } else {
        while (i >= 0 && key < x->keys[i]) i--;
        i++;
        if (x->child[i]->n == BT_ORDER) { bt_split_child(x, i); if (key > x->keys[i]) i++; }
        bt_insert_nonfull(x->child[i], key, val);
    }
}
static void bt_insert(struct BTree* t, long key, long val) {
    if (!t->root) { t->root = bnode_new(1); t->root->keys[0] = key; t->root->vals[0] = val; t->root->n = 1; return; }
    if (t->root->n == BT_ORDER) {
        struct BNode* s = bnode_new(0);
        s->child[0] = t->root;
        t->root = s;
        bt_split_child(s, 0);
    }
    bt_insert_nonfull(t->root, key, val);
}

// ---------------------------------------------------------------------------
// Table storage: a file `<dir>/<table>.tbl` = [schema header][rows...].
// ---------------------------------------------------------------------------
static void table_path(const char* table, char* out) {
    snprintf(out, 256, "%.200s/%.40s.tbl", db_dir, table);
}

static int load_schema(const char* table, struct Schema* s) {
    char path[256]; table_path(table, path);
    FILE* f = fopen(path, "rb");
    if (!f) return 0;
    int ok = fread(s, sizeof(struct Schema), 1, f) == 1;
    fclose(f);
    return ok;
}

static void create_table(const char* table, struct Schema* s) {
    char path[256]; table_path(table, path);
    FILE* f = fopen(path, "wb");
    if (!f) { printf("Error: cannot create table file.\n"); return; }
    fwrite(s, sizeof(struct Schema), 1, f);
    fclose(f);
    printf("Table '%s' created with %d column(s).\n", table, s->ncols);
}

// Read all rows; returns count, fills *rows (caller frees). Builds index if given.
static int read_rows(const struct Schema* s, struct Row** out, struct BTree* idx) {
    char path[256]; table_path(s->table, path);
    FILE* f = fopen(path, "rb");
    if (!f) { *out = NULL; return 0; }
    fseek(f, sizeof(struct Schema), SEEK_SET);
    int cap = 16, n = 0;
    struct Row* rows = malloc(cap * sizeof(struct Row));
    struct Row r;
    while (fread(&r, sizeof(struct Row), 1, f) == 1) {
        if (n == cap) { cap *= 2; rows = realloc(rows, cap * sizeof(struct Row)); }
        rows[n] = r;
        if (idx && !r.deleted && s->cols[0].type == COL_INT)
            bt_insert(idx, r.vals[0].ival, n);
        n++;
    }
    fclose(f);
    *out = rows;
    return n;
}

static void rewrite_rows(const struct Schema* s, struct Row* rows, int n) {
    char path[256]; table_path(s->table, path);
    FILE* f = fopen(path, "wb");
    fwrite(s, sizeof(struct Schema), 1, f);
    for (int i = 0; i < n; i++) fwrite(&rows[i], sizeof(struct Row), 1, f);
    fclose(f);
}

// ---------------------------------------------------------------------------
// Tiny tokenizer.
// ---------------------------------------------------------------------------
static char* trim(char* s) {
    while (isspace((unsigned char)*s)) s++;
    char* e = s + strlen(s) - 1;
    while (e > s && (isspace((unsigned char)*e) || *e == ';')) *e-- = 0;
    return s;
}

static enum ColType type_of(const char* t) {
    return (strcasecmp(t, "INT") == 0) ? COL_INT : COL_TEXT;
}

// ---------------------------------------------------------------------------
// WHERE evaluation: "col OP value"  (OP ∈ = != < > <= >=)
// ---------------------------------------------------------------------------
struct Where { int active, col; char op[3]; struct Value val; };

static int col_index(const struct Schema* s, const char* name) {
    for (int i = 0; i < s->ncols; i++) if (strcasecmp(s->cols[i].name, name) == 0) return i;
    return -1;
}

static int eval_where(const struct Schema* s, const struct Row* r, const struct Where* w) {
    if (!w->active) return 1;
    const struct Value* v = &r->vals[w->col];
    int cmp;
    if (s->cols[w->col].type == COL_INT) cmp = (v->ival > w->val.ival) - (v->ival < w->val.ival);
    else cmp = strcmp(v->text, w->val.text);
    if (!strcmp(w->op, "=")) return cmp == 0;
    if (!strcmp(w->op, "!=")) return cmp != 0;
    if (!strcmp(w->op, "<")) return cmp < 0;
    if (!strcmp(w->op, ">")) return cmp > 0;
    if (!strcmp(w->op, "<=")) return cmp <= 0;
    if (!strcmp(w->op, ">=")) return cmp >= 0;
    return 0;
}

static void parse_where(const struct Schema* s, char* clause, struct Where* w) {
    w->active = 0;
    char* p = strcasestr(clause, "WHERE");
    if (!p) return;
    p += 5;
    char col[MAX_NAME], op[3], val[64];
    if (sscanf(p, " %31s %2s %63[^;\n]", col, op, val) >= 3) {
        char* vv = trim(val);
        if (vv[0] == '\'') { vv++; char* q = strchr(vv, '\''); if (q) *q = 0; }
        w->col = col_index(s, col);
        if (w->col < 0) return;
        strncpy(w->op, op, 2); w->op[2] = 0;
        if (s->cols[w->col].type == COL_INT) w->val.ival = atol(vv);
        else { strncpy(w->val.text, vv, TEXT_LEN - 1); w->val.text[TEXT_LEN - 1] = 0; }
        w->active = 1;
    }
}

// ---------------------------------------------------------------------------
// Statement handlers.
// ---------------------------------------------------------------------------
static void do_create(char* sql) {
    // CREATE TABLE name (col TYPE, col TYPE, ...)
    char table[MAX_NAME];
    char* paren = strchr(sql, '(');
    if (!paren || sscanf(sql, "CREATE TABLE %31s", table) != 1) { printf("Syntax error.\n"); return; }
    char* tp = strchr(table, '(');
    if (tp) *tp = 0;
    struct Schema s; memset(&s, 0, sizeof(s));
    strncpy(s.table, table, MAX_NAME - 1);
    char* body = paren + 1;
    char* end = strrchr(body, ')'); if (end) *end = 0;
    char* tok = strtok(body, ",");
    while (tok && s.ncols < MAX_COLS) {
        char cname[MAX_NAME], ctype[16];
        if (sscanf(tok, " %31s %15s", cname, ctype) == 2) {
            strncpy(s.cols[s.ncols].name, cname, MAX_NAME - 1);
            s.cols[s.ncols].type = type_of(ctype);
            s.ncols++;
        }
        tok = strtok(NULL, ",");
    }
    create_table(table, &s);
}

static void do_insert(char* sql) {
    char table[MAX_NAME];
    char* vp = strcasestr(sql, "VALUES");
    if (!vp || sscanf(sql, "INSERT INTO %31s", table) != 1) { printf("Syntax error.\n"); return; }
    struct Schema s;
    if (!load_schema(table, &s)) { printf("No such table '%s'.\n", table); return; }
    char* paren = strchr(vp, '(');
    if (!paren) { printf("Syntax error.\n"); return; }
    char* body = paren + 1;
    char* end = strrchr(body, ')'); if (end) *end = 0;
    struct Row r; memset(&r, 0, sizeof(r));
    char* tok = strtok(body, ",");
    int i = 0;
    while (tok && i < s.ncols) {
        char* v = trim(tok);
        if (v[0] == '\'') { v++; char* q = strchr(v, '\''); if (q) *q = 0; }
        if (s.cols[i].type == COL_INT) r.vals[i].ival = atol(v);
        else { strncpy(r.vals[i].text, v, TEXT_LEN - 1); }
        tok = strtok(NULL, ","); i++;
    }
    char path[256]; table_path(table, path);
    FILE* f = fopen(path, "ab");
    fwrite(&r, sizeof(struct Row), 1, f);
    fclose(f);
    printf("1 row inserted.\n");
}

static void print_value(const struct Schema* s, const struct Row* r, int c) {
    if (s->cols[c].type == COL_INT) printf("%-12ld", r->vals[c].ival);
    else printf("%-12s", r->vals[c].text);
}

static void do_select(char* sql) {
    char table[MAX_NAME];
    char* fp = strcasestr(sql, "FROM");
    if (!fp || sscanf(fp, "FROM %31s", table) != 1) { printf("Syntax error.\n"); return; }
    char* semi = strchr(table, ';'); if (semi) *semi = 0;
    struct Schema s;
    if (!load_schema(table, &s)) { printf("No such table '%s'.\n", table); return; }
    struct Where w; parse_where(&s, sql, &w);

    struct BTree idx = {0};
    struct Row* rows;
    int n = read_rows(&s, &rows, &idx);

    // Header.
    for (int c = 0; c < s.ncols; c++) printf("%-12s", s.cols[c].name);
    printf("\n");
    for (int c = 0; c < s.ncols; c++) printf("------------");
    printf("\n");

    int shown = 0;
    // Fast path: WHERE pk = value uses the B-tree index.
    if (w.active && w.col == 0 && !strcmp(w.op, "=") && s.cols[0].type == COL_INT) {
        long ri = bt_search(idx.root, w.val.ival);
        if (ri >= 0 && !rows[ri].deleted) {
            for (int c = 0; c < s.ncols; c++) print_value(&s, &rows[ri], c);
            printf("\n"); shown = 1;
        }
        printf("(%d row(s), via B-tree index)\n", shown);
    } else {
        for (int i = 0; i < n; i++) {
            if (rows[i].deleted) continue;
            if (!eval_where(&s, &rows[i], &w)) continue;
            for (int c = 0; c < s.ncols; c++) print_value(&s, &rows[i], c);
            printf("\n"); shown++;
        }
        printf("(%d row(s))\n", shown);
    }
    free(rows);
}

static void do_delete(char* sql) {
    char table[MAX_NAME];
    char* fp = strcasestr(sql, "FROM");
    if (!fp || sscanf(fp, "FROM %31s", table) != 1) { printf("Syntax error.\n"); return; }
    char* semi = strchr(table, ';'); if (semi) *semi = 0;
    struct Schema s;
    if (!load_schema(table, &s)) { printf("No such table '%s'.\n", table); return; }
    struct Where w; parse_where(&s, sql, &w);
    struct Row* rows; int n = read_rows(&s, &rows, NULL);
    int deleted = 0;
    for (int i = 0; i < n; i++) {
        if (rows[i].deleted) continue;
        if (eval_where(&s, &rows[i], &w)) { rows[i].deleted = 1; deleted++; }
    }
    rewrite_rows(&s, rows, n);
    free(rows);
    printf("%d row(s) deleted.\n", deleted);
}

static void execute(char* sql) {
    sql = trim(sql);
    if (!*sql) return;
    if (!strcasecmp(sql, "help")) {
        printf("Commands: CREATE TABLE, INSERT INTO, SELECT, DELETE, .tables, exit\n");
    } else if (!strcasecmp(sql, ".tables")) {
        char cmd[300]; snprintf(cmd, sizeof(cmd), "ls %s 2>/dev/null", db_dir);
        if (system(cmd)) {}
    } else if (!strncasecmp(sql, "CREATE", 6)) do_create(sql);
    else if (!strncasecmp(sql, "INSERT", 6)) do_insert(sql);
    else if (!strncasecmp(sql, "SELECT", 6)) do_select(sql);
    else if (!strncasecmp(sql, "DELETE", 6)) do_delete(sql);
    else printf("Unknown command. Type 'help'.\n");
}

int main(int argc, char** argv) {
    if (argc > 1) strncpy(db_dir, argv[1], sizeof(db_dir) - 1);
    mkdir(db_dir, 0755);

    int interactive = isatty(0);
    if (interactive) {
        printf("SQL Database Engine — by clavexis. Data dir: %s/\n", db_dir);
        printf("Type SQL statements ending in ';'. 'help' for commands, 'exit' to quit.\n");
    }
    char line[1024];
    while (1) {
        if (interactive) { printf("db> "); fflush(stdout); }
        if (!fgets(line, sizeof(line), stdin)) break;
        if (!strncasecmp(trim(line), "exit", 4) || !strncasecmp(line, "quit", 4)) break;
        execute(line);
    }
    return 0;
}
