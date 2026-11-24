DOCS = {}
def d(name, text, ex=(), shown=()):
    DOCS[name] = (text, list(ex), list(shown))

CAP = "In GC-free moxie a `List`, `Set` or `Dict` has a fixed capacity, so adding to a full one aborts; in moxie/gc they grow as needed."

# ---------------------------------------------------------------- collections
d("len", """How many items a collection holds, or how many bytes a `String` has. A `String` is stored as UTF-8, so a character outside plain ASCII counts as more than one byte; use `char_count` for characters and `grapheme_count` for what a reader sees as one character.

**Parameters**

- `xs`: a `String`, `List`, `Array`, `Set`, `Dict`, `Ring`, `Stream` or other collection.

**Returns** an `Int`.""",
 ['len("hello")', 'len("héllo")', "len(List(1, 2, 3))", 'len(Dict("a" -> 1))'])

d("is_empty", """True when a `String` or collection has no items.

**Parameters**

- `xs`: a `String`, `List`, `Array`, `Set`, `Dict` or other collection.

**Returns** a `Bool`.""",
 ['is_empty("")', "is_empty(List(1))", "is_empty(List())"])

d("get", """The item at a position or key, as a `Result`, so that a missing item is something the caller has to deal with and not a crash. To fall back to a default instead, use `get_or`. For a list or array, `xs(i)` reads a position directly and aborts if it is out of range.

**Parameters**

- `xs`: a `List`, `Array` or `Dict`.
- `i` or `k`: the position (counting from 0) or the key.

**Returns** `Ok(item)`, or `Err` with the code `MISSING` ("no such element" for a position, "no such key" for a key).""",
 ["get(List(10, 20, 30), 1)", "get(List(10, 20, 30), 9)", 'get(Dict("a" -> 1), "a")', 'get(Dict("a" -> 1), "b")'])

d("get_or", """The value you ask for, or `default` when it is not there. It works on a `Result` (an `Err` gives the default), an `Option` (`None` gives the default), a `Dict` (a missing key) and a `List` (a position out of range).

**Parameters**

- the first argument: the `Result`, `Option`, `Dict` or `List` to look in.
- for a `Dict`, the key; for a `List`, the position.
- the last argument: the default, of the same type as the values.

**Returns** the value, or the default.""",
 ["get_or(Some(2), 5)", "get_or(None, 5)", 'get_or(Err(Error(1, "x")), 5)', 'get_or(Dict("a" -> 1), "z", 0)', "get_or(List(1, 2, 3), 9, 0)"])

d("contains", """True if a collection holds an item, or a `String` holds a piece of text. For a `Dict` it asks about keys, and for a `Set` about members. Items need `==`.

**Parameters**

- `xs`: a `String`, a `List`/`Array`/`Set`/`Ring`/`Stream` or a `Dict`.
- the second argument: the text, the item or the key to look for.

**Returns** a `Bool`.""",
 ['contains("hello", "ell")', "contains(List(1, 2), 2)", 'contains(Dict("a" -> 1), "a")', "contains(Set(1, 2), 3)"])

d("keys", """The keys of a `Dict`, in the order they were added.

**Parameters**

- `d`: a `Dict`.

**Returns** a `Stream[K]`.""",
 ['Dict("a" -> 1, "b" -> 2) |> keys() |> collect()'])

d("values", """The values of a `Dict`, in the order their keys were added. Not to be confused with the `values()` helper that an enum has, which lists its cases.

**Parameters**

- `d`: a `Dict`.

**Returns** a `Stream[V]`.""",
 ['Dict("a" -> 1, "b" -> 2) |> values() |> collect()'])

d("items", """The key and value pairs of a `Dict`, in the order the keys were added. In a `for`, two names take each pair apart: `for k, v in d |> items()`.

**Parameters**

- `d`: a `Dict`.

**Returns** a `Stream[(K, V)]`.""",
 ['Dict("a" -> 1, "b" -> 2) |> items() |> collect()'])

d("set", """A copy with one position or key replaced; the original is unchanged. For a `List`, `Array` or `MultiArray`, the position must already exist, or the call aborts; it never makes the collection longer. For a `Dict`, an existing key gets the new value and a new key is added. """ + CAP + """

**Parameters**

- `xs`: a `List`, `Array`, `MultiArray` or `Dict`.
- the position or key.
- the new value.

**Returns** the updated collection, of the same kind.""",
 ["set(List(1, 2, 3), 1, 9)", "set(Array(1, 2, 3), 0, 9)", 'set(Dict("a" -> 1), "a", 5)'])

