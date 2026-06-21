// AES Encryption Tool — AES-256 implemented from scratch (no crypto libraries).
//
//   - Pure AES-256 (FIPS-197): SubBytes, ShiftRows, MixColumns, key expansion
//   - CBC mode with a random IV
//   - Password-based key derivation (iterated hashing into a 256-bit key)
//   - Encrypts/decrypts any file type
//   - Built-in self-test against the official FIPS-197 AES-256 test vector
//
// Build:  g++ -O2 -std=c++17 -o aes aes.cpp
// Run  :  ./aes --test                       (verify the AES core)
//         ./aes -e secret.txt secret.enc      (encrypt; prompts for password)
//         ./aes -d secret.enc secret.out      (decrypt)
//
// Built by clavexis — github.com/clavexis

#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iostream>
#include <random>
#include <string>
#include <vector>

typedef uint8_t u8;

// --- AES S-box and inverse S-box (FIPS-197) -------------------------------
static const u8 SBOX[256] = {
0x63,0x7c,0x77,0x7b,0xf2,0x6b,0x6f,0xc5,0x30,0x01,0x67,0x2b,0xfe,0xd7,0xab,0x76,
0xca,0x82,0xc9,0x7d,0xfa,0x59,0x47,0xf0,0xad,0xd4,0xa2,0xaf,0x9c,0xa4,0x72,0xc0,
0xb7,0xfd,0x93,0x26,0x36,0x3f,0xf7,0xcc,0x34,0xa5,0xe5,0xf1,0x71,0xd8,0x31,0x15,
0x04,0xc7,0x23,0xc3,0x18,0x96,0x05,0x9a,0x07,0x12,0x80,0xe2,0xeb,0x27,0xb2,0x75,
0x09,0x83,0x2c,0x1a,0x1b,0x6e,0x5a,0xa0,0x52,0x3b,0xd6,0xb3,0x29,0xe3,0x2f,0x84,
0x53,0xd1,0x00,0xed,0x20,0xfc,0xb1,0x5b,0x6a,0xcb,0xbe,0x39,0x4a,0x4c,0x58,0xcf,
0xd0,0xef,0xaa,0xfb,0x43,0x4d,0x33,0x85,0x45,0xf9,0x02,0x7f,0x50,0x3c,0x9f,0xa8,
0x51,0xa3,0x40,0x8f,0x92,0x9d,0x38,0xf5,0xbc,0xb6,0xda,0x21,0x10,0xff,0xf3,0xd2,
0xcd,0x0c,0x13,0xec,0x5f,0x97,0x44,0x17,0xc4,0xa7,0x7e,0x3d,0x64,0x5d,0x19,0x73,
0x60,0x81,0x4f,0xdc,0x22,0x2a,0x90,0x88,0x46,0xee,0xb8,0x14,0xde,0x5e,0x0b,0xdb,
0xe0,0x32,0x3a,0x0a,0x49,0x06,0x24,0x5c,0xc2,0xd3,0xac,0x62,0x91,0x95,0xe4,0x79,
0xe7,0xc8,0x37,0x6d,0x8d,0xd5,0x4e,0xa9,0x6c,0x56,0xf4,0xea,0x65,0x7a,0xae,0x08,
0xba,0x78,0x25,0x2e,0x1c,0xa6,0xb4,0xc6,0xe8,0xdd,0x74,0x1f,0x4b,0xbd,0x8b,0x8a,
0x70,0x3e,0xb5,0x66,0x48,0x03,0xf6,0x0e,0x61,0x35,0x57,0xb9,0x86,0xc1,0x1d,0x9e,
0xe1,0xf8,0x98,0x11,0x69,0xd9,0x8e,0x94,0x9b,0x1e,0x87,0xe9,0xce,0x55,0x28,0xdf,
0x8c,0xa1,0x89,0x0d,0xbf,0xe6,0x42,0x68,0x41,0x99,0x2d,0x0f,0xb0,0x54,0xbb,0x16};

