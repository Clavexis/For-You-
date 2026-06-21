// popup.js — drives the summariser popup.
// Built by clavexis — github.com/clavexis

// Cross-browser API handle (Chrome uses `chrome`, Firefox supports `browser`).
const api = typeof browser !== "undefined" ? browser : chrome;

const summariseBtn = document.getElementById("summarise");
const copyBtn = document.getElementById("copy");
const summaryEl = document.getElementById("summary");

document.getElementById("openOptions").addEventListener("click", (e) => {
  e.preventDefault();
  api.runtime.openOptionsPage();
});

// Runs inside the page to extract readable text (truncated to keep tokens sane).
function extractPageText() {
  // Prefer the main/article content if present, else the whole body.
  const main = document.querySelector("article, main") || document.body;
  const text = main.innerText || document.body.innerText || "";
  return {
    title: document.title,
    url: location.href,
    text: text.replace(/\s+/g, " ").trim().slice(0, 12000),
  };
}

summariseBtn.addEventListener("click", async () => {
  summariseBtn.disabled = true;
  copyBtn.disabled = true;
  summaryEl.classList.add("muted");
  summaryEl.textContent = "Extracting page text…";

  try {
    const [tab] = await api.tabs.query({ active: true, currentWindow: true });
    const results = await api.scripting.executeScript({
      target: { tabId: tab.id },
      func: extractPageText,
    });
    const page = results[0].result;
    if (!page.text) {
      throw new Error("Could not read any text from this page.");
    }

    summaryEl.textContent = "Summarising with Claude…";

    // Ask the background service worker to call the API (it holds the key).
    const response = await api.runtime.sendMessage({ type: "summarise", page });
    if (response.error) {
      throw new Error(response.error);
    }
    summaryEl.classList.remove("muted");
    summaryEl.textContent = response.summary;
    copyBtn.disabled = false;
  } catch (err) {
    summaryEl.classList.remove("muted");
    summaryEl.textContent = "⚠️ " + err.message;
  } finally {
    summariseBtn.disabled = false;
  }
});

copyBtn.addEventListener("click", async () => {
  await navigator.clipboard.writeText(summaryEl.textContent);
  copyBtn.textContent = "Copied!";
  setTimeout(() => (copyBtn.textContent = "Copy"), 1500);
});
