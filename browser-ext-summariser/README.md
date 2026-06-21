# Browser Extension — AI Page Summariser

One click to get an AI summary of any webpage, shown in a popup with a copy button. Works in **Chrome and Firefox** (Manifest V3), powered by Claude.

## Demo

```text
┌──────────────────────────────┐
│ 📄 AI Page Summariser        │
│ [ Summarise this page ] [Copy]│
│ ┌──────────────────────────┐ │
│ │ • The article argues...  │ │
│ │ • Key point two...       │ │
│ │ • Finally, it concludes… │ │
│ └──────────────────────────┘ │
└──────────────────────────────┘
```

## Features

- **One-click summary** — extracts the page's main text and summarises it.
- **Works in Chrome & Firefox** — single Manifest V3 codebase.
- **Popup UI** with a summary panel and a **Copy to clipboard** button.
- **Smart extraction** — prefers `<article>`/`<main>` content, falls back to the body.
- **Local key storage** — your Anthropic API key lives in `storage.local`, sent only to api.anthropic.com.

## Install (load unpacked)

The extension files are identical on every platform — pick the folder for your OS (`linux/`, `mac/`, or `windows/`); they all contain the same extension.

### Chrome / Edge / Brave
1. Go to `chrome://extensions`.
2. Enable **Developer mode** (top right).
3. Click **Load unpacked** and select the `linux/` (or `mac/`/`windows/`) folder.
4. Click the extension's **Details → Extension options** and paste your Anthropic API key.

### Firefox
1. Go to `about:debugging#/runtime/this-firefox`.
2. Click **Load Temporary Add-on…** and select `manifest.json` in the platform folder.
3. Open the extension's options and add your API key.

Get an API key at [console.anthropic.com](https://console.anthropic.com/).

## Usage

1. Navigate to any article or page.
2. Click the extension icon.
3. Hit **Summarise this page** — the summary appears in a few seconds.
4. Click **Copy** to put it on your clipboard.

## How it works

```text
popup → scripting.executeScript (extract page text)
      → background service worker → fetch api.anthropic.com (Claude)
      → summary back to popup → displayed + copyable
```

The API call is made from the background service worker with the
`anthropic-dangerous-direct-browser-access` header and a `host_permissions`
grant for `api.anthropic.com`, so it works without a proxy server.

## Packaging

```bash
cd linux && ./package.sh        # creates ai-page-summariser.zip for the web stores
```

## Tech stack

- **JavaScript**, Manifest V3 (Chrome + Firefox)
- Service worker, `chrome.scripting`, `chrome.storage`
- Claude API (`claude-opus-4-8`)

---

Built by clavexis — [github.com/clavexis](https://github.com/clavexis)
