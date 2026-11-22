# Moxie for vim

Syntax colors, `.mxi` file detection, and 2-space indent for vim (and neovim).

    mkdir -p ~/.vim
    cp -r syntax ftdetect ftplugin ~/.vim/

Then open any `.mxi` file.  If colors do not appear, add `syntax on` and `filetype plugin on` to `~/.vimrc`.
For neovim use `~/.config/nvim/` in place of `~/.vim/`.

Vim's arrow keys work in normal and insert mode.  Inside a terminal, mouse and touch-screen taps work after `:set mouse=a`.
