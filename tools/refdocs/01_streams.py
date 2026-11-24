"""Documentation for the stream and sequence functions.  Each entry: text, examples (run by tools/make_ref_pages.py), shown (examples not run)."""
DOCS = {}
def d(name, text, ex=(), shown=()):
    DOCS[name] = (text, list(ex), list(shown))

SEQ = "`Seq[T]` is any source of `T` values: a `List`, `Array`, `Set`, `Ring` or `Stream`."

d("map", """Applies `f` to every item and gives the results as a stream. A stream is lazy: nothing is computed until something consumes it, such as `collect`, `sum` or a `for` loop. On a `Result`, `map` changes the value inside an `Ok` and passes an `Err` along; on an `Option`, it changes the value inside a `Some` and passes `None` along.

**Parameters**

- `f`: the function to apply to each item (or to the value inside a `Result` or `Option`).
- `xs`: the items. """ + SEQ + """

**Returns** a `Stream[U]` of the results, in the same order; for a `Result` or `Option`, a value of the same kind.""",
 ["List(1, 2, 3) |> map((x) -> x * 2) |> collect()", "map((x) -> x + 1, Some(1))", "map((x) -> x + 1, None)", "map((x) -> x + 1, Ok(1))", 'map((x) -> x + 1, Err(Error(7, "no")))'])

d("fmap", """Like `map`, but the result has the same shape as the source: a `List` stays a `List`, an `Array` stays an `Array` of the same size, and an `Option` or `Result` stays an `Option` or `Result`. Use `fmap` when you want a collection back and not a stream.

**Parameters**

- `f`: the function to apply to each item.
- `xs`: the `List`, `Array`, `Option` or `Result` to transform.

**Returns** a value of the same kind as `xs`, with each item replaced by `f` of it.""",
 ["fmap((x) -> x * 2, List(1, 2, 3))", "fmap((x) -> x + 1, Some(4))"])

d("filter", """Keeps the items for which `test` is true, in their original order. The result is a lazy stream.

**Parameters**

- `test`: a function from an item to a `Bool`.
- `xs`: the items.

**Returns** a `Stream[T]` of the items that passed.""",
 ["List(1, 2, 3, 4, 5) |> filter((x) -> x % 2 == 1) |> collect()"])
DOCS["filter"] = (DOCS["filter"][0].replace("`test`", "`f`"), DOCS["filter"][1], DOCS["filter"][2])

d("filter_map", """Applies `f`, which gives an `Option`, to every item and keeps the values from the `Some` results. It does a `map` and a `filter` in one step.

**Parameters**

- `f`: a function from an item to an `Option`; `None` drops the item.
- `xs`: the items.

**Returns** a `Stream[U]` of the values that were present.""",
 ["List(1, 2, 3) |> filter_map((x) -> if x > 1 then Some(x * 10) else None) |> collect()"])

d("take", """The first `n` items of a source. If there are fewer than `n`, all of them; if `n` is zero or negative, none. Because the stream is lazy, `take` is how you cut an endless source such as `cycle`, `repeat` or `iterate` down to a size.

**Parameters**

- `n`: how many items to keep.
- `xs`: the items.

**Returns** a `Stream[T]` of at most `n` items.""",
 ["List(1, 2, 3, 4) |> take(2) |> collect()", "List(1, 2, 3) |> take(10) |> collect()", "iterate(1, (x) -> x * 2) |> take(5) |> collect()"])

d("drop", """All but the first `n` items. If there are `n` or fewer items, the result is empty; if `n` is zero or negative, nothing is dropped.

**Parameters**

- `n`: how many items to skip.
- `xs`: the items.

**Returns** a `Stream[T]` of the rest.""",
 ["List(1, 2, 3, 4) |> drop(2) |> collect()", "List(1, 2, 3) |> drop(5) |> collect()"])

