# SQL Database Engine from Scratch

A tiny but real relational database written in C — it parses SQL, stores tables on disk, and uses a **B-tree index** for fast lookups. `CREATE`, `INSERT`, `SELECT` (with `WHERE`), and `DELETE`, all from an interactive REPL.

## Demo

```text
$ ./db mydata
SQL Database Engine — by clavexis. Data dir: mydata/
db> CREATE TABLE users (id INT, name TEXT, age INT);
Table 'users' created with 3 column(s).
db> INSERT INTO users VALUES (1, 'alice', 30);
1 row inserted.
db> SELECT * FROM users WHERE age > 28;
id          name        age
------------------------------------
1           alice       30
3           carol       42
(2 row(s))
db> SELECT * FROM users WHERE id = 2;
id          name        age
------------------------------------
2           bob         25
(1 row(s), via B-tree index)
```

## Features

- **SQL commands** — `CREATE TABLE`, `INSERT INTO`, `SELECT`, `DELETE`.
- **`WHERE` clauses** — `=`, `!=`, `<`, `>`, `<=`, `>=` on any column.
- **B-tree index** on the primary key — `WHERE id = N` lookups go through an in-memory B-tree (O(log n)), not a full scan.
- **Persistent storage** — tables live in `*.tbl` files on disk and survive restarts.
- **Column types** — `INT` and `TEXT`.
- **Interactive REPL** and script-friendly (pipe SQL on stdin).

## Build & run

Requires a C compiler.

### Linux
```bash
cd linux
make                 # or ./build.sh
./db mydata          # interactive REPL (data in mydata/)
./db mydata < demo.sql   # run a script
```

### macOS (Apple Silicon & Intel)
```bash
cd mac
./build.sh           # uses clang
./db mydata
```

### Windows
Uses POSIX-style calls; build under **WSL** with the `linux/` Makefile, or with MinGW gcc.

## Usage

```sql
CREATE TABLE users (id INT, name TEXT, age INT);
INSERT INTO users VALUES (1, 'alice', 30);
SELECT * FROM users;
SELECT * FROM users WHERE age > 28;
SELECT * FROM users WHERE id = 2;     -- uses the B-tree index
DELETE FROM users WHERE name = 'bob';
```

REPL extras: `.tables` lists tables, `help` shows commands, `exit` quits.

## How it works

```text
SQL text ──▶ parser ──▶ executor
table = mydata/<name>.tbl  =  [schema header][fixed-size rows...]
index  = in-memory B-tree (key -> row offset), rebuilt on load
SELECT WHERE pk = N  ──▶ B-tree search   (O(log n))
SELECT WHERE other   ──▶ row scan + filter
DELETE               ──▶ tombstone rows, rewrite file
```

Rows are fixed-size records appended to the table file, so data is durable and the engine can `mmap`-style seek through them. The B-tree (order 5) indexes the integer primary key for fast point lookups.

## Tech stack

- **C** — file I/O for persistence, hand-written SQL parser
- In-memory **B-tree** index, fixed-size row storage

---

Built by clavexis — [github.com/clavexis](https://github.com/clavexis)
