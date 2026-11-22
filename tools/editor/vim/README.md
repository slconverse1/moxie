# Moxie for vim

Syntax colors, `.mxi` file detection, and 2-space indent for vim (and neovim).

    mkdir -p ~/.vim
    cp -r syntax ftdetect ftplugin ~/.vim/

Then open any `.mxi` file.  If colors do not appear, add `syntax on` and `filetype plugin on` to `~/.vimrc`.
For neovim use `~/.config/nvim/` in place of `~/.vim/`.

Vim's arrow keys work in normal and insert mode.  Inside a terminal, mouse and touch-screen taps work after `:set mouse=a`.

## Language server

`python3 -m moxie lsp` speaks the Language Server Protocol (diagnostics, formatting, outline). With Neovim 0.8 or later:

```lua
vim.api.nvim_create_autocmd("FileType", { pattern = "moxie", callback = function()
  vim.lsp.start({ name = "moxie", cmd = { "python3", "-m", "moxie", "lsp" }, root_dir = vim.fn.getcwd() })
end })
```

Use `["python3", "-m", "moxie", "--gc", "lsp"]` for moxie/gc. Run it from the repository folder, or put the moxie package on `PYTHONPATH`. This setup has not been run in a live editor; the server itself is tested by `tests/run_lsp.py`.
