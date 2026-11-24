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
<dt id="fn-abs"><a href="ref/abs.html"><code>abs</code></a> <span class="tag">function</span></dt>
<dd>Absolute value. <a href="spec.html#s5">Spec §5</a> <a href="ref/abs.html">Full description</a><br><code class="sig">fn abs(n Int) Int
fn abs(x Double) Double</code></dd>
<dt id="fn-accept"><a href="ref/accept.html"><code>accept</code></a> <span class="tag">function</span></dt>
<dd>Waits for a connection. <a href="spec.html#s19c">Spec §19c</a> <a href="ref/accept.html">Full description</a><br><code class="sig">fn accept(l Listener) Result[Io, Error]</code><br><span class="eff">Effect: parks</span></dd>
<dt id="fn-after"><a href="ref/after.html"><code>after</code></a> <span class="tag">function</span></dt>
<dd>A timer that fires once after a duration. <a href="spec.html#s17">Spec §17</a> <a href="ref/after.html">Full description</a><br><code class="sig">fn after(d Duration) Timer</code><br><span class="eff">Effect: uses a resource</span></dd>
<dt id="kw-alias"><code>alias</code> <span class="tag">soft keyword</span></dt>
<dd>Follows <code>type</code> to make a second name for a type. <a href="spec.html#s6">Spec §6</a></dd>
<dt id="fn-all"><a href="ref/all.html"><code>all</code></a> <span class="tag">function</span></dt>
<dd>True if the test holds for every item. <a href="spec.html#s13">Spec §13</a> <a href="ref/all.html">Full description</a><br><code class="sig">fn all[T](f (T) -&gt; Bool, xs Seq[T]) Bool</code></dd>
<dt id="kw-and"><code>and</code> <span class="tag">hard keyword</span></dt>
<dd>True when both sides are true; the right side is evaluated only if needed. <a href="spec.html#s10">Spec §10</a></dd>
<dt id="kw-any"><code>any</code> <span class="tag">soft keyword</span></dt>
<dd>In a type, before an interface name, means a value of any type that has that interface. <a href="spec.html#s12">Spec §12</a></dd>
<dt id="fn-any"><a href="ref/any.html"><code>any</code></a> <span class="tag">function</span></dt>
<dd>True if the test holds for at least one item. <a href="spec.html#s13">Spec §13</a> <a href="ref/any.html">Full description</a><br><code class="sig">fn any[T](f (T) -&gt; Bool, xs Seq[T]) Bool</code></dd>
<dt id="fn-arm"><a href="ref/arm.html"><code>arm</code></a> <span class="tag">function</span></dt>
<dd>Starts a timer. <a href="spec.html#s17">Spec §17</a> <a href="ref/arm.html">Full description</a><br><code class="sig">fn arm(t Timer, d Duration) Unit</code><br><span class="eff">Effect: uses a resource</span></dd>
<dt id="fn-arm_every"><a href="ref/arm_every.html"><code>arm_every</code></a> <span class="tag">function</span></dt>
<dd>Starts a timer that fires repeatedly. <a href="spec.html#s17">Spec §17</a> <a href="ref/arm_every.html">Full description</a><br><code class="sig">fn arm_every(t Timer, d Duration) Unit</code><br><span class="eff">Effect: uses a resource</span></dd>
<dt id="ty-Array"><code>Array</code> <span class="tag">type</span></dt>
<dd>A fixed-size sequence of one type.</dd>
<dt id="kw-as"><code>as</code> <span class="tag">soft keyword</span></dt>
<dd>Renames a name in an import. <a href="spec.html#s4">Spec §4</a></dd>
<dt id="fn-assert"><a href="ref/assert.html"><code>assert</code></a> <span class="tag">function</span></dt>
<dd>Aborts if a condition is false. <a href="spec.html#s22">Spec §22</a> <a href="ref/assert.html">Full description</a><br><code class="sig">fn assert(ok Bool) Unit
fn assert(ok Bool, message String) Unit</code></dd>
<dt id="fn-assert_eq"><a href="ref/assert_eq.html"><code>assert_eq</code></a> <span class="tag">function</span></dt>
<dd>Aborts if two values differ. <a href="spec.html#s22">Spec §22</a> <a href="ref/assert_eq.html">Full description</a><br><code class="sig">fn assert_eq[T](a T, b T) Unit</code></dd>
<dt id="fn-assert_ne"><a href="ref/assert_ne.html"><code>assert_ne</code></a> <span class="tag">function</span></dt>
<dd>Aborts if two values are equal. <a href="spec.html#s22">Spec §22</a> <a href="ref/assert_ne.html">Full description</a><br><code class="sig">fn assert_ne[T](a T, b T) Unit</code></dd>
<dt id="ty-Atom"><code>Atom</code> <span class="tag">type</span></dt>
<dd>A shared cell whose value is replaced by <code>swap</code> and <code>reset</code>.</dd>
<dt id="fn-avg"><a href="ref/avg.html"><code>avg</code></a> <span class="tag">function</span></dt>
<dd>The mean of the items, as a Float; an Err for an empty source. <a href="spec.html#s13">Spec §13</a> <a href="ref/avg.html">Full description</a><br><code class="sig">fn avg(xs Seq[Int]) Result[Float, Error]
fn avg(xs Seq[Float]) Result[Float, Error]
fn avg(xs Seq[Decimal]) Result[Float, Error]</code></dd>
</dl>

## B {#b}

<dl class="ref">
<dt id="fn-bind_udp"><a href="ref/bind_udp.html"><code>bind_udp</code></a> <span class="tag">function</span></dt>
<dd>Opens a UDP socket. <a href="spec.html#s19c">Spec §19c</a> <a href="ref/bind_udp.html">Full description</a><br><code class="sig">fn bind_udp(port Int) Result[Udp, Error]</code><br><span class="eff">Effect: parks · Needs permission: net</span></dd>
<dt id="fn-bit_and"><a href="ref/bit_and.html"><code>bit_and</code></a> <span class="tag">function</span></dt>
<dd>Bitwise and. <a href="spec.html#s5">Spec §5</a> <a href="ref/bit_and.html">Full description</a><br><code class="sig">fn bit_and[T](a T, b T) T</code></dd>
<dt id="fn-bit_not"><a href="ref/bit_not.html"><code>bit_not</code></a> <span class="tag">function</span></dt>
<dd>Bitwise complement. <a href="spec.html#s5">Spec §5</a> <a href="ref/bit_not.html">Full description</a><br><code class="sig">fn bit_not[T](a T) T</code></dd>
<dt id="fn-bit_or"><a href="ref/bit_or.html"><code>bit_or</code></a> <span class="tag">function</span></dt>
<dd>Bitwise or. <a href="spec.html#s5">Spec §5</a> <a href="ref/bit_or.html">Full description</a><br><code class="sig">fn bit_or[T](a T, b T) T</code></dd>
<dt id="fn-bit_xor"><a href="ref/bit_xor.html"><code>bit_xor</code></a> <span class="tag">function</span></dt>
<dd>Bitwise exclusive or. <a href="spec.html#s5">Spec §5</a> <a href="ref/bit_xor.html">Full description</a><br><code class="sig">fn bit_xor[T](a T, b T) T</code></dd>
<dt id="ty-Bool"><code>Bool</code> <span class="tag">type</span></dt>
<dd>true or false.</dd>
<dt id="kw-break"><code>break</code> <span class="tag">hard keyword</span></dt>
<dd>Leaves the innermost loop, or the one named by a label; <code>break(value)</code> gives the loop a value. <a href="spec.html#s18a">Spec §18a</a></dd>
</dl>

## C {#c}

<dl class="ref">
<dt id="ty-Cancel"><code>Cancel</code> <span class="tag">type</span></dt>
<dd>A token that tells running fibers to stop.</dd>
<dt id="fn-cancel"><a href="ref/cancel.html"><code>cancel</code></a> <span class="tag">function</span></dt>
<dd>Sets a cancel token. <a href="spec.html#s17">Spec §17</a> <a href="ref/cancel.html">Full description</a><br><code class="sig">fn cancel(c Cancel) Unit</code><br><span class="eff">Effect: uses a resource</span></dd>
<dt id="kw-cancelled"><code>cancelled</code> <span class="tag">soft keyword</span></dt>
<dd>A <code>select</code> arm that runs when a cancel token has been set. <a href="spec.html#s17">Spec §17</a></dd>
<dt id="fn-cast"><a href="ref/cast.html"><code>cast</code></a> <span class="tag">function</span></dt>
<dd>Converts a number to another numeric type, <code>cast[Double](n)</code>. <a href="spec.html#s5">Spec §5</a> <a href="ref/cast.html">Full description</a><br><code class="sig">fn cast[T Numeric, N Numeric](x N) T</code></dd>
<dt id="fn-ceil"><a href="ref/ceil.html"><code>ceil</code></a> <span class="tag">function</span></dt>
<dd>Rounds up to an Int. <a href="spec.html#s5">Spec §5</a> <a href="ref/ceil.html">Full description</a><br><code class="sig">fn ceil(x Double) Int</code></dd>
<dt id="ty-Chan"><code>Chan</code> <span class="tag">type</span></dt>
<dd>A channel between fibers; its read and write ends have separate owners.</dd>
<dt id="ty-Char"><code>Char</code> <span class="tag">type</span></dt>
<dd>One Unicode scalar value, written <code>'a'</code>.</dd>
<dt id="fn-char_count"><a href="ref/char_count.html"><code>char_count</code></a> <span class="tag">function</span></dt>
<dd>How many characters. <a href="spec.html#s5">Spec §5</a> <a href="ref/char_count.html">Full description</a><br><code class="sig">fn char_count(s String) Int</code></dd>
<dt id="fn-chars"><a href="ref/chars.html"><code>chars</code></a> <span class="tag">function</span></dt>
<dd>The characters of a String. <a href="spec.html#s5">Spec §5</a> <a href="ref/chars.html">Full description</a><br><code class="sig">fn chars(s String) Stream[Char]</code></dd>
<dt id="fn-checked_add"><a href="ref/checked_add.html"><code>checked_add</code></a> <span class="tag">function</span></dt>
<dd>Addition that gives an Err instead of overflowing. <a href="spec.html#s5">Spec §5</a> <a href="ref/checked_add.html">Full description</a><br><code class="sig">fn checked_add[T](a T, b T) Result[T, Error]</code></dd>
<dt id="fn-checked_div"><a href="ref/checked_div.html"><code>checked_div</code></a> <span class="tag">function</span></dt>
<dd>Division that gives an Err for zero or overflow. <a href="spec.html#s5">Spec §5</a> <a href="ref/checked_div.html">Full description</a><br><code class="sig">fn checked_div[T](a T, b T) Result[T, Error]</code></dd>
<dt id="fn-checked_mul"><a href="ref/checked_mul.html"><code>checked_mul</code></a> <span class="tag">function</span></dt>
<dd>Multiplication that gives an Err instead of overflowing. <a href="spec.html#s5">Spec §5</a> <a href="ref/checked_mul.html">Full description</a><br><code class="sig">fn checked_mul[T](a T, b T) Result[T, Error]</code></dd>
<dt id="fn-checked_sub"><a href="ref/checked_sub.html"><code>checked_sub</code></a> <span class="tag">function</span></dt>
<dd>Subtraction that gives an Err instead of overflowing. <a href="spec.html#s5">Spec §5</a> <a href="ref/checked_sub.html">Full description</a><br><code class="sig">fn checked_sub[T](a T, b T) Result[T, Error]</code></dd>
<dt id="fn-chunks"><a href="ref/chunks.html"><code>chunks</code></a> <span class="tag">function</span></dt>
<dd>Groups the items in Lists of n. <a href="spec.html#s13">Spec §13</a> <a href="ref/chunks.html">Full description</a><br><code class="sig">fn chunks[T](n Int, xs Seq[T]) Stream[List[T]]</code></dd>
<dt id="fn-clamp"><a href="ref/clamp.html"><code>clamp</code></a> <span class="tag">function</span></dt>
<dd>Limits a value to a low and high bound, or to a range. <a href="spec.html#s5">Spec §5</a> <a href="ref/clamp.html">Full description</a><br><code class="sig">fn clamp[T](x T, lo T, hi T) T
fn clamp[T](x T, r Range) T</code></dd>
<dt id="fn-clear"><a href="ref/clear.html"><code>clear</code></a> <span class="tag">function</span></dt>
<dd>An empty collection of the same kind. <a href="spec.html#s7">Spec §7</a> <a href="ref/clear.html">Full description</a><br><code class="sig">fn clear[K, V](d Dict[K, V]) Dict[K, V]
fn clear[T](s Set[T]) Set[T]
fn clear[T](xs List[T]) List[T]</code></dd>
<dt id="fn-close"><a href="ref/close.html"><code>close</code></a> <span class="tag">function</span></dt>
<dd>Closes a channel end, file or socket. <a href="spec.html#s17">Spec §17</a> <a href="ref/close.html">Full description</a><br><code class="sig">fn close[T](x T) Unit</code><br><span class="eff">Effect: uses a resource</span></dd>
<dt id="kw-closed"><code>closed</code> <span class="tag">soft keyword</span></dt>
<dd>A <code>select</code> arm that runs when a channel has been closed. <a href="spec.html#s17">Spec §17</a></dd>
<dt id="fn-collect"><a href="ref/collect.html"><code>collect</code></a> <span class="tag">function</span></dt>
<dd>Gathers a stream into a List. <a href="spec.html#s13">Spec §13</a> <a href="ref/collect.html">Full description</a><br><code class="sig">fn collect[T](xs Seq[T]) List[T]</code></dd>
<dt id="fn-collect_errors"><a href="ref/collect_errors.html"><code>collect_errors</code></a> <span class="tag">function</span></dt>
<dd>Ok of all values, or Err of all errors. <a href="spec.html#s15">Spec §15</a> <a href="ref/collect_errors.html">Full description</a><br><code class="sig">fn collect_errors[T, E](rs Seq[Result[T, E]]) Result[List[T], List[E]]</code></dd>
<dt id="fn-connect"><a href="ref/connect.html"><code>connect</code></a> <span class="tag">function</span></dt>
<dd>Opens a connection. <a href="spec.html#s19c">Spec §19c</a> <a href="ref/connect.html">Full description</a><br><code class="sig">fn connect(host String, port Int) Result[Io, Error]</code><br><span class="eff">Effect: parks · Needs permission: net</span></dd>
<dt id="fn-connect_tls"><a href="ref/connect_tls.html"><code>connect_tls</code></a> <span class="tag">function</span></dt>
<dd>Like <code>connect</code>, with TLS. <a href="spec.html#s19c">Spec §19c</a> <a href="ref/connect_tls.html">Full description</a><br><code class="sig">fn connect_tls(host String, port Int) Result[Io, Error]</code><br><span class="eff">Effect: parks · Needs permission: net</span></dd>
<dt id="fn-const"><a href="ref/const.html"><code>const</code></a> <span class="tag">function</span></dt>
<dd>A function that always gives one value. <a href="spec.html#s23">Spec §23</a> <a href="ref/const.html">Full description</a><br><code class="sig">fn const[A, B](x A) (B) -&gt; A</code></dd>
<dt id="fn-contains"><a href="ref/contains.html"><code>contains</code></a> <span class="tag">function</span></dt>
<dd>True if a String contains a piece of text, or a collection an item. <a href="spec.html#s7">Spec §7</a> <a href="ref/contains.html">Full description</a><br><code class="sig">fn contains(s String, t String) Bool
fn contains[T Equatable](xs Seq[T], x T) Bool
fn contains[K, V](d Dict[K, V], k K) Bool</code></dd>
<dt id="kw-continue"><code>continue</code> <span class="tag">hard keyword</span></dt>
<dd>Skips to the next pass of a loop, or of the loop named by a label. <a href="spec.html#s18a">Spec §18a</a></dd>
<dt id="fn-count"><a href="ref/count.html"><code>count</code></a> <span class="tag">function</span></dt>
<dd>How many items there are. <a href="spec.html#s13">Spec §13</a> <a href="ref/count.html">Full description</a><br><code class="sig">fn count[T](xs Seq[T]) Int</code></dd>
<dt id="fn-count_by"><a href="ref/count_by.html"><code>count_by</code></a> <span class="tag">function</span></dt>
<dd>A Dict of how many items have each key. <a href="spec.html#s13">Spec §13</a> <a href="ref/count_by.html">Full description</a><br><code class="sig">fn count_by[T, K](f (T) -&gt; K, xs Seq[T]) Dict[K, Int]</code></dd>
<dt id="fn-cwd"><a href="ref/cwd.html"><code>cwd</code></a> <span class="tag">function</span></dt>
<dd>The current directory. <a href="spec.html#s19c">Spec §19c</a> <a href="ref/cwd.html">Full description</a><br><code class="sig">fn cwd() String</code><br><span class="eff">Effect: uses the system</span></dd>
<dt id="fn-cycle"><a href="ref/cycle.html"><code>cycle</code></a> <span class="tag">function</span></dt>
<dd>Repeats a source forever. <a href="spec.html#s13">Spec §13</a> <a href="ref/cycle.html">Full description</a><br><code class="sig">fn cycle[T](xs Seq[T]) Stream[T]</code></dd>
</dl>

