DOCS = {}
def d(name, text, ex=(), shown=()):
    DOCS[name] = (text, list(ex), list(shown))

# ---------------------------------------------------------------- text
d("upper", """Converts text to upper case. Given a `String`, every letter is converted; given a `Char`, just that character.

**Parameters**

- `s`: a `String` or a `Char`.

**Returns** the same type.""",
 ['upper("Hello")', "upper('a')"])
d("lower", """Converts text to lower case. Given a `String`, every letter is converted; given a `Char`, just that character.

**Parameters**

- `s`: a `String` or a `Char`.

**Returns** the same type.""",
 ['lower("Hello")', "lower('A')"])
d("trim", """Removes white space (spaces, tabs and line ends) from both ends of a `String`. White space inside is kept.

**Parameters**

- `s`: a `String`.

**Returns** the trimmed `String`.""",
 ['trim("  a b  ")'])
d("chars", """The characters of a `String`, one at a time. A `Char` is one Unicode code point, so a letter with a combining accent is two of them; use `graphemes` for what a reader sees as one character.

**Parameters**

- `s`: a `String`.

**Returns** a `Stream[Char]`.""",
 ['"abc" |> chars() |> collect()'])
d("graphemes", """The characters of a `String` as a reader sees them, each as a small `String`. An accented letter, or an emoji built from several code points, is one grapheme.

**Parameters**

- `s`: a `String`.

**Returns** a `Stream[String]`.""",
 ['"abc" |> graphemes() |> collect()'])
d("char_count", """How many Unicode code points a `String` has. `len` counts bytes, which is larger for any character outside plain ASCII.

**Parameters**

- `s`: a `String`.

**Returns** an `Int`.""",
 ['char_count("héllo")', 'len("héllo")'])
d("grapheme_count", """How many characters a reader would count in a `String`, so an accented letter or emoji counts once however it is encoded.

**Parameters**

- `s`: a `String`.

**Returns** an `Int`.""",
 ['grapheme_count("abc")'])
d("split", """Cuts a `String` at every occurrence of a separator. Neighbouring separators give empty pieces, and a `String` that does not contain the separator comes back as a one-item list.

**Parameters**

- `s`: the text.
- `sep`: the separator.

**Returns** a `List[String]`.""",
 ['split("a,b,c", ",")', 'split("a,,b", ",")', 'split("abc", ",")'])
d("split_once", """Cuts a `String` at the first occurrence of a separator only, which suits `key=value` text.

**Parameters**

- `s`: the text.
- `sep`: the separator.

**Returns** `Some((before, after))`, or `None` if the separator is not there.""",
 ['split_once("k=v=w", "=")', 'split_once("kv", "=")'])
d("starts_with", """True if a `String` begins with a prefix.

**Parameters**

- `s`: the text.
- `prefix`: a `String` or a `Char`.

**Returns** a `Bool`.""",
 ['starts_with("hello", "he")', 'starts_with("hello", \'x\')'])
d("ends_with", """True if a `String` ends with a suffix.

**Parameters**

- `s`: the text.
- `suffix`: a `String` or a `Char`.

**Returns** a `Bool`.""",
 ['ends_with("hello", "llo")', 'ends_with("hello", \'x\')'])
d("strip_prefix", """Removes a prefix from a `String`, and tells you whether there was one to remove.

**Parameters**

- `s`: the text.
- `prefix`: the prefix.

**Returns** `Some(rest)`, or `None` if the text does not begin with the prefix.""",
 ['strip_prefix("hello", "he")', 'strip_prefix("hello", "x")'])
d("strip_suffix", """Removes a suffix from a `String`, and tells you whether there was one to remove.

**Parameters**

- `s`: the text.
- `suffix`: the suffix.

**Returns** `Some(rest)`, or `None` if the text does not end with the suffix.""",
 ['strip_suffix("a.txt", ".txt")', 'strip_suffix("a.txt", ".md")'])
d("pad_left", """Adds fill on the left until the text is `n` characters long (right-aligning it). Text that is already long enough is left alone; nothing is cut. The fill defaults to a space.

**Parameters**

- `s`: the text.
- `n`: the width to reach.
- `c` (optional): the fill, a `String` or `Char`.

**Returns** a `String`.""",
 ['pad_left("7", 3)', 'pad_left("7", 3, "0")', 'pad_left("7", 3, \'0\')', 'pad_left("abcd", 3)'])
d("pad_right", """Adds fill on the right until the text is `n` characters long (left-aligning it). Text that is already long enough is left alone. The fill defaults to a space.

**Parameters**

- `s`: the text.
- `n`: the width to reach.
- `c` (optional): the fill, a `String` or `Char`.

**Returns** a `String`.""",
 ['pad_right("7", 3, "0")', 'pad_right("ab", 4, \'.\')'])