d("remove", """A copy without one item. For a `Dict` the item is a key, for a `Set` a member, and for a `List` or `Array` the first item equal to it. If it is not there, the collection comes back unchanged.

**Parameters**

- `xs`: a `Dict`, `Set`, `List` or `Array`.
- the key or item to leave out.

**Returns** the smaller collection, of the same kind.""",
 ['remove(Dict("a" -> 1, "b" -> 2), "a")', "remove(Set(1, 2), 1)", "remove(List(1, 2, 1), 1)", "remove(List(1, 2), 9)"])

d("remove_at", """A copy without the item at a position. The position must exist, or the call aborts.

**Parameters**

- `xs`: a `List` or `Array`.
- `i`: the position, counting from 0.

**Returns** the shorter collection.""",
 ["remove_at(List(5, 6, 7), 1)"])

d("clear", """An empty collection of the same kind and type, with the same capacity.

**Parameters**

- `xs`: a `Dict`, `Set` or `List`.

**Returns** the empty collection.""",
 ['clear(Dict("a" -> 1))', "clear(List(1, 2))"])

d("indices", """The positions of a list, array or string, from 0 up to one less than its length. For a `String` the positions are byte positions.

**Parameters**

- `xs`: a collection or a `String`.

**Returns** a `Range`, such as `0..<3`, which can be used in a `for`.""",
 ["indices(List(5, 6, 7))", 'indices("abc")'])

d("join", """Makes one `String` from the items, with `sep` between them. Each item is shown as text first, so numbers and other values can be joined too. Without a separator the items are run together.

**Parameters**

- `xs`: the items.
- `sep` (optional): the text to put between items.

**Returns** a `String`.""",
 ['join(List("a", "b", "c"), ", ")', "join(List(1, 2, 3), \"-\")", "join(List(1, 2, 3))"])

d("replace", """A copy of a value with the part at a data path replaced. The path says where to go: `/User/firm/name` is the `name` field of the `firm` field of a `User`. The value you pass in is unchanged. Paths are checked when the program is compiled, so a path that doesn't exist is an error.

**Parameters**

- `x`: the value to update (a tuple, or something containing tuples).
- `path`: a data path.
- `v`: the new value.

**Returns** the updated copy.""",
 [], [("replace(a, /User/firm/name, \"Acme\")", "a copy of `a` whose firm is named Acme")])

d("modify", """A copy of a value with the part at a data path changed by a function. It is `replace` where the new value is computed from the old one.

**Parameters**

- `x`: the value to update.
- `path`: a data path such as `/User/firm/floor`.
- `f`: a function from the old part to the new one; a placeholder works too: `_ + 1`.

**Returns** the updated copy.""",
 [], [("modify(a, /User/firm/floor, _ + 1)", "a copy of `a` whose firm is one floor higher")])

# ---------------------------------------------------------------- numbers
d("abs", """The absolute value: a number without its sign. For a fixed-width integer, the most negative value has no positive twin, so `abs` of it aborts.

**Parameters**

- `n`: an integer or a floating-point number.

**Returns** a number of the same type.""",
 ["abs(-3)", "abs(2.5)", "abs(-2.5)"])

d("min", """The smaller of two values, or, given a source, its smallest item. Values must be orderable (`deriving ord` for a tuple or enum you declare).

**Parameters**

- `a`, `b`: two values of one type; or
- `xs`: a source of items.

**Returns** the smaller value; for a source, `Ok(item)`, or `Err` (code `MISSING`) when it is empty.""",
 ["min(3, 5)", 'min("b", "a")', "List(3, 1, 2) |> min()", "List() |> min()"])

d("max", """The larger of two values, or, given a source, its largest item. Values must be orderable (`deriving ord` for a tuple or enum you declare).

**Parameters**

- `a`, `b`: two values of one type; or
- `xs`: a source of items.

**Returns** the larger value; for a source, `Ok(item)`, or `Err` (code `MISSING`) when it is empty.""",
 ["max(3, 5)", 'max("a", "b")', "List(3, 1, 2) |> max()", "List() |> max()"])

