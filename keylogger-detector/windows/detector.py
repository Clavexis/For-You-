#!/usr/bin/env python3
"""
Keylogger Detector — scan your system for signs of an active keylogger.

Platform-specific checks:
  Linux   — processes with open file descriptors on /dev/input/event* devices
            (how most Linux keyloggers read keystrokes), plus suspicious names.
  macOS   — Launch Agents / Daemons whose programs look like input monitors.
  Windows — autostart (Run) registry entries and suspicious process names.

This is a defensive / educational tool. A match is a *signal* to investigate,
not proof of malware — legitimate software (remote desktops, accessibility
tools, some games) can also read input devices.

Usage:
  detector.py            # scan and print a report
  detector.py --json     # machine-readable output

Built by clavexis — github.com/clavexis
"""

import argparse
import json
import os
import platform
import re
import sys


class C:
    RESET = "\033[0m"; BOLD = "\033[1m"; DIM = "\033[2m"
    GREEN = "\033[32m"; YELLOW = "\033[33m"; RED = "\033[31m"; CYAN = "\033[36m"

    @classmethod
    def off(cls):
        for n in ("RESET", "BOLD", "DIM", "GREEN", "YELLOW", "RED", "CYAN"):
            setattr(cls, n, "")


if not sys.stdout.isatty() or os.environ.get("NO_COLOR"):
    C.off()


# Process names that are commonly associated with keyloggers / input grabbing.
SUSPICIOUS_NAMES = [
    "keylog", "klog", "logkeys", "lkl", "pykeylogger", "spyrix",
    "refog", "actualspy", "ardamax", "hook",
]


# ---------------------------------------------------------------------------
# Linux: inspect /proc for processes reading input devices.
# ---------------------------------------------------------------------------
def scan_linux() -> list:
    findings = []
    if not os.path.isdir("/proc"):
        return findings
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        # Process name / command line.
        name = ""
        cmdline = ""
        try:
            with open(f"/proc/{pid}/comm") as f:
                name = f.read().strip()
            with open(f"/proc/{pid}/cmdline", "rb") as f:
                cmdline = f.read().replace(b"\x00", b" ").decode("utf-8", "ignore").strip()
        except OSError:
            continue

        reasons = []

        # Check open file descriptors for /dev/input/event* (keystroke source).
        fd_dir = f"/proc/{pid}/fd"
        try:
            for fd in os.listdir(fd_dir):
                try:
                    target = os.readlink(os.path.join(fd_dir, fd))
                except OSError:
                    continue
                if re.match(r"/dev/input/event\d+", target):
                    reasons.append(f"open fd on input device {target}")
        except OSError:
            pass

        # Check for a suspicious name.
        haystack = (name + " " + cmdline).lower()
        for s in SUSPICIOUS_NAMES:
            if s in haystack:
                reasons.append(f"suspicious name keyword '{s}'")

        if reasons:
            findings.append({"pid": int(pid), "name": name or "?",
                             "cmdline": cmdline[:120], "reasons": reasons})
    return findings


# ---------------------------------------------------------------------------
# macOS: scan Launch Agents / Daemons.
# ---------------------------------------------------------------------------
def scan_macos() -> list:
    findings = []
    dirs = [
        os.path.expanduser("~/Library/LaunchAgents"),
        "/Library/LaunchAgents",
        "/Library/LaunchDaemons",
    ]
    keywords = SUSPICIOUS_NAMES + ["eventtap", "cgevent", "inputmonitor"]
    for d in dirs:
        if not os.path.isdir(d):
            continue
        for fn in os.listdir(d):
            if not fn.endswith(".plist"):
                continue
            path = os.path.join(d, fn)
            try:
                with open(path, "r", errors="ignore") as f:
                    content = f.read().lower()
            except OSError:
                continue
            reasons = [f"keyword '{k}' in plist" for k in keywords if k in content]
            if reasons:
                findings.append({"plist": path, "reasons": reasons})
    return findings


# ---------------------------------------------------------------------------
# Windows: autostart registry entries.
# ---------------------------------------------------------------------------
def scan_windows() -> list:
    findings = []
    try:
        import winreg
    except ImportError:
        return findings
    run_keys = [
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
    ]
    for hive, subkey in run_keys:
        try:
            key = winreg.OpenKey(hive, subkey)
        except OSError:
            continue
        i = 0
        while True:
            try:
                name, value, _ = winreg.EnumValue(key, i)
            except OSError:
                break
            i += 1
            haystack = (str(name) + " " + str(value)).lower()
            reasons = [f"suspicious keyword '{s}'" for s in SUSPICIOUS_NAMES if s in haystack]
            if reasons:
                findings.append({"autostart": name, "command": str(value),
                                 "hive": "HKCU" if hive == winreg.HKEY_CURRENT_USER else "HKLM",
                                 "reasons": reasons})
        winreg.CloseKey(key)
    return findings


def scan() -> dict:
    system = platform.system()
    if system == "Linux":
        findings = scan_linux()
    elif system == "Darwin":
        findings = scan_macos()
    elif system == "Windows":
        findings = scan_windows()
    else:
        findings = []
    return {"platform": system, "findings": findings}


def print_report(result: dict):
    print(f"{C.CYAN}{C.BOLD}Keylogger Detector — {result['platform']} scan{C.RESET}")
    findings = result["findings"]
    if not findings:
        print(f"{C.GREEN}✓ No suspicious keyboard-hook activity detected.{C.RESET}")
        print(f"{C.DIM}(A clean result is not a guarantee — sophisticated tools can hide.){C.RESET}")
        return
    print(f"{C.RED}⚠ {len(findings)} item(s) worth investigating:{C.RESET}\n")
    for f in findings:
        if "pid" in f:
            print(f"  {C.YELLOW}PID {f['pid']}{C.RESET} {C.BOLD}{f['name']}{C.RESET}")
            if f["cmdline"]:
                print(f"    {C.DIM}{f['cmdline']}{C.RESET}")
        elif "plist" in f:
            print(f"  {C.YELLOW}{f['plist']}{C.RESET}")
        elif "autostart" in f:
            print(f"  {C.YELLOW}[{f['hive']}] {f['autostart']}{C.RESET} -> {f['command']}")
        for r in f["reasons"]:
            print(f"    {C.RED}•{C.RESET} {r}")
    print(f"\n{C.DIM}Investigate these processes/entries. Legitimate software "
          f"(remote desktop, accessibility, some games) may also appear.{C.RESET}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Scan for signs of an active keylogger.")
    ap.add_argument("--json", action="store_true", help="Machine-readable output.")
    args = ap.parse_args()

    result = scan()
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print_report(result)
    # Non-zero exit if anything was flagged (handy for monitoring).
    return 1 if result["findings"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
