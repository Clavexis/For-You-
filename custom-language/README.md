# Claw — a Custom Programming Language

A minimal, dynamically-typed interpreted language with its own syntax — built from scratch in C++ with a hand-written lexer, recursive-descent parser, and tree-walking interpreter. **No parser generators, no libraries.**

## Demo

```claw
# fib.claw — recursion + a while loop
fn fib(n) {
  if (n < 2) return n;
  return fib(n - 1) + fib(n - 2);
}
let i = 0;
while (i < 10) {
  print fib(i);
  i = i + 1;
}
```

```text
$ claw examples/fib.claw
0
1
1
2
3
5
8
13
21
34
```

## Features

- **Values:** numbers, strings, booleans, `nil`, and first-class functions.
- **Variables:** `let x = 5;` with assignment and lexical scoping.
- **Operators:** `+ - * / %`, comparisons `== != < <= > >=`, logical `and` / `or` / `!`, string `+` concatenation.
- **Control flow:** `if` / `else`, `while` loops, blocks `{ }`.
- **Functions:** `fn name(params) { ... }` with `return`, recursion, and **closures** that capture their environment.
- **Built-in `print`.**
- **Friendly errors with line numbers** — both parse-time and runtime.
- **File runner and an interactive REPL.**

## Language at a glance

```claw
let name = "Claw";
print "hello, " + name;        # string concatenation

fn makeCounter() {             # closures
  let count = 0;
  fn inc() { count = count + 1; return count; }
  return inc;
}
let c = makeCounter();
print c(); print c();          # 1, then 2

let n = 1;                     # FizzBuzz
while (n <= 15) {
  if (n % 15 == 0) { print "FizzBuzz"; }
  else if (n % 3 == 0) { print "Fizz"; }
  else if (n % 5 == 0) { print "Buzz"; }
  else { print n; }
  n = n + 1;
}
```

Comments start with `#`. Statements end with `;`.

## Build & run

Requires a C++17 compiler.

### Linux
```bash
cd linux && make        # or ./build.sh
./claw ../examples/fib.claw
./claw                  # interactive REPL
```

### macOS (Apple Silicon & Intel)
```bash
cd mac && ./build.sh    # uses clang++
./claw ../examples/closures.claw
```

### Windows
```powershell
cd windows
build.bat               # MinGW g++ or MSVC cl
claw.exe ..\examples\fizzbuzz.claw
```

## Example programs

The `examples/` folder includes:
- `fib.claw` — recursive Fibonacci
- `fizzbuzz.claw` — loops and nested conditionals
- `closures.claw` — functions that capture state

## Error messages

```text
$ claw bad.claw
Error [line 3]: undefined variable 'y'
Error [line 2]: division by zero
Error [line 1]: operator '-' needs numbers
```

## Tech stack

- **C++17**, single self-contained file (`claw.cpp`)
- Lexer → recursive-descent parser → tree-walking interpreter
- `shared_ptr`-based AST, lexically-scoped environments for closures

---

Built by clavexis — [github.com/clavexis](https://github.com/clavexis)
