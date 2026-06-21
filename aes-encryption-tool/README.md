# AES Encryption Tool

AES-256 file encryption implemented **entirely from scratch** — no OpenSSL, no crypto libraries. The core is verified correct against the official **FIPS-197** test vector.

## Demo

```text
$ ./aes --test
FIPS-197 AES-256 encrypt: PASS
FIPS-197 AES-256 decrypt: PASS

$ ./aes -e secret.txt secret.enc
Password: ********
Encrypted secret.txt -> secret.enc (2512 bytes)

$ ./aes -d secret.enc restored.txt
Password: ********
Decrypted secret.enc -> restored.txt (2500 bytes)
```

## Correctness

The implementation is verified against the **FIPS-197 AES-256 known-answer test**:
- Key `000102…1f`, plaintext `00112233…ff` → ciphertext `8ea2b7ca516745bfeafc49904b496089`.

`./aes --test` runs this vector (and the inverse) every build.

## Features

- **AES-256 from scratch** — SubBytes, ShiftRows, MixColumns, AddRoundKey, and the 14-round key schedule, all hand-written.
- **CBC mode** with a **random IV** per file (so the same plaintext encrypts differently each time).
- **Password-based key derivation** — an iterated mixing of password + random salt into the 256-bit key.
- **PKCS#7 padding** — handles files of any length.
- **Binary-safe** — encrypts any file type.
- **Self-test** against the NIST test vector.

## Build & run

Requires a C++17 compiler.

### Linux
```bash
cd linux
make                          # or ./build.sh
./aes --test                  # verify the AES core
./aes -e file.txt file.enc    # encrypt
./aes -d file.enc file.out    # decrypt
```

### macOS (Apple Silicon & Intel)
```bash
cd mac
./build.sh                    # uses clang++
./aes --test
```

### Windows
```powershell
cd windows
build.bat
aes.exe --test
```

## File format

```text
[ "AES2" ][ salt : 16 bytes ][ IV : 16 bytes ][ AES-256-CBC ciphertext ]
```

The salt and IV are stored in the clear (as they should be) so decryption can derive the same key and reverse CBC; only the password is secret.

## Security note

> This is an **educational from-scratch implementation**. The AES core matches the standard exactly, but for production use a vetted library (OpenSSL/libsodium) and a standard KDF (PBKDF2/Argon2) with authenticated encryption (AES-GCM). The included key derivation is intentionally simple.

## Tech stack

- **C++17**, single file, standard library only
- AES-256 (FIPS-197), CBC mode, PKCS#7 padding

---

Built by clavexis — [github.com/clavexis](https://github.com/clavexis)
