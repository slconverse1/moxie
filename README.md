# moxie

Moxie is a language-design exercise: (mostly) compile-time type-safe, immutable, practical functional programming, Go-style channels and fibers, and, in the plain dialect, no garbage collector and no heap. A second dialect, moxie/gc, adds a collector; the two are kept apart because they make different promises. This repository holds the language documents and a reference interpreter written in plain Python 3.

- **Site:** https://slconverse1.github.io/moxie/ (the Site Intro, Tutorial, Mixer's Guide, Spec, and an in-browser "Try moxie" page)
- **`docs/`** the documents, as the site's source: `index.md` (Site Intro), `tutorial.md`, `guide.md`, `spec.md`, and `gc/` for moxie/gc, the garbage-collected dialect (its Site Intro, Spec, and Guide)
- **`moxie/`** the reference interpreter (standard library only)
- **`examples/`**, **`tests/`**, **`INTERPRETER.md`**, **`FIXLIST.md`** the interpreter's samples, tests, notes, and a list of problems found in the Spec and Guide

## Run a program

    git clone https://github.com/slconverse1/moxie
    cd moxie
    python3 -m moxie run examples/gradebook.mxi
    python3 -m moxie test examples/gradebook.mxi

The interpreter needs Python 3.11 or later (tested on 3.11, 3.12, and 3.13) and nothing else. `INTERPRETER.md` lists what it checks and what it doesn't yet.

## License

MIT. See `LICENSE`. It covers the interpreter and the documents.