static u8 INV_SBOX[256];
static void init_inv_sbox() { for (int i = 0; i < 256; i++) INV_SBOX[SBOX[i]] = (u8)i; }

// Galois-field multiply (used by MixColumns).
static u8 xtime(u8 x) { return (u8)((x << 1) ^ ((x >> 7) * 0x1b)); }
static u8 gmul(u8 a, u8 b) {
    u8 p = 0;
    for (int i = 0; i < 8; i++) {
        if (b & 1) p ^= a;
        u8 hi = a & 0x80;
        a <<= 1;
        if (hi) a ^= 0x1b;
        b >>= 1;
    }
    return p;
}

// --- AES-256: 14 rounds, 60-word expanded key -----------------------------
static const int Nk = 8, Nr = 14;

static void key_expansion(const u8 key[32], u8 round_keys[240]) {
    memcpy(round_keys, key, 32);
    u8 temp[4];
    int bytes = 32;
    u8 rcon = 1;
    while (bytes < 240) {
        for (int i = 0; i < 4; i++) temp[i] = round_keys[bytes - 4 + i];
        if (bytes % 32 == 0) {
            u8 t = temp[0]; temp[0] = temp[1]; temp[1] = temp[2]; temp[2] = temp[3]; temp[3] = t; // rotword
            for (int i = 0; i < 4; i++) temp[i] = SBOX[temp[i]];                                  // subword
            temp[0] ^= rcon;
            rcon = xtime(rcon);
        } else if (bytes % 32 == 16) {
            for (int i = 0; i < 4; i++) temp[i] = SBOX[temp[i]];                                  // subword (256-bit)
        }
        for (int i = 0; i < 4; i++) { round_keys[bytes] = round_keys[bytes - 32] ^ temp[i]; bytes++; }
    }
}

static void add_round_key(u8 s[16], const u8* rk) { for (int i = 0; i < 16; i++) s[i] ^= rk[i]; }
static void sub_bytes(u8 s[16], const u8* box) { for (int i = 0; i < 16; i++) s[i] = box[s[i]]; }

static void shift_rows(u8 s[16]) {
    u8 t;
    // row 1 << 1
    t = s[1]; s[1] = s[5]; s[5] = s[9]; s[9] = s[13]; s[13] = t;
    // row 2 << 2
    t = s[2]; s[2] = s[10]; s[10] = t; t = s[6]; s[6] = s[14]; s[14] = t;
    // row 3 << 3
    t = s[15]; s[15] = s[11]; s[11] = s[7]; s[7] = s[3]; s[3] = t;
}
static void inv_shift_rows(u8 s[16]) {
    u8 t;
    t = s[13]; s[13] = s[9]; s[9] = s[5]; s[5] = s[1]; s[1] = t;
    t = s[2]; s[2] = s[10]; s[10] = t; t = s[6]; s[6] = s[14]; s[14] = t;
    t = s[3]; s[3] = s[7]; s[7] = s[11]; s[11] = s[15]; s[15] = t;
}
static void mix_columns(u8 s[16]) {
    for (int c = 0; c < 4; c++) {
        u8* col = s + c * 4;
        u8 a0 = col[0], a1 = col[1], a2 = col[2], a3 = col[3];
        col[0] = (u8)(xtime(a0) ^ (xtime(a1) ^ a1) ^ a2 ^ a3);
        col[1] = (u8)(a0 ^ xtime(a1) ^ (xtime(a2) ^ a2) ^ a3);
        col[2] = (u8)(a0 ^ a1 ^ xtime(a2) ^ (xtime(a3) ^ a3));
        col[3] = (u8)((xtime(a0) ^ a0) ^ a1 ^ a2 ^ xtime(a3));
    }
}
static void inv_mix_columns(u8 s[16]) {
    for (int c = 0; c < 4; c++) {
        u8* col = s + c * 4;
        u8 a0 = col[0], a1 = col[1], a2 = col[2], a3 = col[3];
        col[0] = (u8)(gmul(a0,14) ^ gmul(a1,11) ^ gmul(a2,13) ^ gmul(a3,9));
        col[1] = (u8)(gmul(a0,9) ^ gmul(a1,14) ^ gmul(a2,11) ^ gmul(a3,13));
        col[2] = (u8)(gmul(a0,13) ^ gmul(a1,9) ^ gmul(a2,14) ^ gmul(a3,11));
        col[3] = (u8)(gmul(a0,11) ^ gmul(a1,13) ^ gmul(a2,9) ^ gmul(a3,14));
    }
}

