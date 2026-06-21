# Keylogger Detector

Scan your system for signs of an active keylogger — pure Python, no dependencies. A **defensive / educational** tool that surfaces processes and autostart entries worth investigating.

## Demo

```text
Keylogger Detector — Linux scan
⚠ 1 item(s) worth investigating:

  PID 4821 logkeys
    /usr/bin/logkeys --start --output /tmp/log.txt
    • open fd on input device /dev/input/event3
    • suspicious name keyword 'logkeys'

Investigate these processes/entries. Legitimate software (remote desktop,
accessibility, some games) may also appear.
```

A clean system prints:
```text
✓ No suspicious keyboard-hook activity detected.
```

## How it detects keyloggers

| Platform | Check |
|----------|-------|
| **Linux** | Processes with open file descriptors on `/dev/input/event*` (how Linux keyloggers read keystrokes), via `/proc/<pid>/fd`, plus suspicious process names. |
| **macOS** | Launch Agents / Daemons (`~/Library/LaunchAgents`, `/Library/LaunchAgents`, `/Library/LaunchDaemons`) whose plists reference input monitoring (`eventtap`, `CGEvent`, …). |
| **Windows** | Autostart entries in the `Run` registry keys (HKCU/HKLM) with suspicious names/commands. |

## Features

- **Platform-aware** — runs the right checks for your OS automatically.
- **Reads the actual keystroke source** on Linux (`/dev/input/event*` fds) — the most reliable signal.
- **Clean report** with the process/entry and *why* it was flagged.
- **`--json`** output for monitoring/automation; **exit code 1** when anything is flagged.

## Installation

Requires only **Python 3.6+** — no dependencies.

### Linux
```bash
cd linux && ./install.sh
keylogger-detector
```

### macOS (Apple Silicon & Intel)
```bash
cd mac && ./install.sh
keylogger-detector
```

### Windows
```powershell
cd windows
python detector.py
```

## Usage

```bash
keylogger-detector           # human-readable report
keylogger-detector --json    # machine-readable

# In a monitoring cron job (non-zero exit = something flagged):
keylogger-detector --json || alert "possible keylogger"
```

> ⚠️ **A match is a signal, not a verdict.** Legitimate software (remote desktop tools, accessibility software, some games, the desktop environment itself) also reads input devices. Investigate flagged items — don't blindly kill them. Likewise, a clean result is not a guarantee; advanced rootkits can hide.

## Tech stack

- **Python 3** standard library (`/proc` inspection, `winreg`, plist scanning)
- Zero dependencies, single file, cross-platform dispatch

---

Built by clavexis — [github.com/clavexis](https://github.com/clavexis)
