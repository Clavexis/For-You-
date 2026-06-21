# Tiny OS Kernel

A minimal x86 operating-system kernel that boots via GRUB (Multiboot), prints to the screen, sets up its own GDT and IDT, and reads the keyboard — written in C and assembly, with **no libraries**.

## Demo

```text
Tiny OS Kernel — by clavexis
GDT installed. IDT installed. VGA text mode active.
Type something (PS/2 keyboard, polled):

> hello world_
```

## Features

- **Boots as a Multiboot kernel** — GRUB loads `kernel.elf`; verified with `grub-file --is-x86-multiboot`.
- **VGA text-mode driver** — direct writes to `0xB8000`, with scrolling and backspace.
- **Custom GDT** — null / ring-0 code / ring-0 data descriptors, loaded with `lgdt` and a far jump to reload CS.
- **IDT setup** — 256 descriptors loaded with `lidt` (default handler stub in assembly).
- **Polled PS/2 keyboard input** — reads scancodes from ports `0x64`/`0x60` and echoes typed characters.
- **Makefile** that builds `kernel.elf` and a bootable `tinyos.iso`.

## Build & run

The kernel is built in a **Linux build environment** and runs in **QEMU** on any OS (as the project spec intends).

### Linux (recommended)
```bash
cd linux
make                 # builds kernel.elf
make verify          # confirms it's a valid multiboot kernel
make run-kernel      # boot directly in QEMU (needs qemu-system-i386)
# or build a real ISO:
make iso             # needs grub-mkrescue + xorriso
make run             # boots tinyos.iso in QEMU
```

Install the toolchain on Debian/Ubuntu:
```bash
sudo apt install build-essential xorriso grub-pc-bin qemu-system-x86
```

> This build uses GCC's own assembler — **no NASM required**. For a strict
> freestanding setup an `i686-elf-gcc` cross-compiler is ideal; plain
> `gcc -m32` also works.

### macOS (Apple Silicon & Intel)
macOS's clang can't easily emit 32-bit ELF, so use the cross toolchain:
```bash
brew install i686-elf-gcc i686-elf-binutils xorriso qemu
cd mac
./build.sh
make run
```

### Windows
Build under **WSL** (Ubuntu) using the `linux/` Makefile, then run the ISO with
QEMU for Windows:
```bat
cd windows
build.bat            REM prints WSL build steps and launches QEMU on the ISO
```

## How it boots

1. GRUB finds the **Multiboot header** in `boot.s` and loads the kernel at 1 MiB (`linker.ld`).
2. `_start` sets up a stack and calls `kernel_main`.
3. `kernel_main` installs the GDT, installs the IDT, clears the screen, and enters a keyboard loop.

```text
GRUB ──(multiboot)──▶ _start (boot.s) ──▶ kernel_main (kernel.c)
                                              ├── gdt_install()
                                              ├── idt_install()
                                              └── keyboard loop
```

## Verifying correctness

```bash
$ make verify
kernel.elf is a valid multiboot kernel
```

## Tech stack

- **C (freestanding)** + **x86 assembly** (GAS)
- GRUB Multiboot, QEMU for running
- No standard library, no external dependencies

---

Built by clavexis — [github.com/clavexis](https://github.com/clavexis)