d("take_while", """Items from the start of a source for as long as `f` is true. It stops at the first item for which `f` is false, even if later items would pass.

**Parameters**

- `f`: a test on one item.
- `xs`: the items.

**Returns** a `Stream[T]`.""",
 ["List(1, 2, 3, 4, 1) |> take_while((x) -> x < 3) |> collect()"])

d("drop_while", """Skips items from the start of a source while `f` is true, then gives the first item that fails the test and everything after it, whether or not later items pass.

**Parameters**

- `f`: a test on one item.
- `xs`: the items.

**Returns** a `Stream[T]`.""",
 ["List(1, 2, 3, 4, 1) |> drop_while((x) -> x < 3) |> collect()"])

d("take_last", """The last `n` items of a source. The whole source is read before anything is given back, so it must be finite.

**Parameters**

- `n`: how many items to keep.
- `xs`: the items.

**Returns** a `Stream[T]` of at most `n` items, in their original order.""",
 ["List(1, 2, 3, 4) |> take_last(2) |> collect()"])

d("drop_last", """All but the last `n` items of a source. The whole source is read before anything is given back, so it must be finite.

**Parameters**

- `n`: how many items to leave out at the end.
- `xs`: the items.

**Returns** a `Stream[T]`.""",
 ["List(1, 2, 3, 4) |> drop_last(1) |> collect()"])

d("enumerate", """Pairs each item with its position, counting from 0. In a `for`, a binding with two names takes each pair apart: `for i, x in xs |> enumerate()`.

**Parameters**

- `xs`: the items.

**Returns** a `Stream[(Int, T)]`.""",
 ['List("a", "b", "c") |> enumerate() |> collect()'])

d("zip", """Pairs up the items of two sources, first with first, second with second, and so on. It stops when the shorter source runs out.

**Parameters**

- `a`: the first source.
- `b`: the second source.

**Returns** a `Stream[(A, B)]`.""",
 ['zip(List(1, 2, 3), List("a", "b")) |> collect()'])

d("zip3", """Like `zip`, for three sources: it makes triples and stops when the shortest source runs out.

**Parameters**

- `a`, `b`, `c`: the three sources.

**Returns** a `Stream[(A, B, C)]`.""",
 ['zip3(List(1, 2), List("a", "b"), List(true, false)) |> collect()'])

d("zip_with", """Walks two sources together and combines each pair of items with `f`. It is `zip` followed by `map`, in one step. It stops when the shorter source runs out.

**Parameters**

- `f`: a function of two arguments, an item from each source.
- `xs`, `ys`: the two sources.

**Returns** a `Stream[C]` of the results.""",
 ["zip_with((a, b) -> a + b, List(1, 2), List(10, 20)) |> collect()"])

d("unzip", """Splits a source of pairs into two lists: the first parts and the second parts. It is the opposite of `zip`.

**Parameters**

- `xs`: a source of pairs.

**Returns** a pair of lists, `(List[A], List[B])`.""",
 ['unzip(List((1, "a"), (2, "b")))'])

d("sort", """Orders the items from smallest to largest by `<`. The sort is stable: items that compare equal keep their original order. The items must be orderable: numbers, text and characters are, and a tuple or enum you declare is when it says `deriving ord` (or has an `impl Ordered`). The whole source is read first, so it must be finite.

**Parameters**

- `xs`: the items.

**Returns** a `Stream[T]` in order. Use `sort_by` to order by a key instead of the item itself.""",
 ["List(3, 1, 2) |> sort() |> collect()", 'List("pear", "apple", "fig") |> sort() |> collect()'])

d("sort_by", """Orders the items by a key that `f` computes from each one, smallest key first. The sort is stable, so items with equal keys keep their original order. The whole source is read first, so it must be finite.

**Parameters**

- `f`: a function from an item to its sort key.
- `xs`: the items.

**Returns** a `Stream[T]` in key order.""",
 ['List("pear", "fig", "apple") |> sort_by((s) -> len(s)) |> collect()'])

