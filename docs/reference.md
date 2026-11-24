---
layout: default
toc: true
terms: false
refpage: true
title: "Moxie Spec · keywords, types, and functions"
---

# Spec reference: keywords, types, and functions

This is part of the [moxie Spec](spec.html). Every keyword, type and prelude function, in one alphabetical list: use the letters above to jump. Each word in the Mixer’s Guide and the intro links to its entry here. A parameter written `Seq[T]` takes any source of `T` values: a `List`, `Array`, `Set`, `Ring` or `Stream`. Where a name has several signatures, each is listed. A line starting `Effect:` says what a call does (prints, parks to wait, uses the system, or uses a resource); a function with no such line is pure. `Needs permission:` names what the program must be allowed to reach (Spec §19d). A type parameter written `T Ordered` must have that interface, and `Error` in a result is the standard error value.

<div class="az" aria-label="Jump to a letter"><a href="#a">a</a><a href="#b">b</a><a href="#c">c</a><a href="#d">d</a><a href="#e">e</a><a href="#f">f</a><a href="#g">g</a><a href="#h">h</a><a href="#i">i</a><a href="#j">j</a><a href="#k">k</a><a href="#l">l</a><a href="#m">m</a><a href="#n">n</a><a href="#o">o</a><a href="#p">p</a><span>q</span><a href="#r">r</a><a href="#s">s</a><a href="#t">t</a><a href="#u">u</a><a href="#v">v</a><a href="#w">w</a><span>x</span><a href="#y">y</a><a href="#z">z</a></div>

## A {#a}

<dl class="ref">
<dt id="fn-abs"><code>abs</code> <span class="tag">function</span></dt>
<dd>Absolute value. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn abs(n Int) Int
fn abs(x Double) Double</code></dd>
<dt id="fn-accept"><code>accept</code> <span class="tag">function</span></dt>
<dd>Waits for a connection. <a href="spec.html#s19c">Spec §19c</a><br><code class="sig">fn accept(l Listener) Result[Io, Error]</code><br><span class="eff">Effect: parks</span></dd>
<dt id="fn-after"><code>after</code> <span class="tag">function</span></dt>
<dd>A timer that fires once after a duration. <a href="spec.html#s17">Spec §17</a><br><code class="sig">fn after(d Duration) Timer</code><br><span class="eff">Effect: uses a resource</span></dd>
<dt id="kw-alias"><code>alias</code> <span class="tag">soft keyword</span></dt>
<dd>Follows <code>type</code> to make a second name for a type. <a href="spec.html#s6">Spec §6</a></dd>
<dt id="fn-all"><code>all</code> <span class="tag">function</span></dt>
<dd>True if the test holds for every item. <a href="spec.html#s13">Spec §13</a><br><code class="sig">fn all[T](f (T) -&gt; Bool, xs Seq[T]) Bool</code></dd>
<dt id="kw-and"><code>and</code> <span class="tag">hard keyword</span></dt>
<dd>True when both sides are true; the right side is evaluated only if needed. <a href="spec.html#s10">Spec §10</a></dd>
<dt id="kw-any"><code>any</code> <span class="tag">soft keyword</span></dt>
<dd>In a type, before an interface name, means a value of any type that has that interface. <a href="spec.html#s12">Spec §12</a></dd>
<dt id="fn-any"><code>any</code> <span class="tag">function</span></dt>
<dd>True if the test holds for at least one item. <a href="spec.html#s13">Spec §13</a><br><code class="sig">fn any[T](f (T) -&gt; Bool, xs Seq[T]) Bool</code></dd>
<dt id="fn-arm"><code>arm</code> <span class="tag">function</span></dt>
<dd>Starts a timer. <a href="spec.html#s17">Spec §17</a><br><code class="sig">fn arm(t Timer, d Duration) Unit</code><br><span class="eff">Effect: uses a resource</span></dd>
<dt id="fn-arm_every"><code>arm_every</code> <span class="tag">function</span></dt>
<dd>Starts a timer that fires repeatedly. <a href="spec.html#s17">Spec §17</a><br><code class="sig">fn arm_every(t Timer, d Duration) Unit</code><br><span class="eff">Effect: uses a resource</span></dd>
<dt id="ty-Array"><code>Array</code> <span class="tag">type</span></dt>
<dd>A fixed-size sequence of one type.</dd>
<dt id="kw-as"><code>as</code> <span class="tag">soft keyword</span></dt>
<dd>Renames a name in an import. <a href="spec.html#s4">Spec §4</a></dd>
<dt id="fn-assert"><code>assert</code> <span class="tag">function</span></dt>
<dd>Aborts if a condition is false. <a href="spec.html#s22">Spec §22</a><br><code class="sig">fn assert(ok Bool) Unit
fn assert(ok Bool, message String) Unit</code></dd>
<dt id="fn-assert_eq"><code>assert_eq</code> <span class="tag">function</span></dt>
<dd>Aborts if two values differ. <a href="spec.html#s22">Spec §22</a><br><code class="sig">fn assert_eq[T](a T, b T) Unit</code></dd>
<dt id="fn-assert_ne"><code>assert_ne</code> <span class="tag">function</span></dt>
<dd>Aborts if two values are equal. <a href="spec.html#s22">Spec §22</a><br><code class="sig">fn assert_ne[T](a T, b T) Unit</code></dd>
<dt id="ty-Atom"><code>Atom</code> <span class="tag">type</span></dt>
<dd>A shared cell whose value is replaced by <code>swap</code> and <code>reset</code>.</dd>
<dt id="fn-avg"><code>avg</code> <span class="tag">function</span></dt>
<dd>The mean of the items, as a Float; an Err for an empty source. <a href="spec.html#s13">Spec §13</a><br><code class="sig">fn avg(xs Seq[Int]) Result[Float, Error]
fn avg(xs Seq[Float]) Result[Float, Error]
fn avg(xs Seq[Decimal]) Result[Float, Error]</code></dd>
</dl>

## B {#b}

<dl class="ref">
<dt id="fn-bind_udp"><code>bind_udp</code> <span class="tag">function</span></dt>
<dd>Opens a UDP socket. <a href="spec.html#s19c">Spec §19c</a><br><code class="sig">fn bind_udp(port Int) Result[Udp, Error]</code><br><span class="eff">Effect: parks · Needs permission: net</span></dd>
<dt id="fn-bit_and"><code>bit_and</code> <span class="tag">function</span></dt>
<dd>Bitwise and. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn bit_and[T](a T, b T) T</code></dd>
<dt id="fn-bit_not"><code>bit_not</code> <span class="tag">function</span></dt>
<dd>Bitwise complement. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn bit_not[T](a T) T</code></dd>
<dt id="fn-bit_or"><code>bit_or</code> <span class="tag">function</span></dt>
<dd>Bitwise or. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn bit_or[T](a T, b T) T</code></dd>
<dt id="fn-bit_xor"><code>bit_xor</code> <span class="tag">function</span></dt>
<dd>Bitwise exclusive or. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn bit_xor[T](a T, b T) T</code></dd>
<dt id="ty-Bool"><code>Bool</code> <span class="tag">type</span></dt>
<dd>true or false.</dd>
<dt id="kw-break"><code>break</code> <span class="tag">hard keyword</span></dt>
<dd>Leaves the innermost loop, or the one named by a label; <code>break(value)</code> gives the loop a value. <a href="spec.html#s18a">Spec §18a</a></dd>
</dl>

## C {#c}

<dl class="ref">
<dt id="ty-Cancel"><code>Cancel</code> <span class="tag">type</span></dt>
<dd>A token that tells running fibers to stop.</dd>
<dt id="fn-cancel"><code>cancel</code> <span class="tag">function</span></dt>
<dd>Sets a cancel token. <a href="spec.html#s17">Spec §17</a><br><code class="sig">fn cancel(c Cancel) Unit</code><br><span class="eff">Effect: uses a resource</span></dd>
<dt id="kw-cancelled"><code>cancelled</code> <span class="tag">soft keyword</span></dt>
<dd>A <code>select</code> arm that runs when a cancel token has been set. <a href="spec.html#s17">Spec §17</a></dd>
<dt id="fn-cast"><code>cast</code> <span class="tag">function</span></dt>
<dd>Converts a number to another numeric type, <code>cast[Double](n)</code>. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn cast[T Numeric, N Numeric](x N) T</code></dd>
<dt id="fn-ceil"><code>ceil</code> <span class="tag">function</span></dt>
<dd>Rounds up to an Int. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn ceil(x Double) Int</code></dd>
<dt id="ty-Chan"><code>Chan</code> <span class="tag">type</span></dt>
<dd>A channel between fibers; its read and write ends have separate owners.</dd>
<dt id="ty-Char"><code>Char</code> <span class="tag">type</span></dt>
<dd>One Unicode scalar value, written <code>'a'</code>.</dd>
<dt id="fn-char_count"><code>char_count</code> <span class="tag">function</span></dt>
<dd>How many characters. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn char_count(s String) Int</code></dd>
<dt id="fn-chars"><code>chars</code> <span class="tag">function</span></dt>
<dd>The characters of a String. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn chars(s String) Stream[Char]</code></dd>
<dt id="fn-checked_add"><code>checked_add</code> <span class="tag">function</span></dt>
<dd>Addition that gives an Err instead of overflowing. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn checked_add[T](a T, b T) Result[T, Error]</code></dd>
<dt id="fn-checked_div"><code>checked_div</code> <span class="tag">function</span></dt>
<dd>Division that gives an Err for zero or overflow. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn checked_div[T](a T, b T) Result[T, Error]</code></dd>
<dt id="fn-checked_mul"><code>checked_mul</code> <span class="tag">function</span></dt>
<dd>Multiplication that gives an Err instead of overflowing. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn checked_mul[T](a T, b T) Result[T, Error]</code></dd>
<dt id="fn-checked_sub"><code>checked_sub</code> <span class="tag">function</span></dt>
<dd>Subtraction that gives an Err instead of overflowing. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn checked_sub[T](a T, b T) Result[T, Error]</code></dd>
<dt id="fn-chunks"><code>chunks</code> <span class="tag">function</span></dt>
<dd>Groups the items in Lists of n. <a href="spec.html#s13">Spec §13</a><br><code class="sig">fn chunks[T](n Int, xs Seq[T]) Stream[List[T]]</code></dd>
<dt id="fn-clamp"><code>clamp</code> <span class="tag">function</span></dt>
<dd>Limits a value to a low and high bound, or to a range. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn clamp[T](x T, lo T, hi T) T
fn clamp[T](x T, r Range) T</code></dd>
<dt id="fn-clear"><code>clear</code> <span class="tag">function</span></dt>
<dd>An empty collection of the same kind. <a href="spec.html#s7">Spec §7</a><br><code class="sig">fn clear[K, V](d Dict[K, V]) Dict[K, V]
fn clear[T](s Set[T]) Set[T]
fn clear[T](xs List[T]) List[T]</code></dd>
<dt id="fn-close"><code>close</code> <span class="tag">function</span></dt>
<dd>Closes a channel end, file or socket. <a href="spec.html#s17">Spec §17</a><br><code class="sig">fn close[T](x T) Unit</code><br><span class="eff">Effect: uses a resource</span></dd>
<dt id="kw-closed"><code>closed</code> <span class="tag">soft keyword</span></dt>
<dd>A <code>select</code> arm that runs when a channel has been closed. <a href="spec.html#s17">Spec §17</a></dd>
<dt id="fn-collect"><code>collect</code> <span class="tag">function</span></dt>
<dd>Gathers a stream into a List. <a href="spec.html#s13">Spec §13</a><br><code class="sig">fn collect[T](xs Seq[T]) List[T]</code></dd>
<dt id="fn-collect_errors"><code>collect_errors</code> <span class="tag">function</span></dt>
<dd>Ok of all values, or Err of all errors. <a href="spec.html#s15">Spec §15</a><br><code class="sig">fn collect_errors[T, E](rs Seq[Result[T, E]]) Result[List[T], List[E]]</code></dd>
<dt id="fn-connect"><code>connect</code> <span class="tag">function</span></dt>
<dd>Opens a connection. <a href="spec.html#s19c">Spec §19c</a><br><code class="sig">fn connect(host String, port Int) Result[Io, Error]</code><br><span class="eff">Effect: parks · Needs permission: net</span></dd>
<dt id="fn-connect_tls"><code>connect_tls</code> <span class="tag">function</span></dt>
<dd>Like <code>connect</code>, with TLS. <a href="spec.html#s19c">Spec §19c</a><br><code class="sig">fn connect_tls(host String, port Int) Result[Io, Error]</code><br><span class="eff">Effect: parks · Needs permission: net</span></dd>
<dt id="fn-const"><code>const</code> <span class="tag">function</span></dt>
<dd>A function that always gives one value. <a href="spec.html#s23">Spec §23</a><br><code class="sig">fn const[A, B](x A) (B) -&gt; A</code></dd>
<dt id="fn-contains"><code>contains</code> <span class="tag">function</span></dt>
<dd>True if a String contains a piece of text, or a collection an item. <a href="spec.html#s7">Spec §7</a><br><code class="sig">fn contains(s String, t String) Bool
fn contains[T Equatable](xs Seq[T], x T) Bool
fn contains[K, V](d Dict[K, V], k K) Bool</code></dd>
<dt id="kw-continue"><code>continue</code> <span class="tag">hard keyword</span></dt>
<dd>Skips to the next pass of a loop, or of the loop named by a label. <a href="spec.html#s18a">Spec §18a</a></dd>
<dt id="fn-count"><code>count</code> <span class="tag">function</span></dt>
<dd>How many items there are. <a href="spec.html#s13">Spec §13</a><br><code class="sig">fn count[T](xs Seq[T]) Int</code></dd>
<dt id="fn-count_by"><code>count_by</code> <span class="tag">function</span></dt>
<dd>A Dict of how many items have each key. <a href="spec.html#s13">Spec §13</a><br><code class="sig">fn count_by[T, K](f (T) -&gt; K, xs Seq[T]) Dict[K, Int]</code></dd>
<dt id="fn-cwd"><code>cwd</code> <span class="tag">function</span></dt>
<dd>The current directory. <a href="spec.html#s19c">Spec §19c</a><br><code class="sig">fn cwd() String</code><br><span class="eff">Effect: uses the system</span></dd>
<dt id="fn-cycle"><code>cycle</code> <span class="tag">function</span></dt>
<dd>Repeats a source forever. <a href="spec.html#s13">Spec §13</a><br><code class="sig">fn cycle[T](xs Seq[T]) Stream[T]</code></dd>
</dl>

