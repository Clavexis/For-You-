@echo off
REM Tiny OS Kernel — Windows build helper. Built by clavexis - github.com/clavexis
REM
REM The kernel needs an ELF/cross toolchain, which is easiest under WSL.
REM Recommended: install WSL (Ubuntu), then inside WSL run the linux/ Makefile:
REM   sudo apt install build-essential nasm xorriso grub-pc-bin qemu-system-x86
REM   cd /mnt/c/path/to/tiny-os-kernel/linux && make iso
REM
REM To run the resulting tinyos.iso with QEMU for Windows:
where qemu-system-i386 >nul 2>nul
if %errorlevel%==0 (
  if exist "%~dp0tinyos.iso" (
    qemu-system-i386 -cdrom "%~dp0tinyos.iso"
  ) else (
    echo Build the ISO first (see WSL instructions above), then re-run.
  )
) else (
  echo Install QEMU for Windows from https://www.qemu.org/download/#windows
  echo and build the ISO under WSL using the linux/ Makefile.
)
