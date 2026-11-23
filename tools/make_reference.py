#!/usr/bin/env python3
"""Build the Spec reference page (docs/reference.md, docs/gc/reference.md) and the term index the layout uses to link words in the
text to it (docs/_includes/terms.html).  Function signatures come from moxie/sigs.py, the checker's own table, so they cannot drift;
the one-line descriptions are written here.  Run: python3 tools/make_reference.py"""
import os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from moxie import sigs

# ---- keywords: name -> (description, spec section id)
HARD = [
 ("fn", "Declares a function, `fn name(params) Result = body`, or a function value.", "s9"),
 ("tuple", "Declares a tuple type with named fields.", "s6"),
 ("enum", "Declares an enum: a closed set of cases, each optionally carrying values.", "s6"),
 ("interface", "Declares an interface: the methods a type must have.", "s12"),
 ("impl", "Gives a type the methods of an interface (`impl Show for Point`).", "s12"),
 ("forward", "`forward fn` declares a function's signature ahead of its body, so earlier code can call it in a one-pass compile.", "s9"),
 ("inline", "`inline fn` marks a helper that is expanded where it is called; a helper that returns a stream must be one.", "s13"),
 ("fiber", "`fiber fn` declares a function that runs as its own fiber when started with `go`.", "s18"),
 ("import", "Brings in a package or some of its names.", "s4"),
 ("export", "Makes a name visible to the packages that import this one.", "s4"),
 ("internal", "Keeps a name visible inside its package but hidden from importers.", "s4"),
 ("using", "Puts a named value in scope for the code that follows, as in `using locale = Locale.de_de`.", "s5"),
 ("if", "Chooses between two expressions, `if c then a else b`, or between blocks.", "s1"),
 ("elif", "A further condition in an `if` chain.", "s1"),
 ("else", "The branch taken when no `if` or `elif` condition holds; also what a `for` loop yields when it ends without `break`.", "s1"),
 ("when", "Matches a value against patterns, one arm per pattern, and checks that every case is covered.", "s8"),
 ("select", "Waits on several channel, timer or future operations and runs the arm for the first that is ready.", "s17"),
 ("for", "Moxie's only loop: over a collection or range, or on a condition, and it can produce a value.", "s18"),
 ("while", "Reserved: writing it is an error that tells you to write `for`.", "s18"),
 ("in", "Separates the name from the collection in `for x in xs`, and tests membership.", "s18"),
 ("is", "Tests a value against a pattern and binds its names: `r is Ok(v)`.", "s8"),
 ("break", "Leaves the innermost loop, or the one named by a label; `break(value)` gives the loop a value.", "s18a"),
 ("continue", "Skips to the next pass of a loop, or of the loop named by a label.", "s18a"),
 ("return", "Leaves the function early with a value.", "s9"),
 ("daemon", "The main cycle of a server program, which runs until it is stopped.", "s16"),
 ("do", "Joins a one-line `for` header to its body, and opens a block that is itself an expression.", "s1"),
 ("go", "Starts a fiber: `go worker(args)` returns at once and the function runs concurrently.", "s18"),
 ("ref", "Marks a parameter that the function may rebind; the final value is copied back to the caller's variable.", "s9"),
 ("try_go", "Like `go`, but gives an Err (NO_SLOT) instead of waiting when the fiber function has no free slot.", "s18"),
 ("move", "Passes a resource to a new owner, so the old name can no longer use it.", "s19"),
 ("static", "Marks a function that belongs to a type and has no `self`, as in `static fn read(text String)`.", "s12"),
 ("and", "True when both sides are true; the right side is evaluated only if needed.", "s10"),
 ("or", "True when either side is true; the right side is evaluated only if needed.", "s10"),
 ("not", "Reverses a Bool.", "s10"),
 ("true", "The Bool value true.", "s5"),
 ("false", "The Bool value false.", "s5"),
 ("Self", "Inside an interface or impl, the type being described.", "s12"),
 ("self", "The receiver value inside a method.", "s12"),
 ("todo", "Stands for an expression of whatever type is expected, with an optional message; aborts if it runs.", "s2"),
]
SOFT = [
 ("end", "An optional line after a block that names the keyword that opened it, as in `end fn`.", "s1"),
 ("eval", "Opens an indented block of steps that are chained with `flat_map`.", "s23"),
 ("mutable", "Opens a block in which names may be updated in place and cannot leak out.", "s3"),
 ("deriving", "In a tuple or enum header, asks for generated methods such as `show`, `eq`, `ord` or `read`.", "s6"),
 ("delegate", "After a field's type, forwards the interface methods of that field.", "s12"),
 ("proxy", "After the target of an `impl ... for`, forwards the impl to a field: `proxy(field)`.", "s12"),
 ("closed", "A `select` arm that runs when a channel has been closed.", "s17"),
 ("cancelled", "A `select` arm that runs when a cancel token has been set.", "s17"),
 ("wait", "At the start of a statement, waits for the fibers started below it, or for a cancel token.", "s18"),
 ("as", "Renames a name in an import.", "s4"),
 ("type", "Declares a type alias, an opaque type or a union: `type Id = Int`.", "s6"),
 ("alias", "Follows `type` to make a second name for a type.", "s6"),
 ("opaque", "Follows `type` to make a type whose inside is hidden from other packages.", "s6"),
 ("union", "Follows `type` to declare a type that is any one of several types.", "s6"),
 ("step", "After a range, gives the stride: `0..10 step 5`.", "s5"),
 ("seq", "After `|>`, begins a stream pipeline written one stage per line.", "s13"),
 ("init", "Opens an initializer block that runs when its package loads.", "s4"),
 ("lazy", "Marks a parameter that is evaluated each time the function reads it, and not at all if it never does.", "s9"),
 ("foreign", "Opens a block of declarations for functions in a C library.", "s19a"),
 ("pure", "Function modifier: the function has no effects.", "s14"),
 ("prints", "Function modifier: the function may print, and nothing else.", "s14"),
 ("parks", "Function modifier: the function may wait, for example on a channel or the network.", "s14"),
 ("impure", "Function modifier: the function may have any effect.", "s14"),
 ("tailrec", "Function modifier: the function must call itself only in tail position, so it runs in constant stack.", "s9"),
 ("invariant", "A line among a tuple's fields that states a condition every value of the tuple must satisfy.", "s9c"),
 ("update", "After `x.` and before `:`, builds a copy of `x` with some fields changed.", "s6"),
 ("test", "At the start of a statement, before a string, declares a test block.", "s22"),
 ("where", "States a condition on a type parameter, a parameter or a result.", "s9c"),
 ("yield", "Gives one value of a `for` comprehension.", "s13"),
 ("any", "In a type, before an interface name, means a value of any type that has that interface.", "s12"),
]