## D {#d}

<dl class="ref">
<dt id="kw-daemon"><code>daemon</code> <span class="tag">hard keyword</span></dt>
<dd>The main cycle of a server program, which runs until it is stopped. <a href="spec.html#s16">Spec §16</a></dd>
<dt id="ty-DateTime"><code>DateTime</code> <span class="tag">type</span></dt>
<dd>A calendar date and time of day.</dd>
<dt id="fn-day_of_year"><code>day_of_year</code> <span class="tag">function</span></dt>
<dd>1 to 366. <a href="spec.html#s19e">Spec §19e</a><br><code class="sig">fn day_of_year(t DateTime) Int</code></dd>
<dt id="fn-days_in_month"><code>days_in_month</code> <span class="tag">function</span></dt>
<dd>Days in a month, leap years included. <a href="spec.html#s19e">Spec §19e</a><br><code class="sig">fn days_in_month(y Int, m Int) Int</code></dd>
<dt id="fn-dbg"><code>dbg</code> <span class="tag">function</span></dt>
<dd>Prints a value and where it came from, and gives the value back. <a href="spec.html#s22">Spec §22</a><br><code class="sig">fn dbg[T](x T) T</code><br><span class="eff">Effect: prints, but is allowed in any code</span></dd>
<dt id="fn-debug_assert"><code>debug_assert</code> <span class="tag">function</span></dt>
<dd>An <code>assert</code> that a release build leaves out. <a href="spec.html#s22">Spec §22</a><br><code class="sig">fn debug_assert(ok Bool) Unit</code></dd>
<dt id="ty-Decimal"><code>Decimal</code> <span class="tag">type</span></dt>
<dd>An exact base-ten number with a fixed scale, for money.</dd>
<dt id="kw-delegate"><code>delegate</code> <span class="tag">soft keyword</span></dt>
<dd>After a field's type, forwards the interface methods of that field. <a href="spec.html#s12">Spec §12</a></dd>
<dt id="kw-deriving"><code>deriving</code> <span class="tag">soft keyword</span></dt>
<dd>In a tuple or enum header, asks for generated methods such as <code>show</code>, <code>eq</code>, <code>ord</code> or <code>read</code>. <a href="spec.html#s6">Spec §6</a></dd>
<dt id="ty-Dict"><code>Dict</code> <span class="tag">type</span></dt>
<dd>A collection of key-value pairs.</dd>
<dt id="fn-disarm"><code>disarm</code> <span class="tag">function</span></dt>
<dd>Stops a timer. <a href="spec.html#s17">Spec §17</a><br><code class="sig">fn disarm(t Timer) Unit</code><br><span class="eff">Effect: uses a resource</span></dd>
<dt id="fn-distinct"><code>distinct</code> <span class="tag">function</span></dt>
<dd>Drops repeated items, keeping the first of each. <a href="spec.html#s13">Spec §13</a><br><code class="sig">fn distinct[T Equatable](xs Seq[T]) Stream[T]</code></dd>
<dt id="fn-distinct_by"><code>distinct_by</code> <span class="tag">function</span></dt>
<dd>Drops items whose key has been seen. <a href="spec.html#s13">Spec §13</a><br><code class="sig">fn distinct_by[T, K](f (T) -&gt; K, xs Seq[T]) Stream[T]</code></dd>
<dt id="fn-div"><code>div</code> <span class="tag">function</span></dt>
<dd>Divides Decimals to a scale and <code>Mode</code>; an Err for division by zero. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn div(a Decimal, b Decimal, scale Int, mode Mode) Result[Decimal, Error]</code></dd>
<dt id="kw-do"><code>do</code> <span class="tag">hard keyword</span></dt>
<dd>Joins a one-line <code>for</code> header to its body, and opens a block that is itself an expression. <a href="spec.html#s1">Spec §1</a></dd>
<dt id="ty-Double"><code>Double</code> <span class="tag">type</span></dt>
<dd>A 64-bit floating-point number; <code>Float</code> is the 32-bit one.</dd>
<dt id="fn-drop"><code>drop</code> <span class="tag">function</span></dt>
<dd>All but the first n items. <a href="spec.html#s13">Spec §13</a><br><code class="sig">fn drop[T](n Int, xs Seq[T]) Stream[T]</code></dd>
<dt id="fn-drop_last"><code>drop_last</code> <span class="tag">function</span></dt>
<dd>All but the last n items. <a href="spec.html#s13">Spec §13</a><br><code class="sig">fn drop_last[T](n Int, xs Seq[T]) Stream[T]</code></dd>
<dt id="fn-drop_while"><code>drop_while</code> <span class="tag">function</span></dt>
<dd>Skips items from the start while a test holds. <a href="spec.html#s13">Spec §13</a><br><code class="sig">fn drop_while[T](f (T) -&gt; Bool, xs Seq[T]) Stream[T]</code></dd>
<dt id="ty-Duration"><code>Duration</code> <span class="tag">type</span></dt>
<dd>A length of time, written <code>5s</code>, <code>250ms</code>, <code>1h</code>.</dd>
</dl>

## E {#e}

<dl class="ref">
<dt id="kw-elif"><code>elif</code> <span class="tag">hard keyword</span></dt>
<dd>A further condition in an <code>if</code> chain. <a href="spec.html#s1">Spec §1</a></dd>
<dt id="kw-else"><code>else</code> <span class="tag">hard keyword</span></dt>
<dd>The branch taken when no <code>if</code> or <code>elif</code> condition holds; also what a <code>for</code> loop yields when it ends without <code>break</code>. <a href="spec.html#s1">Spec §1</a></dd>
<dt id="kw-end"><code>end</code> <span class="tag">soft keyword</span></dt>
<dd>An optional line after a block that names the keyword that opened it, as in <code>end fn</code>. <a href="spec.html#s1">Spec §1</a></dd>
<dt id="fn-ends_with"><code>ends_with</code> <span class="tag">function</span></dt>
<dd>True if the text ends with a suffix. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn ends_with(s String, suffix String) Bool
fn ends_with(s String, c Char) Bool</code></dd>
<dt id="fn-ensure"><code>ensure</code> <span class="tag">function</span></dt>
<dd>Ok(()) when a condition holds, else Err(e). <a href="spec.html#s15">Spec §15</a><br><code class="sig">fn ensure[E](ok Bool, e E) Result[Unit, E]</code></dd>
<dt id="kw-enum"><code>enum</code> <span class="tag">hard keyword</span></dt>
<dd>Declares an enum: a closed set of cases, each optionally carrying values. <a href="spec.html#s6">Spec §6</a></dd>
<dt id="fn-enumerate"><code>enumerate</code> <span class="tag">function</span></dt>
<dd>Pairs each item with its position, from 0. <a href="spec.html#s13">Spec §13</a><br><code class="sig">fn enumerate[T](xs Seq[T]) Stream[(Int, T)]</code></dd>
<dt id="fn-eprint"><code>eprint</code> <span class="tag">function</span></dt>
<dd>Prints a value on standard error. <a href="spec.html#s19b">Spec §19b</a><br><code class="sig">fn eprint[T](x T) Unit
fn eprint[T](out Io, x T) Unit</code><br><span class="eff">Effect: prints</span></dd>
<dt id="fn-eprintln"><code>eprintln</code> <span class="tag">function</span></dt>
<dd>Prints a value and a newline on standard error. <a href="spec.html#s19b">Spec §19b</a><br><code class="sig">fn eprintln() Unit
fn eprintln[T](x T) Unit
fn eprintln[T](out Io, x T) Unit</code><br><span class="eff">Effect: prints</span></dd>
<dt id="ty-Error"><code>Error</code> <span class="tag">type</span></dt>
<dd>The standard error value: a code and a message.</dd>
<dt id="kw-eval"><code>eval</code> <span class="tag">soft keyword</span></dt>
<dd>Opens an indented block of steps that are chained with <code>flat_map</code>. <a href="spec.html#s23">Spec §23</a></dd>
<dt id="kw-export"><code>export</code> <span class="tag">hard keyword</span></dt>
<dd>Makes a name visible to the packages that import this one. <a href="spec.html#s4">Spec §4</a></dd>
</dl>

## F {#f}

