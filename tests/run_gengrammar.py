"""The grammar from the other side: programs generated from docs/grammar.ebnf are fed to moxie's own parser.
The grammar is looser than the language in places (it is a recognizer, and shapes such as which modifiers go with which
declaration, or where `else` may follow a block, are only partly modeled), so this holds a floor on the share the parser
accepts instead of demanding all of them. Raise GEN_MIN when the grammar gets tighter.
Run: python3 tests/run_gengrammar.py   (tools/gen_from_grammar.py -v lists why the parser refuses the others)"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.argv = [sys.argv[0], "-n", "300", "-s", "7"]
import gen_from_grammar                          # noqa: E402
ok, n = gen_from_grammar.main()
need = float(os.environ.get("GEN_MIN", "0.5"))
sys.exit(0 if ok / n >= need else 1)
