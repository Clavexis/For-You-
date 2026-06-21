-- ~/.config/nvim/init.lua — Neovim configuration
--
-- A clean, modern setup using lazy.nvim for plugin management:
--   * LSP (via mason + nvim-lspconfig)
--   * Treesitter syntax highlighting
--   * Telescope fuzzy finder
--   * tokyonight colourscheme + lualine status line
--
-- Built by clavexis — github.com/clavexis

-- ---------------------------------------------------------------------------
-- Core options
-- ---------------------------------------------------------------------------
vim.g.mapleader = " "                 -- space as the leader key
vim.g.maplocalleader = " "

local opt = vim.opt
opt.number = true                      -- absolute line numbers
opt.relativenumber = true              -- relative numbers for easy motions
opt.expandtab = true                   -- spaces, not tabs
opt.shiftwidth = 4
opt.tabstop = 4
opt.smartindent = true
opt.wrap = false
opt.ignorecase = true                  -- case-insensitive search...
opt.smartcase = true                   -- ...unless the query has capitals
opt.termguicolors = true               -- 24-bit colour
opt.scrolloff = 8                      -- keep 8 lines visible above/below cursor
opt.signcolumn = "yes"
opt.updatetime = 250
opt.clipboard = "unnamedplus"          -- use the system clipboard
opt.undofile = true                    -- persistent undo

-- ---------------------------------------------------------------------------
-- Bootstrap lazy.nvim (auto-installs the plugin manager on first run)
-- ---------------------------------------------------------------------------
local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not vim.loop.fs_stat(lazypath) then
  vim.fn.system({
    "git", "clone", "--filter=blob:none",
    "https://github.com/folke/lazy.nvim.git", "--branch=stable", lazypath,
  })
end
vim.opt.rtp:prepend(lazypath)

-- ---------------------------------------------------------------------------
-- Plugins
-- ---------------------------------------------------------------------------
require("lazy").setup({
  -- Colourscheme
  {
    "folke/tokyonight.nvim",
    lazy = false,
    priority = 1000,
    config = function()
      vim.cmd.colorscheme("tokyonight-night")
    end,
  },

  -- Status line
  {
    "nvim-lualine/lualine.nvim",
    dependencies = { "nvim-tree/nvim-web-devicons" },
    config = function()
      require("lualine").setup({ options = { theme = "tokyonight" } })
    end,
  },

  -- Fuzzy finder
  {
    "nvim-telescope/telescope.nvim",
    branch = "0.1.x",
    dependencies = { "nvim-lua/plenary.nvim" },
    config = function()
      local builtin = require("telescope.builtin")
      vim.keymap.set("n", "<leader>ff", builtin.find_files, { desc = "Find files" })
      vim.keymap.set("n", "<leader>fg", builtin.live_grep,  { desc = "Live grep" })
      vim.keymap.set("n", "<leader>fb", builtin.buffers,    { desc = "Buffers" })
    end,
  },

  -- Treesitter (better syntax highlighting)
  {
    "nvim-treesitter/nvim-treesitter",
    build = ":TSUpdate",
    config = function()
      require("nvim-treesitter.configs").setup({
        ensure_installed = { "lua", "python", "javascript", "c", "cpp", "go", "rust", "bash" },
        highlight = { enable = true },
        indent = { enable = true },
      })
    end,
  },

  -- LSP: mason installs servers, lspconfig wires them up
  { "williamboman/mason.nvim", config = true },
  {
    "williamboman/mason-lspconfig.nvim",
    dependencies = { "neovim/nvim-lspconfig" },
    config = function()
      require("mason-lspconfig").setup({
        ensure_installed = { "lua_ls", "pyright" },
      })
      local lspconfig = require("lspconfig")
      -- Keymaps applied when an LSP attaches to a buffer.
      local on_attach = function(_, bufnr)
        local map = function(keys, fn, desc)
          vim.keymap.set("n", keys, fn, { buffer = bufnr, desc = desc })
        end
        map("gd", vim.lsp.buf.definition,      "Go to definition")
        map("K",  vim.lsp.buf.hover,           "Hover docs")
        map("<leader>rn", vim.lsp.buf.rename,  "Rename symbol")
        map("<leader>ca", vim.lsp.buf.code_action, "Code action")
      end
      for _, server in ipairs({ "lua_ls", "pyright" }) do
        lspconfig[server].setup({ on_attach = on_attach })
      end
    end,
  },
})

-- ---------------------------------------------------------------------------
-- Handy keymaps
-- ---------------------------------------------------------------------------
local map = vim.keymap.set
map("n", "<leader>w", "<cmd>w<cr>", { desc = "Save" })
map("n", "<leader>q", "<cmd>q<cr>", { desc = "Quit" })
map("n", "<Esc>", "<cmd>nohlsearch<cr>", { desc = "Clear search highlight" })
-- Move between splits with Ctrl-h/j/k/l
map("n", "<C-h>", "<C-w>h")
map("n", "<C-j>", "<C-w>j")
map("n", "<C-k>", "<C-w>k")
map("n", "<C-l>", "<C-w>l")