<dl class="ref">
<dt id="fn-fail"><code>fail</code> <span class="tag">function</span></dt>
<dd>An Err with a code and optional message. <a href="spec.html#s15">Spec §15</a><br><code class="sig">fn fail[T](code Int) Result[T, Error]
fn fail[T](code Int, message String) Result[T, Error]</code></dd>
<dt id="kw-false"><code>false</code> <span class="tag">hard keyword</span></dt>
<dd>The Bool value false. <a href="spec.html#s5">Spec §5</a></dd>
<dt id="kw-fiber"><code>fiber</code> <span class="tag">hard keyword</span></dt>
<dd><code>fiber fn</code> declares a function that runs as its own fiber when started with <code>go</code>. <a href="spec.html#s18">Spec §18</a></dd>
<dt id="fn-file_info"><code>file_info</code> <span class="tag">function</span></dt>
<dd>A file's kind and size. <a href="spec.html#s19c">Spec §19c</a><br><code class="sig">fn file_info(p String) Result[FileInfo, Error]</code><br><span class="eff">Effect: parks · Needs permission: fs</span></dd>
<dt id="fn-filter"><code>filter</code> <span class="tag">function</span></dt>
<dd>Keeps the items for which a test is true. <a href="spec.html#s13">Spec §13</a><br><code class="sig">fn filter[T](f (T) -&gt; Bool, xs Seq[T]) Stream[T]</code></dd>
<dt id="fn-filter_map"><code>filter_map</code> <span class="tag">function</span></dt>
<dd>Applies a function that gives an Option and keeps the values that are present. <a href="spec.html#s13">Spec §13</a><br><code class="sig">fn filter_map[T, U](f (T) -&gt; Option[U], xs Seq[T]) Stream[U]</code></dd>
<dt id="fn-find"><code>find</code> <span class="tag">function</span></dt>
<dd>The first item for which a test is true; an Err if there is none. <a href="spec.html#s13">Spec §13</a><br><code class="sig">fn find[T](f (T) -&gt; Bool, xs Seq[T]) Result[T, Error]</code></dd>
<dt id="fn-find_map"><code>find_map</code> <span class="tag">function</span></dt>
<dd>The first present value a function gives; an Err if there is none. <a href="spec.html#s13">Spec §13</a><br><code class="sig">fn find_map[T, U](f (T) -&gt; Option[U], xs Seq[T]) Result[U, Error]</code></dd>
<dt id="fn-finite"><code>finite</code> <span class="tag">function</span></dt>
<dd>Ok(x) when x is a finite number, an Err otherwise. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn finite(x Double) Result[Double, Error]</code></dd>
<dt id="fn-first"><code>first</code> <span class="tag">function</span></dt>
<dd>The first item; an Err if empty. <a href="spec.html#s13">Spec §13</a><br><code class="sig">fn first[T](xs Seq[T]) Result[T, Error]</code></dd>
<dt id="fn-flatten"><code>flatten</code> <span class="tag">function</span></dt>
<dd>Turns a source of sources into one source. <a href="spec.html#s13">Spec §13</a><br><code class="sig">fn flatten[T](xs Seq[Seq[T]]) Stream[T]</code></dd>
<dt id="fn-flip"><code>flip</code> <span class="tag">function</span></dt>
<dd>Swaps the order of a two-parameter function's arguments. <a href="spec.html#s23">Spec §23</a><br><code class="sig">fn flip[A, B, R](f (A, B) -&gt; R) (B, A) -&gt; R</code></dd>
<dt id="fn-floor"><code>floor</code> <span class="tag">function</span></dt>
<dd>Rounds down to an Int. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn floor(x Double) Int</code></dd>
<dt id="fn-flush"><code>flush</code> <span class="tag">function</span></dt>
<dd>Sends buffered output on. <a href="spec.html#s19b">Spec §19b</a><br><code class="sig">fn flush() Unit
fn flush(out Io) Unit</code></dd>
<dt id="fn-fmap"><code>fmap</code> <span class="tag">function</span></dt>
<dd>Like <code>map</code>, but a List stays a List and an Array an Array. <a href="spec.html#s13">Spec §13</a><br><code class="sig">fn fmap[T, U](f (T) -&gt; U, xs List[T]) List[U]
fn fmap[T, U, N](f (T) -&gt; U, xs Array[T][N]) Array[U][N]
fn fmap[T, U](f (T) -&gt; U, o Option[T]) Option[U]
fn fmap[T, U](f (T) -&gt; U, r Result[T, Error]) Result[U, Error]</code></dd>
<dt id="fn-fmt"><code>fmt</code> <span class="tag">function</span></dt>
<dd>Fills a template of <code>{}</code> slots with values. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn fmt(template String, args...) String</code></dd>
<dt id="kw-fn"><code>fn</code> <span class="tag">hard keyword</span></dt>
<dd>Declares a function, <code>fn name(params) Result = body</code>, or a function value. <a href="spec.html#s9">Spec §9</a></dd>
<dt id="fn-fold_all"><code>fold_all</code> <span class="tag">function</span></dt>
<dd>Combines the items of a collection with their Monoid. <a href="spec.html#s23">Spec §23</a><br><code class="sig">fn fold_all[T Monoid](xs Seq[T]) T</code></dd>
<dt id="fn-fold_map"><code>fold_map</code> <span class="tag">function</span></dt>
<dd>Maps each item to a Monoid value, then combines them. <a href="spec.html#s23">Spec §23</a><br><code class="sig">fn fold_map[T, M Monoid](f (T) -&gt; M, xs Seq[T]) M</code></dd>
<dt id="kw-for"><code>for</code> <span class="tag">hard keyword</span></dt>
<dd>Moxie's only loop: over a collection or range, or on a condition, and it can produce a value. <a href="spec.html#s18">Spec §18</a></dd>
<dt id="kw-foreign"><code>foreign</code> <span class="tag">soft keyword</span></dt>
<dd>Opens a block of declarations for functions in a C library. <a href="spec.html#s19a">Spec §19a</a></dd>
<dt id="fn-format_time"><code>format_time</code> <span class="tag">function</span></dt>
<dd>A DateTime as text, from a pattern. <a href="spec.html#s19e">Spec §19e</a><br><code class="sig">fn format_time(t DateTime, fmt String) String
fn format_time(t DateTime, fmt String, loc Locale) String</code></dd>
<dt id="kw-forward"><code>forward</code> <span class="tag">hard keyword</span></dt>
<dd><code>forward fn</code> declares a function's signature ahead of its body, so earlier code can call it in a one-pass compile. <a href="spec.html#s9">Spec §9</a></dd>
<dt id="fn-frequencies"><code>frequencies</code> <span class="tag">function</span></dt>
<dd>A Dict of how many times each item occurs. <a href="spec.html#s13">Spec §13</a><br><code class="sig">fn frequencies[T](xs Seq[T]) Dict[T, Int]</code></dd>
<dt id="ty-Future"><code>Future</code> <span class="tag">type</span></dt>
<dd>A value that will be supplied once, by <code>resolve</code> or <code>reject</code>.</dd>
</dl>

## G {#g}

<dl class="ref">
<dt id="ty-Gen"><code>Gen</code> <span class="tag">type</span></dt>
<dd>A seeded source of values for property tests.</dd>
<dt id="fn-gen_bool"><code>gen_bool</code> <span class="tag">function</span></dt>
<dd>A generated Bool. <a href="spec.html#s22">Spec §22</a><br><code class="sig">fn gen_bool(g Gen) Bool</code></dd>
<dt id="fn-gen_int"><code>gen_int</code> <span class="tag">function</span></dt>
<dd>A generated Int between two bounds. <a href="spec.html#s22">Spec §22</a><br><code class="sig">fn gen_int[T](g Gen, lo T, hi T) T</code></dd>
<dt id="fn-gen_pick"><code>gen_pick</code> <span class="tag">function</span></dt>
<dd>A generated pick from a List. <a href="spec.html#s22">Spec §22</a><br><code class="sig">fn gen_pick[T](g Gen, xs List[T]) T</code></dd>
<dt id="fn-get"><code>get</code> <span class="tag">function</span></dt>
<dd>The item at a key or position; an Err if absent. <a href="spec.html#s7">Spec §7</a><br><code class="sig">fn get[K, V](d Dict[K, V], k K) Result[V, Error]
fn get[T](xs List[T], i Int) Result[T, Error]
fn get[T](xs Array[T], i Int) Result[T, Error]</code></dd>
<dt id="fn-get_or"><code>get_or</code> <span class="tag">function</span></dt>
<dd>The value, or a default when it is absent or an Err. <a href="spec.html#s7">Spec §7</a><br><code class="sig">fn get_or[T, E](r Result[T, E], d T) T
fn get_or[T](o Option[T], d T) T
fn get_or[K, V](d Dict[K, V], k K, d2 V) V
fn get_or[T](xs List[T], i Int, d T) T</code></dd>
<dt id="kw-go"><code>go</code> <span class="tag">hard keyword</span></dt>
<dd>Starts a fiber: <code>go worker(args)</code> returns at once and the function runs concurrently. <a href="spec.html#s18">Spec §18</a></dd>
<dt id="fn-grapheme_count"><code>grapheme_count</code> <span class="tag">function</span></dt>
<dd>How many user-perceived characters. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn grapheme_count(s String) Int</code></dd>
<dt id="fn-graphemes"><code>graphemes</code> <span class="tag">function</span></dt>
<dd>The user-perceived characters of a String. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn graphemes(s String) Stream[String]</code></dd>
<dt id="fn-group_by"><code>group_by</code> <span class="tag">function</span></dt>
<dd>A Dict from key to the Lists of items with that key. <a href="spec.html#s13">Spec §13</a><br><code class="sig">fn group_by[T, K](f (T) -&gt; K, xs Seq[T]) Dict[K, List[T]]</code></dd>
<dt id="fn-guard"><code>guard</code> <span class="tag">function</span></dt>
<dd>Ok(()) when a condition holds, else an Err with the code MISSING. <a href="spec.html#s15">Spec §15</a><br><code class="sig">fn guard(ok Bool) Result[Unit, Error]</code></dd>
</dl>

## H {#h}

<dl class="ref">
<dt id="fn-hash"><code>hash</code> <span class="tag">function</span></dt>
<dd>A hash code for a value. <a href="spec.html#s23">Spec §23</a><br><code class="sig">fn hash[T](x T) Int</code></dd>
<dt id="fn-home_dir"><code>home_dir</code> <span class="tag">function</span></dt>
<dd>The user's home directory. <a href="spec.html#s19c">Spec §19c</a><br><code class="sig">fn home_dir() Result[String, Error]</code><br><span class="eff">Effect: uses the system</span></dd>
<dt id="fn-hostname"><code>hostname</code> <span class="tag">function</span></dt>
<dd>This computer's name. <a href="spec.html#s19c">Spec §19c</a><br><code class="sig">fn hostname() String</code><br><span class="eff">Effect: uses the system</span></dd>
</dl>

## I {#i}

<dl class="ref">
<dt id="fn-identity"><code>identity</code> <span class="tag">function</span></dt>
<dd>Gives its argument back. <a href="spec.html#s23">Spec §23</a><br><code class="sig">fn identity[T](x T) T</code></dd>
<dt id="kw-if"><code>if</code> <span class="tag">hard keyword</span></dt>
<dd>Chooses between two expressions, <code>if c then a else b</code>, or between blocks. <a href="spec.html#s1">Spec §1</a></dd>
<dt id="kw-impl"><code>impl</code> <span class="tag">hard keyword</span></dt>
<dd>Gives a type the methods of an interface (<code>impl Show for Point</code>). <a href="spec.html#s12">Spec §12</a></dd>
<dt id="kw-import"><code>import</code> <span class="tag">hard keyword</span></dt>
<dd>Brings in a package or some of its names. <a href="spec.html#s4">Spec §4</a></dd>
<dt id="kw-impure"><code>impure</code> <span class="tag">soft keyword</span></dt>
<dd>Function modifier: the function may have any effect. <a href="spec.html#s14">Spec §14</a></dd>
<dt id="kw-in"><code>in</code> <span class="tag">hard keyword</span></dt>
<dd>Separates the name from the collection in <code>for x in xs</code>, and tests membership. <a href="spec.html#s18">Spec §18</a></dd>
<dt id="fn-index"><code>index</code> <span class="tag">function</span></dt>
<dd>The position of an enum case in its declaration. <a href="spec.html#s23">Spec §23</a><br><code class="sig">fn index[E](x E) Int</code></dd>
<dt id="fn-indices"><code>indices</code> <span class="tag">function</span></dt>
<dd>The range of valid positions. <a href="spec.html#s7">Spec §7</a><br><code class="sig">fn indices[T](xs Seq[T]) Range
fn indices(s String) Range</code></dd>
<dt id="kw-init"><code>init</code> <span class="tag">soft keyword</span></dt>
<dd>Opens an initializer block that runs when its package loads. <a href="spec.html#s4">Spec §4</a></dd>
<dt id="kw-inline"><code>inline</code> <span class="tag">hard keyword</span></dt>
<dd><code>inline fn</code> marks a helper that is expanded where it is called; a helper that returns a stream must be one. <a href="spec.html#s13">Spec §13</a></dd>
<dt id="ty-Int"><code>Int</code> <span class="tag">type</span></dt>
<dd>A whole number; <code>Int8</code> to <code>Int64</code> and <code>UInt8</code> to <code>UInt64</code> fix the width.</dd>
<dt id="kw-interface"><code>interface</code> <span class="tag">hard keyword</span></dt>
<dd>Declares an interface: the methods a type must have. <a href="spec.html#s12">Spec §12</a></dd>
<dt id="kw-internal"><code>internal</code> <span class="tag">hard keyword</span></dt>
<dd>Keeps a name visible inside its package but hidden from importers. <a href="spec.html#s4">Spec §4</a></dd>
<dt id="fn-intersperse"><code>intersperse</code> <span class="tag">function</span></dt>
<dd>Puts a separator between items. <a href="spec.html#s13">Spec §13</a><br><code class="sig">fn intersperse[T](sep T, xs Seq[T]) Stream[T]</code></dd>
<dt id="kw-invariant"><code>invariant</code> <span class="tag">soft keyword</span></dt>
<dd>A line among a tuple's fields that states a condition every value of the tuple must satisfy. <a href="spec.html#s9c">Spec §9c</a></dd>
<dt id="ty-Io"><code>Io</code> <span class="tag">type</span></dt>
<dd>A readable and writable stream: a socket or a standard stream.</dd>
<dt id="kw-is"><code>is</code> <span class="tag">hard keyword</span></dt>
<dd>Tests a value against a pattern and binds its names: <code>r is Ok(v)</code>. <a href="spec.html#s8">Spec §8</a></dd>
<dt id="fn-is_empty"><code>is_empty</code> <span class="tag">function</span></dt>
<dd>True when there are no items. <a href="spec.html#s7">Spec §7</a><br><code class="sig">fn is_empty(s String) Bool
fn is_empty[T](xs Seq[T]) Bool
fn is_empty[K, V](d Dict[K, V]) Bool
fn is_empty[T](s Set[T]) Bool</code></dd>
<dt id="fn-is_err"><code>is_err</code> <span class="tag">function</span></dt>
<dd>True for an Err. <a href="spec.html#s15">Spec §15</a><br><code class="sig">fn is_err[T, E](r Result[T, E]) Bool</code></dd>
<dt id="fn-is_finite"><code>is_finite</code> <span class="tag">function</span></dt>
<dd>True for an ordinary number. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn is_finite(x Double) Bool</code></dd>
<dt id="fn-is_inf"><code>is_inf</code> <span class="tag">function</span></dt>
<dd>True for infinity. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn is_inf(x Double) Bool</code></dd>
<dt id="fn-is_nan"><code>is_nan</code> <span class="tag">function</span></dt>
<dd>True for not-a-number. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn is_nan(x Double) Bool</code></dd>
<dt id="fn-is_ok"><code>is_ok</code> <span class="tag">function</span></dt>
<dd>True for an Ok. <a href="spec.html#s15">Spec §15</a><br><code class="sig">fn is_ok[T, E](r Result[T, E]) Bool</code></dd>
<dt id="fn-iso"><code>iso</code> <span class="tag">function</span></dt>
<dd>A DateTime as ISO 8601 text. <a href="spec.html#s19e">Spec §19e</a><br><code class="sig">fn iso(t DateTime) String</code></dd>
<dt id="fn-items"><code>items</code> <span class="tag">function</span></dt>
<dd>The (key, value) pairs of a Dict. <a href="spec.html#s7">Spec §7</a><br><code class="sig">fn items[K, V](d Dict[K, V]) Stream[(K, V)]</code></dd>
<dt id="fn-iterate"><code>iterate</code> <span class="tag">function</span></dt>
<dd>A seed, then the function applied again and again. <a href="spec.html#s13">Spec §13</a><br><code class="sig">fn iterate[T](seed T, f (T) -&gt; T) Stream[T]</code></dd>
</dl>

