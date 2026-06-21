// chip8.cpp — implementation of the CHIP-8 virtual machine.
//
// The heart of the emulator is emulateCycle(): it fetches a 2-byte big-endian
// opcode, decodes it by its nibbles, and executes the matching instruction.
// All 35 standard CHIP-8 opcodes are implemented.
//
// Built by clavexis — github.com/clavexis
#include "chip8.h"

#include <cstdio>
#include <cstring>
#include <cstdlib>
#include <fstream>
#include <sstream>
#include <iomanip>

// The standard CHIP-8 fontset: 16 hexadecimal digits, 5 bytes (rows) each.
// Each nibble bit that is set lights a pixel, forming a 4x5 glyph.
static const uint8_t kFontset[80] = {
    0xF0, 0x90, 0x90, 0x90, 0xF0,  // 0
    0x20, 0x60, 0x20, 0x20, 0x70,  // 1
    0xF0, 0x10, 0xF0, 0x80, 0xF0,  // 2
    0xF0, 0x10, 0xF0, 0x10, 0xF0,  // 3
    0x90, 0x90, 0xF0, 0x10, 0x10,  // 4
    0xF0, 0x80, 0xF0, 0x10, 0xF0,  // 5
    0xF0, 0x80, 0xF0, 0x90, 0xF0,  // 6
    0xF0, 0x10, 0x20, 0x40, 0x40,  // 7
    0xF0, 0x90, 0xF0, 0x90, 0xF0,  // 8
    0xF0, 0x90, 0xF0, 0x10, 0xF0,  // 9
    0xF0, 0x90, 0xF0, 0x90, 0x90,  // A
    0xE0, 0x90, 0xE0, 0x90, 0xE0,  // B
    0xF0, 0x80, 0x80, 0x80, 0xF0,  // C
    0xE0, 0x90, 0x90, 0x90, 0xE0,  // D
    0xF0, 0x80, 0xF0, 0x80, 0xF0,  // E
    0xF0, 0x80, 0xF0, 0x80, 0x80,  // F
};

Chip8::Chip8() { reset(); }

void Chip8::reset() {
    memory.fill(0);
    V.fill(0);
    stack.fill(0);
    gfx.fill(0);
    keys.fill(0);
    I = 0;
    pc = kProgramStart;
    sp = 0;
    delayTimer = 0;
    soundTimer = 0;
    drawFlag = false;
    loadFontset();
}

void Chip8::loadFontset() {
    // Convention places the fontset at the start of memory (0x00..0x4F).
    std::memcpy(memory.data(), kFontset, sizeof(kFontset));
}

bool Chip8::loadRom(const std::string& path) {
    std::ifstream file(path, std::ios::binary | std::ios::ate);
    if (!file) return false;
    std::streamsize size = file.tellg();
    file.seekg(0, std::ios::beg);
    if (size <= 0 || static_cast<size_t>(size) > memory.size() - kProgramStart)
        return false;
    return file.read(reinterpret_cast<char*>(memory.data() + kProgramStart), size)
           ? true : false;
}

bool Chip8::loadRom(const uint8_t* data, size_t size) {
    if (size > memory.size() - kProgramStart) return false;
    std::memcpy(memory.data() + kProgramStart, data, size);
    return true;
}

