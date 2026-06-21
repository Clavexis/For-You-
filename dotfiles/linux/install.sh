#!/usr/bin/env bash
#
# Dotfiles installer — symlinks the configs into your home directory.
# Existing files are backed up with a timestamped .bak suffix.
#
# Usage:
#   ./install.sh              # symlink everything
#   ./install.sh --dry-run    # preview only
#
# Built by clavexis — github.com/clavexis

set -euo pipefail

DRY_RUN=0
[ "${1:-}" = "--dry-run" ] && DRY_RUN=1

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOTFILES="${SCRIPT_DIR}/dotfiles"
STAMP="$(date +%Y%m%d%H%M%S)"

c_green=$'\033[32m'; c_yellow=$'\033[33m'; c_reset=$'\033[0m'

link() {
    local src="$1" dest="$2"
    if [ "$DRY_RUN" -eq 1 ]; then
        echo "   ${c_yellow}[dry-run]${c_reset} ln -s ${src} ${dest}"
        return
    fi
    mkdir -p "$(dirname "$dest")"
    if [ -e "$dest" ] && [ ! -L "$dest" ]; then
        mv "$dest" "${dest}.bak.${STAMP}"
        echo "   backed up ${dest} -> ${dest}.bak.${STAMP}"
    fi
    ln -sfn "$src" "$dest"
    echo "   ${c_green}linked${c_reset} ${dest}"
}

echo "Installing dotfiles from ${DOTFILES}"

link "${DOTFILES}/.zshrc"        "${HOME}/.zshrc"
link "${DOTFILES}/.tmux.conf"    "${HOME}/.tmux.conf"
link "${DOTFILES}/.gitconfig"    "${HOME}/.gitconfig"
link "${DOTFILES}/nvim/init.lua" "${HOME}/.config/nvim/init.lua"

echo
echo "${c_green}Done.${c_reset}"
[ "$DRY_RUN" -eq 1 ] && echo "${c_yellow}(dry run — nothing changed)${c_reset}"
echo "Next: set your git identity:"
echo "  git config --global user.name  \"Your Name\""
echo "  git config --global user.email \"you@example.com\""
echo "Built by clavexis — github.com/clavexis"