## J {#j}

<dl class="ref">
<dt id="fn-join"><code>join</code> <span class="tag">function</span></dt>
<dd>Makes one String of the items, with an optional separator. <a href="spec.html#s7">Spec §7</a><br><code class="sig">fn join[T](xs Seq[T], sep String) String
fn join[T](xs Seq[T]) String</code></dd>
</dl>

## K {#k}

<dl class="ref">
<dt id="fn-keys"><code>keys</code> <span class="tag">function</span></dt>
<dd>The keys of a Dict. <a href="spec.html#s7">Spec §7</a><br><code class="sig">fn keys[K, V](d Dict[K, V]) Stream[K]</code></dd>
<dt id="fn-kill_child"><code>kill_child</code> <span class="tag">function</span></dt>
<dd>Stops it. <a href="spec.html#s19c">Spec §19c</a><br><code class="sig">fn kill_child(c Child) Unit</code><br><span class="eff">Effect: parks</span></dd>
</dl>

## L {#l}

<dl class="ref">
<dt id="fn-last"><code>last</code> <span class="tag">function</span></dt>
<dd>The last item; an Err if empty. <a href="spec.html#s13">Spec §13</a><br><code class="sig">fn last[T](xs Seq[T]) Result[T, Error]</code></dd>
<dt id="kw-lazy"><code>lazy</code> <span class="tag">soft keyword</span></dt>
<dd>Marks a parameter that is evaluated each time the function reads it, and not at all if it never does. <a href="spec.html#s9">Spec §9</a></dd>
<dt id="fn-len"><code>len</code> <span class="tag">function</span></dt>
<dd>The number of items in a collection, or of bytes in a String. <a href="spec.html#s7">Spec §7</a><br><code class="sig">fn len(s String) Int
fn len[T](xs Seq[T]) Int
fn len[K, V](d Dict[K, V]) Int</code></dd>
<dt id="fn-lines"><code>lines</code> <span class="tag">function</span></dt>
<dd>The lines of a socket or file, as a stream. <a href="spec.html#s19b">Spec §19b</a><br><code class="sig">fn lines(src Io) Stream[String]</code><br><span class="eff">Effect: parks</span></dd>
<dt id="ty-List"><code>List</code> <span class="tag">type</span></dt>
<dd>An immutable sequence that shares structure when updated.</dd>
<dt id="fn-list_dir"><code>list_dir</code> <span class="tag">function</span></dt>
<dd>The sorted names in a directory. <a href="spec.html#s19c">Spec §19c</a><br><code class="sig">fn list_dir(p String) Result[Array[String], Error]</code><br><span class="eff">Effect: parks · Needs permission: fs</span></dd>
<dt id="fn-listen"><code>listen</code> <span class="tag">function</span></dt>
<dd>Starts listening on a port. <a href="spec.html#s19c">Spec §19c</a><br><code class="sig">fn listen(port Int) Result[Listener, Error]</code><br><span class="eff">Effect: parks · Needs permission: net</span></dd>
<dt id="fn-listen_tls"><code>listen_tls</code> <span class="tag">function</span></dt>
<dd>Like <code>listen</code>, with TLS. <a href="spec.html#s19c">Spec §19c</a><br><code class="sig">fn listen_tls(port Int, cert String, key String) Result[Listener, Error]</code><br><span class="eff">Effect: parks · Needs permission: net</span></dd>
<dt id="ty-Listener"><code>Listener</code> <span class="tag">type</span></dt>
<dd>A listening socket that gives connections through <code>accept</code>.</dd>
<dt id="fn-lower"><code>lower</code> <span class="tag">function</span></dt>
<dd>Lower case. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn lower(s String) String
fn lower(c Char) Char</code></dd>
</dl>

## M {#m}

<dl class="ref">
<dt id="fn-make_dir"><code>make_dir</code> <span class="tag">function</span></dt>
<dd>Creates a directory. <a href="spec.html#s19c">Spec §19c</a><br><code class="sig">fn make_dir(p String) Result[Unit, Error]</code><br><span class="eff">Effect: parks · Needs permission: fs</span></dd>
<dt id="fn-map"><code>map</code> <span class="tag">function</span></dt>
<dd>Applies a function to each item (<code>Result</code> and <code>Option</code> too: it changes the value inside). <a href="spec.html#s13">Spec §13</a><br><code class="sig">fn map[T, U](f (T) -&gt; U, xs Seq[T]) Stream[U]
fn map[T, U](f (T) -&gt; U, r Result[T, Error]) Result[U, Error]
fn map[T, U](f (T) -&gt; U, o Option[T]) Option[U]</code></dd>
<dt id="fn-map_all"><code>map_all</code> <span class="tag">function</span></dt>
<dd>Combines two to six Results with a function, collecting all errors. <a href="spec.html#s15">Spec §15</a><br><code class="sig">fn map_all[A, B, R](f (A, B) -&gt; R, a Result[A, Error], b Result[B, Error]) Result[R, List[Error]]
fn map_all[A, B, C, R](f (A, B, C) -&gt; R, a Result[A, Error], b Result[B, Error], c Result[C, Error]) Result[R, List[Error]]
fn map_all[A, B, C, D, R](f (A, B, C, D) -&gt; R, a Result[A, Error], b Result[B, Error], c Result[C, Error], d Result[D, Error]) Result[R, List[Error]]
fn map_all[A, B, C, D, E, R, E](f (A, B, C, D, E) -&gt; R, a Result[A, E], b Result[B, E], c Result[C, E], d Result[D, E], e Result[E, E]) Result[R, List[E]]
fn map_all[A, B, C, D, E, F, R, E](f (A, B, C, D, E, F) -&gt; R, a Result[A, E], b Result[B, E], c Result[C, E], d Result[D, E], e Result[E, E], f Result[F, E]) Result[R, List[E]]
fn map_all[A, B, R, X](rs (Result[A, X], Result[B, X]), f (A, B) -&gt; R) Result[R, List[X]]
fn map_all[A, B, C, R, X](rs (Result[A, X], Result[B, X], Result[C, X]), f (A, B, C) -&gt; R) Result[R, List[X]]
fn map_all[A, B, C, D, R, X](rs (Result[A, X], Result[B, X], Result[C, X], Result[D, X]), f (A, B, C, D) -&gt; R) Result[R, List[X]]
fn map_all[A, B, C, D, E, R, X](rs (Result[A, X], Result[B, X], Result[C, X], Result[D, X], Result[E, X]), f (A, B, C, D, E) -&gt; R) Result[R, List[X]]
fn map_all[A, B, C, D, E, F, R, X](rs (Result[A, X], Result[B, X], Result[C, X], Result[D, X], Result[E, X], Result[F, X]), f (A, B, C, D, E, F) -&gt; R) Result[R, List[X]]</code></dd>
<dt id="fn-map_err"><code>map_err</code> <span class="tag">function</span></dt>
<dd>Changes the error inside an Err. <a href="spec.html#s15">Spec §15</a><br><code class="sig">fn map_err[T, E, F](r Result[T, E], f (E) -&gt; F) Result[T, F]</code></dd>
<dt id="fn-map_ok"><code>map_ok</code> <span class="tag">function</span></dt>
<dd>Changes the value inside an Ok. <a href="spec.html#s15">Spec §15</a><br><code class="sig">fn map_ok[T, U, E](r Result[T, E], f (T) -&gt; U) Result[U, E]</code></dd>
<dt id="fn-max"><code>max</code> <span class="tag">function</span></dt>
<dd>The larger of two values. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn max[T Ordered](a T, b T) T</code></dd>
<dt id="fn-max_by"><code>max_by</code> <span class="tag">function</span></dt>
<dd>The item with the largest key; an Err if empty. <a href="spec.html#s13">Spec §13</a><br><code class="sig">fn max_by[T, K](f (T) -&gt; K, xs Seq[T]) Result[T, Error]</code></dd>
<dt id="fn-millis"><code>millis</code> <span class="tag">function</span></dt>
<dd>A Duration in milliseconds. <a href="spec.html#s19e">Spec §19e</a><br><code class="sig">fn millis(d Duration) Int</code></dd>
<dt id="fn-min"><code>min</code> <span class="tag">function</span></dt>
<dd>The smaller of two values. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn min[T Ordered](a T, b T) T</code></dd>
<dt id="fn-min_by"><code>min_by</code> <span class="tag">function</span></dt>
<dd>The item with the smallest key; an Err if empty. <a href="spec.html#s13">Spec §13</a><br><code class="sig">fn min_by[T, K](f (T) -&gt; K, xs Seq[T]) Result[T, Error]</code></dd>
<dt id="fn-modify"><code>modify</code> <span class="tag">function</span></dt>
<dd>A copy with the value at a data path changed by a function. <a href="spec.html#s7">Spec §7</a><br><code class="sig">fn modify[T, P, A](x T, path P, f (A) -&gt; A) T</code></dd>
<dt id="fn-monotonic"><code>monotonic</code> <span class="tag">function</span></dt>
<dd>A steadily increasing clock, for measuring. <a href="spec.html#s19e">Spec §19e</a><br><code class="sig">fn monotonic() Duration</code><br><span class="eff">Effect: uses the system</span></dd>
<dt id="kw-move"><code>move</code> <span class="tag">hard keyword</span></dt>
<dd>Passes a resource to a new owner, so the old name can no longer use it. <a href="spec.html#s19">Spec §19</a></dd>
<dt id="ty-MultiArray"><code>MultiArray</code> <span class="tag">type</span></dt>
<dd>An array with more than one dimension.</dd>
<dt id="kw-mutable"><code>mutable</code> <span class="tag">soft keyword</span></dt>
<dd>Opens a block in which names may be updated in place and cannot leak out. <a href="spec.html#s3">Spec §3</a></dd>
</dl>