## D {#d}

<dl class="ref">
<dt id="kw-daemon"><code>daemon</code> <span class="tag">hard keyword</span></dt>
<dd>The main cycle of a server program, which runs until it is stopped. <a href="spec.html#s16">Spec §16</a></dd>
<dt id="ty-DateTime"><code>DateTime</code> <span class="tag">type</span></dt>
<dd>A calendar date and time of day.</dd>
<dt id="fn-day_of_year"><a href="ref/day_of_year.html"><code>day_of_year</code></a> <span class="tag">function</span></dt>
<dd>1 to 366. <a href="spec.html#s19e">Spec §19e</a> <a href="ref/day_of_year.html">Full description</a><br><code class="sig">fn day_of_year(t DateTime) Int</code></dd>
<dt id="fn-days_in_month"><a href="ref/days_in_month.html"><code>days_in_month</code></a> <span class="tag">function</span></dt>
<dd>Days in a month, leap years included. <a href="spec.html#s19e">Spec §19e</a> <a href="ref/days_in_month.html">Full description</a><br><code class="sig">fn days_in_month(y Int, m Int) Int</code></dd>
<dt id="fn-dbg"><a href="ref/dbg.html"><code>dbg</code></a> <span class="tag">function</span></dt>
<dd>Prints a value and where it came from, and gives the value back. <a href="spec.html#s22">Spec §22</a> <a href="ref/dbg.html">Full description</a><br><code class="sig">fn dbg[T](x T) T</code><br><span class="eff">Effect: prints, but is allowed in any code</span></dd>
<dt id="fn-debug_assert"><a href="ref/debug_assert.html"><code>debug_assert</code></a> <span class="tag">function</span></dt>
<dd>An <code>assert</code> that a release build leaves out. <a href="spec.html#s22">Spec §22</a> <a href="ref/debug_assert.html">Full description</a><br><code class="sig">fn debug_assert(ok Bool) Unit</code></dd>
<dt id="ty-Decimal"><code>Decimal</code> <span class="tag">type</span></dt>
<dd>An exact base-ten number with a fixed scale, for money.</dd>
<dt id="kw-delegate"><code>delegate</code> <span class="tag">soft keyword</span></dt>
<dd>After a field's type, forwards the interface methods of that field. <a href="spec.html#s12">Spec §12</a></dd>
<dt id="kw-deriving"><code>deriving</code> <span class="tag">soft keyword</span></dt>
<dd>In a tuple or enum header, asks for generated methods such as <code>show</code>, <code>eq</code>, <code>ord</code> or <code>read</code>. <a href="spec.html#s6">Spec §6</a></dd>
<dt id="ty-Dict"><code>Dict</code> <span class="tag">type</span></dt>
<dd>A collection of key-value pairs.</dd>
<dt id="fn-disarm"><a href="ref/disarm.html"><code>disarm</code></a> <span class="tag">function</span></dt>
<dd>Stops a timer. <a href="spec.html#s17">Spec §17</a> <a href="ref/disarm.html">Full description</a><br><code class="sig">fn disarm(t Timer) Unit</code><br><span class="eff">Effect: uses a resource</span></dd>
<dt id="fn-distinct"><a href="ref/distinct.html"><code>distinct</code></a> <span class="tag">function</span></dt>
<dd>Drops repeated items, keeping the first of each. <a href="spec.html#s13">Spec §13</a> <a href="ref/distinct.html">Full description</a><br><code class="sig">fn distinct[T Equatable](xs Seq[T]) Stream[T]</code></dd>
<dt id="fn-distinct_by"><a href="ref/distinct_by.html"><code>distinct_by</code></a> <span class="tag">function</span></dt>
<dd>Drops items whose key has been seen. <a href="spec.html#s13">Spec §13</a> <a href="ref/distinct_by.html">Full description</a><br><code class="sig">fn distinct_by[T, K](f (T) -&gt; K, xs Seq[T]) Stream[T]</code></dd>
<dt id="fn-div"><a href="ref/div.html"><code>div</code></a> <span class="tag">function</span></dt>
<dd>Divides Decimals to a scale and <code>Mode</code>; an Err for division by zero. <a href="spec.html#s5">Spec §5</a> <a href="ref/div.html">Full description</a><br><code class="sig">fn div(a Decimal, b Decimal, scale Int, mode Mode) Result[Decimal, Error]</code></dd>
<dt id="kw-do"><code>do</code> <span class="tag">hard keyword</span></dt>
<dd>Joins a one-line <code>for</code> header to its body, and opens a block that is itself an expression. <a href="spec.html#s1">Spec §1</a></dd>
<dt id="ty-Double"><code>Double</code> <span class="tag">type</span></dt>
<dd>A 64-bit floating-point number; <code>Float</code> is the 32-bit one.</dd>
<dt id="fn-drop"><a href="ref/drop.html"><code>drop</code></a> <span class="tag">function</span></dt>
<dd>All but the first n items. <a href="spec.html#s13">Spec §13</a> <a href="ref/drop.html">Full description</a><br><code class="sig">fn drop[T](n Int, xs Seq[T]) Stream[T]</code></dd>
<dt id="fn-drop_last"><a href="ref/drop_last.html"><code>drop_last</code></a> <span class="tag">function</span></dt>
<dd>All but the last n items. <a href="spec.html#s13">Spec §13</a> <a href="ref/drop_last.html">Full description</a><br><code class="sig">fn drop_last[T](n Int, xs Seq[T]) Stream[T]</code></dd>
<dt id="fn-drop_while"><a href="ref/drop_while.html"><code>drop_while</code></a> <span class="tag">function</span></dt>
<dd>Skips items from the start while a test holds. <a href="spec.html#s13">Spec §13</a> <a href="ref/drop_while.html">Full description</a><br><code class="sig">fn drop_while[T](f (T) -&gt; Bool, xs Seq[T]) Stream[T]</code></dd>
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
<dt id="fn-ends_with"><a href="ref/ends_with.html"><code>ends_with</code></a> <span class="tag">function</span></dt>
<dd>True if the text ends with a suffix. <a href="spec.html#s5">Spec §5</a> <a href="ref/ends_with.html">Full description</a><br><code class="sig">fn ends_with(s String, suffix String) Bool
fn ends_with(s String, c Char) Bool</code></dd>
<dt id="fn-ensure"><a href="ref/ensure.html"><code>ensure</code></a> <span class="tag">function</span></dt>
<dd>Ok(()) when a condition holds, else Err(e). <a href="spec.html#s15">Spec §15</a> <a href="ref/ensure.html">Full description</a><br><code class="sig">fn ensure[E](ok Bool, e E) Result[Unit, E]</code></dd>
<dt id="kw-enum"><code>enum</code> <span class="tag">hard keyword</span></dt>
<dd>Declares an enum: a closed set of cases, each optionally carrying values. <a href="spec.html#s6">Spec §6</a></dd>
<dt id="fn-enumerate"><a href="ref/enumerate.html"><code>enumerate</code></a> <span class="tag">function</span></dt>
<dd>Pairs each item with its position, from 0. <a href="spec.html#s13">Spec §13</a> <a href="ref/enumerate.html">Full description</a><br><code class="sig">fn enumerate[T](xs Seq[T]) Stream[(Int, T)]</code></dd>
<dt id="fn-eprint"><a href="ref/eprint.html"><code>eprint</code></a> <span class="tag">function</span></dt>
<dd>Prints a value on standard error. <a href="spec.html#s19b">Spec §19b</a> <a href="ref/eprint.html">Full description</a><br><code class="sig">fn eprint[T](x T) Unit
fn eprint[T](out Io, x T) Unit</code><br><span class="eff">Effect: prints</span></dd>
<dt id="fn-eprintln"><a href="ref/eprintln.html"><code>eprintln</code></a> <span class="tag">function</span></dt>
<dd>Prints a value and a newline on standard error. <a href="spec.html#s19b">Spec §19b</a> <a href="ref/eprintln.html">Full description</a><br><code class="sig">fn eprintln() Unit
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
<dt id="fn-fail"><a href="ref/fail.html"><code>fail</code></a> <span class="tag">function</span></dt>
<dd>An Err with a code and optional message. <a href="spec.html#s15">Spec §15</a> <a href="ref/fail.html">Full description</a><br><code class="sig">fn fail[T](code Int) Result[T, Error]
fn fail[T](code Int, message String) Result[T, Error]</code></dd>
<dt id="kw-false"><code>false</code> <span class="tag">hard keyword</span></dt>
<dd>The Bool value false. <a href="spec.html#s5">Spec §5</a></dd>
<dt id="kw-fiber"><code>fiber</code> <span class="tag">hard keyword</span></dt>
<dd><code>fiber fn</code> declares a function that runs as its own fiber when started with <code>go</code>. <a href="spec.html#s18">Spec §18</a></dd>
<dt id="fn-file_info"><a href="ref/file_info.html"><code>file_info</code></a> <span class="tag">function</span></dt>
<dd>A file's kind and size. <a href="spec.html#s19c">Spec §19c</a> <a href="ref/file_info.html">Full description</a><br><code class="sig">fn file_info(p String) Result[FileInfo, Error]</code><br><span class="eff">Effect: parks · Needs permission: fs</span></dd>
<dt id="fn-filter"><a href="ref/filter.html"><code>filter</code></a> <span class="tag">function</span></dt>
<dd>Keeps the items for which a test is true. <a href="spec.html#s13">Spec §13</a> <a href="ref/filter.html">Full description</a><br><code class="sig">fn filter[T](f (T) -&gt; Bool, xs Seq[T]) Stream[T]</code></dd>
<dt id="fn-filter_map"><a href="ref/filter_map.html"><code>filter_map</code></a> <span class="tag">function</span></dt>
<dd>Applies a function that gives an Option and keeps the values that are present. <a href="spec.html#s13">Spec §13</a> <a href="ref/filter_map.html">Full description</a><br><code class="sig">fn filter_map[T, U](f (T) -&gt; Option[U], xs Seq[T]) Stream[U]</code></dd>
<dt id="fn-find"><a href="ref/find.html"><code>find</code></a> <span class="tag">function</span></dt>
<dd>The first item for which a test is true; an Err if there is none. <a href="spec.html#s13">Spec §13</a> <a href="ref/find.html">Full description</a><br><code class="sig">fn find[T](f (T) -&gt; Bool, xs Seq[T]) Result[T, Error]</code></dd>
<dt id="fn-find_map"><a href="ref/find_map.html"><code>find_map</code></a> <span class="tag">function</span></dt>
<dd>The first present value a function gives; an Err if there is none. <a href="spec.html#s13">Spec §13</a> <a href="ref/find_map.html">Full description</a><br><code class="sig">fn find_map[T, U](f (T) -&gt; Option[U], xs Seq[T]) Result[U, Error]</code></dd>
<dt id="fn-finite"><a href="ref/finite.html"><code>finite</code></a> <span class="tag">function</span></dt>
<dd>Ok(x) when x is a finite number, an Err otherwise. <a href="spec.html#s5">Spec §5</a> <a href="ref/finite.html">Full description</a><br><code class="sig">fn finite(x Double) Result[Double, Error]</code></dd>
<dt id="fn-first"><a href="ref/first.html"><code>first</code></a> <span class="tag">function</span></dt>
<dd>The first item; an Err if empty. <a href="spec.html#s13">Spec §13</a> <a href="ref/first.html">Full description</a><br><code class="sig">fn first[T](xs Seq[T]) Result[T, Error]</code></dd>
<dt id="fn-flatten"><a href="ref/flatten.html"><code>flatten</code></a> <span class="tag">function</span></dt>
<dd>Turns a source of sources into one source. <a href="spec.html#s13">Spec §13</a> <a href="ref/flatten.html">Full description</a><br><code class="sig">fn flatten[T](xs Seq[Seq[T]]) Stream[T]</code></dd>
<dt id="fn-flip"><a href="ref/flip.html"><code>flip</code></a> <span class="tag">function</span></dt>
<dd>Swaps the order of a two-parameter function's arguments. <a href="spec.html#s23">Spec §23</a> <a href="ref/flip.html">Full description</a><br><code class="sig">fn flip[A, B, R](f (A, B) -&gt; R) (B, A) -&gt; R</code></dd>
<dt id="fn-floor"><a href="ref/floor.html"><code>floor</code></a> <span class="tag">function</span></dt>
<dd>Rounds down to an Int. <a href="spec.html#s5">Spec §5</a> <a href="ref/floor.html">Full description</a><br><code class="sig">fn floor(x Double) Int</code></dd>
<dt id="fn-flush"><a href="ref/flush.html"><code>flush</code></a> <span class="tag">function</span></dt>
<dd>Sends buffered output on. <a href="spec.html#s19b">Spec §19b</a> <a href="ref/flush.html">Full description</a><br><code class="sig">fn flush() Unit
fn flush(out Io) Unit</code></dd>
<dt id="fn-fmap"><a href="ref/fmap.html"><code>fmap</code></a> <span class="tag">function</span></dt>
<dd>Like <code>map</code>, but a List stays a List and an Array an Array. <a href="spec.html#s13">Spec §13</a> <a href="ref/fmap.html">Full description</a><br><code class="sig">fn fmap[T, U](f (T) -&gt; U, xs List[T]) List[U]
fn fmap[T, U, N](f (T) -&gt; U, xs Array[T][N]) Array[U][N]
fn fmap[T, U](f (T) -&gt; U, o Option[T]) Option[U]
fn fmap[T, U](f (T) -&gt; U, r Result[T, Error]) Result[U, Error]</code></dd>
<dt id="fn-fmt"><a href="ref/fmt.html"><code>fmt</code></a> <span class="tag">function</span></dt>
<dd>Fills a template of <code>{}</code> slots with values. <a href="spec.html#s5">Spec §5</a> <a href="ref/fmt.html">Full description</a><br><code class="sig">fn fmt(template String, args...) String</code></dd>
<dt id="kw-fn"><code>fn</code> <span class="tag">hard keyword</span></dt>
<dd>Declares a function, <code>fn name(params) Result = body</code>, or a function value. <a href="spec.html#s9">Spec §9</a></dd>
<dt id="fn-fold_all"><a href="ref/fold_all.html"><code>fold_all</code></a> <span class="tag">function</span></dt>
<dd>Combines the items of a collection with their Monoid. <a href="spec.html#s23">Spec §23</a> <a href="ref/fold_all.html">Full description</a><br><code class="sig">fn fold_all[T Monoid](xs Seq[T]) T</code></dd>
<dt id="fn-fold_map"><a href="ref/fold_map.html"><code>fold_map</code></a> <span class="tag">function</span></dt>
<dd>Maps each item to a Monoid value, then combines them. <a href="spec.html#s23">Spec §23</a> <a href="ref/fold_map.html">Full description</a><br><code class="sig">fn fold_map[T, M Monoid](f (T) -&gt; M, xs Seq[T]) M</code></dd>
<dt id="kw-for"><code>for</code> <span class="tag">hard keyword</span></dt>
<dd>Moxie's only loop: over a collection or range, or on a condition, and it can produce a value. <a href="spec.html#s18">Spec §18</a></dd>
<dt id="kw-foreign"><code>foreign</code> <span class="tag">soft keyword</span></dt>
<dd>Opens a block of declarations for functions in a C library. <a href="spec.html#s19a">Spec §19a</a></dd>
<dt id="fn-format_time"><a href="ref/format_time.html"><code>format_time</code></a> <span class="tag">function</span></dt>
<dd>A DateTime as text, from a pattern. <a href="spec.html#s19e">Spec §19e</a> <a href="ref/format_time.html">Full description</a><br><code class="sig">fn format_time(t DateTime, fmt String) String
fn format_time(t DateTime, fmt String, loc Locale) String</code></dd>
<dt id="kw-forward"><code>forward</code> <span class="tag">hard keyword</span></dt>
<dd><code>forward fn</code> declares a function's signature ahead of its body, so earlier code can call it in a one-pass compile. <a href="spec.html#s9">Spec §9</a></dd>
<dt id="fn-frequencies"><a href="ref/frequencies.html"><code>frequencies</code></a> <span class="tag">function</span></dt>
<dd>A Dict of how many times each item occurs. <a href="spec.html#s13">Spec §13</a> <a href="ref/frequencies.html">Full description</a><br><code class="sig">fn frequencies[T](xs Seq[T]) Dict[T, Int]</code></dd>
<dt id="ty-Future"><code>Future</code> <span class="tag">type</span></dt>
<dd>A value that will be supplied once, by <code>resolve</code> or <code>reject</code>.</dd>
</dl>

