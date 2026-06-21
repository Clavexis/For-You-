# Dotfiles installer (Windows). Built by clavexis - github.com/clavexis
# Creates symlinks for Neovim/git config. tmux & zsh are best used via WSL.
# Run in an elevated PowerShell, or enable Developer Mode for symlinks.
param([switch]$DryRun)

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$dot  = Join-Path $root "dotfiles"

function Link($src, $dest) {
    if ($DryRun) { Write-Host "   [dry-run] link $dest -> $src" -ForegroundColor Yellow; return }
    $parent = Split-Path -Parent $dest
    if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
    if (Test-Path $dest) { Move-Item $dest "$dest.bak" -Force }
    New-Item -ItemType SymbolicLink -Path $dest -Target $src -Force | Out-Null
    Write-Host "   linked $dest" -ForegroundColor Green
}

Write-Host "Installing dotfiles from $dot"
Link (Join-Path $dot "nvim\init.lua") "$env:LOCALAPPDATA\nvim\init.lua"
Link (Join-Path $dot ".gitconfig")    "$env:USERPROFILE\.gitconfig"
Write-Host "`nDone. For tmux & zsh, use WSL and run linux/install.sh inside it."
Write-Host "Built by clavexis - github.com/clavexis"
