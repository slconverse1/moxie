# Moxie for VS Code

Syntax highlighting for the moxie design language (`.mxi`): keywords, declarations, types, numbers (with width suffixes and durations), strings with `$name` and `${expr}` interpolation, nested `/* */` comments, `///` doc comments, and the operators `->`, `|>`, `...`, `..<`.

To try it, copy this folder to `~/.vscode/extensions/moxie-0.1.0` and restart VS Code. The same `syntaxes/moxie.tmLanguage.json` works in any TextMate-compatible editor (Sublime Text, TextMate) and for GitHub highlighting via linguist.

## Language server

`extension.js` starts the moxie language server (`python3 -m moxie lsp`) and gives you the errors and warnings of `moxie check` as you type, **Format Document** (the `moxie fmt` layout), and the outline and "Go to Symbol". Run `npm install` in this folder once (it fetches `vscode-languageclient`). The server needs the moxie package: set `moxie.cwd` to the repository folder if moxie is not on your Python path, and tick `moxie.gc` for the moxie/gc rules. The server itself is tested by `tests/run_lsp.py`; this client has not been run in a live VS Code.

Not yet: hover types, completion, and go to definition.
