# clawpkg — Custom Package Manager

A minimal, fast package manager written in Rust — with recursive dependency resolution, a local cache, and a lock file. Install, remove, and update packages from a simple JSON-manifest registry.

## Demo

```text
$ clawpkg install app@1.0.0
Resolved 4 package(s):
  + app@1.0.0
  + http@2.0.0
  + json@1.6.0
  + socket@1.0.0
Installed. Lock file updated.

$ clawpkg list
Installed packages:
  app @ 1.0.0
  http @ 2.0.0
  json @ 1.6.0
  socket @ 1.0.0
```

## Features

- **Install / remove / update** packages with one command.
- **Recursive dependency resolution** — transitive deps are pulled in automatically, with **cycle detection**.
- **Version selection** — pin an exact version (`name@1.2.3`) or use `*` for the latest.
- **JSON manifests** — each package declares its name, version, and dependencies.
- **Local package cache** (`.clawpkg/cache`) so re-installs are fast.
- **Lock file** (`clawpkg.lock`) recording the exact installed version of every package.

## Build

Requires **Rust** (install via [rustup](https://rustup.rs)).

### Linux
```bash
cd linux
cargo build --release          # or ./build.sh
./target/release/clawpkg install leftpad
```

### macOS (Apple Silicon & Intel)
```bash
cd mac
cargo build --release
./target/release/clawpkg install leftpad
```

### Windows
```powershell
cd windows
cargo build --release
target\release\clawpkg.exe install leftpad
```

## Usage

```bash
clawpkg install <name>          # latest version + dependencies
clawpkg install <name>@1.2.3    # a specific version
clawpkg remove <name>
clawpkg update                  # upgrade installed packages to the latest
clawpkg list                    # show installed packages
```

By default the registry is `./registry`; override with `CLAWPKG_REGISTRY=/path`.

## Registry & manifest format

A registry is just a directory tree (simulating a remote repo):

```text
registry/
  leftpad/
    1.0.0/
      package.json        # the manifest
      files/              # the package contents
        leftpad.js
```

```json
// package.json
{
  "name": "leftpad",
  "version": "1.0.0",
  "dependencies": { "utils": "*" }
}
```

A sample registry (`leftpad` → `utils`) is included — try `clawpkg install leftpad`.

## How it works

```text
install name ──▶ resolve deps (recursive, cycle-checked)
             ──▶ copy each package: registry → .clawpkg/cache → clawpkg_modules/
             ──▶ write exact versions to clawpkg.lock
```

## Tech stack

- **Rust** (2021 edition), `serde` / `serde_json` for manifests
- Filesystem-backed registry, recursive resolver, lock file

---

Built by clavexis — [github.com/clavexis](https://github.com/clavexis)