## G {#g}

<dl class="ref">
<dt id="ty-Gen"><code>Gen</code> <span class="tag">type</span></dt>
<dd>A seeded source of values for property tests.</dd>
<dt id="fn-gen_bool"><a href="ref/gen_bool.html"><code>gen_bool</code></a> <span class="tag">function</span></dt>
<dd>A generated Bool. <a href="spec.html#s22">Spec §22</a> <a href="ref/gen_bool.html">Full description</a><br><code class="sig">fn gen_bool(g Gen) Bool</code></dd>
<dt id="fn-gen_int"><a href="ref/gen_int.html"><code>gen_int</code></a> <span class="tag">function</span></dt>
<dd>A generated Int between two bounds. <a href="spec.html#s22">Spec §22</a> <a href="ref/gen_int.html">Full description</a><br><code class="sig">fn gen_int[T](g Gen, lo T, hi T) T</code></dd>
<dt id="fn-gen_pick"><a href="ref/gen_pick.html"><code>gen_pick</code></a> <span class="tag">function</span></dt>
<dd>A generated pick from a List. <a href="spec.html#s22">Spec §22</a> <a href="ref/gen_pick.html">Full description</a><br><code class="sig">fn gen_pick[T](g Gen, xs List[T]) T</code></dd>
<dt id="fn-get"><a href="ref/get.html"><code>get</code></a> <span class="tag">function</span></dt>
<dd>The item at a key or position; an Err if absent. <a href="spec.html#s7">Spec §7</a> <a href="ref/get.html">Full description</a><br><code class="sig">fn get[K, V](d Dict[K, V], k K) Result[V, Error]
fn get[T](xs List[T], i Int) Result[T, Error]
fn get[T](xs Array[T], i Int) Result[T, Error]</code></dd>
<dt id="fn-get_or"><a href="ref/get_or.html"><code>get_or</code></a> <span class="tag">function</span></dt>
<dd>The value, or a default when it is absent or an Err. <a href="spec.html#s7">Spec §7</a> <a href="ref/get_or.html">Full description</a><br><code class="sig">fn get_or[T, E](r Result[T, E], d T) T
fn get_or[T](o Option[T], d T) T
fn get_or[K, V](d Dict[K, V], k K, d2 V) V
fn get_or[T](xs List[T], i Int, d T) T</code></dd>
<dt id="kw-go"><code>go</code> <span class="tag">hard keyword</span></dt>
<dd>Starts a fiber: <code>go worker(args)</code> returns at once and the function runs concurrently. <a href="spec.html#s18">Spec §18</a></dd>
<dt id="fn-grapheme_count"><a href="ref/grapheme_count.html"><code>grapheme_count</code></a> <span class="tag">function</span></dt>
<dd>How many user-perceived characters. <a href="spec.html#s5">Spec §5</a> <a href="ref/grapheme_count.html">Full description</a><br><code class="sig">fn grapheme_count(s String) Int</code></dd>
<dt id="fn-graphemes"><a href="ref/graphemes.html"><code>graphemes</code></a> <span class="tag">function</span></dt>
<dd>The user-perceived characters of a String. <a href="spec.html#s5">Spec §5</a> <a href="ref/graphemes.html">Full description</a><br><code class="sig">fn graphemes(s String) Stream[String]</code></dd>
<dt id="fn-group_by"><a href="ref/group_by.html"><code>group_by</code></a> <span class="tag">function</span></dt>
<dd>A Dict from key to the Lists of items with that key. <a href="spec.html#s13">Spec §13</a> <a href="ref/group_by.html">Full description</a><br><code class="sig">fn group_by[T, K](f (T) -&gt; K, xs Seq[T]) Dict[K, List[T]]</code></dd>
<dt id="fn-guard"><a href="ref/guard.html"><code>guard</code></a> <span class="tag">function</span></dt>
<dd>Ok(()) when a condition holds, else an Err with the code MISSING. <a href="spec.html#s15">Spec §15</a> <a href="ref/guard.html">Full description</a><br><code class="sig">fn guard(ok Bool) Result[Unit, Error]</code></dd>
</dl>

## H {#h}

<dl class="ref">
<dt id="fn-hash"><a href="ref/hash.html"><code>hash</code></a> <span class="tag">function</span></dt>
<dd>A hash code for a value. <a href="spec.html#s23">Spec §23</a> <a href="ref/hash.html">Full description</a><br><code class="sig">fn hash[T](x T) Int</code></dd>
<dt id="fn-home_dir"><a href="ref/home_dir.html"><code>home_dir</code></a> <span class="tag">function</span></dt>
<dd>The user's home directory. <a href="spec.html#s19c">Spec §19c</a> <a href="ref/home_dir.html">Full description</a><br><code class="sig">fn home_dir() Result[String, Error]</code><br><span class="eff">Effect: uses the system</span></dd>
<dt id="fn-hostname"><a href="ref/hostname.html"><code>hostname</code></a> <span class="tag">function</span></dt>
<dd>This computer's name. <a href="spec.html#s19c">Spec §19c</a> <a href="ref/hostname.html">Full description</a><br><code class="sig">fn hostname() String</code><br><span class="eff">Effect: uses the system</span></dd>
</dl>

## I {#i}

<dl class="ref">
<dt id="fn-identity"><a href="ref/identity.html"><code>identity</code></a> <span class="tag">function</span></dt>
<dd>Gives its argument back. <a href="spec.html#s23">Spec §23</a> <a href="ref/identity.html">Full description</a><br><code class="sig">fn identity[T](x T) T</code></dd>
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
<dt id="fn-index"><a href="ref/index.html"><code>index</code></a> <span class="tag">function</span></dt>
<dd>The position of an enum case in its declaration. <a href="spec.html#s23">Spec §23</a> <a href="ref/index.html">Full description</a><br><code class="sig">fn index[E](x E) Int</code></dd>
<dt id="fn-indices"><a href="ref/indices.html"><code>indices</code></a> <span class="tag">function</span></dt>
<dd>The range of valid positions. <a href="spec.html#s7">Spec §7</a> <a href="ref/indices.html">Full description</a><br><code class="sig">fn indices[T](xs Seq[T]) Range
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
<dt id="fn-intersperse"><a href="ref/intersperse.html"><code>intersperse</code></a> <span class="tag">function</span></dt>
<dd>Puts a separator between items. <a href="spec.html#s13">Spec §13</a> <a href="ref/intersperse.html">Full description</a><br><code class="sig">fn intersperse[T](sep T, xs Seq[T]) Stream[T]</code></dd>
<dt id="kw-invariant"><code>invariant</code> <span class="tag">soft keyword</span></dt>
<dd>A line among a tuple's fields that states a condition every value of the tuple must satisfy. <a href="spec.html#s9c">Spec §9c</a></dd>
<dt id="ty-Io"><code>Io</code> <span class="tag">type</span></dt>
<dd>A readable and writable stream: a socket or a standard stream.</dd>
<dt id="kw-is"><code>is</code> <span class="tag">hard keyword</span></dt>
<dd>Tests a value against a pattern and binds its names: <code>r is Ok(v)</code>. <a href="spec.html#s8">Spec §8</a></dd>
<dt id="fn-is_empty"><a href="ref/is_empty.html"><code>is_empty</code></a> <span class="tag">function</span></dt>
<dd>True when there are no items. <a href="spec.html#s7">Spec §7</a> <a href="ref/is_empty.html">Full description</a><br><code class="sig">fn is_empty(s String) Bool
fn is_empty[T](xs Seq[T]) Bool
fn is_empty[K, V](d Dict[K, V]) Bool
fn is_empty[T](s Set[T]) Bool</code></dd>
<dt id="fn-is_err"><a href="ref/is_err.html"><code>is_err</code></a> <span class="tag">function</span></dt>
<dd>True for an Err. <a href="spec.html#s15">Spec §15</a> <a href="ref/is_err.html">Full description</a><br><code class="sig">fn is_err[T, E](r Result[T, E]) Bool</code></dd>
<dt id="fn-is_finite"><a href="ref/is_finite.html"><code>is_finite</code></a> <span class="tag">function</span></dt>
<dd>True for an ordinary number. <a href="spec.html#s5">Spec §5</a> <a href="ref/is_finite.html">Full description</a><br><code class="sig">fn is_finite(x Double) Bool</code></dd>
<dt id="fn-is_inf"><a href="ref/is_inf.html"><code>is_inf</code></a> <span class="tag">function</span></dt>
<dd>True for infinity. <a href="spec.html#s5">Spec §5</a> <a href="ref/is_inf.html">Full description</a><br><code class="sig">fn is_inf(x Double) Bool</code></dd>
<dt id="fn-is_nan"><a href="ref/is_nan.html"><code>is_nan</code></a> <span class="tag">function</span></dt>
<dd>True for not-a-number. <a href="spec.html#s5">Spec §5</a> <a href="ref/is_nan.html">Full description</a><br><code class="sig">fn is_nan(x Double) Bool</code></dd>
<dt id="fn-is_ok"><a href="ref/is_ok.html"><code>is_ok</code></a> <span class="tag">function</span></dt>
<dd>True for an Ok. <a href="spec.html#s15">Spec §15</a> <a href="ref/is_ok.html">Full description</a><br><code class="sig">fn is_ok[T, E](r Result[T, E]) Bool</code></dd>
<dt id="fn-iso"><a href="ref/iso.html"><code>iso</code></a> <span class="tag">function</span></dt>
<dd>A DateTime as ISO 8601 text. <a href="spec.html#s19e">Spec §19e</a> <a href="ref/iso.html">Full description</a><br><code class="sig">fn iso(t DateTime) String</code></dd>
<dt id="fn-items"><a href="ref/items.html"><code>items</code></a> <span class="tag">function</span></dt>
<dd>The (key, value) pairs of a Dict. <a href="spec.html#s7">Spec §7</a> <a href="ref/items.html">Full description</a><br><code class="sig">fn items[K, V](d Dict[K, V]) Stream[(K, V)]</code></dd>
<dt id="fn-iterate"><a href="ref/iterate.html"><code>iterate</code></a> <span class="tag">function</span></dt>
<dd>A seed, then the function applied again and again. <a href="spec.html#s13">Spec §13</a> <a href="ref/iterate.html">Full description</a><br><code class="sig">fn iterate[T](seed T, f (T) -&gt; T) Stream[T]</code></dd>
</dl>

