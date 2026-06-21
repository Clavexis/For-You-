#!/usr/bin/env bash
#
# Linux Auto-Setup — set up a full development environment with one command.
#
#   Installs: git, neovim, tmux, zsh, docker, python, node, rust, go
#   Sets up oh-my-zsh (+ autosuggestions & syntax-highlighting plugins)
#   Configures git (prompts for name/email)
#   Works on Ubuntu / Debian (apt) and Arch (pacman)
#   --dry-run shows exactly what it would do without changing anything
#
# Usage:
#   ./setup.sh                # full setup (asks before big changes)
#   ./setup.sh --dry-run      # preview only
#   ./setup.sh --minimal      # core tools only (git, neovim, tmux, zsh)
#
# Built by clavexis — github.com/clavexis

set -euo pipefail

DRY_RUN=0
MINIMAL=0

for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=1 ;;
        --minimal) MINIMAL=1 ;;
        --help)
            grep '^#' "$0" | sed 's/^# \{0,1\}//' | head -20
            exit 0 ;;
        *) echo "Unknown option: $arg"; exit 1 ;;
    esac
done

# --- pretty output --------------------------------------------------------
c_green=$'\033[32m'; c_blue=$'\033[34m'; c_yellow=$'\033[33m'; c_reset=$'\033[0m'
info()  { echo "${c_blue}==>${c_reset} $*"; }
ok()    { echo "${c_green} ok${c_reset} $*"; }
warn()  { echo "${c_yellow} ! ${c_reset} $*"; }

# run CMD — executes it, or just prints it in --dry-run mode
run() {
    if [ "$DRY_RUN" -eq 1 ]; then
        echo "   ${c_yellow}[dry-run]${c_reset} $*"
    else
        echo "   + $*"
        "$@"
    fi
}

# --- detect the package manager ------------------------------------------
detect_pm() {
    if command -v apt-get >/dev/null 2>&1; then echo "apt"
    elif command -v pacman >/dev/null 2>&1; then echo "pacman"
    elif command -v dnf >/dev/null 2>&1; then echo "dnf"
    else echo "unknown"; fi
}

PM="$(detect_pm)"
info "Detected package manager: ${PM}"
[ "$PM" = "unknown" ] && { warn "Unsupported distro. Supported: apt, pacman, dnf."; exit 1; }

# Map a logical package name to the distro-specific package(s).
pkg_name() {
    local name="$1"
    case "$PM:$name" in
        apt:neovim|pacman:neovim|dnf:neovim) echo "neovim" ;;
        apt:python) echo "python3 python3-pip" ;;
        pacman:python|dnf:python) echo "python python-pip" ;;
        apt:node) echo "nodejs npm" ;;
        pacman:node) echo "nodejs npm" ;;
        dnf:node) echo "nodejs npm" ;;
        apt:go) echo "golang-go" ;;
        dnf:go) echo "golang" ;;
        pacman:go) echo "go" ;;
        *) echo "$name" ;;
    esac
}

install_pkg() {
    local logical="$1" pkgs
    pkgs="$(pkg_name "$logical")"
    info "Installing ${logical} (${pkgs})"
    case "$PM" in
        apt)    run sudo apt-get install -y $pkgs ;;
        pacman) run sudo pacman -S --noconfirm --needed $pkgs ;;
        dnf)    run sudo dnf install -y $pkgs ;;
    esac
}

# --- refresh package lists ------------------------------------------------
info "Refreshing package lists"
case "$PM" in
    apt)    run sudo apt-get update ;;
    pacman) run sudo pacman -Sy ;;
    dnf)    run sudo dnf check-update || true ;;
esac

# --- core tools -----------------------------------------------------------
CORE=(git neovim tmux zsh curl)
EXTRA=(docker python node rust go)

for p in "${CORE[@]}"; do install_pkg "$p"; done

if [ "$MINIMAL" -eq 0 ]; then
    for p in "${EXTRA[@]}"; do
        case "$p" in
            rust)
                info "Installing Rust via rustup"
                run sh -c 'command -v cargo >/dev/null || curl --proto "=https" --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y' ;;
            docker)
                install_pkg "docker.io" 2>/dev/null || install_pkg "docker" ;;
            *) install_pkg "$p" ;;
        esac
    done
fi

# --- oh-my-zsh + plugins --------------------------------------------------
info "Setting up oh-my-zsh"
OMZ_DIR="${HOME}/.oh-my-zsh"
if [ ! -d "$OMZ_DIR" ]; then
    run sh -c 'RUNZSH=no CHSH=no sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"'
else
    ok "oh-my-zsh already installed"
fi
ZSH_CUSTOM="${OMZ_DIR}/custom"
run git clone --depth 1 https://github.com/zsh-users/zsh-autosuggestions "${ZSH_CUSTOM}/plugins/zsh-autosuggestions" 2>/dev/null || true
run git clone --depth 1 https://github.com/zsh-users/zsh-syntax-highlighting "${ZSH_CUSTOM}/plugins/zsh-syntax-highlighting" 2>/dev/null || true

# --- dotfiles -------------------------------------------------------------
info "Writing starter dotfiles"
write_file() {
    local path="$1" content="$2"
    if [ "$DRY_RUN" -eq 1 ]; then
        echo "   ${c_yellow}[dry-run]${c_reset} would write ${path}"
    else
        [ -f "$path" ] && cp "$path" "${path}.bak.$(date +%s)"
        printf '%s\n' "$content" > "$path"
        ok "wrote ${path}"
    fi
}
write_file "${HOME}/.tmux.conf" "# tmux config — clavexis
set -g mouse on
set -g history-limit 10000
set -g base-index 1
setw -g mode-keys vi
set -g status-bg colour237
set -g status-fg white"

# --- git config -----------------------------------------------------------
info "Configuring git"
if [ "$DRY_RUN" -eq 1 ]; then
    echo "   ${c_yellow}[dry-run]${c_reset} would prompt for git user.name / user.email"
else
    if ! git config --global user.name >/dev/null 2>&1; then
        read -rp "   git user.name: " GIT_NAME
        read -rp "   git user.email: " GIT_EMAIL
        git config --global user.name "$GIT_NAME"
        git config --global user.email "$GIT_EMAIL"
    fi
    git config --global init.defaultBranch main
    git config --global pull.rebase false
    git config --global alias.st status
    git config --global alias.co checkout
    git config --global alias.lg "log --oneline --graph --decorate"
    ok "git configured"
fi

echo
ok "Setup complete!"
[ "$DRY_RUN" -eq 1 ] && warn "This was a dry run — nothing was changed."
echo "   To make zsh your default shell:  chsh -s \$(which zsh)"
echo "   Built by clavexis — github.com/clavexis"
