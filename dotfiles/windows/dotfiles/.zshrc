# ~/.zshrc — zsh configuration
# Built by clavexis — github.com/clavexis

export ZSH="$HOME/.oh-my-zsh"
ZSH_THEME="robbyrussell"

# Plugins (install via the dotfiles installer / auto-setup script)
plugins=(git zsh-autosuggestions zsh-syntax-highlighting)

[ -f "$ZSH/oh-my-zsh.sh" ] && source "$ZSH/oh-my-zsh.sh"

# --- aliases --------------------------------------------------------------
alias ll='ls -lah'
alias la='ls -A'
alias ..='cd ..'
alias ...='cd ../..'
alias gs='git status'
alias gc='git commit'
alias gco='git checkout'
alias gp='git push'
alias gl='git log --oneline --graph --decorate'
alias v='nvim'
alias please='sudo $(fc -ln -1)'   # re-run last command with sudo

# --- environment ----------------------------------------------------------
export EDITOR='nvim'
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

# Fast directory jumping
setopt AUTO_CD
setopt HIST_IGNORE_DUPS
HISTSIZE=10000
SAVEHIST=10000

# A minimal, fast prompt if oh-my-zsh is not present
if [ ! -f "$ZSH/oh-my-zsh.sh" ]; then
  autoload -Uz vcs_info
  precmd() { vcs_info }
  zstyle ':vcs_info:git:*' formats ' (%b)'
  setopt PROMPT_SUBST
  PROMPT='%F{green}%n@%m%f %F{blue}%~%f%F{yellow}${vcs_info_msg_0_}%f $ '
fi