## J {#j}

<dl class="ref">
<dt id="fn-join"><a href="ref/join.html"><code>join</code></a> <span class="tag">function</span></dt>
<dd>Makes one String of the items, with an optional separator. <a href="spec.html#s7">Spec §7</a> <a href="ref/join.html">Full description</a><br><code class="sig">fn join[T](xs Seq[T], sep String) String
fn join[T](xs Seq[T]) String</code></dd>
</dl>

## K {#k}

<dl class="ref">
<dt id="fn-keys"><a href="ref/keys.html"><code>keys</code></a> <span class="tag">function</span></dt>
<dd>The keys of a Dict. <a href="spec.html#s7">Spec §7</a> <a href="ref/keys.html">Full description</a><br><code class="sig">fn keys[K, V](d Dict[K, V]) Stream[K]</code></dd>
<dt id="fn-kill_child"><a href="ref/kill_child.html"><code>kill_child</code></a> <span class="tag">function</span></dt>
<dd>Stops it. <a href="spec.html#s19c">Spec §19c</a> <a href="ref/kill_child.html">Full description</a><br><code class="sig">fn kill_child(c Child) Unit</code><br><span class="eff">Effect: parks</span></dd>
</dl>

## L {#l}

<dl class="ref">
<dt id="fn-last"><a href="ref/last.html"><code>last</code></a> <span class="tag">function</span></dt>
<dd>The last item; an Err if empty. <a href="spec.html#s13">Spec §13</a> <a href="ref/last.html">Full description</a><br><code class="sig">fn last[T](xs Seq[T]) Result[T, Error]</code></dd>
<dt id="kw-lazy"><code>lazy</code> <span class="tag">soft keyword</span></dt>
<dd>Marks a parameter that is evaluated each time the function reads it, and not at all if it never does. <a href="spec.html#s9">Spec §9</a></dd>
<dt id="fn-len"><a href="ref/len.html"><code>len</code></a> <span class="tag">function</span></dt>
<dd>The number of items in a collection, or of bytes in a String. <a href="spec.html#s7">Spec §7</a> <a href="ref/len.html">Full description</a><br><code class="sig">fn len(s String) Int
fn len[T](xs Seq[T]) Int
fn len[K, V](d Dict[K, V]) Int</code></dd>
<dt id="fn-lines"><a href="ref/lines.html"><code>lines</code></a> <span class="tag">function</span></dt>
<dd>The lines of a socket or file, as a stream. <a href="spec.html#s19b">Spec §19b</a> <a href="ref/lines.html">Full description</a><br><code class="sig">fn lines(src Io) Stream[String]</code><br><span class="eff">Effect: parks</span></dd>
<dt id="ty-List"><code>List</code> <span class="tag">type</span></dt>
<dd>An immutable sequence that shares structure when updated.</dd>
<dt id="fn-list_dir"><a href="ref/list_dir.html"><code>list_dir</code></a> <span class="tag">function</span></dt>
<dd>The sorted names in a directory. <a href="spec.html#s19c">Spec §19c</a> <a href="ref/list_dir.html">Full description</a><br><code class="sig">fn list_dir(p String) Result[Array[String], Error]</code><br><span class="eff">Effect: parks · Needs permission: fs</span></dd>
<dt id="fn-listen"><a href="ref/listen.html"><code>listen</code></a> <span class="tag">function</span></dt>
<dd>Starts listening on a port. <a href="spec.html#s19c">Spec §19c</a> <a href="ref/listen.html">Full description</a><br><code class="sig">fn listen(port Int) Result[Listener, Error]</code><br><span class="eff">Effect: parks · Needs permission: net</span></dd>
<dt id="fn-listen_tls"><a href="ref/listen_tls.html"><code>listen_tls</code></a> <span class="tag">function</span></dt>
<dd>Like <code>listen</code>, with TLS. <a href="spec.html#s19c">Spec §19c</a> <a href="ref/listen_tls.html">Full description</a><br><code class="sig">fn listen_tls(port Int, cert String, key String) Result[Listener, Error]</code><br><span class="eff">Effect: parks · Needs permission: net</span></dd>
<dt id="ty-Listener"><code>Listener</code> <span class="tag">type</span></dt>
<dd>A listening socket that gives connections through <code>accept</code>.</dd>
<dt id="fn-lower"><a href="ref/lower.html"><code>lower</code></a> <span class="tag">function</span></dt>
<dd>Lower case. <a href="spec.html#s5">Spec §5</a> <a href="ref/lower.html">Full description</a><br><code class="sig">fn lower(s String) String
fn lower(c Char) Char</code></dd>
</dl>

## M {#m}

<dl class="ref">
<dt id="fn-make_dir"><a href="ref/make_dir.html"><code>make_dir</code></a> <span class="tag">function</span></dt>
<dd>Creates a directory. <a href="spec.html#s19c">Spec §19c</a> <a href="ref/make_dir.html">Full description</a><br><code class="sig">fn make_dir(p String) Result[Unit, Error]</code><br><span class="eff">Effect: parks · Needs permission: fs</span></dd>
<dt id="fn-map"><a href="ref/map.html"><code>map</code></a> <span class="tag">function</span></dt>
<dd>Applies a function to each item (<code>Result</code> and <code>Option</code> too: it changes the value inside). <a href="spec.html#s13">Spec §13</a> <a href="ref/map.html">Full description</a><br><code class="sig">fn map[T, U](f (T) -&gt; U, xs Seq[T]) Stream[U]
fn map[T, U](f (T) -&gt; U, r Result[T, Error]) Result[U, Error]
fn map[T, U](f (T) -&gt; U, o Option[T]) Option[U]</code></dd>
<dt id="fn-map_all"><a href="ref/map_all.html"><code>map_all</code></a> <span class="tag">function</span></dt>
<dd>Combines two to six Results with a function, collecting all errors. <a href="spec.html#s15">Spec §15</a> <a href="ref/map_all.html">Full description</a><br><code class="sig">fn map_all[A, B, R](f (A, B) -&gt; R, a Result[A, Error], b Result[B, Error]) Result[R, List[Error]]
fn map_all[A, B, C, R](f (A, B, C) -&gt; R, a Result[A, Error], b Result[B, Error], c Result[C, Error]) Result[R, List[Error]]
fn map_all[A, B, C, D, R](f (A, B, C, D) -&gt; R, a Result[A, Error], b Result[B, Error], c Result[C, Error], d Result[D, Error]) Result[R, List[Error]]
fn map_all[A, B, C, D, E, R, E](f (A, B, C, D, E) -&gt; R, a Result[A, E], b Result[B, E], c Result[C, E], d Result[D, E], e Result[E, E]) Result[R, List[E]]
fn map_all[A, B, C, D, E, F, R, E](f (A, B, C, D, E, F) -&gt; R, a Result[A, E], b Result[B, E], c Result[C, E], d Result[D, E], e Result[E, E], f Result[F, E]) Result[R, List[E]]
fn map_all[A, B, R, X](rs (Result[A, X], Result[B, X]), f (A, B) -&gt; R) Result[R, List[X]]
fn map_all[A, B, C, R, X](rs (Result[A, X], Result[B, X], Result[C, X]), f (A, B, C) -&gt; R) Result[R, List[X]]
fn map_all[A, B, C, D, R, X](rs (Result[A, X], Result[B, X], Result[C, X], Result[D, X]), f (A, B, C, D) -&gt; R) Result[R, List[X]]
fn map_all[A, B, C, D, E, R, X](rs (Result[A, X], Result[B, X], Result[C, X], Result[D, X], Result[E, X]), f (A, B, C, D, E) -&gt; R) Result[R, List[X]]
fn map_all[A, B, C, D, E, F, R, X](rs (Result[A, X], Result[B, X], Result[C, X], Result[D, X], Result[E, X], Result[F, X]), f (A, B, C, D, E, F) -&gt; R) Result[R, List[X]]</code></dd>
<dt id="fn-map_err"><a href="ref/map_err.html"><code>map_err</code></a> <span class="tag">function</span></dt>
<dd>Changes the error inside an Err. <a href="spec.html#s15">Spec §15</a> <a href="ref/map_err.html">Full description</a><br><code class="sig">fn map_err[T, E, F](r Result[T, E], f (E) -&gt; F) Result[T, F]</code></dd>
<dt id="fn-map_ok"><a href="ref/map_ok.html"><code>map_ok</code></a> <span class="tag">function</span></dt>
<dd>Changes the value inside an Ok. <a href="spec.html#s15">Spec §15</a> <a href="ref/map_ok.html">Full description</a><br><code class="sig">fn map_ok[T, U, E](r Result[T, E], f (T) -&gt; U) Result[U, E]</code></dd>
<dt id="fn-max"><a href="ref/max.html"><code>max</code></a> <span class="tag">function</span></dt>
<dd>The larger of two values. <a href="spec.html#s5">Spec §5</a> <a href="ref/max.html">Full description</a><br><code class="sig">fn max[T Ordered](a T, b T) T
fn max[T Ordered](xs Seq[T]) Result[T, Error]</code></dd>
<dt id="fn-max_by"><a href="ref/max_by.html"><code>max_by</code></a> <span class="tag">function</span></dt>
<dd>The item with the largest key; an Err if empty. <a href="spec.html#s13">Spec §13</a> <a href="ref/max_by.html">Full description</a><br><code class="sig">fn max_by[T, K](f (T) -&gt; K, xs Seq[T]) Result[T, Error]</code></dd>
<dt id="fn-millis"><a href="ref/millis.html"><code>millis</code></a> <span class="tag">function</span></dt>
<dd>A Duration in milliseconds. <a href="spec.html#s19e">Spec §19e</a> <a href="ref/millis.html">Full description</a><br><code class="sig">fn millis(d Duration) Int</code></dd>
<dt id="fn-min"><a href="ref/min.html"><code>min</code></a> <span class="tag">function</span></dt>
<dd>The smaller of two values. <a href="spec.html#s5">Spec §5</a> <a href="ref/min.html">Full description</a><br><code class="sig">fn min[T Ordered](a T, b T) T
fn min[T Ordered](xs Seq[T]) Result[T, Error]</code></dd>
<dt id="fn-min_by"><a href="ref/min_by.html"><code>min_by</code></a> <span class="tag">function</span></dt>
<dd>The item with the smallest key; an Err if empty. <a href="spec.html#s13">Spec §13</a> <a href="ref/min_by.html">Full description</a><br><code class="sig">fn min_by[T, K](f (T) -&gt; K, xs Seq[T]) Result[T, Error]</code></dd>
<dt id="fn-modify"><a href="ref/modify.html"><code>modify</code></a> <span class="tag">function</span></dt>
<dd>A copy with the value at a data path changed by a function. <a href="spec.html#s7">Spec §7</a> <a href="ref/modify.html">Full description</a><br><code class="sig">fn modify[T, P, A](x T, path P, f (A) -&gt; A) T</code></dd>
<dt id="fn-monotonic"><a href="ref/monotonic.html"><code>monotonic</code></a> <span class="tag">function</span></dt>
<dd>A steadily increasing clock, for measuring. <a href="spec.html#s19e">Spec §19e</a> <a href="ref/monotonic.html">Full description</a><br><code class="sig">fn monotonic() Duration</code><br><span class="eff">Effect: uses the system</span></dd>
<dt id="kw-move"><code>move</code> <span class="tag">hard keyword</span></dt>
<dd>Passes a resource to a new owner, so the old name can no longer use it. <a href="spec.html#s19">Spec §19</a></dd>
<dt id="ty-MultiArray"><code>MultiArray</code> <span class="tag">type</span></dt>
<dd>An array with more than one dimension.</dd>
<dt id="kw-mutable"><code>mutable</code> <span class="tag">soft keyword</span></dt>
<dd>Opens a block in which names may be updated in place and cannot leak out. <a href="spec.html#s3">Spec §3</a></dd>
</dl>

## N {#n}

<dl class="ref">
<dt id="fn-nanos"><a href="ref/nanos.html"><code>nanos</code></a> <span class="tag">function</span></dt>
<dd>A Duration in nanoseconds. <a href="spec.html#s19e">Spec §19e</a> <a href="ref/nanos.html">Full description</a><br><code class="sig">fn nanos(d Duration) Int</code></dd>
<dt id="fn-non_empty"><a href="ref/non_empty.html"><code>non_empty</code></a> <span class="tag">function</span></dt>
<dd>Ok of a NonEmpty from a List, or an Err if it is empty. <a href="spec.html#s15">Spec §15</a> <a href="ref/non_empty.html">Full description</a><br><code class="sig">fn non_empty[T](xs List[T]) Result[NonEmpty[T], Error]</code></dd>
<dt id="ty-NonEmpty"><code>NonEmpty</code> <span class="tag">type</span></dt>
<dd>A list with a first item guaranteed, as <code>head</code> and <code>tail</code>.</dd>
<dt id="kw-not"><code>not</code> <span class="tag">hard keyword</span></dt>
<dd>Reverses a Bool. <a href="spec.html#s10">Spec §10</a></dd>
<dt id="fn-now"><a href="ref/now.html"><code>now</code></a> <span class="tag">function</span></dt>
<dd>The current time as a Duration since the epoch. <a href="spec.html#s19e">Spec §19e</a> <a href="ref/now.html">Full description</a><br><code class="sig">fn now() Duration</code><br><span class="eff">Effect: uses the system</span></dd>
</dl>

## O {#o}