d("replace_text", """Replaces every occurrence of one piece of text with another. It is for text; for changing a part of a data value, see `replace`.

**Parameters**

- `s`: the text.
- `from`: what to look for.
- `to`: what to put in its place.

**Returns** a `String`.""",
 ['replace_text("a-b-c", "-", "+")', 'replace_text("aaa", "a", "bb")'])
d("fmt", """Builds a `String` from a template, with each `{}` replaced by the next argument shown as text. A `{}` with no argument left, or an argument with no `{}`, aborts: the compiler reports it when the template is a literal. Use `try_fmt` for a template that comes from outside. Write `{{` and `}}` for literal braces.

**Parameters**

- `template`: the text with `{}` holes.
- `args`: the values to put in.

**Returns** a `String`.""",
 ['fmt("{} + {} = {}", 1, 2, 3)', 'fmt("name: {}", "Ada")', 'fmt("{{}}")'])
d("try_fmt", """Like `fmt`, but a template that doesn't match its arguments is a `Result`, not an abort. Use it when the template comes from a file or a user.

**Parameters**

- `template`: the text with `{}` holes.
- `args`: the values to put in.

**Returns** `Ok(text)`, or `Err` with code `BAD_FORMAT` if the number of holes and arguments differ.""",
 ['try_fmt("{}-{}", 1, 2)', 'try_fmt(trim("{}-{} "), 1)'])
d("show", """Turns any value into text, in the form you would write it in a program, so `show("a")` includes the quotes. `println` and `fmt` use it for you; call it when you need the text itself. A `Secret` shows as `Secret(...)`, never its contents.

**Parameters**

- `x`: any value.

**Returns** a `String`.""",
 ['show(42)', 'show("a")', 'show(List(1, 2))', 'show(Some(1))', 'show((1, "a"))'])

# ---------------------------------------------------------------- results and options
d("is_ok", """True if a `Result` is `Ok`.

**Parameters**

- `r`: a `Result`.

**Returns** a `Bool`.""",
 ["is_ok(Ok(1))", 'is_ok(Err(Error(1, "x")))'])
d("is_err", """True if a `Result` is `Err`.

**Parameters**

- `r`: a `Result`.

**Returns** a `Bool`.""",
 ["is_err(Ok(1))", 'is_err(Err(Error(1, "x")))'])
d("ok", """Turns a `Result` into an `Option`, keeping the value and dropping the error.

**Parameters**

- `r`: a `Result`.

**Returns** `Some(value)` for `Ok`, `None` for `Err`.""",
 ["ok(Ok(1))", 'ok(Err(Error(1, "x")))'])
d("ok_or", """Turns an `Option` into a `Result`, supplying the error to use if there is no value.

**Parameters**

- `o`: an `Option`.
- `err`: the `Error` for the `None` case.

**Returns** `Ok(value)` for `Some`, `Err(err)` for `None`.""",
 ['ok_or(Some(1), Error(4, "missing"))', 'ok_or(None, Error(4, "missing"))'])
d("unwrap", """The value inside an `Ok`. An `Err` aborts the program, so use it only where an error would mean a bug, for instance on a literal you know is valid. Everywhere else, handle the `Err`, or pass it on with `?`.

**Parameters**

- `r`: a `Result`.

**Returns** the value.""",
 ["unwrap(Ok(5))"], [('unwrap(Err(Error(4, "missing")))', "aborts the program with the error")])
d("map_ok", """Applies a function to the value inside an `Ok`; an `Err` passes through untouched.

**Parameters**

- `r`: a `Result`.
- `f`: a function from the value to a new value.

**Returns** a `Result` with the new value type and the same error type.""",
 ["map_ok(Ok(2), (x) -> x * 10)", 'map_ok(Err(Error(1, "x")), (x) -> x * 10)'])
d("map_err", """Applies a function to the error inside an `Err`, for example to wrap it in your own error type; an `Ok` passes through untouched.

**Parameters**

- `r`: a `Result`.
- `f`: a function from the old error to the new one.

**Returns** a `Result` with the same value type and the new error type.""",
 ['map_err(Err(Error(1, "x")), (e) -> e.code)', "map_err(Ok(1), (e) -> 0)"])
d("or_else", """If the `Result` is an `Err`, try something else, which may itself fail. An `Ok` passes through untouched. It chains fallbacks: try the cache, else the disk, else the network.

**Parameters**

- `r`: a `Result`.
- `f`: a function from the error to another `Result`.

**Returns** the `Result` of the fallback, or the original `Ok`.""",
 ['or_else(Err(Error(1, "x")), (e) -> Ok(0))', "or_else(Ok(7), (e) -> Ok(0))"])
d("recover", """If the `Result` is an `Err`, replace it with a plain value from a function; the result is then always an `Ok`.

**Parameters**

- `r`: a `Result`.
- `f`: a function from the error to a value.

**Returns** an `Ok`.""",
 ['recover(Err(Error(1, "x")), (e) -> 0)', "recover(Ok(5), (e) -> 0)"])