void Chip8::emulateCycle() {
    drawFlag = false;

    // Fetch: opcodes are two bytes, big-endian.
    uint16_t opcode = (memory[pc] << 8) | memory[pc + 1];

    // Decode the common operand fields once.
    uint8_t x   = (opcode & 0x0F00) >> 8;     // second nibble  -> register index
    uint8_t y   = (opcode & 0x00F0) >> 4;     // third nibble   -> register index
    uint8_t n   = opcode & 0x000F;            // fourth nibble  (sprite height)
    uint8_t nn  = opcode & 0x00FF;            // low byte       (immediate)
    uint16_t nnn = opcode & 0x0FFF;           // low 12 bits    (address)

    pc += 2;  // advance now; jumps/skips adjust pc afterwards

    switch (opcode & 0xF000) {
    case 0x0000:
        switch (nn) {
        case 0xE0:  // 00E0: clear the display
            gfx.fill(0);
            drawFlag = true;
            break;
        case 0xEE:  // 00EE: return from a subroutine
            pc = stack[--sp];
            break;
        default:
            // 0NNN (call machine code) is ignored on modern interpreters.
            break;
        }
        break;

    case 0x1000:  // 1NNN: jump to NNN
        pc = nnn;
        break;

    case 0x2000:  // 2NNN: call subroutine at NNN
        stack[sp++] = pc;
        pc = nnn;
        break;

    case 0x3000:  // 3XNN: skip next instruction if VX == NN
        if (V[x] == nn) pc += 2;
        break;

    case 0x4000:  // 4XNN: skip next instruction if VX != NN
        if (V[x] != nn) pc += 2;
        break;

    case 0x5000:  // 5XY0: skip next instruction if VX == VY
        if (V[x] == V[y]) pc += 2;
        break;

    case 0x6000:  // 6XNN: VX = NN
        V[x] = nn;
        break;

    case 0x7000:  // 7XNN: VX += NN (carry flag is NOT affected)
        V[x] += nn;
        break;

    case 0x8000:  // arithmetic / logic group, selected by the low nibble
        switch (n) {
        case 0x0: V[x] = V[y]; break;                 // 8XY0: VX = VY
        case 0x1: V[x] |= V[y]; break;                // 8XY1: VX |= VY
        case 0x2: V[x] &= V[y]; break;                // 8XY2: VX &= VY
        case 0x3: V[x] ^= V[y]; break;                // 8XY3: VX ^= VY
        case 0x4: {                                   // 8XY4: VX += VY, VF = carry
            uint16_t sum = V[x] + V[y];
            V[0xF] = sum > 0xFF ? 1 : 0;
            V[x] = sum & 0xFF;
            break;
        }
        case 0x5:                                     // 8XY5: VX -= VY, VF = !borrow
            V[0xF] = V[x] >= V[y] ? 1 : 0;
            V[x] = V[x] - V[y];
            break;
        case 0x6:                                     // 8XY6: VX >>= 1, VF = lost bit
            V[0xF] = V[x] & 0x1;
            V[x] >>= 1;
            break;
        case 0x7:                                     // 8XY7: VX = VY - VX, VF = !borrow
            V[0xF] = V[y] >= V[x] ? 1 : 0;
            V[x] = V[y] - V[x];
            break;
        case 0xE:                                     // 8XYE: VX <<= 1, VF = lost bit
            V[0xF] = (V[x] & 0x80) >> 7;
            V[x] <<= 1;
            break;
        }
        break;

    case 0x9000:  // 9XY0: skip next instruction if VX != VY
        if (V[x] != V[y]) pc += 2;
        break;

    case 0xA000:  // ANNN: I = NNN
        I = nnn;
        break;

    case 0xB000:  // BNNN: jump to NNN + V0
        pc = nnn + V[0];
        break;

    case 0xC000:  // CXNN: VX = random byte & NN
        V[x] = (std::rand() % 256) & nn;
        break;

    case 0xD000: {  // DXYN: draw an N-byte sprite from memory[I] at (VX, VY)
        uint8_t px = V[x] % kScreenWidth;
        uint8_t py = V[y] % kScreenHeight;
        V[0xF] = 0;  // collision flag, set if any lit pixel gets erased
        for (int row = 0; row < n; ++row) {
            uint8_t spriteByte = memory[I + row];
            for (int col = 0; col < 8; ++col) {
                if ((spriteByte & (0x80 >> col)) == 0) continue;  // bit not set
                int sx = (px + col);
                int sy = (py + row);
                if (sx >= kScreenWidth || sy >= kScreenHeight) continue;  // clip
                int idx = sy * kScreenWidth + sx;
                if (gfx[idx]) V[0xF] = 1;  // pixel was on -> collision
                gfx[idx] ^= 1;             // XOR draw
            }
        }
        drawFlag = true;
        break;
    }

    case 0xE000:  // keypad-conditional skips
        if (nn == 0x9E) {           // EX9E: skip if key VX is pressed
            if (keys[V[x] & 0xF]) pc += 2;
        } else if (nn == 0xA1) {    // EXA1: skip if key VX is NOT pressed
            if (!keys[V[x] & 0xF]) pc += 2;
        }
        break;

    case 0xF000:
        switch (nn) {
        case 0x07:  // FX07: VX = delay timer
            V[x] = delayTimer;
            break;
        case 0x0A: {  // FX0A: wait for a key press, store its index in VX
            bool pressed = false;
            for (uint8_t k = 0; k < 16; ++k) {
                if (keys[k]) { V[x] = k; pressed = true; break; }
            }
            if (!pressed) pc -= 2;  // no key yet: re-run this instruction
            break;
        }
        case 0x15: delayTimer = V[x]; break;          // FX15: delay timer = VX
        case 0x18: soundTimer = V[x]; break;          // FX18: sound timer = VX
        case 0x1E: I += V[x]; break;                  // FX1E: I += VX
        case 0x29: I = (V[x] & 0xF) * 5; break;       // FX29: I = sprite addr for digit VX
        case 0x33:                                    // FX33: BCD of VX into I,I+1,I+2
            memory[I]     = V[x] / 100;
            memory[I + 1] = (V[x] / 10) % 10;
            memory[I + 2] = V[x] % 10;
            break;
        case 0x55:  // FX55: store V0..VX into memory starting at I
            for (uint8_t i = 0; i <= x; ++i) memory[I + i] = V[i];
            break;
        case 0x65:  // FX65: load V0..VX from memory starting at I
            for (uint8_t i = 0; i <= x; ++i) V[i] = memory[I + i];
            break;
        }
        break;
    }
}

