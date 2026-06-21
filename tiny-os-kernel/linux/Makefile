# Tiny OS Kernel — Linux build. Built by clavexis — github.com/clavexis
#
# Targets:
#   make            -> build kernel.elf (a bootable multiboot kernel)
#   make iso        -> build tinyos.iso  (needs grub-mkrescue + xorriso)
#   make run        -> boot the ISO in QEMU (needs qemu-system-i386)
#   make verify     -> check kernel.elf is a valid multiboot image
#   make clean
#
# Uses GCC's assembler (no NASM needed). For a strict freestanding build a
# cross-compiler (i686-elf-gcc) is ideal; plain gcc with -m32 works too.

CC      := gcc
LD      := ld
CFLAGS  := -m32 -ffreestanding -fno-stack-protector -fno-pic -nostdlib -Wall -Wextra
LDFLAGS := -m elf_i386 -T linker.ld -nostdlib

OBJS := boot.o kernel.o

all: kernel.elf

boot.o: boot.s
	$(CC) -m32 -c boot.s -o boot.o

kernel.o: kernel.c
	$(CC) $(CFLAGS) -c kernel.c -o kernel.o

kernel.elf: $(OBJS) linker.ld
	$(LD) $(LDFLAGS) -o kernel.elf $(OBJS)

verify: kernel.elf
	@grub-file --is-x86-multiboot kernel.elf && echo "kernel.elf is a valid multiboot kernel" \
		|| (echo "NOT a valid multiboot kernel" && false)

iso: kernel.elf
	mkdir -p isodir/boot/grub
	cp kernel.elf isodir/boot/kernel.elf
	printf 'menuentry "Tiny OS" {\n  multiboot /boot/kernel.elf\n}\n' > isodir/boot/grub/grub.cfg
	grub-mkrescue -o tinyos.iso isodir

run: iso
	qemu-system-i386 -cdrom tinyos.iso

# Run directly from the ELF without building an ISO (fastest dev loop):
run-kernel: kernel.elf
	qemu-system-i386 -kernel kernel.elf

clean:
	rm -rf *.o kernel.elf tinyos.iso isodir

.PHONY: all verify iso run run-kernel clean
