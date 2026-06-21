// chip8.h — a complete CHIP-8 virtual machine (the classic 1970s interpreter).
//
// This header declares the Chip8 class: 4 KB of memory, 16 registers, a stack,
// two 60 Hz timers, a 64x32 monochrome framebuffer and a 16-key hex keypad. The
// core is pure logic with no I/O, so it can be unit-tested headlessly and driven
// by any frontend (terminal, SDL, etc.).
//
// Built by clavexis — github.com/clavexis
#ifndef CHIP8_H
#define CHIP8_H

#include <cstdint>
#include <string>
#include <array>

// Display geometry — CHIP-8 is a fixed 64x32 monochrome grid.
constexpr int kScreenWidth = 64;
constexpr int kScreenHeight = 32;

// Programs are loaded here; the lower 512 bytes were the original interpreter.
constexpr uint16_t kProgramStart = 0x200;

class Chip8 {
public:
    Chip8();

    // Reset all state and reload the built-in fontset.
    void reset();

    // Load a ROM from a file (returns false if it can't be read or is too big).
    bool loadRom(const std::string& path);

    // Load a ROM from memory (used by tests and embedded programs).
    bool loadRom(const uint8_t* data, size_t size);

    // Fetch–decode–execute exactly one instruction.
    void emulateCycle();

    // Decrement the delay/sound timers; call this at ~60 Hz.
    void tickTimers();

    // True when the last drawn frame changed the screen (frontend should redraw).
    bool drawFlag = false;

    // Public state so frontends and tests can read/poke it directly.
    std::array<uint8_t, 4096> memory{};        // 4 KB RAM
    std::array<uint8_t, 16> V{};               // V0..VF registers (VF = flags)
    uint16_t I = 0;                            // index register
    uint16_t pc = kProgramStart;              // program counter
    std::array<uint16_t, 16> stack{};          // call stack
    uint8_t sp = 0;                            // stack pointer
    uint8_t delayTimer = 0;
    uint8_t soundTimer = 0;

    // 64x32 framebuffer, one byte per pixel (0 or 1).
    std::array<uint8_t, kScreenWidth * kScreenHeight> gfx{};

    // 16-key keypad state (1 = pressed).
    std::array<uint8_t, 16> keys{};

    // Human-readable disassembly of the opcode at a given address (for debug UI).
    std::string disassemble(uint16_t address) const;

private:
    void loadFontset();
};

#endif  // CHIP8_H