<dl class="ref">
<dt id="fn-ok"><a href="ref/ok.html"><code>ok</code></a> <span class="tag">function</span></dt>
<dd>Turns a Result into an Option, dropping the error. <a href="spec.html#s15">Spec §15</a> <a href="ref/ok.html">Full description</a><br><code class="sig">fn ok[T, E](r Result[T, E]) Option[T]</code></dd>
<dt id="fn-ok_or"><a href="ref/ok_or.html"><code>ok_or</code></a> <span class="tag">function</span></dt>
<dd>Turns an Option into a Result with a given error. <a href="spec.html#s15">Spec §15</a> <a href="ref/ok_or.html">Full description</a><br><code class="sig">fn ok_or[T](o Option[T], err Error) Result[T, Error]</code></dd>
<dt id="kw-opaque"><code>opaque</code> <span class="tag">soft keyword</span></dt>
<dd>Follows <code>type</code> to make a type whose inside is hidden from other packages. <a href="spec.html#s6">Spec §6</a></dd>
<dt id="ty-Option"><code>Option</code> <span class="tag">type</span></dt>
<dd>Some(value) or None: a value that may be absent.</dd>
<dt id="kw-or"><code>or</code> <span class="tag">hard keyword</span></dt>
<dd>True when either side is true; the right side is evaluated only if needed. <a href="spec.html#s10">Spec §10</a></dd>
<dt id="fn-or_else"><a href="ref/or_else.html"><code>or_else</code></a> <span class="tag">function</span></dt>
<dd>Tries a recovery function on an Err. <a href="spec.html#s15">Spec §15</a> <a href="ref/or_else.html">Full description</a><br><code class="sig">fn or_else[T, E, F](r Result[T, E], f (E) -&gt; Result[T, F]) Result[T, F]</code></dd>
<dt id="fn-os_name"><a href="ref/os_name.html"><code>os_name</code></a> <span class="tag">function</span></dt>
<dd>The operating system's name. <a href="spec.html#s19c">Spec §19c</a> <a href="ref/os_name.html">Full description</a><br><code class="sig">fn os_name() String</code><br><span class="eff">Effect: uses the system</span></dd>
</dl>

## P {#p}

<dl class="ref">
<dt id="fn-pad_left"><a href="ref/pad_left.html"><code>pad_left</code></a> <span class="tag">function</span></dt>
<dd>Pads on the left to a width. <a href="spec.html#s5">Spec §5</a> <a href="ref/pad_left.html">Full description</a><br><code class="sig">fn pad_left(s String, n Int) String
fn pad_left(s String, n Int, c String) String
fn pad_left(s String, n Int, c Char) String</code></dd>
<dt id="fn-pad_right"><a href="ref/pad_right.html"><code>pad_right</code></a> <span class="tag">function</span></dt>
<dd>Pads on the right to a width. <a href="spec.html#s5">Spec §5</a> <a href="ref/pad_right.html">Full description</a><br><code class="sig">fn pad_right(s String, n Int) String
fn pad_right(s String, n Int, c String) String
fn pad_right(s String, n Int, c Char) String</code></dd>
<dt id="fn-par_map"><a href="ref/par_map.html"><code>par_map</code></a> <span class="tag">function</span></dt>
<dd>Maps in parallel, at most <code>limit</code> at once, keeping order. <a href="spec.html#s17">Spec §17</a> <a href="ref/par_map.html">Full description</a><br><code class="sig">fn par_map[T, U](f (T) -&gt; U, xs Seq[T], limit: Int) List[U]</code><br><span class="eff">Effect: parks</span></dd>
<dt id="fn-par_map_all"><a href="ref/par_map_all.html"><code>par_map_all</code></a> <span class="tag">function</span></dt>
<dd>Like <code>map_all</code>, with slow checks run in parallel. <a href="spec.html#s15">Spec §15</a> <a href="ref/par_map_all.html">Full description</a><br><code class="sig">fn par_map_all[A, B, R, X](f (A, B) -&gt; R, c1 () -&gt; Result[A, X], c2 () -&gt; Result[B, X]) Result[R, List[X]]
fn par_map_all[A, B, C, R, X](f (A, B, C) -&gt; R, c1 () -&gt; Result[A, X], c2 () -&gt; Result[B, X], c3 () -&gt; Result[C, X]) Result[R, List[X]]
fn par_map_all[A, B, C, D, R, X](f (A, B, C, D) -&gt; R, c1 () -&gt; Result[A, X], c2 () -&gt; Result[B, X], c3 () -&gt; Result[C, X], c4 () -&gt; Result[D, X]) Result[R, List[X]]
fn par_map_all[A, B, C, D, E, R, X](f (A, B, C, D, E) -&gt; R, c1 () -&gt; Result[A, X], c2 () -&gt; Result[B, X], c3 () -&gt; Result[C, X], c4 () -&gt; Result[D, X], c5 () -&gt; Result[E, X]) Result[R, List[X]]
fn par_map_all[A, B, C, D, E, F, R, X](f (A, B, C, D, E, F) -&gt; R, c1 () -&gt; Result[A, X], c2 () -&gt; Result[B, X], c3 () -&gt; Result[C, X], c4 () -&gt; Result[D, X], c5 () -&gt; Result[E, X], c6 () -&gt; Result[F, X]) Result[R, List[X]]</code><br><span class="eff">Effect: parks</span></dd>
<dt id="fn-par_traverse"><a href="ref/par_traverse.html"><code>par_traverse</code></a> <span class="tag">function</span></dt>
<dd>Like <code>par_map</code> for Result-returning functions. <a href="spec.html#s17">Spec §17</a> <a href="ref/par_traverse.html">Full description</a><br><code class="sig">fn par_traverse[T, U, E](f (T) -&gt; Result[U, E], xs Seq[T], limit: Int) Result[List[U], E]</code><br><span class="eff">Effect: parks</span></dd>
<dt id="kw-parks"><code>parks</code> <span class="tag">soft keyword</span></dt>
<dd>Function modifier: the function may wait, for example on a channel or the network. <a href="spec.html#s14">Spec §14</a></dd>
<dt id="fn-parse_iso"><a href="ref/parse_iso.html"><code>parse_iso</code></a> <span class="tag">function</span></dt>
<dd>Reads ISO 8601 text. <a href="spec.html#s19e">Spec §19e</a> <a href="ref/parse_iso.html">Full description</a><br><code class="sig">fn parse_iso(s String) Result[DateTime, Error]</code></dd>
<dt id="fn-parse_number"><a href="ref/parse_number.html"><code>parse_number</code></a> <span class="tag">function</span></dt>
<dd>Reads a number from text, optionally in a locale's format; an Err if it isn't one. <a href="spec.html#s5">Spec §5</a> <a href="ref/parse_number.html">Full description</a><br><code class="sig">fn parse_number[N](s String) Result[N, Error]
fn parse_number[N](s String, locale Locale) Result[N, Error]</code></dd>
<dt id="fn-parse_time"><a href="ref/parse_time.html"><code>parse_time</code></a> <span class="tag">function</span></dt>
<dd>Reads text with a pattern. <a href="spec.html#s19e">Spec §19e</a> <a href="ref/parse_time.html">Full description</a><br><code class="sig">fn parse_time(s String, fmt String) Result[DateTime, Error]
fn parse_time(s String, fmt String, loc Locale) Result[DateTime, Error]</code></dd>
<dt id="fn-partition"><a href="ref/partition.html"><code>partition</code></a> <span class="tag">function</span></dt>
<dd>Splits the items into those that pass a test and those that don't. <a href="spec.html#s13">Spec §13</a> <a href="ref/partition.html">Full description</a><br><code class="sig">fn partition[T](f (T) -&gt; Bool, xs Seq[T]) (List[T], List[T])</code></dd>
<dt id="fn-partition_results"><a href="ref/partition_results.html"><code>partition_results</code></a> <span class="tag">function</span></dt>
<dd>Splits Results into the values and the errors. <a href="spec.html#s15">Spec §15</a> <a href="ref/partition_results.html">Full description</a><br><code class="sig">fn partition_results[T, E](rs Seq[Result[T, E]]) (List[T], List[E])</code></dd>
<dt id="fn-path_exists"><a href="ref/path_exists.html"><code>path_exists</code></a> <span class="tag">function</span></dt>
<dd>Ok(true) or Ok(false). <a href="spec.html#s19c">Spec §19c</a> <a href="ref/path_exists.html">Full description</a><br><code class="sig">fn path_exists(p String) Result[Bool, Error]</code><br><span class="eff">Effect: parks · Needs permission: fs</span></dd>
<dt id="fn-path_ext"><a href="ref/path_ext.html"><code>path_ext</code></a> <span class="tag">function</span></dt>
<dd>The file name's extension. <a href="spec.html#s19c">Spec §19c</a> <a href="ref/path_ext.html">Full description</a><br><code class="sig">fn path_ext(p String) String</code></dd>
<dt id="fn-path_join"><a href="ref/path_join.html"><code>path_join</code></a> <span class="tag">function</span></dt>
<dd>Joins path pieces. <a href="spec.html#s19c">Spec §19c</a> <a href="ref/path_join.html">Full description</a><br><code class="sig">fn path_join(base String, rest String) String</code></dd>
<dt id="fn-path_name"><a href="ref/path_name.html"><code>path_name</code></a> <span class="tag">function</span></dt>
<dd>The last piece of a path. <a href="spec.html#s19c">Spec §19c</a> <a href="ref/path_name.html">Full description</a><br><code class="sig">fn path_name(p String) String</code></dd>
<dt id="fn-path_parent"><a href="ref/path_parent.html"><code>path_parent</code></a> <span class="tag">function</span></dt>
<dd>A path without its last piece. <a href="spec.html#s19c">Spec §19c</a> <a href="ref/path_parent.html">Full description</a><br><code class="sig">fn path_parent(p String) String</code></dd>
<dt id="fn-path_stem"><a href="ref/path_stem.html"><code>path_stem</code></a> <span class="tag">function</span></dt>
<dd>The file name without its extension. <a href="spec.html#s19c">Spec §19c</a> <a href="ref/path_stem.html">Full description</a><br><code class="sig">fn path_stem(p String) String</code></dd>
<dt id="fn-port_of"><a href="ref/port_of.html"><code>port_of</code></a> <span class="tag">function</span></dt>
<dd>The port a listener or socket uses. <a href="spec.html#s19c">Spec §19c</a> <a href="ref/port_of.html">Full description</a><br><code class="sig">fn port_of(l Listener) Int
fn port_of(u Udp) Int</code></dd>
<dt id="fn-position"><a href="ref/position.html"><code>position</code></a> <span class="tag">function</span></dt>
<dd>The position of the first item that passes a test; an Err if none does. <a href="spec.html#s13">Spec §13</a> <a href="ref/position.html">Full description</a><br><code class="sig">fn position[T](f (T) -&gt; Bool, xs Seq[T]) Result[Int, Error]</code></dd>
<dt id="fn-pow"><a href="ref/pow.html"><code>pow</code></a> <span class="tag">function</span></dt>
<dd>A number raised to a power. <a href="spec.html#s5">Spec §5</a> <a href="ref/pow.html">Full description</a><br><code class="sig">fn pow(a Int, b Int) Int
fn pow(a Double, b Double) Double</code></dd>
<dt id="fn-print"><a href="ref/print.html"><code>print</code></a> <span class="tag">function</span></dt>
<dd>Prints a value. <a href="spec.html#s19b">Spec §19b</a> <a href="ref/print.html">Full description</a><br><code class="sig">fn print[T](x T) Unit
fn print[T](out Io, x T) Unit</code><br><span class="eff">Effect: prints</span></dd>
<dt id="fn-println"><a href="ref/println.html"><code>println</code></a> <span class="tag">function</span></dt>
<dd>Prints a value and a newline. <a href="spec.html#s19b">Spec §19b</a> <a href="ref/println.html">Full description</a><br><code class="sig">fn println() Unit
fn println[T](x T) Unit
fn println[T](out Io, x T) Unit</code><br><span class="eff">Effect: prints</span></dd>
<dt id="kw-prints"><code>prints</code> <span class="tag">soft keyword</span></dt>
<dd>Function modifier: the function may print, and nothing else. <a href="spec.html#s14">Spec §14</a></dd>
<dt id="fn-product"><a href="ref/product.html"><code>product</code></a> <span class="tag">function</span></dt>
<dd>Multiplies the items. <a href="spec.html#s13">Spec §13</a> <a href="ref/product.html">Full description</a><br><code class="sig">fn product[T](xs Seq[T]) T</code></dd>
<dt id="kw-proxy"><code>proxy</code> <span class="tag">soft keyword</span></dt>
<dd>After the target of an <code>impl ... for</code>, forwards the impl to a field: <code>proxy(field)</code>. <a href="spec.html#s12">Spec §12</a></dd>
<dt id="kw-pure"><code>pure</code> <span class="tag">soft keyword</span></dt>
<dd>Function modifier: the function has no effects. <a href="spec.html#s14">Spec §14</a></dd>
</dl>

## R {#r}

