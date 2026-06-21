# Dotfiles

A complete, well-commented personal configuration — Neovim, tmux, zsh, and git — with a one-command symlink installer. Works across Linux and macOS (and Neovim/git on Windows).

## What's inside

| File | What it configures |
|------|--------------------|
| `nvim/init.lua` | Neovim with **lazy.nvim**, LSP (mason + lspconfig), Treesitter, Telescope, tokyonight theme, lualine |
| `.tmux.conf` | tmux: `Ctrl-a` prefix, mouse, vi keys, intuitive splits, a clean status bar |
| `.zshrc` | zsh: oh-my-zsh + plugins, handy aliases, a fast fallback prompt |
| `.gitconfig` | git: sensible defaults and aliases (`lg`, `st`, `co`, …) |

Every file is heavily commented so you can read and tweak it.

## Install

The installer **symlinks** the configs into your home directory (so edits in this repo take effect immediately) and **backs up** any existing files first.

### Linux & macOS
```bash
cd linux   # (or: cd mac)
./install.sh --dry-run     # preview what it will link
./install.sh               # symlink everything
```

### Windows
```powershell
cd windows
.\install.ps1              # symlinks Neovim + git config (run elevated or in Dev Mode)
# For tmux & zsh, use WSL and run linux/install.sh inside it.
```

## Highlights

### Neovim
- `<leader>ff` find files, `<leader>fg` live grep, `<leader>fb` buffers (Telescope)
- `gd` go-to-definition, `K` hover, `<leader>rn` rename, `<leader>ca` code action (LSP)
- Plugins and language servers install automatically on first launch.

### tmux
- Prefix is `Ctrl-a`; `|` and `-` split panes; `prefix r` reloads the config.
- `prefix h/j/k/l` to move between panes.

### zsh
- Aliases: `ll`, `gs`, `gc`, `gl`, `v` (nvim), and more.
- Works with or without oh-my-zsh (includes a minimal built-in prompt fallback).

## After installing

Set your git identity:
```bash
git config --global user.name  "Your Name"
git config --global user.email "you@example.com"
```
Make zsh your shell: `chsh -s $(which zsh)`.

> Tip: pair this with the **auto-setup script** project to install the tools
> (neovim, tmux, zsh, oh-my-zsh) these dotfiles expect.

## Tech stack

- **Lua** (Neovim), **Bash** (installer), and plain config files
- lazy.nvim, mason, nvim-lspconfig, nvim-treesitter, telescope.nvim, tokyonight, lualine

---

Built by clavexis — [github.com/clavexis](https://github.com/clavexis)
