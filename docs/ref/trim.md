---
layout: default
toc: true
terms: true
title: "trim · moxie function"
---

# `trim`

<p class="specref"><a href="../reference.html#fn-trim">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn trim(s String) String
```

## Description {#description}

Removes white space (spaces, tabs and line ends) from both ends of a `String`. White space inside is kept.

**Parameters**

- `s`: a `String`.

**Returns** the trimmed `String`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> trim("  a b  ")
"a b"
```