# ---- types: name -> description
TYPES = [
 ("Int", "A whole number; `Int8` to `Int64` and `UInt8` to `UInt64` fix the width."),
 ("Double", "A 64-bit floating-point number; `Float` is the 32-bit one."),
 ("Decimal", "An exact base-ten number with a fixed scale, for money."),
 ("Bool", "true or false."),
 ("Char", "One Unicode scalar value, written `'a'`."),
 ("String", "Text, stored as UTF-8 and immutable."),
 ("Unit", "The type with one value, `()`, for a function that gives nothing back."),
 ("Duration", "A length of time, written `5s`, `250ms`, `1h`."),
 ("DateTime", "A calendar date and time of day."),
 ("Range", "A run of integers or characters, `1..5` or `0..<n`."),
 ("List", "An immutable sequence that shares structure when updated."),
 ("Array", "A fixed-size sequence of one type."),
 ("MultiArray", "An array with more than one dimension."),
 ("Set", "A collection of distinct values."),
 ("Dict", "A collection of key-value pairs."),
 ("Ring", "A fixed-capacity buffer that overwrites its oldest item when full."),
 ("Stream", "A lazy pipeline of values that runs when something consumes it."),
 ("Seq", "In a signature, any source of values: a List, Array, Set, Ring or Stream."),
 ("Option", "Some(value) or None: a value that may be absent."),
 ("Result", "Ok(value) or Err(error): the outcome of something that can fail."),
 ("Error", "The standard error value: a code and a message."),
 ("NonEmpty", "A list with a first item guaranteed, as `head` and `tail`."),
 ("Atom", "A shared cell whose value is replaced by `swap` and `reset`."),
 ("Future", "A value that will be supplied once, by `resolve` or `reject`."),
 ("Chan", "A channel between fibers; its read and write ends have separate owners."),
 ("Timer", "A resource that fires once or repeatedly after a duration."),
 ("Cancel", "A token that tells running fibers to stop."),
 ("Secret", "A value that cannot be printed or compared with `==`."),
 ("Io", "A readable and writable stream: a socket or a standard stream."),
 ("Listener", "A listening socket that gives connections through `accept`."),
 ("Gen", "A seeded source of values for property tests."),
]