static void encrypt_block(u8 block[16], const u8 rk[240]) {
    add_round_key(block, rk);
    for (int r = 1; r < Nr; r++) {
        sub_bytes(block, SBOX); shift_rows(block); mix_columns(block);
        add_round_key(block, rk + r * 16);
    }
    sub_bytes(block, SBOX); shift_rows(block);
    add_round_key(block, rk + Nr * 16);
}
static void decrypt_block(u8 block[16], const u8 rk[240]) {
    add_round_key(block, rk + Nr * 16);
    for (int r = Nr - 1; r >= 1; r--) {
        inv_shift_rows(block); sub_bytes(block, INV_SBOX);
        add_round_key(block, rk + r * 16); inv_mix_columns(block);
    }
    inv_shift_rows(block); sub_bytes(block, INV_SBOX);
    add_round_key(block, rk);
}

// --- Password-based key derivation (no external libs) ---------------------
// A simple iterated mixing of the password and salt into a 256-bit key using
// AES itself as the mixing function. (For production, prefer a vetted KDF.)
static void derive_key(const std::string& pw, const u8 salt[16], u8 key[32]) {
    u8 buf[32] = {0};
    for (size_t i = 0; i < pw.size(); i++) buf[i % 32] ^= (u8)pw[i];
    for (int i = 0; i < 16; i++) buf[16 + i] ^= salt[i];
    u8 rk[240];
    for (int iter = 0; iter < 10000; iter++) {
        key_expansion(buf, rk);
        encrypt_block(buf, rk);
        encrypt_block(buf + 16, rk);
    }
    memcpy(key, buf, 32);
}

// --- CBC mode -------------------------------------------------------------
static void random_bytes(u8* p, int n) {
    std::random_device rd;
    for (int i = 0; i < n; i++) p[i] = (u8)rd();
}

static std::vector<u8> cbc_encrypt(const std::vector<u8>& data, const u8 key[32], const u8 iv[16]) {
    u8 rk[240]; key_expansion(key, rk);
    std::vector<u8> in = data;
    // PKCS#7 padding.
    u8 pad = (u8)(16 - (in.size() % 16));
    for (int i = 0; i < pad; i++) in.push_back(pad);
    std::vector<u8> out;
    u8 prev[16]; memcpy(prev, iv, 16);
    for (size_t i = 0; i < in.size(); i += 16) {
        u8 block[16];
        for (int j = 0; j < 16; j++) block[j] = in[i + j] ^ prev[j];
        encrypt_block(block, rk);
        out.insert(out.end(), block, block + 16);
        memcpy(prev, block, 16);
    }
    return out;
}

static std::vector<u8> cbc_decrypt(const std::vector<u8>& data, const u8 key[32], const u8 iv[16]) {
    u8 rk[240]; key_expansion(key, rk);
    std::vector<u8> out;
    u8 prev[16]; memcpy(prev, iv, 16);
    for (size_t i = 0; i < data.size(); i += 16) {
        u8 block[16]; memcpy(block, &data[i], 16);
        u8 cipher[16]; memcpy(cipher, block, 16);
        decrypt_block(block, rk);
        for (int j = 0; j < 16; j++) block[j] ^= prev[j];
        out.insert(out.end(), block, block + 16);
        memcpy(prev, cipher, 16);
    }
    // Strip PKCS#7 padding.
    if (!out.empty()) {
        u8 pad = out.back();
        if (pad >= 1 && pad <= 16 && pad <= out.size()) out.resize(out.size() - pad);
    }
    return out;
}

