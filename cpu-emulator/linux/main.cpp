// main.cpp — terminal frontend and test harness for the CHIP-8 emulator.
//
// Renders the 64x32 framebuffer to the terminal with block characters, maps the
// keyboard to the 16-key CHIP-8 keypad, and offers a debug mode that shows the
// registers and disassembly each step. Also runs a built-in opcode test suite.
//
//   chip8 ROM                 run a ROM interactively in the terminal
//   chip8 --debug ROM         run with a live register/disassembly panel
//   chip8 --headless N ROM    run N cycles with no UI, then dump state (CI/testing)
//   chip8 --test              run the built-in opcode self-tests
//
// Built by clavexis — github.com/clavexis
#include "chip8.h"

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <ctime>
#include <string>
#include <iostream>
#include <iomanip>

#if defined(_WIN32)
#include <windows.h>
#include <conio.h>
#else
#include <termios.h>
#include <unistd.h>
#include <fcntl.h>
#endif

// ---------------------------------------------------------------------------
// Cross-platform non-blocking keyboard input.
// ---------------------------------------------------------------------------

#if !defined(_WIN32)
static struct termios g_origTermios;

static void enableRawMode() {
    tcgetattr(STDIN_FILENO, &g_origTermios);
    struct termios raw = g_origTermios;
    raw.c_lflag &= ~(ICANON | ECHO);  // disable line buffering and echo
    tcsetattr(STDIN_FILENO, TCSANOW, &raw);
    int flags = fcntl(STDIN_FILENO, F_GETFL, 0);
    fcntl(STDIN_FILENO, F_SETFL, flags | O_NONBLOCK);  // non-blocking reads
}

static void disableRawMode() {
    tcsetattr(STDIN_FILENO, TCSANOW, &g_origTermios);
}

static int readKeyNonBlocking() {
    unsigned char c;
    if (read(STDIN_FILENO, &c, 1) == 1) return c;
    return -1;
}
#else
static void enableRawMode() {}
static void disableRawMode() {}
static int readKeyNonBlocking() {
    if (_kbhit()) return _getch();
    return -1;
}
#endif

// Map PC keys to the CHIP-8 hex keypad (the classic 1234/QWER/ASDF/ZXCV layout).
static int mapKey(int c) {
    switch (c) {
    case '1': return 0x1; case '2': return 0x2; case '3': return 0x3; case '4': return 0xC;
    case 'q': return 0x4; case 'w': return 0x5; case 'e': return 0x6; case 'r': return 0xD;
    case 'a': return 0x7; case 's': return 0x8; case 'd': return 0x9; case 'f': return 0xE;
    case 'z': return 0xA; case 'x': return 0x0; case 'c': return 0xB; case 'v': return 0xF;
    default:  return -1;
    }
}

// ---------------------------------------------------------------------------
// Rendering.
// ---------------------------------------------------------------------------

static void clearScreen() { std::cout << "\033[2J\033[H"; }
static void moveHome() { std::cout << "\033[H"; }

// Render the 64x32 buffer using "▀" so each character shows two vertical pixels.
static void render(const Chip8& cpu) {
    std::string out;
    out.reserve(kScreenWidth * (kScreenHeight / 2) * 3);
    for (int y = 0; y < kScreenHeight; y += 2) {
        for (int x = 0; x < kScreenWidth; ++x) {
            bool top = cpu.gfx[y * kScreenWidth + x];
            bool bottom = cpu.gfx[(y + 1) * kScreenWidth + x];
            if (top && bottom) out += "█";       // full block
            else if (top)      out += "▀";       // upper half
            else if (bottom)   out += "▄";       // lower half
            else               out += ' ';
        }
        out += '\n';
    }
    std::cout << out;
}

static void renderDebugPanel(const Chip8& cpu) {
    std::cout << "\n";
    for (int i = 0; i < 16; ++i) {
        std::cout << "V" << std::hex << std::uppercase << i << "="
                  << std::setw(2) << std::setfill('0') << +cpu.V[i] << "  ";
        if (i % 4 == 3) std::cout << "\n";
    }
    std::cout << std::dec << std::setfill(' ')
              << "I=" << cpu.I << "  PC=" << cpu.pc
              << "  SP=" << +cpu.sp << "  DT=" << +cpu.delayTimer
              << "  ST=" << +cpu.soundTimer << "\n";
    std::cout << "next: " << cpu.disassemble(cpu.pc) << "\n";
}

// ---------------------------------------------------------------------------
// Run loops.
// ---------------------------------------------------------------------------

