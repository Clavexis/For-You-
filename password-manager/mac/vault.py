#!/usr/bin/env python3
"""
Password Manager — a secure local password vault.

  - AES-256 encryption of the vault (via Fernet, which is AES-128-CBC + HMAC;
    the master key is derived with PBKDF2-HMAC-SHA256, 200k iterations)
  - Master password unlocks everything; the password itself is never stored
  - add / get / delete / list entries
  - Built-in strong password generator
  - Export to an encrypted backup file

The vault file is fully encrypted at rest — without the master password it is
unreadable.

Usage:
  vault.py init
  vault.py add github --user me --gen
  vault.py get github
  vault.py list
  vault.py delete github
  vault.py generate --length 24
  vault.py export backup.vault

Built by clavexis — github.com/clavexis
"""

import argparse
import base64
import getpass
import json
import os
import secrets
import string
import sys
from pathlib import Path

try:
    from cryptography.fernet import Fernet, InvalidToken
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
except ImportError:
    sys.stderr.write("This tool needs the 'cryptography' package.  pip install cryptography\n")
    sys.exit(1)

PBKDF2_ITERS = 200_000


class C:
    RESET = "\033[0m"; BOLD = "\033[1m"; DIM = "\033[2m"
    GREEN = "\033[32m"; CYAN = "\033[36m"; YELLOW = "\033[33m"; RED = "\033[31m"

    @classmethod
    def off(cls):
        for n in ("RESET", "BOLD", "DIM", "GREEN", "CYAN", "YELLOW", "RED"):
            setattr(cls, n, "")


if not sys.stdout.isatty() or os.environ.get("NO_COLOR"):
    C.off()


def vault_path() -> Path:
    base = os.environ.get("XDG_DATA_HOME") or os.path.join(Path.home(), ".local", "share")
    p = Path(os.environ.get("VAULT_FILE", os.path.join(base, "password-manager", "vault.enc")))
    return p


# ---------------------------------------------------------------------------
# Crypto (pure / testable).
# ---------------------------------------------------------------------------
def derive_key(master: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=PBKDF2_ITERS)
    return base64.urlsafe_b64encode(kdf.derive(master.encode()))


def encrypt_vault(data: dict, master: str, salt: bytes) -> bytes:
    f = Fernet(derive_key(master, salt))
    return f.encrypt(json.dumps(data).encode())


def decrypt_vault(blob: bytes, master: str, salt: bytes) -> dict:
    f = Fernet(derive_key(master, salt))
    return json.loads(f.decrypt(blob).decode())


def generate_password(length: int = 20, symbols: bool = True) -> str:
    alphabet = string.ascii_letters + string.digits
    if symbols:
        alphabet += "!@#$%^&*()-_=+[]{}"
    # Ensure at least one of each class for strength.
    while True:
        pw = "".join(secrets.choice(alphabet) for _ in range(length))
        if (any(c.islower() for c in pw) and any(c.isupper() for c in pw)
                and any(c.isdigit() for c in pw)):
            return pw


# ---------------------------------------------------------------------------
# Vault file = salt (16 bytes) + encrypted blob.
# ---------------------------------------------------------------------------
def load_raw(path: Path):
    raw = path.read_bytes()
    return raw[:16], raw[16:]