# ---- functions: group -> (spec section, [(name, description)])
FUNCS = [
 ("Streams and sequences", "s13", [
  ("map", "Applies a function to each item (`Result` and `Option` too: it changes the value inside)."),
  ("fmap", "Like `map`, but a List stays a List and an Array an Array."),
  ("filter", "Keeps the items for which a test is true."),
  ("filter_map", "Applies a function that gives an Option and keeps the values that are present."),
  ("take", "The first n items."), ("drop", "All but the first n items."),
  ("take_while", "Items from the start while a test holds."), ("drop_while", "Skips items from the start while a test holds."),
  ("take_last", "The last n items."), ("drop_last", "All but the last n items."),
  ("enumerate", "Pairs each item with its position, from 0."),
  ("zip", "Pairs the items of two sources, stopping at the shorter."), ("zip3", "Triples the items of three sources."),
  ("zip_with", "Combines the items of two sources with a function."), ("unzip", "Splits a source of pairs into two Lists."),
  ("sort", "Orders the items by `<`, keeping equal items in their order."), ("sort_by", "Orders the items by a key function."),
  ("reverse", "The items in the opposite order."),
  ("reduce", "Folds the items into one value, from a start value and a combining function."),
  ("reduce_right", "Like `reduce`, folding from the end."), ("scan", "Like `reduce`, but gives every running value."),
  ("collect", "Gathers a stream into a List."),
  ("sum", "Adds the items."), ("product", "Multiplies the items."), ("count", "How many items there are."),
  ("avg", "The mean of the items, as a Float; an Err for an empty source."),
  ("any", "True if the test holds for at least one item."), ("all", "True if the test holds for every item."),
  ("find", "The first item for which a test is true; an Err if there is none."),
  ("find_map", "The first present value a function gives; an Err if there is none."),
  ("position", "The position of the first item that passes a test; an Err if none does."),
  ("first", "The first item; an Err if empty."), ("last", "The last item; an Err if empty."),
  ("min_by", "The item with the smallest key; an Err if empty."), ("max_by", "The item with the largest key; an Err if empty."),
  ("partition", "Splits the items into those that pass a test and those that don't."),
  ("span", "Splits at the first item that fails a test."), ("split_at", "Splits after the first n items."),
  ("distinct", "Drops repeated items, keeping the first of each."), ("distinct_by", "Drops items whose key has been seen."),
  ("flatten", "Turns a source of sources into one source."), ("cycle", "Repeats a source forever."),
  ("repeat", "One value, forever."), ("iterate", "A seed, then the function applied again and again."),
  ("intersperse", "Puts a separator between items."),
  ("chunks", "Groups the items in Lists of n."), ("windows", "Every run of n neighbouring items."),
  ("group_by", "A Dict from key to the Lists of items with that key."),
  ("frequencies", "A Dict of how many times each item occurs."), ("count_by", "A Dict of how many items have each key."),
  ("transpose", "Turns rows into columns."), ("to_stream", "Treats any collection as a stream."),
 ]),
 ("Collections", "s7", [
  ("len", "The number of items in a collection, or of bytes in a String."),
  ("is_empty", "True when there are no items."),
  ("get", "The item at a key or position; an Err if absent."),
  ("get_or", "The value, or a default when it is absent or an Err."),
  ("contains", "True if a String contains a piece of text, or a collection an item."),
  ("keys", "The keys of a Dict."), ("values", "The values of a Dict."), ("items", "The (key, value) pairs of a Dict."),
  ("set", "A copy with the item at a position or key replaced."),
  ("remove", "A copy without a key or item."), ("remove_at", "A copy without the item at a position."),
  ("clear", "An empty collection of the same kind."), ("indices", "The range of valid positions."),
  ("join", "Makes one String of the items, with an optional separator."),
  ("replace", "A copy with the value at a data path replaced."), ("modify", "A copy with the value at a data path changed by a function."),
 ]),
 ("Numbers", "s5", [
  ("abs", "Absolute value."), ("min", "The smaller of two values."), ("max", "The larger of two values."),
  ("clamp", "Limits a value to a low and high bound, or to a range."), ("pow", "A number raised to a power."),
  ("sqrt", "Square root."), ("floor", "Rounds down to an Int."), ("ceil", "Rounds up to an Int."), ("round", "Rounds to the nearest Int."),
  ("finite", "Ok(x) when x is a finite number, an Err otherwise."),
  ("is_nan", "True for not-a-number."), ("is_inf", "True for infinity."), ("is_finite", "True for an ordinary number."),
  ("checked_add", "Addition that gives an Err instead of overflowing."), ("checked_sub", "Subtraction that gives an Err instead of overflowing."),
  ("checked_mul", "Multiplication that gives an Err instead of overflowing."), ("checked_div", "Division that gives an Err for zero or overflow."),
  ("wrapping_add", "Addition that wraps around on overflow."), ("wrapping_sub", "Subtraction that wraps around on overflow."),
  ("wrapping_mul", "Multiplication that wraps around on overflow."),
  ("saturating_add", "Addition that stops at the largest or smallest value."), ("saturating_sub", "Subtraction that stops at the largest or smallest value."),
  ("saturating_mul", "Multiplication that stops at the largest or smallest value."),
  ("bit_and", "Bitwise and."), ("bit_or", "Bitwise or."), ("bit_xor", "Bitwise exclusive or."), ("bit_not", "Bitwise complement."),
  ("shl", "Shifts bits left."), ("shr", "Shifts bits right."),
  ("parse_number", "Reads a number from text, optionally in a locale's format; an Err if it isn't one."),
  ("random", "A Double in [0, 1)."), ("random_int", "An Int drawn uniformly from a range."), ("random_bytes", "n random bytes."),
  ("cast", "Converts a number to another numeric type, `cast[Double](n)`."),
  ("try_cast", "Like `cast`, but gives an Err (OUT_OF_RANGE) when the value does not fit."),
  ("wrap_to", "Converts to another width by keeping the low bits."),
  ("round_to", "Rounds a Decimal to a scale with a mode: `round_to[2](x, #half_even)`."),
  ("div", "Divides Decimals at a scale and mode; an Err for zero."),
 ]),
 ("Text", "s5", [
  ("upper", "Upper case."), ("lower", "Lower case."), ("trim", "Removes spaces from both ends."),
  ("chars", "The characters of a String."), ("graphemes", "The user-perceived characters of a String."),
  ("char_count", "How many characters."), ("grapheme_count", "How many user-perceived characters."),
  ("split", "Cuts a String at every separator."), ("split_once", "Cuts at the first separator; None if there is none."),
  ("starts_with", "True if the text begins with a prefix."), ("ends_with", "True if the text ends with a suffix."),
  ("strip_prefix", "The text without a prefix, or None if it doesn't start with it."),
  ("strip_suffix", "The text without a suffix, or None if it doesn't end with it."),
  ("pad_left", "Pads on the left to a width."), ("pad_right", "Pads on the right to a width."),
  ("replace_text", "Replaces every occurrence of one piece of text with another."),
  ("fmt", "Fills a template of `{}` slots with values."), ("try_fmt", "Like `fmt`, but gives an Err for a bad template."),
  ("show", "The printed form of a value, as a String."),
 ]),
 ("Results and options", "s15", [
  ("is_ok", "True for an Ok."), ("is_err", "True for an Err."),
  ("ok", "Turns a Result into an Option, dropping the error."), ("ok_or", "Turns an Option into a Result with a given error."),
  ("unwrap", "The value of an Ok; aborts on an Err."),
  ("map_ok", "Changes the value inside an Ok."), ("map_err", "Changes the error inside an Err."),
  ("or_else", "Tries a recovery function on an Err."), ("recover", "Turns an Err into a value with a function."),
  ("ensure", "Ok(()) when a condition holds, else Err(e)."), ("guard", "Ok(()) when a condition holds, else an Err with the code MISSING."),
  ("fail", "An Err with a code and optional message."),
  ("traverse", "Applies a Result-returning function to each item; stops at the first Err."),
  ("sequence", "Turns Results into one Result of a List; stops at the first Err."),
  ("validate", "Like `traverse`, but collects every error."), ("collect_errors", "Ok of all values, or Err of all errors."),
  ("partition_results", "Splits Results into the values and the errors."),
  ("map_all", "Combines two to six Results with a function, collecting all errors."),
  ("par_map_all", "Like `map_all`, with slow checks run in parallel."),
  ("non_empty", "Ok of a NonEmpty from a List, or an Err if it is empty."),
 ]),
 ("Functions and combinators", "s23", [
  ("identity", "Gives its argument back."), ("const", "A function that always gives one value."),
  ("flip", "Swaps the order of a two-parameter function's arguments."),
  ("tap", "Calls a function on a value for its effect and gives the value back."),
  ("fold_all", "Combines the items of a collection with their Monoid."), ("fold_map", "Maps each item to a Monoid value, then combines them."),
  ("hash", "A hash code for a value."), ("index", "The position of an enum case in its declaration."),
  ("secret_eq", "Compares two secrets in constant time."),
 ]),
 ("Concurrency", "s17", [
  ("swap", "Changes an Atom's value with a function and gives the new value."), ("reset", "Sets an Atom's value."),
  ("swap_vals", "Like `swap`, giving (old, new)."), ("reset_vals", "Like `reset`, giving (old, new)."),
  ("try_swap", "Like `swap`, with an Err instead of an abort."), ("try_reset", "Like `reset`, with an Err instead of an abort."),
  ("read", "Reads the next value from a channel, or waits for a future."), ("write", "Sends a value on a channel."),
  ("close", "Closes a channel end, file or socket."),
  ("resolve", "Supplies a future's value."), ("reject", "Supplies a future's error."),
  ("cancel", "Sets a cancel token."), ("after", "A timer that fires once after a duration."),
  ("arm", "Starts a timer."), ("arm_every", "Starts a timer that fires repeatedly."), ("disarm", "Stops a timer."),
  ("sleep", "Waits for a duration."),
  ("race", "Runs two functions; gives the first result and cancels the other."),
  ("with_timeout", "Gives a function's result, or Err(TIMED_OUT) if time runs out."),
  ("par_map", "Maps in parallel, at most `limit` at once, keeping order."), ("par_traverse", "Like `par_map` for Result-returning functions."),
  ("retry", "Calls a function up to n times, waiting between tries."),
 ]),
 ("Time", "s19e", [
  ("now", "The current time as a Duration since the epoch."), ("monotonic", "A steadily increasing clock, for measuring."),
  ("millis", "A Duration in milliseconds."), ("nanos", "A Duration in nanoseconds."), ("seconds", "A Duration in seconds."),
  ("weekday", "1 for Monday to 7 for Sunday."), ("day_of_year", "1 to 366."), ("days_in_month", "Days in a month, leap years included."),
  ("iso", "A DateTime as ISO 8601 text."), ("format_time", "A DateTime as text, from a pattern."),
  ("parse_iso", "Reads ISO 8601 text."), ("parse_time", "Reads text with a pattern."),
  ("to_instant", "A DateTime as a Duration since the epoch."), ("to_utc", "A Duration as a UTC DateTime."),
  ("to_local", "A Duration as a DateTime in the system's zone."), ("to_zone", "A Duration as a DateTime in a named zone."),
 ]),
 ("Files and paths", "s19c", [
  ("read_file", "A file's text."), ("write_file", "Writes text to a file."), ("make_dir", "Creates a directory."),
  ("remove_file", "Deletes a file."), ("remove_dir", "Deletes a directory."), ("rename_path", "Renames a file or directory."),
  ("list_dir", "The sorted names in a directory."), ("path_exists", "Ok(true) or Ok(false)."), ("file_info", "A file's kind and size."),
  ("path_join", "Joins path pieces."), ("path_name", "The last piece of a path."), ("path_parent", "A path without its last piece."),
  ("path_stem", "The file name without its extension."), ("path_ext", "The file name's extension."),
  ("cwd", "The current directory."), ("temp_dir", "The temporary directory."), ("home_dir", "The user's home directory."),
 ]),
 ("Input and output", "s19b", [
  ("println", "Prints a value and a newline."), ("print", "Prints a value."),
  ("eprintln", "Prints a value and a newline on standard error."), ("eprint", "Prints a value on standard error."),
  ("flush", "Sends buffered output on."), ("read_line", "The next line of input; an Err at the end."),
  ("read_all", "All the rest of the input."), ("stdin_lines", "The lines of standard input, as a stream."),
  ("lines", "The lines of a socket or file, as a stream."), ("read_bytes", "Up to n bytes."), ("write_bytes", "Writes bytes."),
  ("with_stdin", "Runs a function with given text as standard input."),
  ("raw_terminal", "Puts the terminal in raw mode."), ("read_key", "The next key pressed."),
 ]),
 ("Sockets and programs", "s19c", [
  ("listen", "Starts listening on a port."), ("accept", "Waits for a connection."), ("connect", "Opens a connection."),
  ("listen_tls", "Like `listen`, with TLS."), ("connect_tls", "Like `connect`, with TLS."), ("port_of", "The port a listener or socket uses."),
  ("bind_udp", "Opens a UDP socket."), ("send_to", "Sends one UDP datagram."), ("receive", "Waits for a UDP datagram."),
  ("spawn", "Starts another program."), ("wait_child", "Waits for it to end."), ("kill_child", "Stops it."),
  ("run_command", "Runs another program to the end and gives its output."),
  ("hostname", "This computer's name."), ("os_name", "The operating system's name."),
  ("wire_pair", "Two connected session endpoints."), ("wire_send", "Sends a value on a session endpoint."),
  ("wire_recv", "Receives a value on a session endpoint."), ("wire_close", "Closes a session endpoint."),
 ]),
 ("Testing and debugging", "s22", [
  ("assert", "Aborts if a condition is false."), ("assert_eq", "Aborts if two values differ."), ("assert_ne", "Aborts if two values are equal."),
  ("debug_assert", "An `assert` that a release build leaves out."), ("dbg", "Prints a value and where it came from, and gives the value back."),
  ("trace", "Prints a message with its place."),
  ("gen_int", "A generated Int between two bounds."), ("gen_bool", "A generated Bool."), ("gen_pick", "A generated pick from a List."),
 ]),
]
# signatures that the checker's table only approximates, or lacks
SIGS = {
 "const": "const[A, B](x A) (B) -> A", "index": "index(x Enum) Int", "hash": "hash[T](x T) Int",
 "read": "read[T](c ChanR[T]) Result[T, Error]\nread[T](f FutureR[T]) T",
 "cast": "cast[T](x Number) T", "try_cast": "try_cast[T](x Number) Result[T, Error]", "wrap_to": "wrap_to[T](x Number) T",
 "round_to": "round_to[n](x Decimal, mode Mode) Decimal", "div": "div(a Decimal, b Decimal, scale Int, mode Mode) Result[Decimal, Error]",
 "split_once": "split_once(s String, sep String) Option[(String, String)]",
 "strip_prefix": "strip_prefix(s String, prefix String) Option[String]", "strip_suffix": "strip_suffix(s String, suffix String) Option[String]",
 "fmt": "fmt(template String, args...) String", "try_fmt": "try_fmt(template String, args...) Result[String, Error]",
 "non_empty": "non_empty[T](xs List[T]) Result[NonEmpty[T], Error]",
 "fold_all": "fold_all[T Monoid](xs Seq[T]) T", "fold_map": "fold_map[T, M Monoid](f (T) -> M, xs Seq[T]) M",
 "secret_eq": "secret_eq[T](a Secret[T], b Secret[T]) Bool", "show": "show[T](x T) String",
 "par_map": "par_map[T, U](f (T) -> U, xs Seq[T], limit: Int) List[U]",
 "par_traverse": "par_traverse[T, U, E](f (T) -> Result[U, E], xs Seq[T], limit: Int) Result[List[U], E]",
 "race": "race[T](f (Cancel) -> T, g (Cancel) -> T) T", "tap": "tap[T, U](x T, f (T) -> U) T",
}
CONCEPTS = {}   # prose words -> spec section; filled in the layout script

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def md_inline(s):          # backtick spans to <code>
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", esc(s))