void Chip8::tickTimers() {
    if (delayTimer > 0) --delayTimer;
    if (soundTimer > 0) --soundTimer;
}

std::string Chip8::disassemble(uint16_t address) const {
    uint16_t opcode = (memory[address] << 8) | memory[address + 1];
    uint8_t x = (opcode & 0x0F00) >> 8;
    uint8_t y = (opcode & 0x00F0) >> 4;
    uint8_t n = opcode & 0x000F;
    uint8_t nn = opcode & 0x00FF;
    uint16_t nnn = opcode & 0x0FFF;

    std::ostringstream os;
    os << std::hex << std::uppercase << std::setfill('0');
    os << std::setw(4) << opcode << "  ";

    auto V = [](int r) {
        std::ostringstream s; s << "V" << std::hex << std::uppercase << r; return s.str();
    };

    switch (opcode & 0xF000) {
    case 0x0000:
        if (nn == 0xE0) os << "CLS";
        else if (nn == 0xEE) os << "RET";
        else os << "SYS  " << std::setw(3) << nnn;
        break;
    case 0x1000: os << "JP   " << std::setw(3) << nnn; break;
    case 0x2000: os << "CALL " << std::setw(3) << nnn; break;
    case 0x3000: os << "SE   " << V(x) << ", " << +nn; break;
    case 0x4000: os << "SNE  " << V(x) << ", " << +nn; break;
    case 0x5000: os << "SE   " << V(x) << ", " << V(y); break;
    case 0x6000: os << "LD   " << V(x) << ", " << +nn; break;
    case 0x7000: os << "ADD  " << V(x) << ", " << +nn; break;
    case 0x8000:
        switch (n) {
        case 0x0: os << "LD   " << V(x) << ", " << V(y); break;
        case 0x1: os << "OR   " << V(x) << ", " << V(y); break;
        case 0x2: os << "AND  " << V(x) << ", " << V(y); break;
        case 0x3: os << "XOR  " << V(x) << ", " << V(y); break;
        case 0x4: os << "ADD  " << V(x) << ", " << V(y); break;
        case 0x5: os << "SUB  " << V(x) << ", " << V(y); break;
        case 0x6: os << "SHR  " << V(x); break;
        case 0x7: os << "SUBN " << V(x) << ", " << V(y); break;
        case 0xE: os << "SHL  " << V(x); break;
        default:  os << "???"; break;
        }
        break;
    case 0x9000: os << "SNE  " << V(x) << ", " << V(y); break;
    case 0xA000: os << "LD   I, " << std::setw(3) << nnn; break;
    case 0xB000: os << "JP   V0, " << std::setw(3) << nnn; break;
    case 0xC000: os << "RND  " << V(x) << ", " << +nn; break;
    case 0xD000: os << "DRW  " << V(x) << ", " << V(y) << ", " << +n; break;
    case 0xE000:
        os << (nn == 0x9E ? "SKP  " : "SKNP ") << V(x);
        break;
    case 0xF000:
        switch (nn) {
        case 0x07: os << "LD   " << V(x) << ", DT"; break;
        case 0x0A: os << "LD   " << V(x) << ", K"; break;
        case 0x15: os << "LD   DT, " << V(x); break;
        case 0x18: os << "LD   ST, " << V(x); break;
        case 0x1E: os << "ADD  I, " << V(x); break;
        case 0x29: os << "LD   F, " << V(x); break;
        case 0x33: os << "LD   B, " << V(x); break;
        case 0x55: os << "LD   [I], " << V(x); break;
        case 0x65: os << "LD   " << V(x) << ", [I]"; break;
        default:   os << "???"; break;
        }
        break;
    default: os << "???"; break;
    }
    return os.str();
}
