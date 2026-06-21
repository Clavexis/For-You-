/* boot.s — Multiboot header and 32-bit entry point.
 *
 * GRUB loads this kernel because of the Multiboot header below. Execution
 * starts at _start, which sets up a stack and calls kernel_main (in C).
 *
 * Assembled with GCC's GAS (no NASM required):
 *   gcc -m32 -c boot.s -o boot.o
 *
 * Built by clavexis — github.com/clavexis
 */

/* Multiboot header constants. */
.set ALIGN,    1 << 0            /* align loaded modules on page boundaries */
.set MEMINFO,  1 << 1            /* provide a memory map */
.set FLAGS,    ALIGN | MEMINFO
.set MAGIC,    0x1BADB002        /* the magic number identifying a multiboot kernel */
.set CHECKSUM, -(MAGIC + FLAGS)  /* checksum so MAGIC+FLAGS+CHECKSUM == 0 */

.section .multiboot
.align 4
.long MAGIC
.long FLAGS
.long CHECKSUM

/* A small stack (16 KiB). The System V ABI needs a 16-byte aligned stack. */
.section .bss
.align 16
stack_bottom:
.skip 16384
stack_top:

.section .text
.global _start
.type _start, @function
_start:
    mov $stack_top, %esp        /* set up the stack */
    call kernel_main            /* hand off to C */

    cli                         /* if kernel_main returns, halt forever */
.hang:
    hlt
    jmp .hang
.size _start, . - _start

/* A default interrupt handler used to fill every IDT entry. It simply
 * returns from the interrupt — enough to keep the CPU stable while we use
 * polled keyboard input. */
.global default_isr
.type default_isr, @function
default_isr:
    iret
.size default_isr, . - default_isr

/* Mark the stack as non-executable to silence the linker warning. */
.section .note.GNU-stack, "", @progbits
