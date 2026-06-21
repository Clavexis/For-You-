/* linker.ld — link the kernel at the 1 MiB physical address GRUB loads it to.
 * Built by clavexis — github.com/clavexis */

ENTRY(_start)

SECTIONS
{
    . = 1M;                     /* kernel starts at 1 MiB */

    .text BLOCK(4K) : ALIGN(4K)
    {
        *(.multiboot)           /* the multiboot header must come first */
        *(.text)
    }

    .rodata BLOCK(4K) : ALIGN(4K) { *(.rodata) }
    .data   BLOCK(4K) : ALIGN(4K) { *(.data) }
    .bss    BLOCK(4K) : ALIGN(4K) { *(COMMON) *(.bss) }
}
