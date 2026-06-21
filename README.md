# clavexis — 100 Projects (40 complete)

A growing collection of **production-quality, from-scratch open-source projects**, each built for **Windows, Linux, and macOS**. Every project is self-contained in its own folder with platform subfolders (`windows/ linux/ mac/`), an individual `README.md` (demo, features, per-OS install, usage, tech stack), a `LICENSE`, and a `.gitignore`. Most run with no third-party dependencies and ship with built-in self-tests.

> **40 of 100 complete.** This folder contains the finished projects, ready to clone and run.

Built by **clavexis** — [github.com/clavexis](https://github.com/clavexis)

---

## How to use this repo

Each project is independent. Pick one, open its folder, read its `README.md`, and follow the install steps for your OS. For example:

```bash
# Python projects (no dependencies, pure standard library):
cd torrent-client/linux && ./install.sh

# C++ projects (need a compiler):
cd cpu-emulator/linux && ./build.sh && ./chip8 --test
```

Projects with a `test` / `--test` command can be verified instantly after building.

---

## The projects

| # | Project | What it is | Language |
|---|---------|-----------|----------|
| 1 | [ai-terminal-assistant](ai-terminal-assistant) | Chat with an LLM from your shell, with streaming + history | Python |
| 2 | [warzone-ai-coach](warzone-ai-coach) | Analyses Warzone stats and gives AI coaching tips | Python |
| 3 | [auto-code-reviewer](auto-code-reviewer) | AI code review with bug/style/security findings | Python |
| 4 | [voice-to-code](voice-to-code) | Speak an idea, get working code back (Whisper + LLM) | Python |
| 5 | [chess-engine](chess-engine) | Full chess engine with minimax + alpha-beta, no libs | C++ |
| 6 | [tiny-os-kernel](tiny-os-kernel) | Minimal x86 multiboot kernel that boots and prints | C + ASM |
| 7 | [custom-language](custom-language) | "Claw" — a tree-walking interpreted language | C++ |
| 8 | [http-server-cpp](http-server-cpp) | HTTP/1.1 server from raw sockets, multithreaded | C++ |
| 9 | [ai-chess-terminal](ai-chess-terminal) | Play chess vs minimax AI in the terminal | Python |
| 10 | [discord-ai-bot](discord-ai-bot) | Discord bot with AI chat, slash commands, moderation | Python |
| 11 | [linux-auto-setup](linux-auto-setup) | One-command dev-environment installer | Bash + PowerShell |
| 12 | [dotfiles](dotfiles) | Neovim/tmux/zsh/git config with symlink installer | Lua + Bash |
| 13 | [ai-thumbnail-generator](ai-thumbnail-generator) | Title → 1280×720 YouTube thumbnail | Python |
| 14 | [realtime-code-collab](realtime-code-collab) | Real-time collaborative editor over WebSockets | Python |
| 15 | [malware-scanner-ai](malware-scanner-ai) | Static analysis + AI risk opinion (metadata only) | Python |
| 16 | [ai-resume-builder](ai-resume-builder) | Tailor a resume to a job description with AI | Python |
| 17 | [packet-sniffer](packet-sniffer) | Capture + decode Ethernet/IP/TCP/UDP, pcap export | C + Python |
| 18 | [gpu-ray-tracer](gpu-ray-tracer) | Software ray tracer → PNG, shadows + reflections | C++ |
| 19 | [browser-ext-summariser](browser-ext-summariser) | One-click AI page summary (Chrome + Firefox) | JavaScript |
| 20 | [terminal-music-player](terminal-music-player) | Control Spotify from the terminal | Python |
| 21 | [ai-dungeon-game](ai-dungeon-game) | Text RPG with AI-generated story + combat | Python |
| 22 | [keylogger-detector](keylogger-detector) | Scans a system for active keyloggers | Python |
| 23 | [p2p-file-sharing](p2p-file-sharing) | Encrypted peer-to-peer file transfer | Python |
| 24 | [screen-recorder-cli](screen-recorder-cli) | Record your screen from the CLI (ffmpeg) | Python |
| 25 | [ai-code-autocomplete](ai-code-autocomplete) | Local offline code autocomplete (Ollama + VS Code) | Python + JS |
| 26 | [custom-package-manager](custom-package-manager) | `clawpkg` — install/resolve/lock packages | Rust |
| 27 | [warzone-clip-highlighter](warzone-clip-highlighter) | Auto-cut highlight reels from gameplay | Python |
| 28 | [neural-network-scratch](neural-network-scratch) | Neural net with backprop, pure math, no ML libs | C++ |
| 29 | [ai-commit-writer](ai-commit-writer) | Turn a git diff into a conventional commit message | Python |
| 30 | [multiplayer-game-cpp](multiplayer-game-cpp) | Real-time LAN multiplayer over UDP | C++ |
| 31 | [password-manager](password-manager) | AES-256 vault with PBKDF2 master password | Python |
| 32 | [dns-resolver](dns-resolver) | DNS resolver from raw UDP (A/AAAA/MX/CNAME/NS) | C |
| 33 | [git-clone-scratch](git-clone-scratch) | `mygit` — git's object model, hash-compatible | Python |
| 34 | [sql-database-engine](sql-database-engine) | SQL engine: CREATE/INSERT/SELECT/WHERE, B-tree | C |
| 35 | [file-compression-tool](file-compression-tool) | Huffman-coding compressor/decompressor | C++ |
| 36 | [aes-encryption-tool](aes-encryption-tool) | AES-256 from scratch, FIPS-197 verified, CBC | C++ |
| 37 | [torrent-client](torrent-client) | `clawtorrent` — BitTorrent: bencode, trackers, peers | Python |
| 38 | [terminal-web-browser](terminal-web-browser) | `clawbrowse` — browse the web as readable text | Python |
| 39 | [code-formatter-linter](code-formatter-linter) | `clawfmt` — multi-language formatter + linter | Python |
| 40 | [cpu-emulator](cpu-emulator) | `chip8` — full CHIP-8 virtual machine in the terminal | C++ |

---

## Highlights

- **From scratch, on purpose.** The HTTP server, DNS resolver, AES cipher, git, the SQL engine, the BitTorrent client and the CHIP-8 CPU are all built without the libraries that would normally do the work — so the code shows *how* these systems actually function.
- **Cross-platform.** Every project has `windows/`, `linux/` and `mac/` builds with matching install/build scripts.
- **Tested.** Most projects include a self-test command (e.g. `--test` or a `test` subcommand) that verifies the core logic offline.
- **Readable.** Consistent style and commenting across the whole collection — they all belong to the same developer.

## License

Every project is released under the **Clavexis Non-Commercial Attribution License** (see each project's `LICENSE`): free to use, study, and modify for personal and educational purposes; **no commercial/for-profit use** without permission; credit the author if shared publicly.

---

Built by clavexis — [github.com/clavexis](https://github.com/clavexis)
