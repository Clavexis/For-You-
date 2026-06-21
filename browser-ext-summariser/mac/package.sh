#!/usr/bin/env bash
# Package the extension into a zip for upload. Built by clavexis — github.com/clavexis
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
zip -r ../ai-page-summariser.zip manifest.json popup.html popup.js background.js options.html options.js
echo "Created ai-page-summariser.zip"
