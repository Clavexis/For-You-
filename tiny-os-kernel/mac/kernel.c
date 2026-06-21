/* kernel.c — a minimal freestanding x86 kernel.
 *
 *   - Writes text to the screen via the VGA text buffer
 *   - Sets up a custom GDT (Global Descriptor Table)
 *   - Sets up an IDT (Interrupt Descriptor Table)
 *   - Reads the keyboard with polled PS/2 port I/O and echoes typed characters
 *
 * Freestanding: no standard library. Built with -ffreestanding -nostdlib.
 *
 * Built by clavexis — github.com/clavexis
 */

#include <stdint.h>
#include <stddef.h>

/* ----- Port I/O ------------------------------------------------------- */
static inline uint8_t inb(uint16_t port) {
    uint8_t v;
    __asm__ volatile("inb %1, %0" : "=a"(v) : "Nd"(port));
    return v;
}
static inline void outb(uint16_t port, uint8_t val) {
    __asm__ volatile("outb %0, %1" : : "a"(val), "Nd"(port));
}

/* ----- VGA text-mode driver ------------------------------------------ */
#define VGA_WIDTH  80
#define VGA_HEIGHT 25
static volatile uint16_t* const VGA = (uint16_t*)0xB8000;
static size_t vga_row = 0, vga_col = 0;
static uint8_t vga_color = 0x0F; /* white on black */

static uint16_t vga_entry(char c, uint8_t color) {
    return (uint16_t)c | ((uint16_t)color << 8);
}

static void vga_clear(void) {
    for (size_t y = 0; y < VGA_HEIGHT; y++)
        for (size_t x = 0; x < VGA_WIDTH; x++)
            VGA[y * VGA_WIDTH + x] = vga_entry(' ', vga_color);
    vga_row = vga_col = 0;
}

static void vga_scroll(void) {
    for (size_t y = 1; y < VGA_HEIGHT; y++)
        for (size_t x = 0; x < VGA_WIDTH; x++)
            VGA[(y - 1) * VGA_WIDTH + x] = VGA[y * VGA_WIDTH + x];
    for (size_t x = 0; x < VGA_WIDTH; x++)
        VGA[(VGA_HEIGHT - 1) * VGA_WIDTH + x] = vga_entry(' ', vga_color);
    vga_row = VGA_HEIGHT - 1;
}

static void vga_putchar(char c) {
    if (c == '\n') {
        vga_col = 0;
        if (++vga_row >= VGA_HEIGHT) vga_scroll();
        return;
    }
    if (c == '\b') {                 /* backspace */
        if (vga_col > 0) vga_col--;
        VGA[vga_row * VGA_WIDTH + vga_col] = vga_entry(' ', vga_color);
        return;
    }
    VGA[vga_row * VGA_WIDTH + vga_col] = vga_entry(c, vga_color);
    if (++vga_col >= VGA_WIDTH) {
        vga_col = 0;
        if (++vga_row >= VGA_HEIGHT) vga_scroll();
    }
}

static void vga_write(const char* s) {
    for (size_t i = 0; s[i]; i++) vga_putchar(s[i]);
}

/* ----- GDT (Global Descriptor Table) --------------------------------- */
struct gdt_entry {
    uint16_t limit_low;
    uint16_t base_low;
    uint8_t  base_mid;
    uint8_t  access;
    uint8_t  granularity;
    uint8_t  base_high;
} __attribute__((packed));

struct gdt_ptr {
    uint16_t limit;
    uint32_t base;
} __attribute__((packed));

static struct gdt_entry gdt[3];
static struct gdt_ptr   gdtp;

static void gdt_set(int i, uint32_t base, uint32_t limit, uint8_t access, uint8_t gran) {
    gdt[i].base_low    = base & 0xFFFF;
    gdt[i].base_mid    = (base >> 16) & 0xFF;
    gdt[i].base_high   = (base >> 24) & 0xFF;
    gdt[i].limit_low   = limit & 0xFFFF;
    gdt[i].granularity = ((limit >> 16) & 0x0F) | (gran & 0xF0);
    gdt[i].access      = access;
}

static void gdt_install(void) {
    gdt_set(0, 0, 0, 0, 0);                      /* null descriptor */
    gdt_set(1, 0, 0xFFFFF, 0x9A, 0xCF);          /* code: ring 0, exec/read */
    gdt_set(2, 0, 0xFFFFF, 0x92, 0xCF);          /* data: ring 0, read/write */

    gdtp.limit = sizeof(gdt) - 1;
    gdtp.base  = (uint32_t)&gdt;

    __asm__ volatile(
        "lgdt %0\n"
        "mov $0x10, %%ax\n"      /* 0x10 = data segment selector */
        "mov %%ax, %%ds\n"
        "mov %%ax, %%es\n"
        "mov %%ax, %%fs\n"
        "mov %%ax, %%gs\n"
        "mov %%ax, %%ss\n"
        "ljmp $0x08, $1f\n"      /* 0x08 = code segment selector; reload CS */
        "1:\n"
        : : "m"(gdtp) : "ax");
}

/* ----- IDT (Interrupt Descriptor Table) ------------------------------ */
struct idt_entry {
    uint16_t base_low;
    uint16_t selector;
    uint8_t  zero;
    uint8_t  flags;
    uint16_t base_high;
} __attribute__((packed));

struct idt_ptr {
    uint16_t limit;
    uint32_t base;
} __attribute__((packed));

static struct idt_entry idt[256];
static struct idt_ptr   idtp;

extern void default_isr(void);   /* defined in boot.s */

static void idt_set(int i, uint32_t handler, uint16_t sel, uint8_t flags) {
    idt[i].base_low  = handler & 0xFFFF;
    idt[i].base_high = (handler >> 16) & 0xFFFF;
    idt[i].selector  = sel;
    idt[i].zero      = 0;
    idt[i].flags     = flags;
}

static void idt_install(void) {
    for (int i = 0; i < 256; i++)
        idt_set(i, (uint32_t)default_isr, 0x08, 0x8E); /* present, ring0, 32-bit */
    idtp.limit = sizeof(idt) - 1;
    idtp.base  = (uint32_t)&idt;
    __asm__ volatile("lidt %0" : : "m"(idtp));
}

/* ----- Keyboard (polled PS/2) ---------------------------------------- */
/* US scancode set 1 -> ASCII, lowercase, no shift handling for brevity. */
static const char scancode_map[128] = {
    0,  27, '1','2','3','4','5','6','7','8','9','0','-','=','\b',
    '\t','q','w','e','r','t','y','u','i','o','p','[',']','\n',
    0,  'a','s','d','f','g','h','j','k','l',';','\'','`',
    0,  '\\','z','x','c','v','b','n','m',',','.','/', 0,
    '*', 0, ' ',
};

static char keyboard_poll(void) {
    /* Wait until the output buffer has data (status port 0x64, bit 0). */
    while (!(inb(0x64) & 1)) { }
    uint8_t sc = inb(0x60);
    if (sc & 0x80) return 0;             /* key release — ignore */
    if (sc < 128) return scancode_map[sc];
    return 0;
}

/* ----- Kernel entry -------------------------------------------------- */
void kernel_main(void) {
    gdt_install();
    idt_install();

    vga_clear();
    vga_color = 0x0A; /* light green */
    vga_write("Tiny OS Kernel — by clavexis\n");
    vga_color = 0x0F;
    vga_write("GDT installed. IDT installed. VGA text mode active.\n");
    vga_write("Type something (PS/2 keyboard, polled):\n\n> ");

    for (;;) {
        char c = keyboard_poll();
        if (c) vga_putchar(c);
    }
}