static int runInteractive(const std::string& rom, bool debug) {
    Chip8 cpu;
    if (!cpu.loadRom(rom)) {
        std::cerr << "Error: could not load ROM '" << rom << "'\n";
        return 1;
    }
    std::srand(static_cast<unsigned>(std::time(nullptr)));
    enableRawMode();
    clearScreen();

    const int cyclesPerFrame = 10;  // ~600 instructions/sec at 60 fps
    bool running = true;
    while (running) {
        // Drain pending key events; hold each pressed key for one frame.
        cpu.keys.fill(0);
        int c;
        while ((c = readKeyNonBlocking()) != -1) {
            if (c == 27 || c == 'p') { running = false; break; }  // ESC or 'p' quits
            int k = mapKey(c);
            if (k >= 0) cpu.keys[k] = 1;
        }

        for (int i = 0; i < cyclesPerFrame; ++i) cpu.emulateCycle();
        cpu.tickTimers();

        moveHome();
        render(cpu);
        if (debug) renderDebugPanel(cpu);
        std::cout << "[keys: 1234/qwer/asdf/zxcv  —  p or ESC to quit]" << std::flush;

        // ~60 Hz frame pacing.
#if defined(_WIN32)
        Sleep(16);
#else
        usleep(16000);
#endif
    }

    disableRawMode();
    clearScreen();
    std::cout << "Stopped.\n";
    return 0;
}

static int runHeadless(int cycles, const std::string& rom) {
    Chip8 cpu;
    if (!cpu.loadRom(rom)) {
        std::cerr << "Error: could not load ROM '" << rom << "'\n";
        return 1;
    }
    for (int i = 0; i < cycles; ++i) cpu.emulateCycle();
    std::cout << "After " << cycles << " cycles:\n";
    renderDebugPanel(cpu);
    std::cout << "\nFramebuffer:\n";
    render(cpu);
    return 0;
}

// ---------------------------------------------------------------------------
// Self-tests — execute hand-assembled programs and assert on the result.
// ---------------------------------------------------------------------------

static int g_failures = 0;
static void check(const char* name, bool ok) {
    std::cout << "  [" << (ok ? "ok" : "FAIL") << "] " << name << "\n";
    if (!ok) ++g_failures;
}

// Helper: load a sequence of opcodes and run them.
static void runProgram(Chip8& cpu, const uint16_t* ops, size_t count) {
    uint8_t bytes[256];
    for (size_t i = 0; i < count; ++i) {
        bytes[i * 2] = ops[i] >> 8;
        bytes[i * 2 + 1] = ops[i] & 0xFF;
    }
    cpu.loadRom(bytes, count * 2);
    for (size_t i = 0; i < count; ++i) cpu.emulateCycle();
}