d("reverse", """The items in the opposite order. The whole source is read first, so it must be finite.

**Parameters**

- `xs`: the items.

**Returns** a `Stream[T]`.""",
 ["List(1, 2, 3) |> reverse() |> collect()"])

d("reduce", """Folds the items into one value. It starts from `init` and calls `f(acc, item)` for each item in turn, passing each result on as the next `acc`. An empty source gives `init` back.

**Parameters**

- `init`: the starting value.
- `f`: a function of the running value and the next item, giving the new running value.
- `xs`: the items.

**Returns** the final value, of the same type as `init`.""",
 ["List(1, 2, 3) |> reduce(0, (acc, x) -> acc + x)", "List() |> reduce(7, (acc, x) -> acc + x)", 'List("a", "b", "c") |> reduce("", (acc, s) -> acc + s)'])

d("reduce_right", """Like `reduce`, but it works from the end of the source towards the start, and `f` takes the item first and the running value second: `f(item, acc)`.

**Parameters**

- `init`: the starting value.
- `f`: a function of an item and the running value.
- `xs`: the items; read in full before folding, so it must be finite.

**Returns** the final value.""",
 ["List(1, 2, 3) |> reduce_right(0, (x, acc) -> x - acc)"])

d("scan", """Like `reduce`, but it gives every running value and not just the last. The first value given is `f(init, first item)`; `init` itself is not part of the result, so the result has one value per item.

**Parameters**

- `init`: the starting value.
- `f`: a function of the running value and the next item.
- `xs`: the items.

**Returns** a `Stream[A]` of the running values.""",
 ["List(1, 2, 3, 4) |> scan(0, (acc, x) -> acc + x) |> collect()"])

d("collect", """Gathers a stream into a `List`, which runs the pipeline. A `List`, `Array` or `Set` given to it comes back as a list of its items.

**Parameters**

- `xs`: the source to gather.

**Returns** a `List[T]`.""",
 ["List(1, 2, 3, 4) |> filter((x) -> x > 2) |> collect()", "Set(3) |> collect()"])

d("sum", """Adds the items. The sum of no items is 0.

**Parameters**

- `xs`: the items, numbers of one type.

**Returns** the total, of the item type.""",
 ["List(1, 2, 3) |> sum()", "List() |> sum()", "List(1.5, 2.5) |> sum()"])

d("product", """Multiplies the items. The product of no items is 1.

**Parameters**

- `xs`: the items, numbers of one type.

**Returns** the product, of the item type.""",
 ["List(1, 2, 3, 4) |> product()", "List() |> product()"])

d("count", """How many items a source has. It reads the whole source, so it must be finite.

**Parameters**

- `xs`: the items.

**Returns** an `Int`.""",
 ['List("a", "b", "c") |> filter((s) -> s == "b") |> count()'])

d("avg", """The mean of the items, as a floating-point number. An empty source has no mean, so it gives an `Err` with the code `MISSING` and the message "empty".

**Parameters**

- `xs`: numbers: `Int`, `Float` or `Decimal` items.

**Returns** `Ok(mean)`, or `Err` for an empty source.""",
 ["List(1, 2, 3, 4) |> avg()", "List() |> avg()"])

d("any", """True if the test holds for at least one item. It stops at the first item that passes. An empty source gives false.

**Parameters**

- `f`: a test on one item.
- `xs`: the items.

**Returns** a `Bool`.""",
 ["List(1, 2, 3) |> any((x) -> x > 2)", "List(1, 2, 3) |> any((x) -> x > 5)"])

d("all", """True if the test holds for every item. It stops at the first item that fails. An empty source gives true.

**Parameters**

- `f`: a test on one item.
- `xs`: the items.

**Returns** a `Bool`.""",
 ["List(1, 2, 3) |> all((x) -> x > 0)", "List() |> all((x) -> x > 2)"])

