# chip8 — a CHIP-8 CPU emulator

A complete **CHIP-8 virtual machine** written from scratch in C++17. CHIP-8 is the classic 1970s interpreted instruction set that countless emulators cut their teeth on — 4 KB of memory, 16 registers, a 64×32 monochrome display and a 16-key hex keypad. This implementation runs real ROMs in your **terminal** (no SDL, no graphics library), with a live **debug panel** and a built-in **disassembler**. All 35 opcodes are implemented and covered by self-tests.

## Demo

Running a ROM that draws the hex digits using the built-in font sprites:

```text
▄▄▄▄   ▄  ▄▄▄▄ ▄▄▄▄ ▄  ▄ ▄▄▄▄
█  █  ▀█  ▄▄▄█ ▄▄▄█ █▄▄█ █▄▄▄
█▄▄█  ▄█▄ █▄▄▄ ▄▄▄█    █ ▄▄▄█

V0=06  V1=00  V2=1E  V3=01
I=25  PC=520  SP=0  DT=0  ST=0
next: F029  LD   F, V0
```

The 64×32 framebuffer is rendered with half-block characters (`▀▄█`) so two pixel rows fit in one terminal line.

## Features

- **Full CHIP-8 instruction set** — all 35 opcodes: jumps, subroutines, the arithmetic/logic group (`8XYn`), sprite drawing with collision detection (`DXYN`), BCD conversion, register dump/load, timers and keypad input.
- **Fetch–decode–execute** core that's pure logic and I/O-free, so it's easy to test and embed.
- **Terminal rendering** of the 64×32 display — no SDL or external libraries needed.
- **Keypad mapping** to the familiar `1234 / qwer / asdf / zxcv` layout.
- **Debug mode** showing all 16 registers, `I`, `PC`, `SP`, both timers, and a disassembly of the next instruction every frame.
- **Built-in disassembler** producing readable mnemonics (`LD V0, 10`, `DRW V2, V3, 5`, …).
- **Headless mode** (`--headless N ROM`) for scripted/CI runs that execute N cycles and dump the state and framebuffer.
- **22-assertion self-test suite** (`--test`) exercising every opcode group against hand-assembled programs.
- Standard 16×5 hex font built in (`FX29`).

## Installation

Needs a C++17 compiler (g++, clang++, or MSVC).

### Linux
```bash
cd linux && ./build.sh      # or: make
./chip8 --test
```

### macOS (Apple Silicon & Intel)
```bash
cd mac && ./build.sh        # or: make   (uses clang++)
./chip8 --test
```

### Windows
```bat
cd windows
build.bat
chip8.exe --test
```

## Usage

```bash
chip8 ROM                 # run a ROM in the terminal
chip8 --debug ROM         # run with the live register/disassembly panel
chip8 --headless N ROM    # run N cycles, then dump state (no UI)
chip8 --test              # run the opcode self-tests
```

A small demo ROM is included at the project root:

```bash
./chip8 --headless 40 ../demo.ch8     # see the hex-digit font render
./chip8 ../demo.ch8                   # run it live
```

Drop any standard `.ch8` ROM in and it will run. **Keypad:** `1 2 3 4 / q w e r / a s d f / z x c v`, and `p` or `ESC` to quit.

## How it works

```text
        ┌──────────────── emulateCycle() ────────────────┐
PC ─▶  fetch 2 bytes (big-endian) ─▶ decode by nibbles ─▶ execute
        └─ memory[4096]   V0..VF   I   stack[16]   timers ─┘
                                   │
        DXYN sprite XOR ─▶ gfx[64×32] ─▶ terminal half-block render
```

Each cycle reads a two-byte opcode, splits it into its nibble fields (`X`, `Y`, `N`, `NN`, `NNN`), and dispatches on the top nibble. Sprites are drawn by XOR-ing 8-pixel-wide rows into the framebuffer, setting `VF` when a lit pixel is erased (collision) — exactly the trick CHIP-8 games use for hit detection.

## Tech stack

- **C++17** — standard library only (`<array>`, `<fstream>`, `<iostream>`)
- POSIX `termios` (Linux/macOS) / `conio.h` (Windows) for raw non-blocking keyboard input
- ANSI escape codes + Unicode half-block glyphs for rendering

---

Built by clavexis — [github.com/clavexis](https://github.com/clavexis)
