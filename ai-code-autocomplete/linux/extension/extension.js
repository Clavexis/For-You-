// Local AI Autocomplete — VS Code extension.
// Registers an inline completion provider that asks the local bridge (server.py)
// for a suggestion based on the text around the cursor. Tab accepts it.
//
// Built by clavexis — github.com/clavexis

const vscode = require("vscode");
const http = require("http");

function postJSON(endpoint, body) {
  return new Promise((resolve, reject) => {
    const url = new URL(endpoint);
    const data = JSON.stringify(body);
    const req = http.request(
      {
        hostname: url.hostname,
        port: url.port,
        path: url.pathname,
        method: "POST",
        headers: { "Content-Type": "application/json", "Content-Length": Buffer.byteLength(data) },
        timeout: 8000,
      },
      (res) => {
        let chunks = "";
        res.on("data", (c) => (chunks += c));
        res.on("end", () => {
          try {
            resolve(JSON.parse(chunks));
          } catch (e) {
            reject(e);
          }
        });
      }
    );
    req.on("error", reject);
    req.on("timeout", () => req.destroy(new Error("timeout")));
    req.write(data);
    req.end();
  });
}

function activate(context) {
  const provider = {
    async provideInlineCompletionItems(document, position) {
      const cfg = vscode.workspace.getConfiguration("localAiAutocomplete");
      const languages = cfg.get("languages");
      if (!languages.includes(document.languageId)) {
        return { items: [] };
      }

      // Build prefix (before cursor) and suffix (after cursor), bounded for speed.
      const offset = document.offsetAt(position);
      const fullText = document.getText();
      const prefix = fullText.slice(Math.max(0, offset - 2000), offset);
      const suffix = fullText.slice(offset, offset + 1000);

      try {
        const res = await postJSON(cfg.get("endpoint"), {
          prefix,
          suffix,
          language: document.languageId,
        });
        const completion = (res && res.completion) || "";
        if (!completion.trim()) {
          return { items: [] };
        }
        return {
          items: [
            {
              insertText: completion,
              range: new vscode.Range(position, position),
            },
          ],
        };
      } catch (err) {
        // Silent on errors so typing is never interrupted.
        return { items: [] };
      }
    },
  };

  context.subscriptions.push(
    vscode.languages.registerInlineCompletionItemProvider({ pattern: "**" }, provider)
  );

  vscode.window.setStatusBarMessage("Local AI Autocomplete active", 3000);
}

function deactivate() {}

module.exports = { activate, deactivate };