// --- Self-test against the FIPS-197 AES-256 vector ------------------------
static int self_test() {
    u8 key[32] = {0x00,0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x08,0x09,0x0a,0x0b,0x0c,0x0d,0x0e,0x0f,
                  0x10,0x11,0x12,0x13,0x14,0x15,0x16,0x17,0x18,0x19,0x1a,0x1b,0x1c,0x1d,0x1e,0x1f};
    u8 pt[16] = {0x00,0x11,0x22,0x33,0x44,0x55,0x66,0x77,0x88,0x99,0xaa,0xbb,0xcc,0xdd,0xee,0xff};
    u8 expect[16] = {0x8e,0xa2,0xb7,0xca,0x51,0x67,0x45,0xbf,0xea,0xfc,0x49,0x90,0x4b,0x49,0x60,0x89};
    u8 rk[240]; key_expansion(key, rk);
    u8 block[16]; memcpy(block, pt, 16);
    encrypt_block(block, rk);
    bool enc_ok = memcmp(block, expect, 16) == 0;
    decrypt_block(block, rk);
    bool dec_ok = memcmp(block, pt, 16) == 0;
    printf("FIPS-197 AES-256 encrypt: %s\n", enc_ok ? "PASS" : "FAIL");
    printf("FIPS-197 AES-256 decrypt: %s\n", dec_ok ? "PASS" : "FAIL");
    return (enc_ok && dec_ok) ? 0 : 1;
}

static std::string ask_password() {
    std::cout << "Password: " << std::flush;
    std::string pw;
    std::getline(std::cin, pw);
    const char* env = getenv("AES_PASSWORD");
    if (pw.empty() && env) pw = env;
    return pw;
}

static int encrypt_file(const std::string& in, const std::string& out, const std::string& pw) {
    std::ifstream fi(in, std::ios::binary);
    if (!fi) { std::cerr << "Cannot open " << in << "\n"; return 1; }
    std::vector<u8> data((std::istreambuf_iterator<char>(fi)), {});
    u8 salt[16], iv[16];
    random_bytes(salt, 16); random_bytes(iv, 16);
    u8 key[32]; derive_key(pw, salt, key);
    auto ct = cbc_encrypt(data, key, iv);
    std::ofstream fo(out, std::ios::binary);
    fo.write("AES2", 4);
    fo.write((char*)salt, 16);
    fo.write((char*)iv, 16);
    fo.write((char*)ct.data(), ct.size());
    printf("Encrypted %s -> %s (%zu bytes)\n", in.c_str(), out.c_str(), ct.size());
    return 0;
}

static int decrypt_file(const std::string& in, const std::string& out, const std::string& pw) {
    std::ifstream fi(in, std::ios::binary);
    if (!fi) { std::cerr << "Cannot open " << in << "\n"; return 1; }
    char magic[4]; fi.read(magic, 4);
    if (std::string(magic, 4) != "AES2") { std::cerr << "Not an AES2 file.\n"; return 1; }
    u8 salt[16], iv[16];
    fi.read((char*)salt, 16); fi.read((char*)iv, 16);
    std::vector<u8> ct((std::istreambuf_iterator<char>(fi)), {});
    u8 key[32]; derive_key(pw, salt, key);
    auto pt = cbc_decrypt(ct, key, iv);
    std::ofstream fo(out, std::ios::binary);
    fo.write((char*)pt.data(), pt.size());
    printf("Decrypted %s -> %s (%zu bytes)\n", in.c_str(), out.c_str(), pt.size());
    return 0;
}

int main(int argc, char** argv) {
    init_inv_sbox();
    if (argc == 2 && std::string(argv[1]) == "--test") return self_test();
    if (argc == 4 && std::string(argv[1]) == "-e") return encrypt_file(argv[2], argv[3], ask_password());
    if (argc == 4 && std::string(argv[1]) == "-d") return decrypt_file(argv[2], argv[3], ask_password());
    printf("Usage:\n  aes --test\n  aes -e <input> <output.enc>\n  aes -d <input.enc> <output>\n");
    return 1;
}