d("find", """The first item for which the test is true. If no item passes, the result is an `Err` with the code `MISSING` and the message "not found", so the caller must say what to do about it.

**Parameters**

- `f`: a test on one item.
- `xs`: the items.

**Returns** `Ok(item)` or `Err`.""",
 ["List(1, 2, 3) |> find((x) -> x > 1)", "List(1, 2, 3) |> find((x) -> x > 5)"])

d("find_map", """Applies `f`, which gives an `Option`, to the items in turn and returns the first value that is present, without looking at the rest.

**Parameters**

- `f`: a function from an item to an `Option`.
- `xs`: the items.

**Returns** `Ok(value)` for the first `Some`, or `Err` (code `MISSING`) if every result is `None`.""",
 ["List(1, 2, 3) |> find_map((x) -> if x > 1 then Some(x * 10) else None)"])

d("position", """The position, counting from 0, of the first item for which the test is true.

**Parameters**

- `f`: a test on one item.
- `xs`: the items.

**Returns** `Ok(index)`, or `Err` (code `MISSING`, message "not found") if no item passes.""",
 ["List(5, 3, 9) |> position((x) -> x == 9)", "List(5, 3, 9) |> position((x) -> x == 1)"])

d("first", """The first item of a source.

**Parameters**

- `xs`: the items.

**Returns** `Ok(item)`, or `Err` (code `MISSING`, message "empty") if there are none.""",
 ["List(7, 8, 9) |> first()", "List() |> first()"])

d("last", """The last item of a source. It reads the whole source, so it must be finite.

**Parameters**

- `xs`: the items.

**Returns** `Ok(item)`, or `Err` (code `MISSING`, message "empty") if there are none.""",
 ["List(7, 8, 9) |> last()", "List() |> last()"])

d("min_by", """The item whose key is smallest. If several items have the smallest key, the first of them is given.

**Parameters**

- `f`: a function from an item to its key.
- `xs`: the items.

**Returns** `Ok(item)`, or `Err` (code `MISSING`) for an empty source.""",
 ['List("pear", "fig", "apple") |> min_by((s) -> len(s))'])

d("max_by", """The item whose key is largest. If several items have the largest key, the first of them is given.

**Parameters**

- `f`: a function from an item to its key.
- `xs`: the items.

**Returns** `Ok(item)`, or `Err` (code `MISSING`) for an empty source.""",
 ['List("pear", "fig", "apple") |> max_by((s) -> len(s))'])

d("partition", """Splits the items into two lists: those for which the test is true, and the rest. Each list keeps the original order.

**Parameters**

- `f`: a test on one item.
- `xs`: the items.

**Returns** a pair of lists, `(passed, failed)`.""",
 ["List(1, 2, 3, 4) |> partition((x) -> x % 2 == 0)"])

d("span", """Splits the items at the first one that fails the test. The first list holds the items before it, and the second holds that item and everything after it, whether or not later items pass.

**Parameters**

- `f`: a test on one item.
- `xs`: the items.

**Returns** a pair of lists.""",
 ["List(1, 2, 3, 4) |> span((x) -> x < 3)"])

d("split_at", """Splits the items after the first `n`: the first list has up to `n` items and the second has the rest.

**Parameters**

- `n`: how many items go in the first list.
- `xs`: the items.

**Returns** a pair of lists.""",
 ["List(1, 2, 3, 4) |> split_at(1)", "List(1, 2) |> split_at(5)"])

d("distinct", """Drops repeated items, keeping the first of each, in their original order. Items must have `==` (`deriving eq` for a tuple or enum you declare).

**Parameters**

- `xs`: the items.

**Returns** a `Stream[T]` with no repeats.""",
 ["List(1, 1, 2, 1, 3, 2) |> distinct() |> collect()"])

d("distinct_by", """Drops items whose key has already been seen, keeping the first item for each key, in their original order.

**Parameters**

- `f`: a function from an item to its key.
- `xs`: the items.

**Returns** a `Stream[T]`.""",
 ['List("ab", "cd", "e", "f") |> distinct_by((s) -> len(s)) |> collect()'])

