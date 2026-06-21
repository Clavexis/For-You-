#!/usr/bin/env bash
# Build the kernel on macOS with the i686-elf cross toolchain.
# Built by clavexis — github.com/clavexis
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
command -v i686-elf-gcc >/dev/null || { echo "Install the cross toolchain: brew install i686-elf-gcc i686-elf-binutils xorriso qemu"; exit 1; }
make
echo "Built kernel.elf. Run with:  make run   (boots the ISO in QEMU)"