def load_sigs():
    d = {}
    for line in sigs.SRC.splitlines():
        m = re.match(r"fn (\w+)(.*?)( = 0)?$", line)
        if m: d.setdefault(m.group(1), []).append(m.group(1) + m.group(2))
    return d

def build(gc):
    S = load_sigs()
    name = "moxie/gc" if gc else "moxie"
    out = ["---", "layout: default", "toc: true", "terms: false"]
    if gc: out.append("dialect: gc")
    out += ['title: "%s Spec · keywords, types, and functions"' % name.capitalize(), "---", ""]
    out.append("# Spec reference: keywords, types, and functions")
    out.append("")
    out.append("This is part of the [%s Spec](spec.html). Every keyword, type and prelude function the text of this site mentions is described here, with its signature, and each word in the Mixer’s Guide and the intro links to its entry. A parameter written `Seq[T]` takes any source of `T` values: a `List`, `Array`, `Set`, `Ring` or `Stream`. Where a name has several signatures, each is listed." % name)
    out.append("")
    def kw_block(title, hid, items, lead):
        out.append("## %s {#%s}" % (title, hid)); out.append(""); out.append(lead); out.append("")
        out.append('<dl class="ref">')
        for n, d, sec in items:
            out.append('<dt id="kw-%s"><code>%s</code></dt>' % (n, esc(n)))
            out.append('<dd>%s <a href="spec.html#%s">Spec §%s</a></dd>' % (md_inline(d), sec, sec[1:].upper()))
        out.append("</dl>"); out.append("")
    kw_block("Hard keywords", "hard", HARD, "These %d words can never be names." % len(HARD))
    kw_block("Soft keywords", "soft", SOFT, "These %d words are keywords in one position only and are ordinary names elsewhere." % len(SOFT))
    out.append("## Types {#types}"); out.append("")
    out.append('<dl class="ref">')
    for n, d in TYPES:
        out.append('<dt id="ty-%s"><code>%s</code></dt><dd>%s</dd>' % (n, n, md_inline(d)))
    out.append("</dl>"); out.append("")
    index_fn = []
    for title, sec, items in FUNCS:
        out.append("## %s {#f-%s}" % (title, re.sub(r"[^a-z]+", "-", title.lower()).strip("-"))); out.append("")
        out.append('Spec <a href="spec.html#%s">§%s</a>.' % (sec, sec[1:].upper())); out.append("")
        out.append('<dl class="ref">')
        for n, d in items:
            sg = SIGS.get(n) or "\n".join(S.get(n, [n + "(…)"]))
            out.append('<dt id="fn-%s"><code>%s</code></dt>' % (n, esc(n)))
            out.append('<dd>%s<br><code class="sig">%s</code></dd>' % (md_inline(d), esc(sg)))
            index_fn.append(n)
        out.append("</dl>"); out.append("")
    missing = sorted(set(S) - set(index_fn))
    return "\n".join(out) + "\n", missing

def main():
    for gc in (False, True):
        text, missing = build(gc)
        p = os.path.join(ROOT, "docs", "gc" if gc else "", "reference.md")
        open(p, "w").write(text)
        if missing: print("no description for:", " ".join(missing))
    kws = sorted({n for n, _, _ in HARD} | {n for n, _, _ in SOFT})
    # (soft and hard keyword names don't clash; a name that is both a keyword and a function, such as any, lists both)
    fns = sorted({n for _, _, items in FUNCS for n, _ in items})
    tys = sorted(n for n, _ in TYPES)
    inc = "<script>window.MOXIE_TERMS=%s;</script>\n" % __import__("json").dumps({"kw": kws, "fn": fns, "ty": tys}, separators=(",", ":"))
    open(os.path.join(ROOT, "docs", "_includes", "terms.html"), "w").write(inc)
    print("keywords %d, types %d, functions %d" % (len(kws), len(tys), len(fns)))

if __name__ == "__main__":
    main()
