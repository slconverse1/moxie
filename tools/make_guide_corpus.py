"""Rebuild a frozen Guide corpus (tests/guide_corpus.json or tests/gc_guide_corpus.json) from the live Guide.

Each entry is [line, source, expected output lines or None]: every fenced block of the Guide, and the lines named by the
`Output: ...` sentence that follows it (each backticked piece is one line; the sentence ends at the first period outside
backticks). A block with no such sentence has None.

A block that is already in the old corpus keeps its old expected lines (those were checked by hand), so a rebuild only adds
or changes entries for blocks that are new or were edited.

Run: python3 tools/make_guide_corpus.py docs/guide.md tests/guide_corpus.json   (or docs/gc/guide.md tests/gc_guide_corpus.json)
The output file, if it exists, is the old corpus.
"""
import json, os, re, sys


def expected(lines, k):
    while k < len(lines) and lines[k].strip() == "":
        k += 1
    if k >= len(lines) or not lines[k].startswith("Output:"):
        return None
    text, out, i, inside, cur = lines[k][len("Output:"):], [], 0, False, ""
    while i < len(text):
        ch = text[i]
        if ch == "`":
            if inside:
                out.append(cur)
                cur = ""
            inside = not inside
        elif inside:
            cur += ch
        elif not inside and ch != "`":
            # between pieces only a connector may stand (`a`, then `b`); any other prose ends the list
            m = re.match(r"(,? ?(then|and)?,? ?)(?=`)", text[i:])
            if m and m.group(0).strip(" ,") in ("", "then", "and"):
                i += len(m.group(0)) - 1
            else:
                break
        i += 1
    return out or None


def build(path):
    lines = open(path).read().split("\n")
    blocks, i = [], 0
    while i < len(lines):
        if lines[i].startswith("```"):
            j = i + 1
            while j < len(lines) and not lines[j].startswith("```"):
                j += 1
            blocks.append([i + 2, "\n".join(lines[i + 1:j]) + "\n", expected(lines, j + 1)])
            i = j + 1
        else:
            i += 1
    return blocks


if __name__ == "__main__":
    blocks = build(sys.argv[1])
    kept = 0
    if os.path.exists(sys.argv[2]):
        old = {b[1].strip(): b[2] for b in json.load(open(sys.argv[2]))}
        for b in blocks:
            if b[1].strip() in old:
                b[2] = old[b[1].strip()]
                kept += 1
    json.dump(blocks, open(sys.argv[2], "w"), indent=0)
    print(len(blocks), "blocks,", kept, "keep their old expected lines")