## N {#n}

<dl class="ref">
<dt id="fn-nanos"><code>nanos</code> <span class="tag">function</span></dt>
<dd>A Duration in nanoseconds. <a href="spec.html#s19e">Spec §19e</a><br><code class="sig">fn nanos(d Duration) Int</code></dd>
<dt id="fn-non_empty"><code>non_empty</code> <span class="tag">function</span></dt>
<dd>Ok of a NonEmpty from a List, or an Err if it is empty. <a href="spec.html#s15">Spec §15</a><br><code class="sig">fn non_empty[T](xs List[T]) Result[NonEmpty[T], Error]</code></dd>
<dt id="ty-NonEmpty"><code>NonEmpty</code> <span class="tag">type</span></dt>
<dd>A list with a first item guaranteed, as <code>head</code> and <code>tail</code>.</dd>
<dt id="kw-not"><code>not</code> <span class="tag">hard keyword</span></dt>
<dd>Reverses a Bool. <a href="spec.html#s10">Spec §10</a></dd>
<dt id="fn-now"><code>now</code> <span class="tag">function</span></dt>
<dd>The current time as a Duration since the epoch. <a href="spec.html#s19e">Spec §19e</a><br><code class="sig">fn now() Duration</code><br><span class="eff">Effect: uses the system</span></dd>
</dl>

## O {#o}

<dl class="ref">
<dt id="fn-ok"><code>ok</code> <span class="tag">function</span></dt>
<dd>Turns a Result into an Option, dropping the error. <a href="spec.html#s15">Spec §15</a><br><code class="sig">fn ok[T, E](r Result[T, E]) Option[T]</code></dd>
<dt id="fn-ok_or"><code>ok_or</code> <span class="tag">function</span></dt>
<dd>Turns an Option into a Result with a given error. <a href="spec.html#s15">Spec §15</a><br><code class="sig">fn ok_or[T](o Option[T], err Error) Result[T, Error]</code></dd>
<dt id="kw-opaque"><code>opaque</code> <span class="tag">soft keyword</span></dt>
<dd>Follows <code>type</code> to make a type whose inside is hidden from other packages. <a href="spec.html#s6">Spec §6</a></dd>
<dt id="ty-Option"><code>Option</code> <span class="tag">type</span></dt>
<dd>Some(value) or None: a value that may be absent.</dd>
<dt id="kw-or"><code>or</code> <span class="tag">hard keyword</span></dt>
<dd>True when either side is true; the right side is evaluated only if needed. <a href="spec.html#s10">Spec §10</a></dd>
<dt id="fn-or_else"><code>or_else</code> <span class="tag">function</span></dt>
<dd>Tries a recovery function on an Err. <a href="spec.html#s15">Spec §15</a><br><code class="sig">fn or_else[T, E, F](r Result[T, E], f (E) -&gt; Result[T, F]) Result[T, F]</code></dd>
<dt id="fn-os_name"><code>os_name</code> <span class="tag">function</span></dt>
<dd>The operating system's name. <a href="spec.html#s19c">Spec §19c</a><br><code class="sig">fn os_name() String</code><br><span class="eff">Effect: uses the system</span></dd>
</dl>

## P {#p}

<dl class="ref">
<dt id="fn-pad_left"><code>pad_left</code> <span class="tag">function</span></dt>
<dd>Pads on the left to a width. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn pad_left(s String, n Int) String
fn pad_left(s String, n Int, c String) String
fn pad_left(s String, n Int, c Char) String</code></dd>
<dt id="fn-pad_right"><code>pad_right</code> <span class="tag">function</span></dt>
<dd>Pads on the right to a width. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn pad_right(s String, n Int) String
fn pad_right(s String, n Int, c String) String
fn pad_right(s String, n Int, c Char) String</code></dd>
<dt id="fn-par_map"><code>par_map</code> <span class="tag">function</span></dt>
<dd>Maps in parallel, at most <code>limit</code> at once, keeping order. <a href="spec.html#s17">Spec §17</a><br><code class="sig">fn par_map[T, U](f (T) -&gt; U, xs Seq[T], limit: Int) List[U]</code><br><span class="eff">Effect: parks</span></dd>
<dt id="fn-par_map_all"><code>par_map_all</code> <span class="tag">function</span></dt>
<dd>Like <code>map_all</code>, with slow checks run in parallel. <a href="spec.html#s15">Spec §15</a><br><code class="sig">fn par_map_all[A, B, R, X](f (A, B) -&gt; R, c1 () -&gt; Result[A, X], c2 () -&gt; Result[B, X]) Result[R, List[X]]
fn par_map_all[A, B, C, R, X](f (A, B, C) -&gt; R, c1 () -&gt; Result[A, X], c2 () -&gt; Result[B, X], c3 () -&gt; Result[C, X]) Result[R, List[X]]
fn par_map_all[A, B, C, D, R, X](f (A, B, C, D) -&gt; R, c1 () -&gt; Result[A, X], c2 () -&gt; Result[B, X], c3 () -&gt; Result[C, X], c4 () -&gt; Result[D, X]) Result[R, List[X]]
fn par_map_all[A, B, C, D, E, R, X](f (A, B, C, D, E) -&gt; R, c1 () -&gt; Result[A, X], c2 () -&gt; Result[B, X], c3 () -&gt; Result[C, X], c4 () -&gt; Result[D, X], c5 () -&gt; Result[E, X]) Result[R, List[X]]
fn par_map_all[A, B, C, D, E, F, R, X](f (A, B, C, D, E, F) -&gt; R, c1 () -&gt; Result[A, X], c2 () -&gt; Result[B, X], c3 () -&gt; Result[C, X], c4 () -&gt; Result[D, X], c5 () -&gt; Result[E, X], c6 () -&gt; Result[F, X]) Result[R, List[X]]</code><br><span class="eff">Effect: parks</span></dd>
<dt id="fn-par_traverse"><code>par_traverse</code> <span class="tag">function</span></dt>
<dd>Like <code>par_map</code> for Result-returning functions. <a href="spec.html#s17">Spec §17</a><br><code class="sig">fn par_traverse[T, U, E](f (T) -&gt; Result[U, E], xs Seq[T], limit: Int) Result[List[U], E]</code><br><span class="eff">Effect: parks</span></dd>
<dt id="kw-parks"><code>parks</code> <span class="tag">soft keyword</span></dt>
<dd>Function modifier: the function may wait, for example on a channel or the network. <a href="spec.html#s14">Spec §14</a></dd>
<dt id="fn-parse_iso"><code>parse_iso</code> <span class="tag">function</span></dt>
<dd>Reads ISO 8601 text. <a href="spec.html#s19e">Spec §19e</a><br><code class="sig">fn parse_iso(s String) Result[DateTime, Error]</code></dd>
<dt id="fn-parse_number"><code>parse_number</code> <span class="tag">function</span></dt>
<dd>Reads a number from text, optionally in a locale's format; an Err if it isn't one. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn parse_number[N](s String) Result[N, Error]
fn parse_number[N](s String, locale Locale) Result[N, Error]</code></dd>
<dt id="fn-parse_time"><code>parse_time</code> <span class="tag">function</span></dt>
<dd>Reads text with a pattern. <a href="spec.html#s19e">Spec §19e</a><br><code class="sig">fn parse_time(s String, fmt String) Result[DateTime, Error]
fn parse_time(s String, fmt String, loc Locale) Result[DateTime, Error]</code></dd>
<dt id="fn-partition"><code>partition</code> <span class="tag">function</span></dt>
<dd>Splits the items into those that pass a test and those that don't. <a href="spec.html#s13">Spec §13</a><br><code class="sig">fn partition[T](f (T) -&gt; Bool, xs Seq[T]) (List[T], List[T])</code></dd>
<dt id="fn-partition_results"><code>partition_results</code> <span class="tag">function</span></dt>
<dd>Splits Results into the values and the errors. <a href="spec.html#s15">Spec §15</a><br><code class="sig">fn partition_results[T, E](rs Seq[Result[T, E]]) (List[T], List[E])</code></dd>
<dt id="fn-path_exists"><code>path_exists</code> <span class="tag">function</span></dt>
<dd>Ok(true) or Ok(false). <a href="spec.html#s19c">Spec §19c</a><br><code class="sig">fn path_exists(p String) Result[Bool, Error]</code><br><span class="eff">Effect: parks · Needs permission: fs</span></dd>
<dt id="fn-path_ext"><code>path_ext</code> <span class="tag">function</span></dt>
<dd>The file name's extension. <a href="spec.html#s19c">Spec §19c</a><br><code class="sig">fn path_ext(p String) String</code></dd>
<dt id="fn-path_join"><code>path_join</code> <span class="tag">function</span></dt>
<dd>Joins path pieces. <a href="spec.html#s19c">Spec §19c</a><br><code class="sig">fn path_join(base String, rest String) String</code></dd>
<dt id="fn-path_name"><code>path_name</code> <span class="tag">function</span></dt>
<dd>The last piece of a path. <a href="spec.html#s19c">Spec §19c</a><br><code class="sig">fn path_name(p String) String</code></dd>
<dt id="fn-path_parent"><code>path_parent</code> <span class="tag">function</span></dt>
<dd>A path without its last piece. <a href="spec.html#s19c">Spec §19c</a><br><code class="sig">fn path_parent(p String) String</code></dd>
<dt id="fn-path_stem"><code>path_stem</code> <span class="tag">function</span></dt>
<dd>The file name without its extension. <a href="spec.html#s19c">Spec §19c</a><br><code class="sig">fn path_stem(p String) String</code></dd>
<dt id="fn-port_of"><code>port_of</code> <span class="tag">function</span></dt>
<dd>The port a listener or socket uses. <a href="spec.html#s19c">Spec §19c</a><br><code class="sig">fn port_of(l Listener) Int
fn port_of(u Udp) Int</code></dd>
<dt id="fn-position"><code>position</code> <span class="tag">function</span></dt>
<dd>The position of the first item that passes a test; an Err if none does. <a href="spec.html#s13">Spec §13</a><br><code class="sig">fn position[T](f (T) -&gt; Bool, xs Seq[T]) Result[Int, Error]</code></dd>
<dt id="fn-pow"><code>pow</code> <span class="tag">function</span></dt>
<dd>A number raised to a power. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn pow(a Int, b Int) Int
fn pow(a Double, b Double) Double</code></dd>
<dt id="fn-print"><code>print</code> <span class="tag">function</span></dt>
<dd>Prints a value. <a href="spec.html#s19b">Spec §19b</a><br><code class="sig">fn print[T](x T) Unit
fn print[T](out Io, x T) Unit</code><br><span class="eff">Effect: prints</span></dd>
<dt id="fn-println"><code>println</code> <span class="tag">function</span></dt>
<dd>Prints a value and a newline. <a href="spec.html#s19b">Spec §19b</a><br><code class="sig">fn println() Unit
fn println[T](x T) Unit
fn println[T](out Io, x T) Unit</code><br><span class="eff">Effect: prints</span></dd>
<dt id="kw-prints"><code>prints</code> <span class="tag">soft keyword</span></dt>
<dd>Function modifier: the function may print, and nothing else. <a href="spec.html#s14">Spec §14</a></dd>
<dt id="fn-product"><code>product</code> <span class="tag">function</span></dt>
<dd>Multiplies the items. <a href="spec.html#s13">Spec §13</a><br><code class="sig">fn product[T](xs Seq[T]) T</code></dd>
<dt id="kw-proxy"><code>proxy</code> <span class="tag">soft keyword</span></dt>
<dd>After the target of an <code>impl ... for</code>, forwards the impl to a field: <code>proxy(field)</code>. <a href="spec.html#s12">Spec §12</a></dd>
<dt id="kw-pure"><code>pure</code> <span class="tag">soft keyword</span></dt>
<dd>Function modifier: the function has no effects. <a href="spec.html#s14">Spec §14</a></dd>
</dl>

## R {#r}