d("flatten", """Turns a source of sources into one source, taking the inner items in order. Each inner item may be a list, an array or another stream.

**Parameters**

- `xs`: a source whose items are themselves sources.

**Returns** a `Stream[T]`.""",
 ["List(List(1, 2), List(), List(3)) |> flatten() |> collect()"])

d("cycle", """Repeats a source forever: after the last item it starts again at the first. The stream never ends, so cut it with `take`, `take_while` or a `break`. An empty source gives an empty stream.

**Parameters**

- `xs`: the items to repeat.

**Returns** an endless `Stream[T]`.""",
 ["List(1, 2, 3) |> cycle() |> take(7) |> collect()"])

d("repeat", """The same value over and over, forever. Cut it with `take`.

**Parameters**

- `x`: the value to repeat.

**Returns** an endless `Stream[T]`.""",
 ['repeat("ab") |> take(3) |> collect()'])

d("iterate", """A seed, then `f` of the seed, then `f` of that, and so on, forever. Cut it with `take` or `take_while`.

**Parameters**

- `seed`: the first value.
- `f`: a function from one value to the next.

**Returns** an endless `Stream[T]`.""",
 ["iterate(1, (x) -> x * 2) |> take(6) |> collect()"])

d("intersperse", """Puts `sep` between neighbouring items. There is no separator before the first item or after the last.

**Parameters**

- `sep`: the value to put between items.
- `xs`: the items.

**Returns** a `Stream[T]`.""",
 ["List(1, 2, 3) |> intersperse(0) |> collect()"])

d("chunks", """Groups the items in lists of `n`, in order. The last list is shorter when the number of items is not a multiple of `n`.

**Parameters**

- `n`: the size of each group.
- `xs`: the items.

**Returns** a `Stream[List[T]]`. All items are read before the first group is given.""",
 ["List(1, 2, 3, 4, 5) |> chunks(2) |> collect()"])

d("windows", """Every run of `n` neighbouring items, sliding along one item at a time. A source with fewer than `n` items gives no windows.

**Parameters**

- `n`: the length of each window.
- `xs`: the items.

**Returns** a `Stream[Array[T]]`. All items are read before the first window is given.""",
 ["List(1, 2, 3, 4) |> windows(2) |> collect()", "List(1, 2) |> windows(3) |> collect()"])

d("group_by", """Collects the items into a `Dict` from key to the list of items with that key. Keys appear in the order they were first seen, and each list keeps the original order.

**Parameters**

- `f`: a function from an item to its key.
- `xs`: the items.

**Returns** a `Dict[K, List[T]]`.""",
 ['List("ann", "bo", "cy", "dee") |> group_by((s) -> len(s))'])

d("frequencies", """Counts how many times each item occurs.

**Parameters**

- `xs`: the items.

**Returns** a `Dict[T, Int]` from item to count, in the order each item was first seen.""",
 ["List(1, 2, 1, 3, 1) |> frequencies()"])

d("count_by", """Counts how many items have each key.

**Parameters**

- `f`: a function from an item to its key.
- `xs`: the items.

**Returns** a `Dict[K, Int]` from key to count.""",
 ["List(1, 2, 3, 4, 5) |> count_by((x) -> x % 2)"])

d("transpose", """Turns rows into columns: the first list gets the first item of every row, the second list the second item, and so on. Rows of different lengths are allowed; a short row just has nothing in the later columns.

**Parameters**

- `rows`: a source of rows, each a source of items.

**Returns** a `List[List[T]]`.""",
 ["transpose(List(List(1, 2, 3), List(4, 5)))"])

d("to_stream", """Treats any collection as a stream, so that stream functions can be applied to it with `|>`. A `Stream` given to it comes back unchanged.

**Parameters**

- `xs`: a `List`, `Array`, `Set`, `Ring` or `Stream`.

**Returns** a `Stream[T]`.""",
 ["List(7, 8) |> to_stream() |> collect()"])
