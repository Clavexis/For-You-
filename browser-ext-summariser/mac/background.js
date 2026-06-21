// background.js — service worker that calls the Claude API.
// Keeping the API call here (not in the popup) means the key is only read in
// the extension's background context.
// Built by clavexis — github.com/clavexis

const api = typeof browser !== "undefined" ? browser : chrome;
const MODEL = "claude-opus-4-8";

async function summarise(page) {
  const { apiKey } = await api.storage.local.get("apiKey");
  if (!apiKey) {
    return { error: "No API key set. Open the extension options and add your Anthropic API key." };
  }

  const prompt =
    `Summarise the following web page in 4–6 concise bullet points. ` +
    `Title: ${page.title}\nURL: ${page.url}\n\nContent:\n${page.text}`;

  try {
    const res = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "x-api-key": apiKey,
        "anthropic-version": "2023-06-01",
        // Required to allow calling the API directly from a browser context.
        "anthropic-dangerous-direct-browser-access": "true",
      },
      body: JSON.stringify({
        model: MODEL,
        max_tokens: 800,
        system: "You are a helpful assistant that writes clear, faithful summaries.",
        messages: [{ role: "user", content: prompt }],
      }),
    });

    if (!res.ok) {
      const body = await res.text();
      return { error: `API error ${res.status}: ${body.slice(0, 200)}` };
    }
    const data = await res.json();
    const summary = (data.content || [])
      .filter((b) => b.type === "text")
      .map((b) => b.text)
      .join("");
    return { summary: summary || "(empty response)" };
  } catch (err) {
    return { error: "Network error: " + err.message };
  }
}

api.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg.type === "summarise") {
    summarise(msg.page).then(sendResponse);
    return true; // keep the message channel open for the async response
  }
});