static int runTests() {
    std::cout << "Running self-tests...\n";

    {  // 6XNN load + 7XNN add
        Chip8 cpu;
        uint16_t prog[] = {0x600A, 0x7005};  // V0 = 10; V0 += 5
        runProgram(cpu, prog, 2);
        check("LD/ADD immediate (V0 == 15)", cpu.V[0] == 15);
    }
    {  // 8XY4 add with carry sets VF
        Chip8 cpu;
        uint16_t prog[] = {0x60FF, 0x6102, 0x8014};  // V0=255; V1=2; V0+=V1
        runProgram(cpu, prog, 3);
        check("ADD with carry wraps (V0 == 1)", cpu.V[0] == 1);
        check("ADD with carry sets VF", cpu.V[0xF] == 1);
    }
    {  // 8XY5 subtract clears VF on borrow
        Chip8 cpu;
        uint16_t prog[] = {0x6005, 0x610A, 0x8015};  // V0=5; V1=10; V0-=V1
        runProgram(cpu, prog, 3);
        check("SUB borrow result (V0 == 251)", cpu.V[0] == 251);
        check("SUB borrow clears VF", cpu.V[0xF] == 0);
    }
    {  // ANNN set I + FX33 BCD
        Chip8 cpu;
        uint16_t prog[] = {0x60FF, 0xA300, 0xF033};  // V0=255; I=0x300; BCD(V0)
        runProgram(cpu, prog, 3);
        check("BCD hundreds", cpu.memory[0x300] == 2);
        check("BCD tens", cpu.memory[0x301] == 5);
        check("BCD ones", cpu.memory[0x302] == 5);
    }
    {  // FX55 / FX65 register store + load round-trip
        Chip8 cpu;
        uint16_t prog[] = {
            0x600A, 0x6114, 0x621E,   // V0=10, V1=20, V2=30
            0xA400, 0xF255,           // I=0x400; store V0..V2
            0x6000, 0x6100, 0x6200,   // clear V0..V2
            0xA400, 0xF265,           // I=0x400; load V0..V2
        };
        runProgram(cpu, prog, 10);
        check("register dump/load V0", cpu.V[0] == 10);
        check("register dump/load V1", cpu.V[1] == 20);
        check("register dump/load V2", cpu.V[2] == 30);
    }
    {  // 3XNN skip-if-equal actually skips one instruction
        Chip8 cpu;
        uint16_t prog[] = {0x6005, 0x3005, 0x60FF};  // V0=5; skip if V0==5; (skipped) V0=255
        runProgram(cpu, prog, 2);  // only need 2 cycles: load + skip
        check("SE skips next when equal (V0 still 5)", cpu.V[0] == 5);
    }
    {  // 2NNN call + 00EE return
        Chip8 cpu;
        // 0x200: CALL 0x206 ; 0x202: V1=0xAA ; 0x204: JP 0x208 ;
        // 0x206: V0=0x11 ; 0x207?... keep it aligned:
        uint8_t bytes[] = {
            0x22, 0x06,        // 0x200: CALL 0x206
            0x61, 0xAA,        // 0x202: V1 = 0xAA   (runs after return)
            0x12, 0x00,        // 0x204: JP 0x200 (halt-ish; not reached in test)
            0x60, 0x11,        // 0x206: V0 = 0x11
            0x00, 0xEE,        // 0x208: RET
        };
        cpu.loadRom(bytes, sizeof(bytes));
        cpu.emulateCycle();  // CALL
        check("CALL pushes stack", cpu.sp == 1 && cpu.pc == 0x206);
        cpu.emulateCycle();  // V0 = 0x11
        cpu.emulateCycle();  // RET
        check("RET pops stack", cpu.sp == 0 && cpu.pc == 0x202);
        check("subroutine set V0", cpu.V[0] == 0x11);
    }
    {  // DXYN draws a sprite and sets the collision flag on overlap
        Chip8 cpu;
        // Put a 1-row full sprite (0xFF) at memory[0x300]; draw it twice at (0,0).
        cpu.memory[0x300] = 0xFF;
        uint16_t prog[] = {
            0x6000, 0x6100,   // V0=0 (x), V1=0 (y)
            0xA300,           // I = 0x300
            0xD011,           // draw 1-row sprite at (V0,V1)
        };
        runProgram(cpu, prog, 4);
        int lit = 0;
        for (int i = 0; i < 8; ++i) lit += cpu.gfx[i];
        check("DRW lights 8 pixels", lit == 8);
        check("DRW no collision first time", cpu.V[0xF] == 0);
        cpu.emulateCycle();  // re-run DRW (pc wrapped? no—just call draw again)
        // Manually redraw to test collision (XOR turns them off, sets VF):
        cpu.I = 0x300; cpu.V[0] = 0; cpu.V[1] = 0;
        // Execute a DRW by hand via opcode at fresh address:
        uint8_t draw[] = {0xD0, 0x11};
        cpu.loadRom(draw, 2);
        cpu.pc = kProgramStart;
        cpu.emulateCycle();
        check("DRW collision flag on overlap", cpu.V[0xF] == 1);
    }
    {  // FX29 points I at the font sprite for a digit, which renders correctly
        Chip8 cpu;
        uint16_t prog[] = {0x6000, 0xF029};  // V0=0; I = sprite addr for '0'
        runProgram(cpu, prog, 2);
        check("font sprite address for 0", cpu.I == 0);
        check("font data present", cpu.memory[0] == 0xF0);
    }
    {  // Disassembler produces sane mnemonics
        Chip8 cpu;
        uint8_t bytes[] = {0x60, 0x0A, 0x00, 0xE0, 0xA2, 0x00};
        cpu.loadRom(bytes, sizeof(bytes));
        check("disasm LD", cpu.disassemble(0x200).find("LD") != std::string::npos);
        check("disasm CLS", cpu.disassemble(0x202).find("CLS") != std::string::npos);
    }

    std::cout << "\n";
    if (g_failures) {
        std::cout << g_failures << " test(s) FAILED\n";
        return 1;
    }
    std::cout << "All tests passed.\n";
    return 0;
}

// ---------------------------------------------------------------------------
// Entry point.
// ---------------------------------------------------------------------------

static void usage() {
    std::cout <<
        "chip8 — a CHIP-8 virtual machine\n\n"
        "  chip8 ROM                 run a ROM in the terminal\n"
        "  chip8 --debug ROM         run with a live register/disassembly panel\n"
        "  chip8 --headless N ROM    run N cycles then dump state (no UI)\n"
        "  chip8 --test              run the built-in opcode self-tests\n\n"
        "Keypad: 1234 / qwer / asdf / zxcv   (p or ESC to quit)\n"
        "Built by clavexis — github.com/clavexis\n";
}

int main(int argc, char** argv) {
    if (argc < 2) { usage(); return 1; }
    std::string arg1 = argv[1];

    if (arg1 == "--test") return runTests();
    if (arg1 == "--help" || arg1 == "-h") { usage(); return 0; }
    if (arg1 == "--headless") {
        if (argc < 4) { std::cerr << "Usage: chip8 --headless N ROM\n"; return 1; }
        return runHeadless(std::atoi(argv[2]), argv[3]);
    }
    if (arg1 == "--debug") {
        if (argc < 3) { std::cerr << "Usage: chip8 --debug ROM\n"; return 1; }
        return runInteractive(argv[2], true);
    }
    return runInteractive(arg1, false);
}