d("ensure", """Checks a condition, and gives a `Result` you can use with `?` to stop early. It is the usual way to write a guard whose failure carries its own error value.

**Parameters**

- `ok`: the condition that must hold.
- `e`: the error to produce if it does not.

**Returns** `Ok(())` if the condition holds, otherwise `Err(e)`.""",
 ['ensure(1 < 2, "too small")', 'ensure(2 < 1, "too small")'])
d("guard", """A shorter `ensure`, with a built-in error, for when the reason is clear from where the check is.

**Parameters**

- `ok`: the condition that must hold.

**Returns** `Ok(())` if it holds, otherwise an `Err` with code `MISSING` and the message "guard".""",
 ["guard(1 < 2)", "guard(2 < 1)"])
d("fail", """A failed `Result` with an error you make on the spot. The type of the success value is written in brackets.

**Parameters**

- `T` (in brackets): the type the `Result` would have held.
- `code`: an error code.
- `message` (optional): a description.

**Returns** an `Err`.""",
 ['fail[Int](4, "missing")', "fail[String](7)"])
d("traverse", """Applies a function that can fail to every item. If all succeed you get all the results; at the first failure you get that error and no more items are processed.

**Parameters**

- `f`: a function from an item to a `Result`.
- `xs`: the items.

**Returns** `Ok(list)` of the results, or the first `Err`.""",
 ['traverse((x) -> if x > 0 then Ok(x * 2) else fail[Int](6, "not positive"), List(1, 2, 3))', 'traverse((x) -> if x > 0 then Ok(x * 2) else fail[Int](6, "not positive"), List(1, 0, 3))'])
d("sequence", """Turns a list of `Result`s into one `Result` of a list: all the values if every item is `Ok`, otherwise the first error.

**Parameters**

- `rs`: the `Result`s.

**Returns** `Ok(list)` or the first `Err`.""",
 ["sequence(List(Ok(1), Ok(2)))", 'sequence(List(Ok(1), Err(Error(1, "x")), Ok(3)))'])
d("validate", """Like `traverse`, but it does not stop at the first failure: every item is tried and every error is reported. It suits checking a form, where you want to show all the mistakes at once.

**Parameters**

- `f`: a function from an item to a `Result`.
- `xs`: the items.

**Returns** `Ok(list)` if all succeed, otherwise `Err(list of every error)`.""",
 ['validate((x) -> if x > 0 then Ok(x) else fail[Int](6, "bad"), List(1, 2))', 'validate((x) -> if x > 0 then Ok(x) else fail[Int](6, "bad"), List(0, 2, -1)) |> map_err((es) -> len(es))'])
d("collect_errors", """Gathers a list of `Result`s into one: all the values if every item is `Ok`, otherwise all the errors, not just the first.

**Parameters**

- `rs`: the `Result`s.

**Returns** `Ok(values)` or `Err(errors)`.""",
 ["collect_errors(List(Ok(1), Ok(2)))", 'collect_errors(List(Ok(1), Err("a"), Err("b")))'])
d("partition_results", """Splits a list of `Result`s into the values and the errors, keeping the order. Nothing is lost and nothing fails; use it to keep going with what worked and report what did not.

**Parameters**

- `rs`: the `Result`s.

**Returns** a pair `(values, errors)`.""",
 ['partition_results(List(Ok(1), Err("a"), Ok(2)))'])
d("map_all", """Combines several `Result`s with a function, and reports every error if any failed, not only the first. Give it the function and then the `Result`s (two to six of them), or a tuple of `Result`s and then the function.

**Parameters**

- `f`: a function taking the values.
- the `Result`s, separately or as a tuple.

**Returns** `Ok(f(values))` if all are `Ok`, otherwise `Err(list of every error)`.""",
 ["map_all((a, b) -> a + b, Ok(1), Ok(2))", 'map_all((a, b) -> a + b, Err(Error(1, "x")), Err(Error(2, "y"))) |> map_err((es) -> len(es))'])
d("par_map_all", """Like `map_all`, but each input is a function that is run in its own fiber, so they run at the same time, and every error is collected. Give it the combining function and then two to six functions that each make a `Result`.

**Parameters**

- `f`: a function taking the values.
- `c1`, `c2`, ...: functions that take no arguments and return a `Result`.
- `limit:`: how many fibers may run at once, a constant of 1 or more.

**Returns** `Ok(f(values))` if all succeed, otherwise `Err(list of every error)`.""",
 ["par_map_all((a, b) -> a + b, () -> Ok(1), () -> Ok(2), limit: 2)"])
d("non_empty", """Checks that an `Option` or list has something in it, as a `Result`.

**Parameters**

- `x`: an `Option` or a `List`.

**Returns** for a list, `Ok` of a `NonEmpty` (a `head` and a `tail`, so the first item is always there); for an `Option`, `Ok(value)`. Otherwise an `Err` with code `MISSING`.""",
 ["non_empty(List(1))", "non_empty(List())"])