def save_raw(path: Path, salt: bytes, blob: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(salt + blob)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def unlock(path: Path, master: str = None):
    if not path.exists():
        sys.stderr.write(f"{C.RED}No vault found. Run 'vault.py init' first.{C.RESET}\n")
        sys.exit(1)
    salt, blob = load_raw(path)
    if master is None:
        master = os.environ.get("VAULT_MASTER") or getpass.getpass("Master password: ")
    try:
        data = decrypt_vault(blob, master, salt)
    except InvalidToken:
        sys.stderr.write(f"{C.RED}Wrong master password.{C.RESET}\n")
        sys.exit(1)
    return data, salt, master


# ---------------------------------------------------------------------------
# Commands.
# ---------------------------------------------------------------------------
def cmd_init(path: Path):
    if path.exists():
        sys.stderr.write(f"{C.YELLOW}Vault already exists at {path}.{C.RESET}\n")
        return 1
    master = os.environ.get("VAULT_MASTER") or getpass.getpass("Choose a master password: ")
    if os.environ.get("VAULT_MASTER") is None:
        confirm = getpass.getpass("Confirm master password: ")
        if master != confirm:
            sys.stderr.write(f"{C.RED}Passwords do not match.{C.RESET}\n")
            return 1
    salt = secrets.token_bytes(16)
    save_raw(path, salt, encrypt_vault({}, master, salt))
    print(f"{C.GREEN}Vault created at {path}.{C.RESET}")
    return 0


def cmd_add(path: Path, name, user, password, gen, length):
    data, salt, master = unlock(path)
    if gen or not password:
        password = generate_password(length)
        print(f"{C.DIM}Generated password: {password}{C.RESET}")
    data[name] = {"user": user or "", "password": password}
    save_raw(path, salt, encrypt_vault(data, master, salt))
    print(f"{C.GREEN}Saved entry '{name}'.{C.RESET}")
    return 0


def cmd_get(path: Path, name):
    data, _, _ = unlock(path)
    entry = data.get(name)
    if not entry:
        sys.stderr.write(f"{C.RED}No entry '{name}'.{C.RESET}\n")
        return 1
    print(f"{C.BOLD}{name}{C.RESET}")
    print(f"  user:     {entry.get('user','')}")
    print(f"  password: {C.CYAN}{entry['password']}{C.RESET}")
    return 0


def cmd_list(path: Path):
    data, _, _ = unlock(path)
    if not data:
        print(f"{C.DIM}Vault is empty.{C.RESET}")
        return 0
    print(f"{C.BOLD}Entries:{C.RESET}")
    for name in sorted(data):
        print(f"  {name}  {C.DIM}({data[name].get('user','')}){C.RESET}")
    return 0


def cmd_delete(path: Path, name):
    data, salt, master = unlock(path)
    if name not in data:
        sys.stderr.write(f"{C.RED}No entry '{name}'.{C.RESET}\n")
        return 1
    del data[name]
    save_raw(path, salt, encrypt_vault(data, master, salt))
    print(f"{C.GREEN}Deleted '{name}'.{C.RESET}")
    return 0


def cmd_export(path: Path, out):
    # Re-encrypt the current vault under the same master into a backup file.
    data, salt, master = unlock(path)
    new_salt = secrets.token_bytes(16)
    save_raw(Path(out), new_salt, encrypt_vault(data, master, new_salt))
    print(f"{C.GREEN}Encrypted backup written to {out} (same master password).{C.RESET}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="A secure local password vault.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init", help="Create a new vault.")
    a = sub.add_parser("add", help="Add an entry.")
    a.add_argument("name")
    a.add_argument("--user", help="Username/email.")
    a.add_argument("--password", help="Password (omit to be prompted/generated).")
    a.add_argument("--gen", action="store_true", help="Generate a strong password.")
    a.add_argument("--length", type=int, default=20)
    g = sub.add_parser("get", help="Show an entry.")
    g.add_argument("name")
    sub.add_parser("list", help="List entries.")
    d = sub.add_parser("delete", help="Delete an entry.")
    d.add_argument("name")
    gp = sub.add_parser("generate", help="Generate a password (no vault needed).")
    gp.add_argument("--length", type=int, default=20)
    gp.add_argument("--no-symbols", action="store_true")
    e = sub.add_parser("export", help="Export an encrypted backup.")
    e.add_argument("out")
    args = ap.parse_args()

    path = vault_path()

    if args.cmd == "init":
        return cmd_init(path)
    if args.cmd == "generate":
        print(generate_password(args.length, not args.no_symbols))
        return 0
    if args.cmd == "add":
        return cmd_add(path, args.name, args.user, args.password, args.gen, args.length)
    if args.cmd == "get":
        return cmd_get(path, args.name)
    if args.cmd == "list":
        return cmd_list(path)
    if args.cmd == "delete":
        return cmd_delete(path, args.name)
    if args.cmd == "export":
        return cmd_export(path, args.out)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