<dl class="ref">
<dt id="fn-race"><a href="ref/race.html"><code>race</code></a> <span class="tag">function</span></dt>
<dd>Runs two functions; gives the first result and cancels the other. <a href="spec.html#s17">Spec §17</a> <a href="ref/race.html">Full description</a><br><code class="sig">fn race[T](f (Cancel) -&gt; T, g (Cancel) -&gt; T) T</code><br><span class="eff">Effect: parks</span></dd>
<dt id="fn-random"><a href="ref/random.html"><code>random</code></a> <span class="tag">function</span></dt>
<dd>A Double in [0, 1). <a href="spec.html#s5">Spec §5</a> <a href="ref/random.html">Full description</a><br><code class="sig">fn random() Double</code><br><span class="eff">Effect: uses the system</span></dd>
<dt id="fn-random_bytes"><a href="ref/random_bytes.html"><code>random_bytes</code></a> <span class="tag">function</span></dt>
<dd>n random bytes. <a href="spec.html#s5">Spec §5</a> <a href="ref/random_bytes.html">Full description</a><br><code class="sig">fn random_bytes(n Int) Array[Byte]</code><br><span class="eff">Effect: uses the system</span></dd>
<dt id="fn-random_int"><a href="ref/random_int.html"><code>random_int</code></a> <span class="tag">function</span></dt>
<dd>An Int drawn uniformly from a range. <a href="spec.html#s5">Spec §5</a> <a href="ref/random_int.html">Full description</a><br><code class="sig">fn random_int(r Range) Int</code><br><span class="eff">Effect: uses the system</span></dd>
<dt id="ty-Range"><code>Range</code> <span class="tag">type</span></dt>
<dd>A run of integers or characters, <code>1..5</code> or <code>0..&lt;n</code>.</dd>
<dt id="fn-raw_terminal"><a href="ref/raw_terminal.html"><code>raw_terminal</code></a> <span class="tag">function</span></dt>
<dd>Puts the terminal in raw mode. <a href="spec.html#s19b">Spec §19b</a> <a href="ref/raw_terminal.html">Full description</a><br><code class="sig">fn raw_terminal() Result[Terminal, Error]</code><br><span class="eff">Effect: uses the system · Needs permission: stdin</span></dd>
<dt id="fn-read"><a href="ref/read.html"><code>read</code></a> <span class="tag">function</span></dt>
<dd>Reads the next value from a channel, or waits for a future. <a href="spec.html#s17">Spec §17</a> <a href="ref/read.html">Full description</a><br><code class="sig">fn read[T](c ChanR[T]) Result[T, Error]
fn read[T](f FutureR[T]) T</code><br><span class="eff">Effect: parks</span></dd>
<dt id="fn-read_all"><a href="ref/read_all.html"><code>read_all</code></a> <span class="tag">function</span></dt>
<dd>All the rest of the input. <a href="spec.html#s19b">Spec §19b</a> <a href="ref/read_all.html">Full description</a><br><code class="sig">fn read_all() Result[String, Error]
fn read_all(src Io) Result[String, Error]</code><br><span class="eff">Effect: parks · Needs permission: stdin</span></dd>
<dt id="fn-read_bytes"><a href="ref/read_bytes.html"><code>read_bytes</code></a> <span class="tag">function</span></dt>
<dd>Up to n bytes. <a href="spec.html#s19b">Spec §19b</a> <a href="ref/read_bytes.html">Full description</a><br><code class="sig">fn read_bytes(src Io, n Int) Result[Array[Byte], Error]</code><br><span class="eff">Effect: parks</span></dd>
<dt id="fn-read_file"><a href="ref/read_file.html"><code>read_file</code></a> <span class="tag">function</span></dt>
<dd>A file's text. <a href="spec.html#s19c">Spec §19c</a> <a href="ref/read_file.html">Full description</a><br><code class="sig">fn read_file(p String) Result[String, Error]</code><br><span class="eff">Effect: parks · Needs permission: fs</span></dd>
<dt id="fn-read_key"><a href="ref/read_key.html"><code>read_key</code></a> <span class="tag">function</span></dt>
<dd>The next key pressed. <a href="spec.html#s19b">Spec §19b</a> <a href="ref/read_key.html">Full description</a><br><code class="sig">fn read_key(t Terminal) Result[Key, Error]</code><br><span class="eff">Effect: parks</span></dd>
<dt id="fn-read_line"><a href="ref/read_line.html"><code>read_line</code></a> <span class="tag">function</span></dt>
<dd>The next line of input; an Err at the end. <a href="spec.html#s19b">Spec §19b</a> <a href="ref/read_line.html">Full description</a><br><code class="sig">fn read_line() Result[String, Error]
fn read_line(src Io) Result[String, Error]</code><br><span class="eff">Effect: parks · Needs permission: stdin</span></dd>
<dt id="fn-receive"><a href="ref/receive.html"><code>receive</code></a> <span class="tag">function</span></dt>
<dd>Waits for a UDP datagram. <a href="spec.html#s19c">Spec §19c</a> <a href="ref/receive.html">Full description</a><br><code class="sig">fn receive(u Udp) Result[Packet, Error]</code><br><span class="eff">Effect: parks</span></dd>
<dt id="fn-recover"><a href="ref/recover.html"><code>recover</code></a> <span class="tag">function</span></dt>
<dd>Turns an Err into a value with a function. <a href="spec.html#s15">Spec §15</a> <a href="ref/recover.html">Full description</a><br><code class="sig">fn recover[T, E](r Result[T, E], f (E) -&gt; T) Result[T, E]</code></dd>
<dt id="fn-reduce"><a href="ref/reduce.html"><code>reduce</code></a> <span class="tag">function</span></dt>
<dd>Folds the items into one value, from a start value and a combining function. <a href="spec.html#s13">Spec §13</a> <a href="ref/reduce.html">Full description</a><br><code class="sig">fn reduce[T, A](init A, f (A, T) -&gt; A, xs Seq[T]) A</code></dd>
<dt id="fn-reduce_right"><a href="ref/reduce_right.html"><code>reduce_right</code></a> <span class="tag">function</span></dt>
<dd>Like <code>reduce</code>, folding from the end. <a href="spec.html#s13">Spec §13</a> <a href="ref/reduce_right.html">Full description</a><br><code class="sig">fn reduce_right[T, A](init A, f (T, A) -&gt; A, xs Seq[T]) A</code></dd>
<dt id="kw-ref"><code>ref</code> <span class="tag">hard keyword</span></dt>
<dd>Marks a parameter that the function may rebind; the final value is copied back to the caller's variable. <a href="spec.html#s9">Spec §9</a></dd>
<dt id="fn-reject"><a href="ref/reject.html"><code>reject</code></a> <span class="tag">function</span></dt>
<dd>Supplies a future's error. <a href="spec.html#s17">Spec §17</a> <a href="ref/reject.html">Full description</a><br><code class="sig">fn reject[T](w FutureW[T], e Error) Unit</code><br><span class="eff">Effect: uses a resource</span></dd>
<dt id="fn-remove"><a href="ref/remove.html"><code>remove</code></a> <span class="tag">function</span></dt>
<dd>A copy without a key or item. <a href="spec.html#s7">Spec §7</a> <a href="ref/remove.html">Full description</a><br><code class="sig">fn remove[K, V](d Dict[K, V], k K) Dict[K, V]
fn remove[T](s Set[T], x T) Set[T]
fn remove[T](xs List[T], x T) List[T]
fn remove[T](xs Array[T], x T) Array[T]</code></dd>
<dt id="fn-remove_at"><a href="ref/remove_at.html"><code>remove_at</code></a> <span class="tag">function</span></dt>
<dd>A copy without the item at a position. <a href="spec.html#s7">Spec §7</a> <a href="ref/remove_at.html">Full description</a><br><code class="sig">fn remove_at[T](xs List[T], i Int) List[T]
fn remove_at[T](xs Array[T], i Int) Array[T]</code></dd>
<dt id="fn-remove_dir"><a href="ref/remove_dir.html"><code>remove_dir</code></a> <span class="tag">function</span></dt>
<dd>Deletes a directory. <a href="spec.html#s19c">Spec §19c</a> <a href="ref/remove_dir.html">Full description</a><br><code class="sig">fn remove_dir(p String) Result[Unit, Error]</code><br><span class="eff">Effect: parks · Needs permission: fs</span></dd>
<dt id="fn-remove_file"><a href="ref/remove_file.html"><code>remove_file</code></a> <span class="tag">function</span></dt>
<dd>Deletes a file. <a href="spec.html#s19c">Spec §19c</a> <a href="ref/remove_file.html">Full description</a><br><code class="sig">fn remove_file(p String) Result[Unit, Error]</code><br><span class="eff">Effect: parks · Needs permission: fs</span></dd>
<dt id="fn-rename_path"><a href="ref/rename_path.html"><code>rename_path</code></a> <span class="tag">function</span></dt>
<dd>Renames a file or directory. <a href="spec.html#s19c">Spec §19c</a> <a href="ref/rename_path.html">Full description</a><br><code class="sig">fn rename_path(a String, b String) Result[Unit, Error]</code><br><span class="eff">Effect: parks · Needs permission: fs</span></dd>
<dt id="fn-repeat"><a href="ref/repeat.html"><code>repeat</code></a> <span class="tag">function</span></dt>
<dd>One value, forever. <a href="spec.html#s13">Spec §13</a> <a href="ref/repeat.html">Full description</a><br><code class="sig">fn repeat[T](x T) Stream[T]</code></dd>
<dt id="fn-replace"><a href="ref/replace.html"><code>replace</code></a> <span class="tag">function</span></dt>
<dd>A copy with the value at a data path replaced. <a href="spec.html#s7">Spec §7</a> <a href="ref/replace.html">Full description</a><br><code class="sig">fn replace[T, P, V](x T, path P, v V) T</code></dd>
<dt id="fn-replace_text"><a href="ref/replace_text.html"><code>replace_text</code></a> <span class="tag">function</span></dt>
<dd>Replaces every occurrence of one piece of text with another. <a href="spec.html#s5">Spec §5</a> <a href="ref/replace_text.html">Full description</a><br><code class="sig">fn replace_text(s String, from String, to String) String</code></dd>
<dt id="fn-reset"><a href="ref/reset.html"><code>reset</code></a> <span class="tag">function</span></dt>
<dd>Sets an Atom's value. <a href="spec.html#s17">Spec §17</a> <a href="ref/reset.html">Full description</a><br><code class="sig">fn reset[T](a Atom[T], v T) T</code><br><span class="eff">Effect: uses a resource</span></dd>
<dt id="fn-reset_vals"><a href="ref/reset_vals.html"><code>reset_vals</code></a> <span class="tag">function</span></dt>
<dd>Like <code>reset</code>, giving (old, new). <a href="spec.html#s17">Spec §17</a> <a href="ref/reset_vals.html">Full description</a><br><code class="sig">fn reset_vals[T](a Atom[T], v T) (T, T)</code><br><span class="eff">Effect: uses a resource</span></dd>
<dt id="fn-resolve"><a href="ref/resolve.html"><code>resolve</code></a> <span class="tag">function</span></dt>
<dd>Supplies a future's value. <a href="spec.html#s17">Spec §17</a> <a href="ref/resolve.html">Full description</a><br><code class="sig">fn resolve[T](w FutureW[T], v T) Unit</code><br><span class="eff">Effect: uses a resource</span></dd>
<dt id="ty-Result"><code>Result</code> <span class="tag">type</span></dt>
<dd>Ok(value) or Err(error): the outcome of something that can fail.</dd>
<dt id="fn-retry"><a href="ref/retry.html"><code>retry</code></a> <span class="tag">function</span></dt>
<dd>Calls a function up to n times, waiting between tries. <a href="spec.html#s17">Spec §17</a> <a href="ref/retry.html">Full description</a><br><code class="sig">fn retry[T](n Int, delay Duration, f () -&gt; Result[T, Error]) Result[T, Error]</code><br><span class="eff">Effect: parks</span></dd>
<dt id="kw-return"><code>return</code> <span class="tag">hard keyword</span></dt>
<dd>Leaves the function early with a value. <a href="spec.html#s9">Spec §9</a></dd>
<dt id="fn-reverse"><a href="ref/reverse.html"><code>reverse</code></a> <span class="tag">function</span></dt>
<dd>The items in the opposite order. <a href="spec.html#s13">Spec §13</a> <a href="ref/reverse.html">Full description</a><br><code class="sig">fn reverse[T](xs Seq[T]) Stream[T]</code></dd>
<dt id="ty-Ring"><code>Ring</code> <span class="tag">type</span></dt>
<dd>A fixed-capacity buffer that overwrites its oldest item when full.</dd>
<dt id="fn-round"><a href="ref/round.html"><code>round</code></a> <span class="tag">function</span></dt>
<dd>Rounds to the nearest Int. <a href="spec.html#s5">Spec §5</a> <a href="ref/round.html">Full description</a><br><code class="sig">fn round(x Double) Int</code></dd>
<dt id="fn-round_to"><a href="ref/round_to.html"><code>round_to</code></a> <span class="tag">function</span></dt>
<dd>Rounds a Decimal to a scale of n places, as in <code>round_to[2](x, #half_even)</code>; a <code>Mode</code> is <code>#half_even</code>, <code>#half_up</code> or <code>#down</code>. <a href="spec.html#s5">Spec §5</a> <a href="ref/round_to.html">Full description</a><br><code class="sig">fn round_to[n](x Decimal, mode Mode) Decimal</code></dd>
<dt id="fn-run_command"><a href="ref/run_command.html"><code>run_command</code></a> <span class="tag">function</span></dt>
<dd>Runs another program to the end and gives its output. <a href="spec.html#s19c">Spec §19c</a> <a href="ref/run_command.html">Full description</a><br><code class="sig">fn run_command(program String) Result[Output, Error]
fn run_command(program String, args List[String]) Result[Output, Error]</code><br><span class="eff">Effect: parks · Needs permission: process</span></dd>
</dl>

## S {#s}

<dl class="ref">
<dt id="fn-saturating_add"><a href="ref/saturating_add.html"><code>saturating_add</code></a> <span class="tag">function</span></dt>
<dd>Addition that stops at the largest or smallest value. <a href="spec.html#s5">Spec §5</a> <a href="ref/saturating_add.html">Full description</a><br><code class="sig">fn saturating_add[T](a T, b T) T</code></dd>
<dt id="fn-saturating_mul"><a href="ref/saturating_mul.html"><code>saturating_mul</code></a> <span class="tag">function</span></dt>
<dd>Multiplication that stops at the largest or smallest value. <a href="spec.html#s5">Spec §5</a> <a href="ref/saturating_mul.html">Full description</a><br><code class="sig">fn saturating_mul[T](a T, b T) T</code></dd>
<dt id="fn-saturating_sub"><a href="ref/saturating_sub.html"><code>saturating_sub</code></a> <span class="tag">function</span></dt>
<dd>Subtraction that stops at the largest or smallest value. <a href="spec.html#s5">Spec §5</a> <a href="ref/saturating_sub.html">Full description</a><br><code class="sig">fn saturating_sub[T](a T, b T) T</code></dd>
<dt id="fn-scan"><a href="ref/scan.html"><code>scan</code></a> <span class="tag">function</span></dt>
<dd>Like <code>reduce</code>, but gives every running value. <a href="spec.html#s13">Spec §13</a> <a href="ref/scan.html">Full description</a><br><code class="sig">fn scan[T, A](init A, f (A, T) -&gt; A, xs Seq[T]) Stream[A]</code></dd>
<dt id="fn-seconds"><a href="ref/seconds.html"><code>seconds</code></a> <span class="tag">function</span></dt>
<dd>A Duration in seconds. <a href="spec.html#s19e">Spec §19e</a> <a href="ref/seconds.html">Full description</a><br><code class="sig">fn seconds(d Duration) Double</code></dd>
<dt id="ty-Secret"><code>Secret</code> <span class="tag">type</span></dt>
<dd>A value that cannot be printed or compared with <code>==</code>.</dd>
<dt id="fn-secret_eq"><a href="ref/secret_eq.html"><code>secret_eq</code></a> <span class="tag">function</span></dt>
<dd>Compares two secrets in constant time. <a href="spec.html#s23">Spec §23</a> <a href="ref/secret_eq.html">Full description</a><br><code class="sig">fn secret_eq[T](a Secret[T], b Secret[T]) Bool</code></dd>
<dt id="kw-select"><code>select</code> <span class="tag">hard keyword</span></dt>
<dd>Waits on several channel, timer or future operations and runs the arm for the first that is ready. <a href="spec.html#s17">Spec §17</a></dd>
<dt id="kw-Self"><code>Self</code> <span class="tag">hard keyword</span></dt>
<dd>Inside an interface or impl, the type being described. <a href="spec.html#s12">Spec §12</a></dd>
<dt id="kw-self"><code>self</code> <span class="tag">hard keyword</span></dt>
<dd>The receiver value inside a method. <a href="spec.html#s12">Spec §12</a></dd>
<dt id="fn-send_to"><a href="ref/send_to.html"><code>send_to</code></a> <span class="tag">function</span></dt>
<dd>Sends one UDP datagram. <a href="spec.html#s19c">Spec §19c</a> <a href="ref/send_to.html">Full description</a><br><code class="sig">fn send_to(u Udp, host String, port Int, data String) Result[Unit, Error]
fn send_to(u Udp, host String, port Int, data Array[Byte]) Result[Unit, Error]</code><br><span class="eff">Effect: parks · Needs permission: net</span></dd>
<dt id="kw-seq"><code>seq</code> <span class="tag">soft keyword</span></dt>
<dd>After <code>|&gt;</code>, begins a stream pipeline written one stage per line. <a href="spec.html#s13">Spec §13</a></dd>
<dt id="ty-Seq"><code>Seq</code> <span class="tag">type</span></dt>
<dd>In a signature, any source of values: a List, Array, Set, Ring or Stream.</dd>
<dt id="fn-sequence"><a href="ref/sequence.html"><code>sequence</code></a> <span class="tag">function</span></dt>
<dd>Turns Results into one Result of a List; stops at the first Err. <a href="spec.html#s15">Spec §15</a> <a href="ref/sequence.html">Full description</a><br><code class="sig">fn sequence[T, E](rs Seq[Result[T, E]]) Result[List[T], E]</code></dd>
<dt id="ty-Set"><code>Set</code> <span class="tag">type</span></dt>
<dd>A collection of distinct values.</dd>
<dt id="fn-set"><a href="ref/set.html"><code>set</code></a> <span class="tag">function</span></dt>
<dd>A copy with the item at a position or key replaced. <a href="spec.html#s7">Spec §7</a> <a href="ref/set.html">Full description</a><br><code class="sig">fn set[T](xs List[T], i Int, x T) List[T]
fn set[T](xs Array[T], i Int, x T) Array[T]
fn set[T](xs MultiArray[T], i Int, x T) MultiArray[T]
fn set[K, V](d Dict[K, V], k K, v V) Dict[K, V]</code></dd>
<dt id="fn-shl"><a href="ref/shl.html"><code>shl</code></a> <span class="tag">function</span></dt>
<dd>Shifts bits left. <a href="spec.html#s5">Spec §5</a> <a href="ref/shl.html">Full description</a><br><code class="sig">fn shl[T](a T, n Int) T</code></dd>
<dt id="fn-show"><a href="ref/show.html"><code>show</code></a> <span class="tag">function</span></dt>
<dd>The printed form of a value, as a String. <a href="spec.html#s5">Spec §5</a> <a href="ref/show.html">Full description</a><br><code class="sig">fn show[T](x T) String</code></dd>
<dt id="fn-shr"><a href="ref/shr.html"><code>shr</code></a> <span class="tag">function</span></dt>
<dd>Shifts bits right. <a href="spec.html#s5">Spec §5</a> <a href="ref/shr.html">Full description</a><br><code class="sig">fn shr[T](a T, n Int) T</code></dd>
<dt id="fn-sleep"><a href="ref/sleep.html"><code>sleep</code></a> <span class="tag">function</span></dt>
<dd>Waits for a duration. <a href="spec.html#s17">Spec §17</a> <a href="ref/sleep.html">Full description</a><br><code class="sig">fn sleep(d Duration) Unit</code><br><span class="eff">Effect: parks</span></dd>
<dt id="fn-sort"><a href="ref/sort.html"><code>sort</code></a> <span class="tag">function</span></dt>
<dd>Orders the items by <code>&lt;</code>, keeping equal items in their order. <a href="spec.html#s13">Spec §13</a> <a href="ref/sort.html">Full description</a><br><code class="sig">fn sort[T Ordered](xs Seq[T]) Stream[T]</code></dd>
<dt id="fn-sort_by"><a href="ref/sort_by.html"><code>sort_by</code></a> <span class="tag">function</span></dt>
<dd>Orders the items by a key function. <a href="spec.html#s13">Spec §13</a> <a href="ref/sort_by.html">Full description</a><br><code class="sig">fn sort_by[T, K](f (T) -&gt; K, xs Seq[T]) Stream[T]</code></dd>
<dt id="fn-span"><a href="ref/span.html"><code>span</code></a> <span class="tag">function</span></dt>
<dd>Splits at the first item that fails a test. <a href="spec.html#s13">Spec §13</a> <a href="ref/span.html">Full description</a><br><code class="sig">fn span[T](f (T) -&gt; Bool, xs Seq[T]) (List[T], List[T])</code></dd>
<dt id="fn-spawn"><a href="ref/spawn.html"><code>spawn</code></a> <span class="tag">function</span></dt>
<dd>Starts another program. <a href="spec.html#s19c">Spec §19c</a> <a href="ref/spawn.html">Full description</a><br><code class="sig">fn spawn(program String) Result[Child, Error]
fn spawn(program String, args List[String]) Result[Child, Error]</code><br><span class="eff">Effect: parks · Needs permission: process</span></dd>
<dt id="fn-split"><a href="ref/split.html"><code>split</code></a> <span class="tag">function</span></dt>
<dd>Cuts a String at every separator. <a href="spec.html#s5">Spec §5</a> <a href="ref/split.html">Full description</a><br><code class="sig">fn split(s String, sep String) List[String]</code></dd>
<dt id="fn-split_at"><a href="ref/split_at.html"><code>split_at</code></a> <span class="tag">function</span></dt>
<dd>Splits after the first n items. <a href="spec.html#s13">Spec §13</a> <a href="ref/split_at.html">Full description</a><br><code class="sig">fn split_at[T](n Int, xs Seq[T]) (List[T], List[T])</code></dd>
<dt id="fn-split_once"><a href="ref/split_once.html"><code>split_once</code></a> <span class="tag">function</span></dt>
<dd>Cuts at the first separator; None if there is none. <a href="spec.html#s5">Spec §5</a> <a href="ref/split_once.html">Full description</a><br><code class="sig">fn split_once(s String, sep String) Option[(String, String)]</code></dd>
<dt id="fn-sqrt"><a href="ref/sqrt.html"><code>sqrt</code></a> <span class="tag">function</span></dt>
<dd>Square root. <a href="spec.html#s5">Spec §5</a> <a href="ref/sqrt.html">Full description</a><br><code class="sig">fn sqrt(x Double) Double</code></dd>
<dt id="fn-starts_with"><a href="ref/starts_with.html"><code>starts_with</code></a> <span class="tag">function</span></dt>
<dd>True if the text begins with a prefix. <a href="spec.html#s5">Spec §5</a> <a href="ref/starts_with.html">Full description</a><br><code class="sig">fn starts_with(s String, prefix String) Bool
fn starts_with(s String, c Char) Bool</code></dd>
<dt id="kw-static"><code>static</code> <span class="tag">hard keyword</span></dt>
<dd>Marks a function that belongs to a type and has no <code>self</code>, as in <code>static fn read(text String)</code>. <a href="spec.html#s12">Spec §12</a></dd>
<dt id="fn-stdin_lines"><a href="ref/stdin_lines.html"><code>stdin_lines</code></a> <span class="tag">function</span></dt>
<dd>The lines of standard input, as a stream. <a href="spec.html#s19b">Spec §19b</a> <a href="ref/stdin_lines.html">Full description</a><br><code class="sig">fn stdin_lines() Stream[String]</code><br><span class="eff">Effect: parks · Needs permission: stdin</span></dd>
<dt id="kw-step"><code>step</code> <span class="tag">soft keyword</span></dt>
<dd>After a range, gives the stride: <code>0..10 step 5</code>. <a href="spec.html#s5">Spec §5</a></dd>
<dt id="ty-Stream"><code>Stream</code> <span class="tag">type</span></dt>
<dd>A lazy pipeline of values that runs when something consumes it.</dd>
<dt id="ty-String"><code>String</code> <span class="tag">type</span></dt>
<dd>Text, stored as UTF-8 and immutable.</dd>
<dt id="fn-strip_prefix"><a href="ref/strip_prefix.html"><code>strip_prefix</code></a> <span class="tag">function</span></dt>
<dd>The text without a prefix, or None if it doesn't start with it. <a href="spec.html#s5">Spec §5</a> <a href="ref/strip_prefix.html">Full description</a><br><code class="sig">fn strip_prefix(s String, prefix String) Option[String]</code></dd>
<dt id="fn-strip_suffix"><a href="ref/strip_suffix.html"><code>strip_suffix</code></a> <span class="tag">function</span></dt>
<dd>The text without a suffix, or None if it doesn't end with it. <a href="spec.html#s5">Spec §5</a> <a href="ref/strip_suffix.html">Full description</a><br><code class="sig">fn strip_suffix(s String, suffix String) Option[String]</code></dd>
<dt id="fn-sum"><a href="ref/sum.html"><code>sum</code></a> <span class="tag">function</span></dt>
<dd>Adds the items. <a href="spec.html#s13">Spec §13</a> <a href="ref/sum.html">Full description</a><br><code class="sig">fn sum[T](xs Seq[T]) T</code></dd>
<dt id="fn-swap"><a href="ref/swap.html"><code>swap</code></a> <span class="tag">function</span></dt>
<dd>Changes an Atom's value with a function and gives the new value. <a href="spec.html#s17">Spec §17</a> <a href="ref/swap.html">Full description</a><br><code class="sig">fn swap[T](a Atom[T], f (T) -&gt; T) T</code><br><span class="eff">Effect: uses a resource</span></dd>
<dt id="fn-swap_vals"><a href="ref/swap_vals.html"><code>swap_vals</code></a> <span class="tag">function</span></dt>
<dd>Like <code>swap</code>, giving (old, new). <a href="spec.html#s17">Spec §17</a> <a href="ref/swap_vals.html">Full description</a><br><code class="sig">fn swap_vals[T](a Atom[T], f (T) -&gt; T) (T, T)</code><br><span class="eff">Effect: uses a resource</span></dd>
</dl>

## T {#t}

<dl class="ref">
<dt id="kw-tailrec"><code>tailrec</code> <span class="tag">soft keyword</span></dt>
<dd>Function modifier: the function must call itself only in tail position, so it runs in constant stack. <a href="spec.html#s9">Spec §9</a></dd>
<dt id="fn-take"><a href="ref/take.html"><code>take</code></a> <span class="tag">function</span></dt>
<dd>The first n items. <a href="spec.html#s13">Spec §13</a> <a href="ref/take.html">Full description</a><br><code class="sig">fn take[T](n Int, xs Seq[T]) Stream[T]</code></dd>
<dt id="fn-take_last"><a href="ref/take_last.html"><code>take_last</code></a> <span class="tag">function</span></dt>
<dd>The last n items. <a href="spec.html#s13">Spec §13</a> <a href="ref/take_last.html">Full description</a><br><code class="sig">fn take_last[T](n Int, xs Seq[T]) Stream[T]</code></dd>
<dt id="fn-take_while"><a href="ref/take_while.html"><code>take_while</code></a> <span class="tag">function</span></dt>
<dd>Items from the start while a test holds. <a href="spec.html#s13">Spec §13</a> <a href="ref/take_while.html">Full description</a><br><code class="sig">fn take_while[T](f (T) -&gt; Bool, xs Seq[T]) Stream[T]</code></dd>
<dt id="fn-tap"><a href="ref/tap.html"><code>tap</code></a> <span class="tag">function</span></dt>
<dd>Calls a function on a value for its effect and gives the value back. <a href="spec.html#s23">Spec §23</a> <a href="ref/tap.html">Full description</a><br><code class="sig">fn tap[T, U](x T, f (T) -&gt; U) T</code></dd>
<dt id="fn-temp_dir"><a href="ref/temp_dir.html"><code>temp_dir</code></a> <span class="tag">function</span></dt>
<dd>The temporary directory. <a href="spec.html#s19c">Spec §19c</a> <a href="ref/temp_dir.html">Full description</a><br><code class="sig">fn temp_dir() String</code><br><span class="eff">Effect: uses the system</span></dd>
<dt id="kw-test"><code>test</code> <span class="tag">soft keyword</span></dt>
<dd>At the start of a statement, before a string, declares a test block. <a href="spec.html#s22">Spec §22</a></dd>
<dt id="ty-Timer"><code>Timer</code> <span class="tag">type</span></dt>
<dd>A resource that fires once or repeatedly after a duration.</dd>
<dt id="fn-to_instant"><a href="ref/to_instant.html"><code>to_instant</code></a> <span class="tag">function</span></dt>
<dd>A DateTime as a Duration since the epoch. <a href="spec.html#s19e">Spec §19e</a> <a href="ref/to_instant.html">Full description</a><br><code class="sig">fn to_instant(t DateTime) Result[Duration, Error]
fn to_instant(t DateTime, zone String) Result[Duration, Error]</code></dd>
<dt id="fn-to_local"><a href="ref/to_local.html"><code>to_local</code></a> <span class="tag">function</span></dt>
<dd>A Duration as a DateTime in the system's zone. <a href="spec.html#s19e">Spec §19e</a> <a href="ref/to_local.html">Full description</a><br><code class="sig">fn to_local(d Duration) DateTime</code><br><span class="eff">Effect: uses the system</span></dd>
<dt id="fn-to_stream"><a href="ref/to_stream.html"><code>to_stream</code></a> <span class="tag">function</span></dt>
<dd>Treats any collection as a stream. <a href="spec.html#s13">Spec §13</a> <a href="ref/to_stream.html">Full description</a><br><code class="sig">fn to_stream[T](xs Seq[T]) Stream[T]</code></dd>
<dt id="fn-to_utc"><a href="ref/to_utc.html"><code>to_utc</code></a> <span class="tag">function</span></dt>
<dd>A Duration as a UTC DateTime. <a href="spec.html#s19e">Spec §19e</a> <a href="ref/to_utc.html">Full description</a><br><code class="sig">fn to_utc(d Duration) DateTime</code></dd>
<dt id="fn-to_zone"><a href="ref/to_zone.html"><code>to_zone</code></a> <span class="tag">function</span></dt>
<dd>A Duration as a DateTime in a named zone. <a href="spec.html#s19e">Spec §19e</a> <a href="ref/to_zone.html">Full description</a><br><code class="sig">fn to_zone(d Duration, zone String) Result[DateTime, Error]</code></dd>
<dt id="kw-todo"><code>todo</code> <span class="tag">hard keyword</span></dt>
<dd>Stands for an expression of whatever type is expected, with an optional message; aborts if it runs. <a href="spec.html#s2">Spec §2</a></dd>
<dt id="fn-trace"><a href="ref/trace.html"><code>trace</code></a> <span class="tag">function</span></dt>
<dd>Prints a message with its place. <a href="spec.html#s22">Spec §22</a> <a href="ref/trace.html">Full description</a><br><code class="sig">fn trace[T](x T) Unit</code><br><span class="eff">Effect: prints, but is allowed in any code</span></dd>
<dt id="fn-transpose"><a href="ref/transpose.html"><code>transpose</code></a> <span class="tag">function</span></dt>
<dd>Turns rows into columns. <a href="spec.html#s13">Spec §13</a> <a href="ref/transpose.html">Full description</a><br><code class="sig">fn transpose[T](rows Seq[Seq[T]]) List[List[T]]</code></dd>
<dt id="fn-traverse"><a href="ref/traverse.html"><code>traverse</code></a> <span class="tag">function</span></dt>
<dd>Applies a Result-returning function to each item; stops at the first Err. <a href="spec.html#s15">Spec §15</a> <a href="ref/traverse.html">Full description</a><br><code class="sig">fn traverse[T, U](f (T) -&gt; Result[U, Error], xs Seq[T]) Result[List[U], Error]</code></dd>
<dt id="fn-trim"><a href="ref/trim.html"><code>trim</code></a> <span class="tag">function</span></dt>
<dd>Removes spaces from both ends. <a href="spec.html#s5">Spec §5</a> <a href="ref/trim.html">Full description</a><br><code class="sig">fn trim(s String) String</code></dd>
<dt id="kw-true"><code>true</code> <span class="tag">hard keyword</span></dt>
<dd>The Bool value true. <a href="spec.html#s5">Spec §5</a></dd>
<dt id="fn-try_cast"><a href="ref/try_cast.html"><code>try_cast</code></a> <span class="tag">function</span></dt>
<dd>Like <code>cast</code>, but gives an Err (OUT_OF_RANGE) when the value does not fit. <a href="spec.html#s5">Spec §5</a> <a href="ref/try_cast.html">Full description</a><br><code class="sig">fn try_cast[T Numeric, N Numeric](x N) Result[T, Error]</code></dd>
<dt id="fn-try_fmt"><a href="ref/try_fmt.html"><code>try_fmt</code></a> <span class="tag">function</span></dt>
<dd>Like <code>fmt</code>, but gives an Err for a bad template. <a href="spec.html#s5">Spec §5</a> <a href="ref/try_fmt.html">Full description</a><br><code class="sig">fn try_fmt(template String, args...) Result[String, Error]</code></dd>
<dt id="kw-try_go"><code>try_go</code> <span class="tag">hard keyword</span></dt>
<dd>Like <code>go</code>, but gives an Err (NO_SLOT) instead of waiting when the fiber function has no free slot. <a href="spec.html#s18">Spec §18</a></dd>
<dt id="fn-try_reset"><a href="ref/try_reset.html"><code>try_reset</code></a> <span class="tag">function</span></dt>
<dd>Like <code>reset</code>, with an Err instead of an abort. <a href="spec.html#s17">Spec §17</a> <a href="ref/try_reset.html">Full description</a><br><code class="sig">fn try_reset[T](a Atom[T], v T) Result[T, Error]</code><br><span class="eff">Effect: uses a resource</span></dd>
<dt id="fn-try_swap"><a href="ref/try_swap.html"><code>try_swap</code></a> <span class="tag">function</span></dt>
<dd>Like <code>swap</code>, with an Err instead of an abort. <a href="spec.html#s17">Spec §17</a> <a href="ref/try_swap.html">Full description</a><br><code class="sig">fn try_swap[T](a Atom[T], f (T) -&gt; T) Result[T, Error]</code><br><span class="eff">Effect: uses a resource</span></dd>
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
<dt id="fn-unwrap"><a href="ref/unwrap.html"><code>unwrap</code></a> <span class="tag">function</span></dt>
<dd>The value of an Ok; aborts on an Err. <a href="spec.html#s15">Spec §15</a> <a href="ref/unwrap.html">Full description</a><br><code class="sig">fn unwrap[T, E](r Result[T, E]) T</code></dd>
<dt id="fn-unzip"><a href="ref/unzip.html"><code>unzip</code></a> <span class="tag">function</span></dt>
<dd>Splits a source of pairs into two Lists. <a href="spec.html#s13">Spec §13</a> <a href="ref/unzip.html">Full description</a><br><code class="sig">fn unzip[A, B](xs Seq[(A, B)]) (List[A], List[B])</code></dd>
<dt id="kw-update"><code>update</code> <span class="tag">soft keyword</span></dt>
<dd>After <code>x.</code> and before <code>:</code>, builds a copy of <code>x</code> with some fields changed. <a href="spec.html#s6">Spec §6</a></dd>
<dt id="fn-upper"><a href="ref/upper.html"><code>upper</code></a> <span class="tag">function</span></dt>
<dd>Upper case. <a href="spec.html#s5">Spec §5</a> <a href="ref/upper.html">Full description</a><br><code class="sig">fn upper(s String) String
fn upper(c Char) Char</code></dd>
<dt id="kw-using"><code>using</code> <span class="tag">hard keyword</span></dt>
<dd>Puts a named value in scope for the code that follows, as in <code>using locale = Locale.de_de</code>. <a href="spec.html#s5">Spec §5</a></dd>
</dl>

## V {#v}

<dl class="ref">
<dt id="fn-validate"><a href="ref/validate.html"><code>validate</code></a> <span class="tag">function</span></dt>
<dd>Like <code>traverse</code>, but collects every error. <a href="spec.html#s15">Spec §15</a> <a href="ref/validate.html">Full description</a><br><code class="sig">fn validate[T, U](f (T) -&gt; Result[U, Error], xs Seq[T]) Result[List[U], List[Error]]</code></dd>
<dt id="fn-values"><a href="ref/values.html"><code>values</code></a> <span class="tag">function</span></dt>
<dd>The values of a Dict. <a href="spec.html#s7">Spec §7</a> <a href="ref/values.html">Full description</a><br><code class="sig">fn values[K, V](d Dict[K, V]) Stream[V]</code></dd>
</dl>

## W {#w}

<dl class="ref">
<dt id="kw-wait"><code>wait</code> <span class="tag">soft keyword</span></dt>
<dd>At the start of a statement, waits for the fibers started below it, or for a cancel token. <a href="spec.html#s18">Spec §18</a></dd>
<dt id="fn-wait_child"><a href="ref/wait_child.html"><code>wait_child</code></a> <span class="tag">function</span></dt>
<dd>Waits for it to end. <a href="spec.html#s19c">Spec §19c</a> <a href="ref/wait_child.html">Full description</a><br><code class="sig">fn wait_child(c Child) Result[Int, Error]</code><br><span class="eff">Effect: parks</span></dd>
<dt id="fn-weekday"><a href="ref/weekday.html"><code>weekday</code></a> <span class="tag">function</span></dt>
<dd>1 for Monday to 7 for Sunday. <a href="spec.html#s19e">Spec §19e</a> <a href="ref/weekday.html">Full description</a><br><code class="sig">fn weekday(t DateTime) Int</code></dd>
<dt id="kw-when"><code>when</code> <span class="tag">hard keyword</span></dt>
<dd>Matches a value against patterns, one arm per pattern, and checks that every case is covered. <a href="spec.html#s8">Spec §8</a></dd>
<dt id="kw-where"><code>where</code> <span class="tag">soft keyword</span></dt>
<dd>States a condition on a type parameter, a parameter or a result. <a href="spec.html#s9c">Spec §9c</a></dd>
<dt id="kw-while"><code>while</code> <span class="tag">hard keyword</span></dt>
<dd>Reserved: writing it is an error that tells you to write <code>for</code>. <a href="spec.html#s18">Spec §18</a></dd>
<dt id="fn-windows"><a href="ref/windows.html"><code>windows</code></a> <span class="tag">function</span></dt>
<dd>Every run of n neighbouring items. <a href="spec.html#s13">Spec §13</a> <a href="ref/windows.html">Full description</a><br><code class="sig">fn windows[T](n Int, xs Seq[T]) Stream[List[T]]</code></dd>
<dt id="fn-wire_close"><a href="ref/wire_close.html"><code>wire_close</code></a> <span class="tag">function</span></dt>
<dd>Closes a session endpoint. <a href="spec.html#s19c">Spec §19c</a> <a href="ref/wire_close.html">Full description</a><br><code class="sig">fn wire_close(w Wire) Unit</code></dd>
<dt id="fn-wire_pair"><a href="ref/wire_pair.html"><code>wire_pair</code></a> <span class="tag">function</span></dt>
<dd>Two connected session endpoints. <a href="spec.html#s19c">Spec §19c</a> <a href="ref/wire_pair.html">Full description</a><br><code class="sig">fn wire_pair() (Wire, Wire)</code></dd>
<dt id="fn-wire_recv"><a href="ref/wire_recv.html"><code>wire_recv</code></a> <span class="tag">function</span></dt>
<dd>Receives a value on a session endpoint. <a href="spec.html#s19c">Spec §19c</a> <a href="ref/wire_recv.html">Full description</a><br><code class="sig">fn wire_recv[T](w Wire) Result[T, Error]</code></dd>
<dt id="fn-wire_send"><a href="ref/wire_send.html"><code>wire_send</code></a> <span class="tag">function</span></dt>
<dd>Sends a value on a session endpoint. <a href="spec.html#s19c">Spec §19c</a> <a href="ref/wire_send.html">Full description</a><br><code class="sig">fn wire_send[T](w Wire, x T) Result[Unit, Error]</code></dd>
<dt id="fn-with_stdin"><a href="ref/with_stdin.html"><code>with_stdin</code></a> <span class="tag">function</span></dt>
<dd>Runs a function with given text as standard input. <a href="spec.html#s19b">Spec §19b</a> <a href="ref/with_stdin.html">Full description</a><br><code class="sig">fn with_stdin[T](text String, f () -&gt; T) T</code></dd>
<dt id="fn-with_timeout"><a href="ref/with_timeout.html"><code>with_timeout</code></a> <span class="tag">function</span></dt>
<dd>Gives a function's result, or Err(TIMED_OUT) if time runs out. <a href="spec.html#s17">Spec §17</a> <a href="ref/with_timeout.html">Full description</a><br><code class="sig">fn with_timeout[T](d Duration, f (Cancel) -&gt; Result[T, Error]) Result[T, Error]</code><br><span class="eff">Effect: parks</span></dd>
<dt id="fn-wrap_to"><a href="ref/wrap_to.html"><code>wrap_to</code></a> <span class="tag">function</span></dt>
<dd>Converts to another width by keeping the low bits. <a href="spec.html#s5">Spec §5</a> <a href="ref/wrap_to.html">Full description</a><br><code class="sig">fn wrap_to[T Numeric, N Numeric](x N) T</code></dd>
<dt id="fn-wrapping_add"><a href="ref/wrapping_add.html"><code>wrapping_add</code></a> <span class="tag">function</span></dt>
<dd>Addition that wraps around on overflow. <a href="spec.html#s5">Spec §5</a> <a href="ref/wrapping_add.html">Full description</a><br><code class="sig">fn wrapping_add[T](a T, b T) T</code></dd>
<dt id="fn-wrapping_mul"><a href="ref/wrapping_mul.html"><code>wrapping_mul</code></a> <span class="tag">function</span></dt>
<dd>Multiplication that wraps around on overflow. <a href="spec.html#s5">Spec §5</a> <a href="ref/wrapping_mul.html">Full description</a><br><code class="sig">fn wrapping_mul[T](a T, b T) T</code></dd>
<dt id="fn-wrapping_sub"><a href="ref/wrapping_sub.html"><code>wrapping_sub</code></a> <span class="tag">function</span></dt>
<dd>Subtraction that wraps around on overflow. <a href="spec.html#s5">Spec §5</a> <a href="ref/wrapping_sub.html">Full description</a><br><code class="sig">fn wrapping_sub[T](a T, b T) T</code></dd>
<dt id="fn-write"><a href="ref/write.html"><code>write</code></a> <span class="tag">function</span></dt>
<dd>Sends a value on a channel. <a href="spec.html#s17">Spec §17</a> <a href="ref/write.html">Full description</a><br><code class="sig">fn write[T](w ChanW[T], x T) Result[Unit, Error]</code><br><span class="eff">Effect: parks</span></dd>
<dt id="fn-write_bytes"><a href="ref/write_bytes.html"><code>write_bytes</code></a> <span class="tag">function</span></dt>
<dd>Writes bytes. <a href="spec.html#s19b">Spec §19b</a> <a href="ref/write_bytes.html">Full description</a><br><code class="sig">fn write_bytes(out Io, data Array[Byte]) Result[Unit, Error]</code><br><span class="eff">Effect: parks</span></dd>
<dt id="fn-write_file"><a href="ref/write_file.html"><code>write_file</code></a> <span class="tag">function</span></dt>
<dd>Writes text to a file. <a href="spec.html#s19c">Spec §19c</a> <a href="ref/write_file.html">Full description</a><br><code class="sig">fn write_file(p String, s String) Result[Unit, Error]</code><br><span class="eff">Effect: parks · Needs permission: fs</span></dd>
</dl>

## Y {#y}

<dl class="ref">
<dt id="kw-yield"><code>yield</code> <span class="tag">soft keyword</span></dt>
<dd>Gives one value of a <code>for</code> comprehension. <a href="spec.html#s13">Spec §13</a></dd>
</dl>

## Z {#z}

<dl class="ref">
<dt id="fn-zip"><a href="ref/zip.html"><code>zip</code></a> <span class="tag">function</span></dt>
<dd>Pairs the items of two sources, stopping at the shorter. <a href="spec.html#s13">Spec §13</a> <a href="ref/zip.html">Full description</a><br><code class="sig">fn zip[A, B](a Seq[A], b Seq[B]) Stream[(A, B)]</code></dd>
<dt id="fn-zip3"><a href="ref/zip3.html"><code>zip3</code></a> <span class="tag">function</span></dt>
<dd>Triples the items of three sources. <a href="spec.html#s13">Spec §13</a> <a href="ref/zip3.html">Full description</a><br><code class="sig">fn zip3[A, B, C](a Seq[A], b Seq[B], c Seq[C]) Stream[(A, B, C)]</code></dd>
<dt id="fn-zip_with"><a href="ref/zip_with.html"><code>zip_with</code></a> <span class="tag">function</span></dt>
<dd>Combines the items of two sources with a function. <a href="spec.html#s13">Spec §13</a> <a href="ref/zip_with.html">Full description</a><br><code class="sig">fn zip_with[A, B, C](f (A, B) -&gt; C, xs Seq[A], ys Seq[B]) Stream[C]</code></dd>
</dl>

