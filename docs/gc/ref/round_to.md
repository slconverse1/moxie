---
layout: default
toc: true
terms: true
dialect: gc
title: "round_to · moxie/gc function"
---

# `round_to`

<p class="specref"><a href="../reference.html#fn-round_to">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn round_to[n](x Decimal, mode Mode) Decimal
```

## Description {#description}

Rounds a `Decimal` to `n` decimal places. Nothing about a `Decimal` is rounded unless you ask, so you choose the rounding mode too: `#half_even` rounds a tie to the even neighbour (banker's rounding), `#half_up` rounds a tie up, and `#down` cuts digits off.

**Parameters**

- `n` (in brackets): the number of places to keep.
- `x`: the `Decimal`.
- `mode`: `#half_even`, `#half_up` or `#down`.

**Returns** the rounded `Decimal`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> round_to[2](3.14159d, #half_even)
3.14
```

```
> round_to[1](2.25d, #half_even)
2.2
```

```
> round_to[1](2.25d, #half_up)
2.3
```

```
> round_to[1](2.29d, #down)
2.2
```

