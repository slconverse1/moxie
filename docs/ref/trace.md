---
layout: default
toc: true
terms: true
title: "trace · moxie function"
---

# `trace`

<p class="specref"><a href="../reference.html#fn-trace">The alphabetical list</a> · <a href="../spec.html#s22">Spec §22</a></p>

## Signature {#signature}

```
fn trace[T](x T) Unit
```

## Description {#description}

Writes a value to the trace, a log for finding out what a program did, which can be turned on and off from outside. Like `dbg`, it is allowed anywhere.

**Parameters**

- `x`: any value.

**Returns** nothing.

## Effects {#effects}

**Effect:** prints, but is allowed in any code

## Examples {#examples}

```
> trace("step one")
println("done")
done
```

