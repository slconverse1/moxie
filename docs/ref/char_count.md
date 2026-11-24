---
layout: default
toc: true
terms: true
title: "char_count · moxie function"
---

# `char_count`

<p class="specref"><a href="../reference.html#fn-char_count">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn char_count(s String) Int
```

## Description {#description}

How many Unicode code points a `String` has. `len` counts bytes, which is larger for any character outside plain ASCII.

**Parameters**

- `s`: a `String`.

**Returns** an `Int`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> char_count("héllo")
5
```

```
> len("héllo")
6
```

