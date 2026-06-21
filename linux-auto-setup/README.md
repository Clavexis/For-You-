# Auto-Setup Script

One command to set up a complete development environment — tools, shell, dotfiles, and git config — on Linux, macOS, or Windows.

## Demo

```text
$ ./setup.sh --dry-run
==> Detected package manager: apt
==> Installing git (git)
   [dry-run] sudo apt-get install -y git
==> Installing neovim (neovim)
   [dry-run] sudo apt-get install -y neovim
...
==> Setting up oh-my-zsh
==> Configuring git
 ok Setup complete!
 !  This was a dry run — nothing was changed.
```

## Features

- **Installs a full toolchain:** git, neovim, tmux, zsh, docker, python, node, rust, go.
- **oh-my-zsh** with `zsh-autosuggestions` and `zsh-syntax-highlighting` plugins.
- **Starter dotfiles** (`.tmux.conf`) — existing files are backed up first.
- **Git configuration** — prompts for name/email, sets sensible defaults and aliases.
- **Distro-aware (Linux):** works on Ubuntu/Debian (`apt`), Arch (`pacman`), and Fedora (`dnf`).
- **`--dry-run`** — preview every action without changing anything.
- **`--minimal`** — install just the core tools (git, neovim, tmux, zsh).

## Usage

### Linux
```bash
cd linux
./setup.sh --dry-run     # preview first (recommended)
./setup.sh               # full setup
./setup.sh --minimal     # core tools only
```

### macOS (Apple Silicon & Intel)
```bash
cd mac
./setup.sh --dry-run     # installs via Homebrew (installs brew if missing)
./setup.sh
```

### Windows
```powershell
cd windows
.\setup.ps1 -DryRun      # installs via winget
.\setup.ps1
```
(You may need `Set-ExecutionPolicy -Scope Process Bypass` to run the script.)

## What gets installed

| Tool    | Linux            | macOS        | Windows            |
|---------|------------------|--------------|--------------------|
| git     | apt/pacman/dnf   | Homebrew     | winget (Git.Git)   |
| neovim  | ✓                | ✓            | winget             |
| tmux    | ✓                | ✓            | via WSL            |
| zsh     | ✓                | ✓            | via WSL            |
| docker  | docker.io        | Docker cask  | Docker Desktop     |
| python  | python3 + pip    | ✓            | Python 3.12        |
| node    | nodejs + npm     | ✓            | OpenJS.NodeJS      |
| rust    | rustup           | ✓            | Rustup             |
| go      | golang-go        | ✓            | GoLang.Go          |

## Safety

- **Always run `--dry-run` first** to see exactly what will happen.
- Existing dotfiles are backed up with a timestamped `.bak` suffix.
- Nothing is changed in dry-run mode.

## Tech stack

- **Bash** (Linux/macOS) and **PowerShell** (Windows)
- Package managers: apt / pacman / dnf / Homebrew / winget

---

Built by clavexis — [github.com/clavexis](https://github.com/clavexis)
