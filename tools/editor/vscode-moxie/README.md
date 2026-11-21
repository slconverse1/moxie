# Moxie for VS Code

Syntax highlighting for the moxie design language (`.mxi`): keywords, declarations, types, numbers (with width suffixes and durations), strings with `$name` and `${expr}` interpolation, nested `/* */` comments, `///` doc comments, and the operators `->`, `|>`, `...`, `..<`.

To try it, copy this folder to `~/.vscode/extensions/moxie-0.1.0` and restart VS Code. The same `syntaxes/moxie.tmLanguage.json` works in any TextMate-compatible editor (Sublime Text, TextMate) and for GitHub highlighting via linguist.

Status: written against the grammar and the formatter's keyword lists; not yet exercised in a live editor. A language server (checker diagnostics, hover types, format on save) is the next step.