d("clamp", """Limits a value to a range: below the low bound it gives the low bound, above the high bound it gives the high bound, and otherwise the value itself.

**Parameters**

- `x`: the value.
- `lo`, `hi`: the bounds; or
- `r`: a range such as `0..10`.

**Returns** a value of the same type.""",
 ["clamp(15, 0, 10)", "clamp(5, 0, 10)", "clamp(-5, 0, 10)", "clamp(2.5, 0.0, 1.0)", "clamp(15, 0..10)"])

d("pow", """A number raised to a power. With two `Int`s the result is an `Int`; with two floating-point numbers it is a `Double`.

**Parameters**

- `a`: the base.
- `b`: the exponent.

**Returns** `a` to the power `b`.""",
 ["pow(2, 10)", "pow(2.0, 0.5)", "pow(0, 0)"])

d("sqrt", """The square root. The square root of a negative number is `NAN`, which is not an error; test for it with `is_nan`, or use `finite`.

**Parameters**

- `x`: a number.

**Returns** a `Double`.""",
 ["sqrt(16.0)", "sqrt(2)", "sqrt(-1.0)"])

d("floor", """Rounds down, towards negative infinity, to a whole number.

**Parameters**

- `x`: a floating-point number.

**Returns** an `Int`.""",
 ["floor(2.7)", "floor(-2.1)", "floor(7)"])

d("ceil", """Rounds up, towards positive infinity, to a whole number.

**Parameters**

- `x`: a floating-point number.

**Returns** an `Int`.""",
 ["ceil(2.1)", "ceil(-2.9)"])

d("round", """Rounds to the nearest whole number. A number exactly halfway rounds up, towards positive infinity, so 2.5 gives 3 and -2.5 gives -2.

**Parameters**

- `x`: a floating-point number.

**Returns** an `Int`.""",
 ["round(2.4)", "round(2.5)", "round(-2.5)", "round(3.5)"])

d("finite", """Checks that a floating-point number is an ordinary number: not infinity and not `NAN`. It turns the "check later" values of floating point into a `Result` you handle now.

**Parameters**

- `x`: a `Double`.

**Returns** `Ok(x)`, or `Err` (code `OUT_OF_RANGE`, message "not finite").""",
 ["finite(1.5)", "finite(1.0 / 0.0)", "finite(0.0 / 0.0)"])

d("is_nan", """True if the number is `NAN`, "not a number", such as the result of `0.0 / 0.0`. `NAN` is not equal to anything, itself included, so `==` can't find it.

**Parameters**

- `x`: a `Double`.

**Returns** a `Bool`.""",
 ["is_nan(0.0 / 0.0)", "is_nan(1.0)"])

d("is_inf", """True if the number is positive or negative infinity, such as `1.0 / 0.0`.

**Parameters**

- `x`: a `Double`.

**Returns** a `Bool`.""",
 ["is_inf(1.0 / 0.0)", "is_inf(-1.0 / 0.0)", "is_inf(1.0)"])

d("is_finite", """True if the number is neither infinity nor `NAN`.

**Parameters**

- `x`: a `Double`.

**Returns** a `Bool`.""",
 ["is_finite(1.0)", "is_finite(1.0 / 0.0)"])

d("checked_add", """Addition that reports overflow instead of aborting or wrapping. Use it when the numbers come from outside and might be too big.

**Parameters**

- `a`, `b`: two integers of one type.

**Returns** `Ok(sum)`, or `Err` (code `OUT_OF_RANGE`, message "overflow") if the sum doesn't fit the type.""",
 ["checked_add(1, 2)", "checked_add(9223372036854775807, 1)"])

d("checked_sub", """Subtraction that reports overflow instead of aborting or wrapping.

**Parameters**

- `a`, `b`: two integers of one type.

**Returns** `Ok(a - b)`, or `Err` (code `OUT_OF_RANGE`, message "overflow") if the result doesn't fit the type.""",
 ["checked_sub(1, 2)", "checked_sub(cast[UInt8](1), cast[UInt8](2))"])

d("checked_mul", """Multiplication that reports overflow instead of aborting or wrapping.

**Parameters**

- `a`, `b`: two integers of one type.

**Returns** `Ok(product)`, or `Err` (code `OUT_OF_RANGE`, message "overflow") if the product doesn't fit the type.""",
 ["checked_mul(3, 4)", "checked_mul(4611686018427387904, 4)"])

