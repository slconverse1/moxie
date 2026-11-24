---
layout: default
toc: true
terms: true
dialect: gc
title: "days_in_month · moxie/gc function"
---

# `days_in_month`

<p class="specref"><a href="../reference.html#fn-days_in_month">The alphabetical list</a> · <a href="../spec.html#s19e">Spec §19e</a></p>

## Signature {#signature}

```
fn days_in_month(y Int, m Int) Int
```

## Description {#description}

How many days a month has, counting February in a leap year as 29.

**Parameters**

- `y`: the year.
- `m`: the month, 1 to 12.

**Returns** an `Int`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> days_in_month(2026, 2)
28
```

```
> days_in_month(2028, 2)
29
```

```
> days_in_month(2026, 11)
30
```

