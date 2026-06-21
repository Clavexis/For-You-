# Password Manager

A secure, local, command-line password vault. Your passwords are encrypted at rest with a key derived from your master password — nothing is stored in plaintext, and nothing leaves your machine.

## Demo

```text
$ pwvault init
Choose a master password: ********
Vault created at ~/.local/share/password-manager/vault.enc.

$ pwvault add github --user me@example.com --gen
Generated password: 9McBSngydg]t2#=8txRz^G(v
Saved entry 'github'.

$ pwvault get github
github
  user:     me@example.com
  password: 9McBSngydg]t2#=8txRz^G(v
```

## Security

- **Encrypted vault** — the entire vault is encrypted with Fernet (AES-128-CBC + HMAC authentication).
- **PBKDF2-HMAC-SHA256** key derivation, **200,000 iterations**, with a random 16-byte salt per vault.
- **The master password is never stored** — only used to derive the key in memory.
- **Verified encrypted at rest** — the vault file contains no readable entry names or passwords.
- Vault file is created with `0600` permissions.

> Forget your master password and the data is unrecoverable — that's the point.

## Features

- **`init`** — create a vault.
- **`add` / `get` / `delete` / `list`** — manage entries.
- **Password generator** — strong passwords with guaranteed character variety (`--gen` or standalone `generate`).
- **Encrypted backup** — `export` writes a portable encrypted copy.

## Installation

Requires **Python 3.7+** and `cryptography`.

### Linux
```bash
cd linux && ./install.sh
pwvault init
```

### macOS (Apple Silicon & Intel)
```bash
cd mac && ./install.sh
pwvault init
```

### Windows
```powershell
cd windows
install.bat
python vault.py init
```

## Usage

```bash
pwvault init                                   # create the vault
pwvault add github --user me@x.com --gen       # add with a generated password
pwvault add email --user me@x.com --password "..."   # add with your own
pwvault get github                             # show an entry
pwvault list                                   # list all entries
pwvault delete github                          # remove an entry
pwvault generate --length 24                   # just generate a password
pwvault export backup.vault                    # encrypted backup
```

You'll be prompted for your master password (or set `VAULT_MASTER` for scripting). The vault location can be overridden with `VAULT_FILE`.

## Tech stack

- **Python 3** + [`cryptography`](https://pypi.org/project/cryptography/) (Fernet / AES, PBKDF2)
- Salted, iterated key derivation; authenticated encryption

---

Built by clavexis — [github.com/clavexis](https://github.com/clavexis)