d("checked_div", """Division that reports a zero divisor, and overflow, instead of aborting. Integer division rounds towards zero.

**Parameters**

- `a`: the dividend.
- `b`: the divisor.

**Returns** `Ok(quotient)`, or `Err` (code `OUT_OF_RANGE`, message "division by zero") when `b` is 0.""",
 ["checked_div(7, 2)", "checked_div(7, 0)"])

d("wrapping_add", """Addition that wraps around on overflow, as a clock does: past the largest value it continues from the smallest. Without the word `wrapping`, overflow aborts. Useful for hashes and checksums.

**Parameters**

- `a`, `b`: two integers of one type.

**Returns** the sum modulo the size of the type.""",
 ["wrapping_add(cast[Int8](127), cast[Int8](1))", "wrapping_add(cast[UInt8](250), cast[UInt8](10))"])

d("wrapping_sub", """Subtraction that wraps around on overflow.

**Parameters**

- `a`, `b`: two integers of one type.

**Returns** the difference modulo the size of the type.""",
 ["wrapping_sub(cast[UInt8](0), cast[UInt8](1))"])

d("wrapping_mul", """Multiplication that wraps around on overflow.

**Parameters**

- `a`, `b`: two integers of one type.

**Returns** the product modulo the size of the type.""",
 ["wrapping_mul(cast[Int8](100), cast[Int8](2))"])

d("saturating_add", """Addition that stops at the largest or smallest value of the type instead of overflowing.

**Parameters**

- `a`, `b`: two integers of one type.

**Returns** the sum, or the largest value if the true sum is too big.""",
 ["saturating_add(cast[Int8](127), cast[Int8](1))", "saturating_add(cast[Int8](1), cast[Int8](2))"])

d("saturating_sub", """Subtraction that stops at the largest or smallest value of the type instead of overflowing. For an unsigned type the smallest value is 0.

**Parameters**

- `a`, `b`: two integers of one type.

**Returns** the difference, limited to what the type can hold.""",
 ["saturating_sub(cast[UInt8](1), cast[UInt8](5))", "saturating_sub(cast[Int8](-100), cast[Int8](100))"])

d("saturating_mul", """Multiplication that stops at the largest or smallest value of the type instead of overflowing.

**Parameters**

- `a`, `b`: two integers of one type.

**Returns** the product, limited to what the type can hold.""",
 ["saturating_mul(cast[Int8](100), cast[Int8](2))"])

d("bit_and", """Bitwise and: each bit of the result is 1 only where both inputs have a 1.

**Parameters**

- `a`, `b`: two integers of one type.

**Returns** an integer of that type.""",
 ["bit_and(12, 10)"])

d("bit_or", """Bitwise or: each bit of the result is 1 where either input has a 1.

**Parameters**

- `a`, `b`: two integers of one type.

**Returns** an integer of that type.""",
 ["bit_or(12, 10)"])

d("bit_xor", """Bitwise exclusive or: each bit of the result is 1 where the inputs differ.

**Parameters**

- `a`, `b`: two integers of one type.

**Returns** an integer of that type.""",
 ["bit_xor(12, 10)"])

d("bit_not", """Bitwise complement: every 0 bit becomes 1 and every 1 bit becomes 0. For a signed integer, `bit_not(n)` is `-n - 1`.

**Parameters**

- `a`: an integer.

**Returns** an integer of the same type.""",
 ["bit_not(0)", "bit_not(5)"])

d("shl", """Shifts the bits left by `n` places, which multiplies by 2 for each place. Bits shifted out of the top are lost.

**Parameters**

- `a`: an integer.
- `n`: how many places to shift.

**Returns** an integer of the same type.""",
 ["shl(1, 4)", "shl(cast[UInt8](255), 1)"])

d("shr", """Shifts the bits right by `n` places, which divides by 2 for each place, rounding down. For a signed integer the sign is kept, so a negative number stays negative.

**Parameters**

- `a`: an integer.
- `n`: how many places to shift.

**Returns** an integer of the same type.""",
 ["shr(256, 4)", "shr(-8, 1)"])

