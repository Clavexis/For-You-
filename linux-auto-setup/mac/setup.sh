#!/usr/bin/env bash
#
# macOS Auto-Setup — set up a full development environment with one command.
#
#   Installs (via Homebrew): git, neovim, tmux, zsh, docker, python, node, rust, go
#   Sets up oh-my-zsh (+ autosuggestions & syntax-highlighting)
#   Configures git (prompts for name/email)
#   Works on Apple Silicon (M-series) and Intel
#   --dry-run shows what it would do without changing anything
#
# Usage:
#   ./setup.sh              # full setup
#   ./setup.sh --dry-run    # preview only
#   ./setup.sh --minimal    # core tools only
#
# Built by clavexis — github.com/clavexis

set -euo pipefail

DRY_RUN=0
MINIMAL=0
for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=1 ;;
        --minimal) MINIMAL=1 ;;
        --help) grep '^#' "$0" | sed 's/^# \{0,1\}//' | head -18; exit 0 ;;
        *) echo "Unknown option: $arg"; exit 1 ;;
    esac
done

c_green=$'\033[32m'; c_blue=$'\033[34m'; c_yellow=$'\033[33m'; c_reset=$'\033[0m'
info() { echo "${c_blue}==>${c_reset} $*"; }
ok()   { echo "${c_green} ok${c_reset} $*"; }
warn() { echo "${c_yellow} ! ${c_reset} $*"; }

run() {
    if [ "$DRY_RUN" -eq 1 ]; then echo "   ${c_yellow}[dry-run]${c_reset} $*"
    else echo "   + $*"; "$@"; fi
}

# --- ensure Homebrew ------------------------------------------------------
if ! command -v brew >/dev/null 2>&1; then
    info "Homebrew not found — installing it"
    run /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    # Add brew to PATH for Apple Silicon
    if [ -d /opt/homebrew/bin ]; then eval "$(/opt/homebrew/bin/brew shellenv)"; fi
else
    ok "Homebrew present"
fi

brew_install() {
    info "Installing $1"
    run brew install "$1"
}

CORE=(git neovim tmux zsh)
EXTRA=(python node rust go)

info "Updating Homebrew"
run brew update

for p in "${CORE[@]}"; do brew_install "$p"; done
if [ "$MINIMAL" -eq 0 ]; then
    for p in "${EXTRA[@]}"; do brew_install "$p"; done
    info "Installing Docker Desktop (cask)"
    run brew install --cask docker
fi

# --- oh-my-zsh ------------------------------------------------------------
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

# --- dotfiles & git -------------------------------------------------------
info "Writing starter .tmux.conf"
if [ "$DRY_RUN" -eq 1 ]; then
    echo "   ${c_yellow}[dry-run]${c_reset} would write ${HOME}/.tmux.conf"
else
    [ -f "${HOME}/.tmux.conf" ] && cp "${HOME}/.tmux.conf" "${HOME}/.tmux.conf.bak.$(date +%s)"
    printf '%s\n' "# tmux config — clavexis
set -g mouse on
set -g history-limit 10000
setw -g mode-keys vi" > "${HOME}/.tmux.conf"
    ok "wrote ~/.tmux.conf"
fi

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
    git config --global alias.lg "log --oneline --graph --decorate"
    ok "git configured"
fi

echo
ok "Setup complete!"
[ "$DRY_RUN" -eq 1 ] && warn "Dry run — nothing was changed."
echo "   Built by clavexis — github.com/clavexis"
