<#
.SYNOPSIS
  Windows Auto-Setup — set up a full development environment with one command.

.DESCRIPTION
  Installs (via winget): git, neovim, tmux (WSL), zsh (WSL), docker, python,
  node, rust, go. Configures git. Use -DryRun to preview.

.EXAMPLE
  .\setup.ps1
  .\setup.ps1 -DryRun
  .\setup.ps1 -Minimal

  Built by clavexis - github.com/clavexis
#>
param(
    [switch]$DryRun,
    [switch]$Minimal
)

function Info($msg) { Write-Host "==> $msg" -ForegroundColor Blue }
function Ok($msg)   { Write-Host " ok $msg" -ForegroundColor Green }
function Warn($msg) { Write-Host " !  $msg" -ForegroundColor Yellow }

function Run-Cmd($cmd) {
    if ($DryRun) { Write-Host "   [dry-run] $cmd" -ForegroundColor Yellow }
    else { Write-Host "   + $cmd"; Invoke-Expression $cmd }
}

# --- ensure winget --------------------------------------------------------
if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    Warn "winget not found. Install 'App Installer' from the Microsoft Store, then re-run."
    if (-not $DryRun) { exit 1 }
}

function Install-Pkg($id, $name) {
    Info "Installing $name"
    Run-Cmd "winget install --id $id -e --accept-source-agreements --accept-package-agreements"
}

# winget package IDs
$core = @(
    @{ id = "Git.Git";              name = "git" },
    @{ id = "Neovim.Neovim";        name = "neovim" },
    @{ id = "Microsoft.PowerShell"; name = "PowerShell 7" }
)
$extra = @(
    @{ id = "Python.Python.3.12"; name = "python" },
    @{ id = "OpenJS.NodeJS";      name = "node" },
    @{ id = "Rustlang.Rustup";    name = "rust" },
    @{ id = "GoLang.Go";          name = "go" },
    @{ id = "Docker.DockerDesktop"; name = "docker" }
)

foreach ($p in $core) { Install-Pkg $p.id $p.name }
if (-not $Minimal) { foreach ($p in $extra) { Install-Pkg $p.id $p.name } }

# tmux and zsh are Unix tools — recommend WSL.
Info "tmux & zsh: best used via WSL"
Run-Cmd "wsl --install -d Ubuntu"

# --- git config -----------------------------------------------------------
Info "Configuring git"
if ($DryRun) {
    Write-Host "   [dry-run] would prompt for git user.name / user.email" -ForegroundColor Yellow
} else {
    $existing = (& git config --global user.name) 2>$null
    if (-not $existing) {
        $name  = Read-Host "   git user.name"
        $email = Read-Host "   git user.email"
        git config --global user.name $name
        git config --global user.email $email
    }
    git config --global init.defaultBranch main
    git config --global alias.lg "log --oneline --graph --decorate"
    Ok "git configured"
}

Write-Host ""
Ok "Setup complete!"
if ($DryRun) { Warn "Dry run - nothing was changed." }
Write-Host "   Built by clavexis - github.com/clavexis"