d("parse_number", """Reads a number from text. Text with a decimal point gives a `Double`, and text without one gives an `Int`. A sign is allowed and so is a leading space; anything else is an error, and nothing aborts. With a `Locale`, the group and decimal marks of that locale are understood, so `"1.234,5"` can be read in German.

**Parameters**

- `s`: the text.
- `locale` (optional): a `Locale` such as `Locale.de_de`.

**Returns** `Ok(number)`, or `Err` (code `MISSING`, message "not a number").""",
 ['parse_number("42")', 'parse_number("-7")', 'parse_number("3.5")', 'parse_number("x")', 'parse_number("1e3")'])

d("random", """A random `Double` from 0 up to, but not including, 1. Random numbers come from the system's generator, so a program that uses them uses the system.

**Parameters** none.

**Returns** a `Double`.""",
 ["random() < 1.0"], [("random()", "0.7236...  (a different number each time)")])

d("random_int", """A random whole number chosen uniformly from a range. The call aborts if the range is empty or endless.

**Parameters**

- `r`: a range such as `1..6` (both ends included) or `0..<10`; a step is allowed: `1..9 step 2`.

**Returns** an `Int` in the range.""",
 ["random_int(5..5)"], [("random_int(1..6)", "4  (any of 1 to 6)")])

d("random_bytes", """`n` random bytes, for keys, tokens and salts. They come from the system's random source.

**Parameters**

- `n`: how many bytes.

**Returns** an `Array[Byte]` of length `n`.""",
 ["len(random_bytes(4))"])

d("cast", """Converts a number to another numeric type, written with the target in brackets: `cast[Double](n)`. The conversion is explicit because moxie never widens or narrows numbers behind your back. A value that doesn't fit the target aborts (a constant that doesn't fit is a compile error); use `try_cast` to get a `Result` instead, or `wrap_to` to keep the low bits. Converting a floating-point number to an integer drops the fraction, towards zero.

**Parameters**

- `T` (in brackets): the type to convert to.
- `x`: the number.

**Returns** the value as a `T`.""",
 ["cast[Double](3)", "cast[Int](2.9)", "cast[Int](-2.9)", "cast[Int8](100)"])

d("try_cast", """Like `cast`, but a value that doesn't fit is a `Result` and not an abort.

**Parameters**

- `T` (in brackets): the type to convert to.
- `x`: the number.

**Returns** `Ok(value)`, or `Err` (code `OUT_OF_RANGE`, message "does not fit").""",
 ["try_cast[Int8](100)", "try_cast[Int8](300 + len(\"\"))", "try_cast[UInt8](-1)"])

d("wrap_to", """Converts an integer to a narrower or differently signed type by keeping the low bits, as a C cast would. Nothing aborts; values that don't fit wrap around.

**Parameters**

- `T` (in brackets): the type to convert to.
- `x`: the integer.

**Returns** the value as a `T`.""",
 ["wrap_to[Int8](300)", "wrap_to[UInt8](-1)"])

d("round_to", """Rounds a `Decimal` to `n` decimal places. Nothing about a `Decimal` is rounded unless you ask, so you choose the rounding mode too: `#half_even` rounds a tie to the even neighbour (banker's rounding), `#half_up` rounds a tie up, and `#down` cuts digits off.

**Parameters**

- `n` (in brackets): the number of places to keep.
- `x`: the `Decimal`.
- `mode`: `#half_even`, `#half_up` or `#down`.

**Returns** the rounded `Decimal`.""",
 ["round_to[2](3.14159d, #half_even)", "round_to[1](2.25d, #half_even)", "round_to[1](2.25d, #half_up)", "round_to[1](2.29d, #down)"])

d("div", """Divides one `Decimal` by another to a scale you choose. Exact decimal division can have endless digits, so it needs a number of places and a rounding mode. A zero divisor is an `Err`, not an abort.

**Parameters**

- `a`: the dividend.
- `b`: the divisor.
- `scale`: how many decimal places the result has.
- `mode`: `#half_even`, `#half_up` or `#down`.

**Returns** `Ok(quotient)`, or `Err` (code `OUT_OF_RANGE`, message "division by zero").""",
 ["div(10.00d, 3.00d, 4, #half_up)", "div(10.00d, 4.00d, 1, #half_even)", "div(1.0d, 0.0d, 2, #half_up)"])
