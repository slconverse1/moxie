// Starts `python3 -m moxie lsp` and connects VS Code to it: diagnostics as you type, Format Document, and the outline.
const vscode = require("vscode");
const { LanguageClient } = require("vscode-languageclient/node");

let client;

function activate() {
  const cfg = vscode.workspace.getConfiguration("moxie");
  const args = ["-m", "moxie"].concat(cfg.get("gc") ? ["--gc"] : [], ["lsp"]);
  const options = cfg.get("cwd") ? { cwd: cfg.get("cwd"), env: Object.assign({}, process.env, { PYTHONPATH: cfg.get("cwd") }) } : {};
  const run = { command: cfg.get("command"), args, options };
  client = new LanguageClient("moxie", "Moxie", { run, debug: run }, { documentSelector: [{ scheme: "file", language: "moxie" }] });
  client.start();
}

function deactivate() {
  return client ? client.stop() : undefined;
}

module.exports = { activate, deactivate };
