# Tiny OS Kernel — macOS build (via i686-elf cross toolchain).
# Built by clavexis — github.com/clavexis
#
# macOS's system clang can't easily emit 32-bit ELF, so use a cross-compiler:
#   brew install i686-elf-gcc i686-elf-binutils xorriso qemu
#
# Then:  make  ->  kernel.elf ;  make iso ;  make run
CC      := i686-elf-gcc
LD      := i686-elf-ld
CFLAGS  := -ffreestanding -fno-stack-protector -nostdlib -Wall -Wextra
LDFLAGS := -T linker.ld -nostdlib
OBJS := boot.o kernel.o

all: kernel.elf
boot.o: boot.s ; $(CC) -c boot.s -o boot.o
kernel.o: kernel.c ; $(CC) $(CFLAGS) -c kernel.c -o kernel.o
kernel.elf: $(OBJS) linker.ld ; $(LD) $(LDFLAGS) -o kernel.elf $(OBJS)
iso: kernel.elf
	mkdir -p isodir/boot/grub
	cp kernel.elf isodir/boot/kernel.elf
	printf 'menuentry "Tiny OS" {\n  multiboot /boot/kernel.elf\n}\n' > isodir/boot/grub/grub.cfg
	i686-elf-grub-mkrescue -o tinyos.iso isodir 2>/dev/null || grub-mkrescue -o tinyos.iso isodir
run: iso ; qemu-system-i386 -cdrom tinyos.iso
run-kernel: kernel.elf ; qemu-system-i386 -kernel kernel.elf
clean: ; rm -rf *.o kernel.elf tinyos.iso isodir
.PHONY: all iso run run-kernel clean
