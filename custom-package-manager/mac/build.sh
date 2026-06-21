#!/usr/bin/env bash
# Build clawpkg on macOS. Built by clavexis — github.com/clavexis
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
cargo build --release
echo "Built target/release/clawpkg — try: ./target/release/clawpkg install leftpad"
