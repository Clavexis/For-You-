// options.js — save/load the API key. Built by clavexis — github.com/clavexis
const api = typeof browser !== "undefined" ? browser : chrome;

const keyInput = document.getElementById("key");
const status = document.getElementById("status");

// Load any existing key on open.
api.storage.local.get("apiKey").then(({ apiKey }) => {
  if (apiKey) keyInput.value = apiKey;
});

document.getElementById("save").addEventListener("click", async () => {
  const apiKey = keyInput.value.trim();
  await api.storage.local.set({ apiKey });
  status.textContent = apiKey ? "Saved ✓" : "Cleared.";
  setTimeout(() => (status.textContent = ""), 1500);
});