<dl class="ref">
<dt id="fn-race"><code>race</code> <span class="tag">function</span></dt>
<dd>Runs two functions; gives the first result and cancels the other. <a href="spec.html#s17">Spec §17</a><br><code class="sig">fn race[T](f (Cancel) -&gt; T, g (Cancel) -&gt; T) T</code><br><span class="eff">Effect: parks</span></dd>
<dt id="fn-random"><code>random</code> <span class="tag">function</span></dt>
<dd>A Double in [0, 1). <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn random() Double</code><br><span class="eff">Effect: uses the system</span></dd>
<dt id="fn-random_bytes"><code>random_bytes</code> <span class="tag">function</span></dt>
<dd>n random bytes. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn random_bytes(n Int) Array[Byte]</code><br><span class="eff">Effect: uses the system</span></dd>
<dt id="fn-random_int"><code>random_int</code> <span class="tag">function</span></dt>
<dd>An Int drawn uniformly from a range. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn random_int(r Range) Int</code><br><span class="eff">Effect: uses the system</span></dd>
<dt id="ty-Range"><code>Range</code> <span class="tag">type</span></dt>
<dd>A run of integers or characters, <code>1..5</code> or <code>0..&lt;n</code>.</dd>
<dt id="fn-raw_terminal"><code>raw_terminal</code> <span class="tag">function</span></dt>
<dd>Puts the terminal in raw mode. <a href="spec.html#s19b">Spec §19b</a><br><code class="sig">fn raw_terminal() Result[Terminal, Error]</code><br><span class="eff">Effect: uses the system · Needs permission: stdin</span></dd>
<dt id="fn-read"><code>read</code> <span class="tag">function</span></dt>
<dd>Reads the next value from a channel, or waits for a future. <a href="spec.html#s17">Spec §17</a><br><code class="sig">fn read[T](c ChanR[T]) Result[T, Error]
fn read[T](f FutureR[T]) T</code><br><span class="eff">Effect: parks</span></dd>
<dt id="fn-read_all"><code>read_all</code> <span class="tag">function</span></dt>
<dd>All the rest of the input. <a href="spec.html#s19b">Spec §19b</a><br><code class="sig">fn read_all() Result[String, Error]
fn read_all(src Io) Result[String, Error]</code><br><span class="eff">Effect: parks · Needs permission: stdin</span></dd>
<dt id="fn-read_bytes"><code>read_bytes</code> <span class="tag">function</span></dt>
<dd>Up to n bytes. <a href="spec.html#s19b">Spec §19b</a><br><code class="sig">fn read_bytes(src Io, n Int) Result[Array[Byte], Error]</code><br><span class="eff">Effect: parks</span></dd>
<dt id="fn-read_file"><code>read_file</code> <span class="tag">function</span></dt>
<dd>A file's text. <a href="spec.html#s19c">Spec §19c</a><br><code class="sig">fn read_file(p String) Result[String, Error]</code><br><span class="eff">Effect: parks · Needs permission: fs</span></dd>
<dt id="fn-read_key"><code>read_key</code> <span class="tag">function</span></dt>
<dd>The next key pressed. <a href="spec.html#s19b">Spec §19b</a><br><code class="sig">fn read_key(t Terminal) Result[Key, Error]</code><br><span class="eff">Effect: parks</span></dd>
<dt id="fn-read_line"><code>read_line</code> <span class="tag">function</span></dt>
<dd>The next line of input; an Err at the end. <a href="spec.html#s19b">Spec §19b</a><br><code class="sig">fn read_line() Result[String, Error]
fn read_line(src Io) Result[String, Error]</code><br><span class="eff">Effect: parks · Needs permission: stdin</span></dd>
<dt id="fn-receive"><code>receive</code> <span class="tag">function</span></dt>
<dd>Waits for a UDP datagram. <a href="spec.html#s19c">Spec §19c</a><br><code class="sig">fn receive(u Udp) Result[Packet, Error]</code><br><span class="eff">Effect: parks</span></dd>
<dt id="fn-recover"><code>recover</code> <span class="tag">function</span></dt>
<dd>Turns an Err into a value with a function. <a href="spec.html#s15">Spec §15</a><br><code class="sig">fn recover[T, E](r Result[T, E], f (E) -&gt; T) Result[T, E]</code></dd>
<dt id="fn-reduce"><code>reduce</code> <span class="tag">function</span></dt>
<dd>Folds the items into one value, from a start value and a combining function. <a href="spec.html#s13">Spec §13</a><br><code class="sig">fn reduce[T, A](init A, f (A, T) -&gt; A, xs Seq[T]) A</code></dd>
<dt id="fn-reduce_right"><code>reduce_right</code> <span class="tag">function</span></dt>
<dd>Like <code>reduce</code>, folding from the end. <a href="spec.html#s13">Spec §13</a><br><code class="sig">fn reduce_right[T, A](init A, f (T, A) -&gt; A, xs Seq[T]) A</code></dd>
<dt id="kw-ref"><code>ref</code> <span class="tag">hard keyword</span></dt>
<dd>Marks a parameter that the function may rebind; the final value is copied back to the caller's variable. <a href="spec.html#s9">Spec §9</a></dd>
<dt id="fn-reject"><code>reject</code> <span class="tag">function</span></dt>
<dd>Supplies a future's error. <a href="spec.html#s17">Spec §17</a><br><code class="sig">fn reject[T](w FutureW[T], e Error) Unit</code><br><span class="eff">Effect: uses a resource</span></dd>
<dt id="fn-remove"><code>remove</code> <span class="tag">function</span></dt>
<dd>A copy without a key or item. <a href="spec.html#s7">Spec §7</a><br><code class="sig">fn remove[K, V](d Dict[K, V], k K) Dict[K, V]
fn remove[T](s Set[T], x T) Set[T]
fn remove[T](xs List[T], x T) List[T]
fn remove[T](xs Array[T], x T) Array[T]</code></dd>
<dt id="fn-remove_at"><code>remove_at</code> <span class="tag">function</span></dt>
<dd>A copy without the item at a position. <a href="spec.html#s7">Spec §7</a><br><code class="sig">fn remove_at[T](xs List[T], i Int) List[T]
fn remove_at[T](xs Array[T], i Int) Array[T]</code></dd>
<dt id="fn-remove_dir"><code>remove_dir</code> <span class="tag">function</span></dt>
<dd>Deletes a directory. <a href="spec.html#s19c">Spec §19c</a><br><code class="sig">fn remove_dir(p String) Result[Unit, Error]</code><br><span class="eff">Effect: parks · Needs permission: fs</span></dd>
<dt id="fn-remove_file"><code>remove_file</code> <span class="tag">function</span></dt>
<dd>Deletes a file. <a href="spec.html#s19c">Spec §19c</a><br><code class="sig">fn remove_file(p String) Result[Unit, Error]</code><br><span class="eff">Effect: parks · Needs permission: fs</span></dd>
<dt id="fn-rename_path"><code>rename_path</code> <span class="tag">function</span></dt>
<dd>Renames a file or directory. <a href="spec.html#s19c">Spec §19c</a><br><code class="sig">fn rename_path(a String, b String) Result[Unit, Error]</code><br><span class="eff">Effect: parks · Needs permission: fs</span></dd>
<dt id="fn-repeat"><code>repeat</code> <span class="tag">function</span></dt>
<dd>One value, forever. <a href="spec.html#s13">Spec §13</a><br><code class="sig">fn repeat[T](x T) Stream[T]</code></dd>
<dt id="fn-replace"><code>replace</code> <span class="tag">function</span></dt>
<dd>A copy with the value at a data path replaced. <a href="spec.html#s7">Spec §7</a><br><code class="sig">fn replace[T, P, V](x T, path P, v V) T</code></dd>
<dt id="fn-replace_text"><code>replace_text</code> <span class="tag">function</span></dt>
<dd>Replaces every occurrence of one piece of text with another. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn replace_text(s String, from String, to String) String</code></dd>
<dt id="fn-reset"><code>reset</code> <span class="tag">function</span></dt>
<dd>Sets an Atom's value. <a href="spec.html#s17">Spec §17</a><br><code class="sig">fn reset[T](a Atom[T], v T) T</code><br><span class="eff">Effect: uses a resource</span></dd>
<dt id="fn-reset_vals"><code>reset_vals</code> <span class="tag">function</span></dt>
<dd>Like <code>reset</code>, giving (old, new). <a href="spec.html#s17">Spec §17</a><br><code class="sig">fn reset_vals[T](a Atom[T], v T) (T, T)</code><br><span class="eff">Effect: uses a resource</span></dd>
<dt id="fn-resolve"><code>resolve</code> <span class="tag">function</span></dt>
<dd>Supplies a future's value. <a href="spec.html#s17">Spec §17</a><br><code class="sig">fn resolve[T](w FutureW[T], v T) Unit</code><br><span class="eff">Effect: uses a resource</span></dd>
<dt id="ty-Result"><code>Result</code> <span class="tag">type</span></dt>
<dd>Ok(value) or Err(error): the outcome of something that can fail.</dd>
<dt id="fn-retry"><code>retry</code> <span class="tag">function</span></dt>
<dd>Calls a function up to n times, waiting between tries. <a href="spec.html#s17">Spec §17</a><br><code class="sig">fn retry[T](n Int, delay Duration, f () -&gt; Result[T, Error]) Result[T, Error]</code><br><span class="eff">Effect: parks</span></dd>
<dt id="kw-return"><code>return</code> <span class="tag">hard keyword</span></dt>
<dd>Leaves the function early with a value. <a href="spec.html#s9">Spec §9</a></dd>
<dt id="fn-reverse"><code>reverse</code> <span class="tag">function</span></dt>
<dd>The items in the opposite order. <a href="spec.html#s13">Spec §13</a><br><code class="sig">fn reverse[T](xs Seq[T]) Stream[T]</code></dd>
<dt id="ty-Ring"><code>Ring</code> <span class="tag">type</span></dt>
<dd>A fixed-capacity buffer that overwrites its oldest item when full.</dd>
<dt id="fn-round"><code>round</code> <span class="tag">function</span></dt>
<dd>Rounds to the nearest Int. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn round(x Double) Int</code></dd>
<dt id="fn-round_to"><code>round_to</code> <span class="tag">function</span></dt>
<dd>Rounds a Decimal to a scale of n places, as in <code>round_to[2](x, #half_even)</code>; a <code>Mode</code> is <code>#half_even</code>, <code>#half_up</code> or <code>#down</code>. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn round_to[n](x Decimal, mode Mode) Decimal</code></dd>
<dt id="fn-run_command"><code>run_command</code> <span class="tag">function</span></dt>
<dd>Runs another program to the end and gives its output. <a href="spec.html#s19c">Spec §19c</a><br><code class="sig">fn run_command(program String) Result[Output, Error]
fn run_command(program String, args List[String]) Result[Output, Error]</code><br><span class="eff">Effect: parks · Needs permission: process</span></dd>
</dl>

## S {#s}

<dl class="ref">
<dt id="fn-saturating_add"><code>saturating_add</code> <span class="tag">function</span></dt>
<dd>Addition that stops at the largest or smallest value. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn saturating_add[T](a T, b T) T</code></dd>
<dt id="fn-saturating_mul"><code>saturating_mul</code> <span class="tag">function</span></dt>
<dd>Multiplication that stops at the largest or smallest value. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn saturating_mul[T](a T, b T) T</code></dd>
<dt id="fn-saturating_sub"><code>saturating_sub</code> <span class="tag">function</span></dt>
<dd>Subtraction that stops at the largest or smallest value. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn saturating_sub[T](a T, b T) T</code></dd>
<dt id="fn-scan"><code>scan</code> <span class="tag">function</span></dt>
<dd>Like <code>reduce</code>, but gives every running value. <a href="spec.html#s13">Spec §13</a><br><code class="sig">fn scan[T, A](init A, f (A, T) -&gt; A, xs Seq[T]) Stream[A]</code></dd>
<dt id="fn-seconds"><code>seconds</code> <span class="tag">function</span></dt>
<dd>A Duration in seconds. <a href="spec.html#s19e">Spec §19e</a><br><code class="sig">fn seconds(d Duration) Double</code></dd>
<dt id="ty-Secret"><code>Secret</code> <span class="tag">type</span></dt>
<dd>A value that cannot be printed or compared with <code>==</code>.</dd>
<dt id="fn-secret_eq"><code>secret_eq</code> <span class="tag">function</span></dt>
<dd>Compares two secrets in constant time. <a href="spec.html#s23">Spec §23</a><br><code class="sig">fn secret_eq[T](a Secret[T], b Secret[T]) Bool</code></dd>
<dt id="kw-select"><code>select</code> <span class="tag">hard keyword</span></dt>
<dd>Waits on several channel, timer or future operations and runs the arm for the first that is ready. <a href="spec.html#s17">Spec §17</a></dd>
<dt id="kw-Self"><code>Self</code> <span class="tag">hard keyword</span></dt>
<dd>Inside an interface or impl, the type being described. <a href="spec.html#s12">Spec §12</a></dd>
<dt id="kw-self"><code>self</code> <span class="tag">hard keyword</span></dt>
<dd>The receiver value inside a method. <a href="spec.html#s12">Spec §12</a></dd>
<dt id="fn-send_to"><code>send_to</code> <span class="tag">function</span></dt>
<dd>Sends one UDP datagram. <a href="spec.html#s19c">Spec §19c</a><br><code class="sig">fn send_to(u Udp, host String, port Int, data String) Result[Unit, Error]
fn send_to(u Udp, host String, port Int, data Array[Byte]) Result[Unit, Error]</code><br><span class="eff">Effect: parks · Needs permission: net</span></dd>
<dt id="kw-seq"><code>seq</code> <span class="tag">soft keyword</span></dt>
<dd>After <code>|&gt;</code>, begins a stream pipeline written one stage per line. <a href="spec.html#s13">Spec §13</a></dd>
<dt id="ty-Seq"><code>Seq</code> <span class="tag">type</span></dt>
<dd>In a signature, any source of values: a List, Array, Set, Ring or Stream.</dd>
<dt id="fn-sequence"><code>sequence</code> <span class="tag">function</span></dt>
<dd>Turns Results into one Result of a List; stops at the first Err. <a href="spec.html#s15">Spec §15</a><br><code class="sig">fn sequence[T, E](rs Seq[Result[T, E]]) Result[List[T], E]</code></dd>
<dt id="ty-Set"><code>Set</code> <span class="tag">type</span></dt>
<dd>A collection of distinct values.</dd>
<dt id="fn-set"><code>set</code> <span class="tag">function</span></dt>
<dd>A copy with the item at a position or key replaced. <a href="spec.html#s7">Spec §7</a><br><code class="sig">fn set[T](xs List[T], i Int, x T) List[T]
fn set[T](xs Array[T], i Int, x T) Array[T]
fn set[T](xs MultiArray[T], i Int, x T) MultiArray[T]
fn set[K, V](d Dict[K, V], k K, v V) Dict[K, V]</code></dd>
<dt id="fn-shl"><code>shl</code> <span class="tag">function</span></dt>
<dd>Shifts bits left. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn shl[T](a T, n Int) T</code></dd>
<dt id="fn-show"><code>show</code> <span class="tag">function</span></dt>
<dd>The printed form of a value, as a String. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn show[T](x T) String</code></dd>
<dt id="fn-shr"><code>shr</code> <span class="tag">function</span></dt>
<dd>Shifts bits right. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn shr[T](a T, n Int) T</code></dd>
<dt id="fn-sleep"><code>sleep</code> <span class="tag">function</span></dt>
<dd>Waits for a duration. <a href="spec.html#s17">Spec §17</a><br><code class="sig">fn sleep(d Duration) Unit</code><br><span class="eff">Effect: parks</span></dd>
<dt id="fn-sort"><code>sort</code> <span class="tag">function</span></dt>
<dd>Orders the items by <code>&lt;</code>, keeping equal items in their order. <a href="spec.html#s13">Spec §13</a><br><code class="sig">fn sort[T Ordered](xs Seq[T]) Stream[T]</code></dd>
<dt id="fn-sort_by"><code>sort_by</code> <span class="tag">function</span></dt>
<dd>Orders the items by a key function. <a href="spec.html#s13">Spec §13</a><br><code class="sig">fn sort_by[T, K](f (T) -&gt; K, xs Seq[T]) Stream[T]</code></dd>
<dt id="fn-span"><code>span</code> <span class="tag">function</span></dt>
<dd>Splits at the first item that fails a test. <a href="spec.html#s13">Spec §13</a><br><code class="sig">fn span[T](f (T) -&gt; Bool, xs Seq[T]) (List[T], List[T])</code></dd>
<dt id="fn-spawn"><code>spawn</code> <span class="tag">function</span></dt>
<dd>Starts another program. <a href="spec.html#s19c">Spec §19c</a><br><code class="sig">fn spawn(program String) Result[Child, Error]
fn spawn(program String, args List[String]) Result[Child, Error]</code><br><span class="eff">Effect: parks · Needs permission: process</span></dd>
<dt id="fn-split"><code>split</code> <span class="tag">function</span></dt>
<dd>Cuts a String at every separator. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn split(s String, sep String) List[String]</code></dd>
<dt id="fn-split_at"><code>split_at</code> <span class="tag">function</span></dt>
<dd>Splits after the first n items. <a href="spec.html#s13">Spec §13</a><br><code class="sig">fn split_at[T](n Int, xs Seq[T]) (List[T], List[T])</code></dd>
<dt id="fn-split_once"><code>split_once</code> <span class="tag">function</span></dt>
<dd>Cuts at the first separator; None if there is none. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn split_once(s String, sep String) Option[(String, String)]</code></dd>
<dt id="fn-sqrt"><code>sqrt</code> <span class="tag">function</span></dt>
<dd>Square root. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn sqrt(x Double) Double</code></dd>
<dt id="fn-starts_with"><code>starts_with</code> <span class="tag">function</span></dt>
<dd>True if the text begins with a prefix. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn starts_with(s String, prefix String) Bool
fn starts_with(s String, c Char) Bool</code></dd>
<dt id="kw-static"><code>static</code> <span class="tag">hard keyword</span></dt>
<dd>Marks a function that belongs to a type and has no <code>self</code>, as in <code>static fn read(text String)</code>. <a href="spec.html#s12">Spec §12</a></dd>
<dt id="fn-stdin_lines"><code>stdin_lines</code> <span class="tag">function</span></dt>
<dd>The lines of standard input, as a stream. <a href="spec.html#s19b">Spec §19b</a><br><code class="sig">fn stdin_lines() Stream[String]</code><br><span class="eff">Effect: parks · Needs permission: stdin</span></dd>
<dt id="kw-step"><code>step</code> <span class="tag">soft keyword</span></dt>
<dd>After a range, gives the stride: <code>0..10 step 5</code>. <a href="spec.html#s5">Spec §5</a></dd>
<dt id="ty-Stream"><code>Stream</code> <span class="tag">type</span></dt>
<dd>A lazy pipeline of values that runs when something consumes it.</dd>
<dt id="ty-String"><code>String</code> <span class="tag">type</span></dt>
<dd>Text, stored as UTF-8 and immutable.</dd>
<dt id="fn-strip_prefix"><code>strip_prefix</code> <span class="tag">function</span></dt>
<dd>The text without a prefix, or None if it doesn't start with it. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn strip_prefix(s String, prefix String) Option[String]</code></dd>
<dt id="fn-strip_suffix"><code>strip_suffix</code> <span class="tag">function</span></dt>
<dd>The text without a suffix, or None if it doesn't end with it. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn strip_suffix(s String, suffix String) Option[String]</code></dd>
<dt id="fn-sum"><code>sum</code> <span class="tag">function</span></dt>
<dd>Adds the items. <a href="spec.html#s13">Spec §13</a><br><code class="sig">fn sum[T](xs Seq[T]) T</code></dd>
<dt id="fn-swap"><code>swap</code> <span class="tag">function</span></dt>
<dd>Changes an Atom's value with a function and gives the new value. <a href="spec.html#s17">Spec §17</a><br><code class="sig">fn swap[T](a Atom[T], f (T) -&gt; T) T</code><br><span class="eff">Effect: uses a resource</span></dd>
<dt id="fn-swap_vals"><code>swap_vals</code> <span class="tag">function</span></dt>
<dd>Like <code>swap</code>, giving (old, new). <a href="spec.html#s17">Spec §17</a><br><code class="sig">fn swap_vals[T](a Atom[T], f (T) -&gt; T) (T, T)</code><br><span class="eff">Effect: uses a resource</span></dd>
</dl>

## T {#t}

<dl class="ref">
<dt id="kw-tailrec"><code>tailrec</code> <span class="tag">soft keyword</span></dt>
<dd>Function modifier: the function must call itself only in tail position, so it runs in constant stack. <a href="spec.html#s9">Spec §9</a></dd>
<dt id="fn-take"><code>take</code> <span class="tag">function</span></dt>
<dd>The first n items. <a href="spec.html#s13">Spec §13</a><br><code class="sig">fn take[T](n Int, xs Seq[T]) Stream[T]</code></dd>
<dt id="fn-take_last"><code>take_last</code> <span class="tag">function</span></dt>
<dd>The last n items. <a href="spec.html#s13">Spec §13</a><br><code class="sig">fn take_last[T](n Int, xs Seq[T]) Stream[T]</code></dd>
<dt id="fn-take_while"><code>take_while</code> <span class="tag">function</span></dt>
<dd>Items from the start while a test holds. <a href="spec.html#s13">Spec §13</a><br><code class="sig">fn take_while[T](f (T) -&gt; Bool, xs Seq[T]) Stream[T]</code></dd>
<dt id="fn-tap"><code>tap</code> <span class="tag">function</span></dt>
<dd>Calls a function on a value for its effect and gives the value back. <a href="spec.html#s23">Spec §23</a><br><code class="sig">fn tap[T, U](x T, f (T) -&gt; U) T</code></dd>
<dt id="fn-temp_dir"><code>temp_dir</code> <span class="tag">function</span></dt>
<dd>The temporary directory. <a href="spec.html#s19c">Spec §19c</a><br><code class="sig">fn temp_dir() String</code><br><span class="eff">Effect: uses the system</span></dd>
<dt id="kw-test"><code>test</code> <span class="tag">soft keyword</span></dt>
<dd>At the start of a statement, before a string, declares a test block. <a href="spec.html#s22">Spec §22</a></dd>
<dt id="ty-Timer"><code>Timer</code> <span class="tag">type</span></dt>
<dd>A resource that fires once or repeatedly after a duration.</dd>
<dt id="fn-to_instant"><code>to_instant</code> <span class="tag">function</span></dt>
<dd>A DateTime as a Duration since the epoch. <a href="spec.html#s19e">Spec §19e</a><br><code class="sig">fn to_instant(t DateTime) Result[Duration, Error]
fn to_instant(t DateTime, zone String) Result[Duration, Error]</code></dd>
<dt id="fn-to_local"><code>to_local</code> <span class="tag">function</span></dt>
<dd>A Duration as a DateTime in the system's zone. <a href="spec.html#s19e">Spec §19e</a><br><code class="sig">fn to_local(d Duration) DateTime</code><br><span class="eff">Effect: uses the system</span></dd>
<dt id="fn-to_stream"><code>to_stream</code> <span class="tag">function</span></dt>
<dd>Treats any collection as a stream. <a href="spec.html#s13">Spec §13</a><br><code class="sig">fn to_stream[T](xs Seq[T]) Stream[T]</code></dd>
<dt id="fn-to_utc"><code>to_utc</code> <span class="tag">function</span></dt>
<dd>A Duration as a UTC DateTime. <a href="spec.html#s19e">Spec §19e</a><br><code class="sig">fn to_utc(d Duration) DateTime</code></dd>
<dt id="fn-to_zone"><code>to_zone</code> <span class="tag">function</span></dt>
<dd>A Duration as a DateTime in a named zone. <a href="spec.html#s19e">Spec §19e</a><br><code class="sig">fn to_zone(d Duration, zone String) Result[DateTime, Error]</code></dd>
<dt id="kw-todo"><code>todo</code> <span class="tag">hard keyword</span></dt>
<dd>Stands for an expression of whatever type is expected, with an optional message; aborts if it runs. <a href="spec.html#s2">Spec §2</a></dd>
<dt id="fn-trace"><code>trace</code> <span class="tag">function</span></dt>
<dd>Prints a message with its place. <a href="spec.html#s22">Spec §22</a><br><code class="sig">fn trace[T](x T) Unit</code><br><span class="eff">Effect: prints, but is allowed in any code</span></dd>
<dt id="fn-transpose"><code>transpose</code> <span class="tag">function</span></dt>
<dd>Turns rows into columns. <a href="spec.html#s13">Spec §13</a><br><code class="sig">fn transpose[T](rows Seq[Seq[T]]) List[List[T]]</code></dd>
<dt id="fn-traverse"><code>traverse</code> <span class="tag">function</span></dt>
<dd>Applies a Result-returning function to each item; stops at the first Err. <a href="spec.html#s15">Spec §15</a><br><code class="sig">fn traverse[T, U](f (T) -&gt; Result[U, Error], xs Seq[T]) Result[List[U], Error]</code></dd>
<dt id="fn-trim"><code>trim</code> <span class="tag">function</span></dt>
<dd>Removes spaces from both ends. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn trim(s String) String</code></dd>
<dt id="kw-true"><code>true</code> <span class="tag">hard keyword</span></dt>
<dd>The Bool value true. <a href="spec.html#s5">Spec §5</a></dd>
<dt id="fn-try_cast"><code>try_cast</code> <span class="tag">function</span></dt>
<dd>Like <code>cast</code>, but gives an Err (OUT_OF_RANGE) when the value does not fit. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn try_cast[T Numeric, N Numeric](x N) Result[T, Error]</code></dd>
<dt id="fn-try_fmt"><code>try_fmt</code> <span class="tag">function</span></dt>
<dd>Like <code>fmt</code>, but gives an Err for a bad template. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn try_fmt(template String, args...) Result[String, Error]</code></dd>
<dt id="kw-try_go"><code>try_go</code> <span class="tag">hard keyword</span></dt>
<dd>Like <code>go</code>, but gives an Err (NO_SLOT) instead of waiting when the fiber function has no free slot. <a href="spec.html#s18">Spec §18</a></dd>
<dt id="fn-try_reset"><code>try_reset</code> <span class="tag">function</span></dt>
<dd>Like <code>reset</code>, with an Err instead of an abort. <a href="spec.html#s17">Spec §17</a><br><code class="sig">fn try_reset[T](a Atom[T], v T) Result[T, Error]</code><br><span class="eff">Effect: uses a resource</span></dd>
<dt id="fn-try_swap"><code>try_swap</code> <span class="tag">function</span></dt>
<dd>Like <code>swap</code>, with an Err instead of an abort. <a href="spec.html#s17">Spec §17</a><br><code class="sig">fn try_swap[T](a Atom[T], f (T) -&gt; T) Result[T, Error]</code><br><span class="eff">Effect: uses a resource</span></dd>
<dt id="kw-tuple"><code>tuple</code> <span class="tag">hard keyword</span></dt>
<dd>Declares a tuple type with named fields. <a href="spec.html#s6">Spec §6</a></dd>
<dt id="kw-type"><code>type</code> <span class="tag">soft keyword</span></dt>
<dd>Declares a type alias, an opaque type or a union: <code>type Id = Int</code>. <a href="spec.html#s6">Spec §6</a></dd>
</dl>

## U {#u}

<dl class="ref">
<dt id="kw-union"><code>union</code> <span class="tag">soft keyword</span></dt>
<dd>Follows <code>type</code> to declare a type that is any one of several types. <a href="spec.html#s6">Spec §6</a></dd>
<dt id="ty-Unit"><code>Unit</code> <span class="tag">type</span></dt>
<dd>The type with one value, <code>()</code>, for a function that gives nothing back.</dd>
<dt id="fn-unwrap"><code>unwrap</code> <span class="tag">function</span></dt>
<dd>The value of an Ok; aborts on an Err. <a href="spec.html#s15">Spec §15</a><br><code class="sig">fn unwrap[T, E](r Result[T, E]) T</code></dd>
<dt id="fn-unzip"><code>unzip</code> <span class="tag">function</span></dt>
<dd>Splits a source of pairs into two Lists. <a href="spec.html#s13">Spec §13</a><br><code class="sig">fn unzip[A, B](xs Seq[(A, B)]) (List[A], List[B])</code></dd>
<dt id="kw-update"><code>update</code> <span class="tag">soft keyword</span></dt>
<dd>After <code>x.</code> and before <code>:</code>, builds a copy of <code>x</code> with some fields changed. <a href="spec.html#s6">Spec §6</a></dd>
<dt id="fn-upper"><code>upper</code> <span class="tag">function</span></dt>
<dd>Upper case. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn upper(s String) String
fn upper(c Char) Char</code></dd>
<dt id="kw-using"><code>using</code> <span class="tag">hard keyword</span></dt>
<dd>Puts a named value in scope for the code that follows, as in <code>using locale = Locale.de_de</code>. <a href="spec.html#s5">Spec §5</a></dd>
</dl>

## V {#v}

<dl class="ref">
<dt id="fn-validate"><code>validate</code> <span class="tag">function</span></dt>
<dd>Like <code>traverse</code>, but collects every error. <a href="spec.html#s15">Spec §15</a><br><code class="sig">fn validate[T, U](f (T) -&gt; Result[U, Error], xs Seq[T]) Result[List[U], List[Error]]</code></dd>
<dt id="fn-values"><code>values</code> <span class="tag">function</span></dt>
<dd>The values of a Dict. <a href="spec.html#s7">Spec §7</a><br><code class="sig">fn values[K, V](d Dict[K, V]) Stream[V]</code></dd>
</dl>

## W {#w}

<dl class="ref">
<dt id="kw-wait"><code>wait</code> <span class="tag">soft keyword</span></dt>
<dd>At the start of a statement, waits for the fibers started below it, or for a cancel token. <a href="spec.html#s18">Spec §18</a></dd>
<dt id="fn-wait_child"><code>wait_child</code> <span class="tag">function</span></dt>
<dd>Waits for it to end. <a href="spec.html#s19c">Spec §19c</a><br><code class="sig">fn wait_child(c Child) Result[Int, Error]</code><br><span class="eff">Effect: parks</span></dd>
<dt id="fn-weekday"><code>weekday</code> <span class="tag">function</span></dt>
<dd>1 for Monday to 7 for Sunday. <a href="spec.html#s19e">Spec §19e</a><br><code class="sig">fn weekday(t DateTime) Int</code></dd>
<dt id="kw-when"><code>when</code> <span class="tag">hard keyword</span></dt>
<dd>Matches a value against patterns, one arm per pattern, and checks that every case is covered. <a href="spec.html#s8">Spec §8</a></dd>
<dt id="kw-where"><code>where</code> <span class="tag">soft keyword</span></dt>
<dd>States a condition on a type parameter, a parameter or a result. <a href="spec.html#s9c">Spec §9c</a></dd>
<dt id="kw-while"><code>while</code> <span class="tag">hard keyword</span></dt>
<dd>Reserved: writing it is an error that tells you to write <code>for</code>. <a href="spec.html#s18">Spec §18</a></dd>
<dt id="fn-windows"><code>windows</code> <span class="tag">function</span></dt>
<dd>Every run of n neighbouring items. <a href="spec.html#s13">Spec §13</a><br><code class="sig">fn windows[T](n Int, xs Seq[T]) Stream[Array[T]]</code></dd>
<dt id="fn-wire_close"><code>wire_close</code> <span class="tag">function</span></dt>
<dd>Closes a session endpoint. <a href="spec.html#s19c">Spec §19c</a><br><code class="sig">fn wire_close(w Wire) Unit</code></dd>
<dt id="fn-wire_pair"><code>wire_pair</code> <span class="tag">function</span></dt>
<dd>Two connected session endpoints. <a href="spec.html#s19c">Spec §19c</a><br><code class="sig">fn wire_pair() (Wire, Wire)</code></dd>
<dt id="fn-wire_recv"><code>wire_recv</code> <span class="tag">function</span></dt>
<dd>Receives a value on a session endpoint. <a href="spec.html#s19c">Spec §19c</a><br><code class="sig">fn wire_recv[T](w Wire) Result[T, Error]</code></dd>
<dt id="fn-wire_send"><code>wire_send</code> <span class="tag">function</span></dt>
<dd>Sends a value on a session endpoint. <a href="spec.html#s19c">Spec §19c</a><br><code class="sig">fn wire_send[T](w Wire, x T) Result[Unit, Error]</code></dd>
<dt id="fn-with_stdin"><code>with_stdin</code> <span class="tag">function</span></dt>
<dd>Runs a function with given text as standard input. <a href="spec.html#s19b">Spec §19b</a><br><code class="sig">fn with_stdin[T](text String, f () -&gt; T) T</code></dd>
<dt id="fn-with_timeout"><code>with_timeout</code> <span class="tag">function</span></dt>
<dd>Gives a function's result, or Err(TIMED_OUT) if time runs out. <a href="spec.html#s17">Spec §17</a><br><code class="sig">fn with_timeout[T](d Duration, f (Cancel) -&gt; Result[T, Error]) Result[T, Error]</code><br><span class="eff">Effect: parks</span></dd>
<dt id="fn-wrap_to"><code>wrap_to</code> <span class="tag">function</span></dt>
<dd>Converts to another width by keeping the low bits. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn wrap_to[T Numeric, N Numeric](x N) T</code></dd>
<dt id="fn-wrapping_add"><code>wrapping_add</code> <span class="tag">function</span></dt>
<dd>Addition that wraps around on overflow. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn wrapping_add[T](a T, b T) T</code></dd>
<dt id="fn-wrapping_mul"><code>wrapping_mul</code> <span class="tag">function</span></dt>
<dd>Multiplication that wraps around on overflow. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn wrapping_mul[T](a T, b T) T</code></dd>
<dt id="fn-wrapping_sub"><code>wrapping_sub</code> <span class="tag">function</span></dt>
<dd>Subtraction that wraps around on overflow. <a href="spec.html#s5">Spec §5</a><br><code class="sig">fn wrapping_sub[T](a T, b T) T</code></dd>
<dt id="fn-write"><code>write</code> <span class="tag">function</span></dt>
<dd>Sends a value on a channel. <a href="spec.html#s17">Spec §17</a><br><code class="sig">fn write[T](w ChanW[T], x T) Result[Unit, Error]</code><br><span class="eff">Effect: parks</span></dd>
<dt id="fn-write_bytes"><code>write_bytes</code> <span class="tag">function</span></dt>
<dd>Writes bytes. <a href="spec.html#s19b">Spec §19b</a><br><code class="sig">fn write_bytes(out Io, data Array[Byte]) Result[Unit, Error]</code><br><span class="eff">Effect: parks</span></dd>
<dt id="fn-write_file"><code>write_file</code> <span class="tag">function</span></dt>
<dd>Writes text to a file. <a href="spec.html#s19c">Spec §19c</a><br><code class="sig">fn write_file(p String, s String) Result[Unit, Error]</code><br><span class="eff">Effect: parks · Needs permission: fs</span></dd>
</dl>

## Y {#y}

<dl class="ref">
<dt id="kw-yield"><code>yield</code> <span class="tag">soft keyword</span></dt>
<dd>Gives one value of a <code>for</code> comprehension. <a href="spec.html#s13">Spec §13</a></dd>
</dl>

## Z {#z}

<dl class="ref">
<dt id="fn-zip"><code>zip</code> <span class="tag">function</span></dt>
<dd>Pairs the items of two sources, stopping at the shorter. <a href="spec.html#s13">Spec §13</a><br><code class="sig">fn zip[A, B](a Seq[A], b Seq[B]) Stream[(A, B)]</code></dd>
<dt id="fn-zip3"><code>zip3</code> <span class="tag">function</span></dt>
<dd>Triples the items of three sources. <a href="spec.html#s13">Spec §13</a><br><code class="sig">fn zip3[A, B, C](a Seq[A], b Seq[B], c Seq[C]) Stream[(A, B, C)]</code></dd>
<dt id="fn-zip_with"><code>zip_with</code> <span class="tag">function</span></dt>
<dd>Combines the items of two sources with a function. <a href="spec.html#s13">Spec §13</a><br><code class="sig">fn zip_with[A, B, C](f (A, B) -&gt; C, xs Seq[A], ys Seq[B]) Stream[C]</code></dd>
</dl>

