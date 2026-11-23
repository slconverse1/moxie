---
layout: default
toc: true
terms: false
dialect: gc
title: "Moxie/gc Spec · keywords, types, and functions"
---

# Spec reference: keywords, types, and functions

This is part of the [moxie/gc Spec](spec.html). Every keyword, type and prelude function the text of this site mentions is described here, with its signature, and each word in the Mixer’s Guide and the intro links to its entry. A parameter written `Seq[T]` takes any source of `T` values: a `List`, `Array`, `Set`, `Ring` or `Stream`. Where a name has several signatures, each is listed.

## Hard keywords {#hard}

These 39 words can never be names.

<dl class="ref">
<dt id="kw-fn"><code>fn</code></dt>
<dd>Declares a function, <code>fn name(params) Result = body</code>, or a function value. <a href="spec.html#s9">Spec §9</a></dd>
<dt id="kw-tuple"><code>tuple</code></dt>
<dd>Declares a tuple type with named fields. <a href="spec.html#s6">Spec §6</a></dd>
<dt id="kw-enum"><code>enum</code></dt>
<dd>Declares an enum: a closed set of cases, each optionally carrying values. <a href="spec.html#s6">Spec §6</a></dd>
<dt id="kw-interface"><code>interface</code></dt>
<dd>Declares an interface: the methods a type must have. <a href="spec.html#s12">Spec §12</a></dd>
<dt id="kw-impl"><code>impl</code></dt>
<dd>Gives a type the methods of an interface (<code>impl Show for Point</code>). <a href="spec.html#s12">Spec §12</a></dd>
<dt id="kw-forward"><code>forward</code></dt>
<dd><code>forward fn</code> declares a function's signature ahead of its body, so earlier code can call it in a one-pass compile. <a href="spec.html#s9">Spec §9</a></dd>
<dt id="kw-inline"><code>inline</code></dt>
<dd><code>inline fn</code> marks a helper that is expanded where it is called; a helper that returns a stream must be one. <a href="spec.html#s13">Spec §13</a></dd>
<dt id="kw-fiber"><code>fiber</code></dt>
<dd><code>fiber fn</code> declares a function that runs as its own fiber when started with <code>go</code>. <a href="spec.html#s18">Spec §18</a></dd>
<dt id="kw-import"><code>import</code></dt>
<dd>Brings in a package or some of its names. <a href="spec.html#s4">Spec §4</a></dd>
<dt id="kw-export"><code>export</code></dt>
<dd>Makes a name visible to the packages that import this one. <a href="spec.html#s4">Spec §4</a></dd>
<dt id="kw-internal"><code>internal</code></dt>
<dd>Keeps a name visible inside its package but hidden from importers. <a href="spec.html#s4">Spec §4</a></dd>
<dt id="kw-using"><code>using</code></dt>
<dd>Puts a named value in scope for the code that follows, as in <code>using locale = Locale.de_de</code>. <a href="spec.html#s5">Spec §5</a></dd>
<dt id="kw-if"><code>if</code></dt>
<dd>Chooses between two expressions, <code>if c then a else b</code>, or between blocks. <a href="spec.html#s1">Spec §1</a></dd>
<dt id="kw-elif"><code>elif</code></dt>
<dd>A further condition in an <code>if</code> chain. <a href="spec.html#s1">Spec §1</a></dd>
<dt id="kw-else"><code>else</code></dt>
<dd>The branch taken when no <code>if</code> or <code>elif</code> condition holds; also what a <code>for</code> loop yields when it ends without <code>break</code>. <a href="spec.html#s1">Spec §1</a></dd>
<dt id="kw-when"><code>when</code></dt>
<dd>Matches a value against patterns, one arm per pattern, and checks that every case is covered. <a href="spec.html#s8">Spec §8</a></dd>
<dt id="kw-select"><code>select</code></dt>
<dd>Waits on several channel, timer or future operations and runs the arm for the first that is ready. <a href="spec.html#s17">Spec §17</a></dd>
<dt id="kw-for"><code>for</code></dt>
<dd>Moxie's only loop: over a collection or range, or on a condition, and it can produce a value. <a href="spec.html#s18">Spec §18</a></dd>
<dt id="kw-while"><code>while</code></dt>
<dd>Reserved: writing it is an error that tells you to write <code>for</code>. <a href="spec.html#s18">Spec §18</a></dd>
<dt id="kw-in"><code>in</code></dt>
<dd>Separates the name from the collection in <code>for x in xs</code>, and tests membership. <a href="spec.html#s18">Spec §18</a></dd>
<dt id="kw-is"><code>is</code></dt>
<dd>Tests a value against a pattern and binds its names: <code>r is Ok(v)</code>. <a href="spec.html#s8">Spec §8</a></dd>
<dt id="kw-break"><code>break</code></dt>
<dd>Leaves the innermost loop, or the one named by a label; <code>break(value)</code> gives the loop a value. <a href="spec.html#s18a">Spec §18A</a></dd>
<dt id="kw-continue"><code>continue</code></dt>
<dd>Skips to the next pass of a loop, or of the loop named by a label. <a href="spec.html#s18a">Spec §18A</a></dd>
<dt id="kw-return"><code>return</code></dt>
<dd>Leaves the function early with a value. <a href="spec.html#s9">Spec §9</a></dd>
<dt id="kw-daemon"><code>daemon</code></dt>
<dd>The main cycle of a server program, which runs until it is stopped. <a href="spec.html#s16">Spec §16</a></dd>
<dt id="kw-do"><code>do</code></dt>
<dd>Joins a one-line <code>for</code> header to its body, and opens a block that is itself an expression. <a href="spec.html#s1">Spec §1</a></dd>
<dt id="kw-go"><code>go</code></dt>
<dd>Starts a fiber: <code>go worker(args)</code> returns at once and the function runs concurrently. <a href="spec.html#s18">Spec §18</a></dd>
<dt id="kw-ref"><code>ref</code></dt>
<dd>Marks a parameter that the function may rebind; the final value is copied back to the caller's variable. <a href="spec.html#s9">Spec §9</a></dd>
<dt id="kw-try_go"><code>try_go</code></dt>
<dd>Like <code>go</code>, but gives an Err (NO_SLOT) instead of waiting when the fiber function has no free slot. <a href="spec.html#s18">Spec §18</a></dd>
<dt id="kw-move"><code>move</code></dt>
<dd>Passes a resource to a new owner, so the old name can no longer use it. <a href="spec.html#s19">Spec §19</a></dd>
<dt id="kw-static"><code>static</code></dt>
<dd>Marks a function that belongs to a type and has no <code>self</code>, as in <code>static fn read(text String)</code>. <a href="spec.html#s12">Spec §12</a></dd>
<dt id="kw-and"><code>and</code></dt>
<dd>True when both sides are true; the right side is evaluated only if needed. <a href="spec.html#s10">Spec §10</a></dd>
<dt id="kw-or"><code>or</code></dt>
<dd>True when either side is true; the right side is evaluated only if needed. <a href="spec.html#s10">Spec §10</a></dd>
<dt id="kw-not"><code>not</code></dt>
<dd>Reverses a Bool. <a href="spec.html#s10">Spec §10</a></dd>
<dt id="kw-true"><code>true</code></dt>
<dd>The Bool value true. <a href="spec.html#s5">Spec §5</a></dd>
<dt id="kw-false"><code>false</code></dt>
<dd>The Bool value false. <a href="spec.html#s5">Spec §5</a></dd>
<dt id="kw-Self"><code>Self</code></dt>
<dd>Inside an interface or impl, the type being described. <a href="spec.html#s12">Spec §12</a></dd>
<dt id="kw-self"><code>self</code></dt>
<dd>The receiver value inside a method. <a href="spec.html#s12">Spec §12</a></dd>
<dt id="kw-todo"><code>todo</code></dt>
<dd>Stands for an expression of whatever type is expected, with an optional message; aborts if it runs. <a href="spec.html#s2">Spec §2</a></dd>
</dl>

## Soft keywords {#soft}

These 30 words are keywords in one position only and are ordinary names elsewhere.

<dl class="ref">
<dt id="kw-end"><code>end</code></dt>
<dd>An optional line after a block that names the keyword that opened it, as in <code>end fn</code>. <a href="spec.html#s1">Spec §1</a></dd>
<dt id="kw-eval"><code>eval</code></dt>
<dd>Opens an indented block of steps that are chained with <code>flat_map</code>. <a href="spec.html#s23">Spec §23</a></dd>
<dt id="kw-mutable"><code>mutable</code></dt>
<dd>Opens a block in which names may be updated in place and cannot leak out. <a href="spec.html#s3">Spec §3</a></dd>
<dt id="kw-deriving"><code>deriving</code></dt>
<dd>In a tuple or enum header, asks for generated methods such as <code>show</code>, <code>eq</code>, <code>ord</code> or <code>read</code>. <a href="spec.html#s6">Spec §6</a></dd>
<dt id="kw-delegate"><code>delegate</code></dt>
<dd>After a field's type, forwards the interface methods of that field. <a href="spec.html#s12">Spec §12</a></dd>
<dt id="kw-proxy"><code>proxy</code></dt>
<dd>After the target of an <code>impl ... for</code>, forwards the impl to a field: <code>proxy(field)</code>. <a href="spec.html#s12">Spec §12</a></dd>
<dt id="kw-closed"><code>closed</code></dt>
<dd>A <code>select</code> arm that runs when a channel has been closed. <a href="spec.html#s17">Spec §17</a></dd>
<dt id="kw-cancelled"><code>cancelled</code></dt>
<dd>A <code>select</code> arm that runs when a cancel token has been set. <a href="spec.html#s17">Spec §17</a></dd>
<dt id="kw-wait"><code>wait</code></dt>
<dd>At the start of a statement, waits for the fibers started below it, or for a cancel token. <a href="spec.html#s18">Spec §18</a></dd>
<dt id="kw-as"><code>as</code></dt>
<dd>Renames a name in an import. <a href="spec.html#s4">Spec §4</a></dd>
<dt id="kw-type"><code>type</code></dt>
<dd>Declares a type alias, an opaque type or a union: <code>type Id = Int</code>. <a href="spec.html#s6">Spec §6</a></dd>
<dt id="kw-alias"><code>alias</code></dt>
<dd>Follows <code>type</code> to make a second name for a type. <a href="spec.html#s6">Spec §6</a></dd>
<dt id="kw-opaque"><code>opaque</code></dt>
<dd>Follows <code>type</code> to make a type whose inside is hidden from other packages. <a href="spec.html#s6">Spec §6</a></dd>
<dt id="kw-union"><code>union</code></dt>
<dd>Follows <code>type</code> to declare a type that is any one of several types. <a href="spec.html#s6">Spec §6</a></dd>
<dt id="kw-step"><code>step</code></dt>
<dd>After a range, gives the stride: <code>0..10 step 5</code>. <a href="spec.html#s5">Spec §5</a></dd>
<dt id="kw-seq"><code>seq</code></dt>
<dd>After <code>|&gt;</code>, begins a stream pipeline written one stage per line. <a href="spec.html#s13">Spec §13</a></dd>
<dt id="kw-init"><code>init</code></dt>
<dd>Opens an initializer block that runs when its package loads. <a href="spec.html#s4">Spec §4</a></dd>
<dt id="kw-lazy"><code>lazy</code></dt>
<dd>Marks a parameter that is evaluated each time the function reads it, and not at all if it never does. <a href="spec.html#s9">Spec §9</a></dd>
<dt id="kw-foreign"><code>foreign</code></dt>
<dd>Opens a block of declarations for functions in a C library. <a href="spec.html#s19a">Spec §19A</a></dd>
<dt id="kw-pure"><code>pure</code></dt>
<dd>Function modifier: the function has no effects. <a href="spec.html#s14">Spec §14</a></dd>
<dt id="kw-prints"><code>prints</code></dt>
<dd>Function modifier: the function may print, and nothing else. <a href="spec.html#s14">Spec §14</a></dd>
<dt id="kw-parks"><code>parks</code></dt>
<dd>Function modifier: the function may wait, for example on a channel or the network. <a href="spec.html#s14">Spec §14</a></dd>
<dt id="kw-impure"><code>impure</code></dt>
<dd>Function modifier: the function may have any effect. <a href="spec.html#s14">Spec §14</a></dd>
<dt id="kw-tailrec"><code>tailrec</code></dt>
<dd>Function modifier: the function must call itself only in tail position, so it runs in constant stack. <a href="spec.html#s9">Spec §9</a></dd>
<dt id="kw-invariant"><code>invariant</code></dt>
<dd>A line among a tuple's fields that states a condition every value of the tuple must satisfy. <a href="spec.html#s9c">Spec §9C</a></dd>
<dt id="kw-update"><code>update</code></dt>
<dd>After <code>x.</code> and before <code>:</code>, builds a copy of <code>x</code> with some fields changed. <a href="spec.html#s6">Spec §6</a></dd>
<dt id="kw-test"><code>test</code></dt>
<dd>At the start of a statement, before a string, declares a test block. <a href="spec.html#s22">Spec §22</a></dd>
<dt id="kw-where"><code>where</code></dt>
<dd>States a condition on a type parameter, a parameter or a result. <a href="spec.html#s9c">Spec §9C</a></dd>
<dt id="kw-yield"><code>yield</code></dt>
<dd>Gives one value of a <code>for</code> comprehension. <a href="spec.html#s13">Spec §13</a></dd>
<dt id="kw-any"><code>any</code></dt>
<dd>In a type, before an interface name, means a value of any type that has that interface. <a href="spec.html#s12">Spec §12</a></dd>
</dl>

## Types {#types}

<dl class="ref">
<dt id="ty-Int"><code>Int</code></dt><dd>A whole number; <code>Int8</code> to <code>Int64</code> and <code>UInt8</code> to <code>UInt64</code> fix the width.</dd>
<dt id="ty-Double"><code>Double</code></dt><dd>A 64-bit floating-point number; <code>Float</code> is the 32-bit one.</dd>
<dt id="ty-Decimal"><code>Decimal</code></dt><dd>An exact base-ten number with a fixed scale, for money.</dd>
<dt id="ty-Bool"><code>Bool</code></dt><dd>true or false.</dd>
<dt id="ty-Char"><code>Char</code></dt><dd>One Unicode scalar value, written <code>'a'</code>.</dd>
<dt id="ty-String"><code>String</code></dt><dd>Text, stored as UTF-8 and immutable.</dd>
<dt id="ty-Unit"><code>Unit</code></dt><dd>The type with one value, <code>()</code>, for a function that gives nothing back.</dd>
<dt id="ty-Duration"><code>Duration</code></dt><dd>A length of time, written <code>5s</code>, <code>250ms</code>, <code>1h</code>.</dd>
<dt id="ty-DateTime"><code>DateTime</code></dt><dd>A calendar date and time of day.</dd>
<dt id="ty-Range"><code>Range</code></dt><dd>A run of integers or characters, <code>1..5</code> or <code>0..&lt;n</code>.</dd>
<dt id="ty-List"><code>List</code></dt><dd>An immutable sequence that shares structure when updated.</dd>
<dt id="ty-Array"><code>Array</code></dt><dd>A fixed-size sequence of one type.</dd>
<dt id="ty-MultiArray"><code>MultiArray</code></dt><dd>An array with more than one dimension.</dd>
<dt id="ty-Set"><code>Set</code></dt><dd>A collection of distinct values.</dd>
<dt id="ty-Dict"><code>Dict</code></dt><dd>A collection of key-value pairs.</dd>
<dt id="ty-Ring"><code>Ring</code></dt><dd>A fixed-capacity buffer that overwrites its oldest item when full.</dd>
<dt id="ty-Stream"><code>Stream</code></dt><dd>A lazy pipeline of values that runs when something consumes it.</dd>
<dt id="ty-Seq"><code>Seq</code></dt><dd>In a signature, any source of values: a List, Array, Set, Ring or Stream.</dd>
<dt id="ty-Option"><code>Option</code></dt><dd>Some(value) or None: a value that may be absent.</dd>
<dt id="ty-Result"><code>Result</code></dt><dd>Ok(value) or Err(error): the outcome of something that can fail.</dd>
<dt id="ty-Error"><code>Error</code></dt><dd>The standard error value: a code and a message.</dd>
<dt id="ty-NonEmpty"><code>NonEmpty</code></dt><dd>A list with a first item guaranteed, as <code>head</code> and <code>tail</code>.</dd>
<dt id="ty-Atom"><code>Atom</code></dt><dd>A shared cell whose value is replaced by <code>swap</code> and <code>reset</code>.</dd>
<dt id="ty-Future"><code>Future</code></dt><dd>A value that will be supplied once, by <code>resolve</code> or <code>reject</code>.</dd>
<dt id="ty-Chan"><code>Chan</code></dt><dd>A channel between fibers; its read and write ends have separate owners.</dd>
<dt id="ty-Timer"><code>Timer</code></dt><dd>A resource that fires once or repeatedly after a duration.</dd>
<dt id="ty-Cancel"><code>Cancel</code></dt><dd>A token that tells running fibers to stop.</dd>
<dt id="ty-Secret"><code>Secret</code></dt><dd>A value that cannot be printed or compared with <code>==</code>.</dd>
<dt id="ty-Io"><code>Io</code></dt><dd>A readable and writable stream: a socket or a standard stream.</dd>
<dt id="ty-Listener"><code>Listener</code></dt><dd>A listening socket that gives connections through <code>accept</code>.</dd>
<dt id="ty-Gen"><code>Gen</code></dt><dd>A seeded source of values for property tests.</dd>
</dl>

## Streams and sequences {#f-streams-and-sequences}

Spec <a href="spec.html#s13">§13</a>.

<dl class="ref">
<dt id="fn-map"><code>map</code></dt>
<dd>Applies a function to each item (<code>Result</code> and <code>Option</code> too: it changes the value inside).<br><code class="sig">map[T, U](f (T) -&gt; U, xs Seq[T]) Stream[U]
map[T, U, E](f (T) -&gt; U, r Result[T, E]) Result[U, E]
map[T, U](f (T) -&gt; U, o Option[T]) Option[U]</code></dd>
<dt id="fn-fmap"><code>fmap</code></dt>
<dd>Like <code>map</code>, but a List stays a List and an Array an Array.<br><code class="sig">fmap[T, U](f (T) -&gt; U, xs List[T]) List[U]
fmap[T, U, N](f (T) -&gt; U, xs Array[T][N]) Array[U][N]
fmap[T, U](f (T) -&gt; U, o Option[T]) Option[U]
fmap[T, U, E](f (T) -&gt; U, r Result[T, E]) Result[U, E]</code></dd>
<dt id="fn-filter"><code>filter</code></dt>
<dd>Keeps the items for which a test is true.<br><code class="sig">filter[T](f (T) -&gt; Bool, xs Seq[T]) Stream[T]</code></dd>
<dt id="fn-filter_map"><code>filter_map</code></dt>
<dd>Applies a function that gives an Option and keeps the values that are present.<br><code class="sig">filter_map[T, U](f (T) -&gt; Option[U], xs Seq[T]) Stream[U]</code></dd>
<dt id="fn-take"><code>take</code></dt>
<dd>The first n items.<br><code class="sig">take[T](n Int, xs Seq[T]) Stream[T]</code></dd>
<dt id="fn-drop"><code>drop</code></dt>
<dd>All but the first n items.<br><code class="sig">drop[T](n Int, xs Seq[T]) Stream[T]</code></dd>
<dt id="fn-take_while"><code>take_while</code></dt>
<dd>Items from the start while a test holds.<br><code class="sig">take_while[T](f (T) -&gt; Bool, xs Seq[T]) Stream[T]</code></dd>
<dt id="fn-drop_while"><code>drop_while</code></dt>
<dd>Skips items from the start while a test holds.<br><code class="sig">drop_while[T](f (T) -&gt; Bool, xs Seq[T]) Stream[T]</code></dd>
<dt id="fn-take_last"><code>take_last</code></dt>
<dd>The last n items.<br><code class="sig">take_last[T](n Int, xs Seq[T]) Stream[T]</code></dd>
<dt id="fn-drop_last"><code>drop_last</code></dt>
<dd>All but the last n items.<br><code class="sig">drop_last[T](n Int, xs Seq[T]) Stream[T]</code></dd>
<dt id="fn-enumerate"><code>enumerate</code></dt>
<dd>Pairs each item with its position, from 0.<br><code class="sig">enumerate[T](xs Seq[T]) Stream[(Int, T)]</code></dd>
<dt id="fn-zip"><code>zip</code></dt>
<dd>Pairs the items of two sources, stopping at the shorter.<br><code class="sig">zip[A, B](a Seq[A], b Seq[B]) Stream[(A, B)]</code></dd>
<dt id="fn-zip3"><code>zip3</code></dt>
<dd>Triples the items of three sources.<br><code class="sig">zip3[A, B, C](a Seq[A], b Seq[B], c Seq[C]) Stream[(A, B, C)]</code></dd>
<dt id="fn-zip_with"><code>zip_with</code></dt>
<dd>Combines the items of two sources with a function.<br><code class="sig">zip_with[A, B, C](f (A, B) -&gt; C, xs Seq[A], ys Seq[B]) Stream[C]</code></dd>
<dt id="fn-unzip"><code>unzip</code></dt>
<dd>Splits a source of pairs into two Lists.<br><code class="sig">unzip[A, B](xs Seq[(A, B)]) (List[A], List[B])</code></dd>
<dt id="fn-sort"><code>sort</code></dt>
<dd>Orders the items by <code>&lt;</code>, keeping equal items in their order.<br><code class="sig">sort[T](xs Seq[T]) Stream[T]</code></dd>
<dt id="fn-sort_by"><code>sort_by</code></dt>
<dd>Orders the items by a key function.<br><code class="sig">sort_by[T, K](f (T) -&gt; K, xs Seq[T]) Stream[T]</code></dd>
<dt id="fn-reverse"><code>reverse</code></dt>
<dd>The items in the opposite order.<br><code class="sig">reverse[T](xs Seq[T]) Stream[T]</code></dd>
<dt id="fn-reduce"><code>reduce</code></dt>
<dd>Folds the items into one value, from a start value and a combining function.<br><code class="sig">reduce[T, A](init A, f (A, T) -&gt; A, xs Seq[T]) A</code></dd>
<dt id="fn-reduce_right"><code>reduce_right</code></dt>
<dd>Like <code>reduce</code>, folding from the end.<br><code class="sig">reduce_right[T, A](init A, f (T, A) -&gt; A, xs Seq[T]) A</code></dd>
<dt id="fn-scan"><code>scan</code></dt>
<dd>Like <code>reduce</code>, but gives every running value.<br><code class="sig">scan[T, A](init A, f (A, T) -&gt; A, xs Seq[T]) Stream[A]</code></dd>
<dt id="fn-collect"><code>collect</code></dt>
<dd>Gathers a stream into a List.<br><code class="sig">collect[T](xs Seq[T]) List[T]</code></dd>
<dt id="fn-sum"><code>sum</code></dt>
<dd>Adds the items.<br><code class="sig">sum[T](xs Seq[T]) T</code></dd>
<dt id="fn-product"><code>product</code></dt>
<dd>Multiplies the items.<br><code class="sig">product[T](xs Seq[T]) T</code></dd>
<dt id="fn-count"><code>count</code></dt>
<dd>How many items there are.<br><code class="sig">count[T](xs Seq[T]) Int</code></dd>
<dt id="fn-avg"><code>avg</code></dt>
<dd>The mean of the items, as a Float; an Err for an empty source.<br><code class="sig">avg(xs Seq[Int]) Result[Float, Error]
avg(xs Seq[Float]) Result[Float, Error]
avg(xs Seq[Decimal]) Result[Float, Error]</code></dd>
<dt id="fn-any"><code>any</code></dt>
<dd>True if the test holds for at least one item.<br><code class="sig">any[T](f (T) -&gt; Bool, xs Seq[T]) Bool</code></dd>
<dt id="fn-all"><code>all</code></dt>
<dd>True if the test holds for every item.<br><code class="sig">all[T](f (T) -&gt; Bool, xs Seq[T]) Bool</code></dd>
<dt id="fn-find"><code>find</code></dt>
<dd>The first item for which a test is true; an Err if there is none.<br><code class="sig">find[T, E](f (T) -&gt; Bool, xs Seq[T]) Result[T, E]</code></dd>
<dt id="fn-find_map"><code>find_map</code></dt>
<dd>The first present value a function gives; an Err if there is none.<br><code class="sig">find_map[T, U, E](f (T) -&gt; Option[U], xs Seq[T]) Result[U, E]</code></dd>
<dt id="fn-position"><code>position</code></dt>
<dd>The position of the first item that passes a test; an Err if none does.<br><code class="sig">position[T, E](f (T) -&gt; Bool, xs Seq[T]) Result[Int, E]</code></dd>
<dt id="fn-first"><code>first</code></dt>
<dd>The first item; an Err if empty.<br><code class="sig">first[T, E](xs Seq[T]) Result[T, E]</code></dd>
<dt id="fn-last"><code>last</code></dt>
<dd>The last item; an Err if empty.<br><code class="sig">last[T, E](xs Seq[T]) Result[T, E]</code></dd>
<dt id="fn-min_by"><code>min_by</code></dt>
<dd>The item with the smallest key; an Err if empty.<br><code class="sig">min_by[T, K, E](f (T) -&gt; K, xs Seq[T]) Result[T, E]</code></dd>
<dt id="fn-max_by"><code>max_by</code></dt>
<dd>The item with the largest key; an Err if empty.<br><code class="sig">max_by[T, K, E](f (T) -&gt; K, xs Seq[T]) Result[T, E]</code></dd>
<dt id="fn-partition"><code>partition</code></dt>
<dd>Splits the items into those that pass a test and those that don't.<br><code class="sig">partition[T](f (T) -&gt; Bool, xs Seq[T]) (List[T], List[T])</code></dd>
<dt id="fn-span"><code>span</code></dt>
<dd>Splits at the first item that fails a test.<br><code class="sig">span[T](f (T) -&gt; Bool, xs Seq[T]) (List[T], List[T])</code></dd>
<dt id="fn-split_at"><code>split_at</code></dt>
<dd>Splits after the first n items.<br><code class="sig">split_at[T](n Int, xs Seq[T]) (List[T], List[T])</code></dd>
<dt id="fn-distinct"><code>distinct</code></dt>
<dd>Drops repeated items, keeping the first of each.<br><code class="sig">distinct[T](xs Seq[T]) Stream[T]</code></dd>
<dt id="fn-distinct_by"><code>distinct_by</code></dt>
<dd>Drops items whose key has been seen.<br><code class="sig">distinct_by[T, K](f (T) -&gt; K, xs Seq[T]) Stream[T]</code></dd>
<dt id="fn-flatten"><code>flatten</code></dt>
<dd>Turns a source of sources into one source.<br><code class="sig">flatten[T](xs Seq[Seq[T]]) Stream[T]</code></dd>
<dt id="fn-cycle"><code>cycle</code></dt>
<dd>Repeats a source forever.<br><code class="sig">cycle[T](xs Seq[T]) Stream[T]</code></dd>
<dt id="fn-repeat"><code>repeat</code></dt>
<dd>One value, forever.<br><code class="sig">repeat[T](x T) Stream[T]</code></dd>
<dt id="fn-iterate"><code>iterate</code></dt>
<dd>A seed, then the function applied again and again.<br><code class="sig">iterate[T](seed T, f (T) -&gt; T) Stream[T]</code></dd>
<dt id="fn-intersperse"><code>intersperse</code></dt>
<dd>Puts a separator between items.<br><code class="sig">intersperse[T](sep T, xs Seq[T]) Stream[T]</code></dd>
<dt id="fn-chunks"><code>chunks</code></dt>
<dd>Groups the items in Lists of n.<br><code class="sig">chunks[T](n Int, xs Seq[T]) Stream[List[T]]</code></dd>
<dt id="fn-windows"><code>windows</code></dt>
<dd>Every run of n neighbouring items.<br><code class="sig">windows[T](n Int, xs Seq[T]) Stream[Array[T]]</code></dd>
<dt id="fn-group_by"><code>group_by</code></dt>
<dd>A Dict from key to the Lists of items with that key.<br><code class="sig">group_by[T, K](f (T) -&gt; K, xs Seq[T]) Dict[K, List[T]]</code></dd>
<dt id="fn-frequencies"><code>frequencies</code></dt>
<dd>A Dict of how many times each item occurs.<br><code class="sig">frequencies[T](xs Seq[T]) Dict[T, Int]</code></dd>
<dt id="fn-count_by"><code>count_by</code></dt>
<dd>A Dict of how many items have each key.<br><code class="sig">count_by[T, K](f (T) -&gt; K, xs Seq[T]) Dict[K, Int]</code></dd>
<dt id="fn-transpose"><code>transpose</code></dt>
<dd>Turns rows into columns.<br><code class="sig">transpose[T](rows Seq[Seq[T]]) List[List[T]]</code></dd>
<dt id="fn-to_stream"><code>to_stream</code></dt>
<dd>Treats any collection as a stream.<br><code class="sig">to_stream[T](xs Seq[T]) Stream[T]</code></dd>
</dl>

## Collections {#f-collections}

Spec <a href="spec.html#s7">§7</a>.

<dl class="ref">
<dt id="fn-len"><code>len</code></dt>
<dd>The number of items in a collection, or of bytes in a String.<br><code class="sig">len(s String) Int
len[T](xs Seq[T]) Int
len[K, V](d Dict[K, V]) Int</code></dd>
<dt id="fn-is_empty"><code>is_empty</code></dt>
<dd>True when there are no items.<br><code class="sig">is_empty(s String) Bool
is_empty[T](xs Seq[T]) Bool
is_empty[K, V](d Dict[K, V]) Bool
is_empty[T](s Set[T]) Bool</code></dd>
<dt id="fn-get"><code>get</code></dt>
<dd>The item at a key or position; an Err if absent.<br><code class="sig">get[K, V, E](d Dict[K, V], k K) Result[V, E]
get[T, E](xs List[T], i Int) Result[T, E]
get[T, E](xs Array[T], i Int) Result[T, E]</code></dd>
<dt id="fn-get_or"><code>get_or</code></dt>
<dd>The value, or a default when it is absent or an Err.<br><code class="sig">get_or[T, E](r Result[T, E], d T) T
get_or[T](o Option[T], d T) T
get_or[K, V](d Dict[K, V], k K, d2 V) V
get_or[T](xs List[T], i Int, d T) T</code></dd>
<dt id="fn-contains"><code>contains</code></dt>
<dd>True if a String contains a piece of text, or a collection an item.<br><code class="sig">contains(s String, t String) Bool
contains[T](xs Seq[T], x T) Bool
contains[K, V](d Dict[K, V], k K) Bool</code></dd>
<dt id="fn-keys"><code>keys</code></dt>
<dd>The keys of a Dict.<br><code class="sig">keys[K, V](d Dict[K, V]) Stream[K]</code></dd>
<dt id="fn-values"><code>values</code></dt>
<dd>The values of a Dict.<br><code class="sig">values[K, V](d Dict[K, V]) Stream[V]</code></dd>
<dt id="fn-items"><code>items</code></dt>
<dd>The (key, value) pairs of a Dict.<br><code class="sig">items[K, V](d Dict[K, V]) Stream[(K, V)]</code></dd>
<dt id="fn-set"><code>set</code></dt>
<dd>A copy with the item at a position or key replaced.<br><code class="sig">set[T](xs List[T], i Int, x T) List[T]
set[T](xs Array[T], i Int, x T) Array[T]
set[T](xs MultiArray[T], i Int, x T) MultiArray[T]
set[K, V](d Dict[K, V], k K, v V) Dict[K, V]</code></dd>
<dt id="fn-remove"><code>remove</code></dt>
<dd>A copy without a key or item.<br><code class="sig">remove[K, V](d Dict[K, V], k K) Dict[K, V]
remove[T](s Set[T], x T) Set[T]
remove[T](xs List[T], x T) List[T]
remove[T](xs Array[T], x T) Array[T]</code></dd>
<dt id="fn-remove_at"><code>remove_at</code></dt>
<dd>A copy without the item at a position.<br><code class="sig">remove_at[T](xs List[T], i Int) List[T]
remove_at[T](xs Array[T], i Int) Array[T]</code></dd>
<dt id="fn-clear"><code>clear</code></dt>
<dd>An empty collection of the same kind.<br><code class="sig">clear[K, V](d Dict[K, V]) Dict[K, V]
clear[T](s Set[T]) Set[T]
clear[T](xs List[T]) List[T]</code></dd>
<dt id="fn-indices"><code>indices</code></dt>
<dd>The range of valid positions.<br><code class="sig">indices[T](xs Seq[T]) Range
indices(s String) Range</code></dd>
<dt id="fn-join"><code>join</code></dt>
<dd>Makes one String of the items, with an optional separator.<br><code class="sig">join[T](xs Seq[T], sep String) String
join[T](xs Seq[T]) String</code></dd>
<dt id="fn-replace"><code>replace</code></dt>
<dd>A copy with the value at a data path replaced.<br><code class="sig">replace[T, P, V](x T, path P, v V) T</code></dd>
<dt id="fn-modify"><code>modify</code></dt>
<dd>A copy with the value at a data path changed by a function.<br><code class="sig">modify[T, P, A](x T, path P, f (A) -&gt; A) T</code></dd>
</dl>

## Numbers {#f-numbers}

Spec <a href="spec.html#s5">§5</a>.

<dl class="ref">
<dt id="fn-abs"><code>abs</code></dt>
<dd>Absolute value.<br><code class="sig">abs(n Int) Int
abs(x Double) Double</code></dd>
<dt id="fn-min"><code>min</code></dt>
<dd>The smaller of two values.<br><code class="sig">min[T](a T, b T) T</code></dd>
<dt id="fn-max"><code>max</code></dt>
<dd>The larger of two values.<br><code class="sig">max[T](a T, b T) T</code></dd>
<dt id="fn-clamp"><code>clamp</code></dt>
<dd>Limits a value to a low and high bound, or to a range.<br><code class="sig">clamp[T](x T, lo T, hi T) T
clamp[T](x T, r Range) T</code></dd>
<dt id="fn-pow"><code>pow</code></dt>
<dd>A number raised to a power.<br><code class="sig">pow(a Int, b Int) Int
pow(a Double, b Double) Double</code></dd>
<dt id="fn-sqrt"><code>sqrt</code></dt>
<dd>Square root.<br><code class="sig">sqrt(x Double) Double</code></dd>
<dt id="fn-floor"><code>floor</code></dt>
<dd>Rounds down to an Int.<br><code class="sig">floor(x Double) Int</code></dd>
<dt id="fn-ceil"><code>ceil</code></dt>
<dd>Rounds up to an Int.<br><code class="sig">ceil(x Double) Int</code></dd>
<dt id="fn-round"><code>round</code></dt>
<dd>Rounds to the nearest Int.<br><code class="sig">round(x Double) Int</code></dd>
<dt id="fn-finite"><code>finite</code></dt>
<dd>Ok(x) when x is a finite number, an Err otherwise.<br><code class="sig">finite[E](x Double) Result[Double, E]</code></dd>
<dt id="fn-is_nan"><code>is_nan</code></dt>
<dd>True for not-a-number.<br><code class="sig">is_nan(x Double) Bool</code></dd>
<dt id="fn-is_inf"><code>is_inf</code></dt>
<dd>True for infinity.<br><code class="sig">is_inf(x Double) Bool</code></dd>
<dt id="fn-is_finite"><code>is_finite</code></dt>
<dd>True for an ordinary number.<br><code class="sig">is_finite(x Double) Bool</code></dd>
<dt id="fn-checked_add"><code>checked_add</code></dt>
<dd>Addition that gives an Err instead of overflowing.<br><code class="sig">checked_add[T, E](a T, b T) Result[T, E]</code></dd>
<dt id="fn-checked_sub"><code>checked_sub</code></dt>
<dd>Subtraction that gives an Err instead of overflowing.<br><code class="sig">checked_sub[T, E](a T, b T) Result[T, E]</code></dd>
<dt id="fn-checked_mul"><code>checked_mul</code></dt>
<dd>Multiplication that gives an Err instead of overflowing.<br><code class="sig">checked_mul[T, E](a T, b T) Result[T, E]</code></dd>
<dt id="fn-checked_div"><code>checked_div</code></dt>
<dd>Division that gives an Err for zero or overflow.<br><code class="sig">checked_div[T, E](a T, b T) Result[T, E]</code></dd>
<dt id="fn-wrapping_add"><code>wrapping_add</code></dt>
<dd>Addition that wraps around on overflow.<br><code class="sig">wrapping_add[T](a T, b T) T</code></dd>
<dt id="fn-wrapping_sub"><code>wrapping_sub</code></dt>
<dd>Subtraction that wraps around on overflow.<br><code class="sig">wrapping_sub[T](a T, b T) T</code></dd>
<dt id="fn-wrapping_mul"><code>wrapping_mul</code></dt>
<dd>Multiplication that wraps around on overflow.<br><code class="sig">wrapping_mul[T](a T, b T) T</code></dd>
<dt id="fn-saturating_add"><code>saturating_add</code></dt>
<dd>Addition that stops at the largest or smallest value.<br><code class="sig">saturating_add[T](a T, b T) T</code></dd>
<dt id="fn-saturating_sub"><code>saturating_sub</code></dt>
<dd>Subtraction that stops at the largest or smallest value.<br><code class="sig">saturating_sub[T](a T, b T) T</code></dd>
<dt id="fn-saturating_mul"><code>saturating_mul</code></dt>
<dd>Multiplication that stops at the largest or smallest value.<br><code class="sig">saturating_mul[T](a T, b T) T</code></dd>
<dt id="fn-bit_and"><code>bit_and</code></dt>
<dd>Bitwise and.<br><code class="sig">bit_and[T](a T, b T) T</code></dd>
<dt id="fn-bit_or"><code>bit_or</code></dt>
<dd>Bitwise or.<br><code class="sig">bit_or[T](a T, b T) T</code></dd>
<dt id="fn-bit_xor"><code>bit_xor</code></dt>
<dd>Bitwise exclusive or.<br><code class="sig">bit_xor[T](a T, b T) T</code></dd>
<dt id="fn-bit_not"><code>bit_not</code></dt>
<dd>Bitwise complement.<br><code class="sig">bit_not[T](a T) T</code></dd>
<dt id="fn-shl"><code>shl</code></dt>
<dd>Shifts bits left.<br><code class="sig">shl[T](a T, n Int) T</code></dd>
<dt id="fn-shr"><code>shr</code></dt>
<dd>Shifts bits right.<br><code class="sig">shr[T](a T, n Int) T</code></dd>
<dt id="fn-parse_number"><code>parse_number</code></dt>
<dd>Reads a number from text, optionally in a locale's format; an Err if it isn't one.<br><code class="sig">parse_number[N, E](s String) Result[N, E]
parse_number[N, E](s String, locale Locale) Result[N, E]</code></dd>
<dt id="fn-random"><code>random</code></dt>
<dd>A Double in [0, 1).<br><code class="sig">random() Double</code></dd>
<dt id="fn-random_int"><code>random_int</code></dt>
<dd>An Int drawn uniformly from a range.<br><code class="sig">random_int(r Range) Int</code></dd>
<dt id="fn-random_bytes"><code>random_bytes</code></dt>
<dd>n random bytes.<br><code class="sig">random_bytes(n Int) Array[Byte]</code></dd>
<dt id="fn-cast"><code>cast</code></dt>
<dd>Converts a number to another numeric type, <code>cast[Double](n)</code>.<br><code class="sig">cast[T](x Number) T</code></dd>
<dt id="fn-try_cast"><code>try_cast</code></dt>
<dd>Like <code>cast</code>, but gives an Err (OUT_OF_RANGE) when the value does not fit.<br><code class="sig">try_cast[T](x Number) Result[T, Error]</code></dd>
<dt id="fn-wrap_to"><code>wrap_to</code></dt>
<dd>Converts to another width by keeping the low bits.<br><code class="sig">wrap_to[T](x Number) T</code></dd>
<dt id="fn-round_to"><code>round_to</code></dt>
<dd>Rounds a Decimal to a scale with a mode: <code>round_to[2](x, #half_even)</code>.<br><code class="sig">round_to[n](x Decimal, mode Mode) Decimal</code></dd>
<dt id="fn-div"><code>div</code></dt>
<dd>Divides Decimals at a scale and mode; an Err for zero.<br><code class="sig">div(a Decimal, b Decimal, scale Int, mode Mode) Result[Decimal, Error]</code></dd>
</dl>

## Text {#f-text}

Spec <a href="spec.html#s5">§5</a>.

<dl class="ref">
<dt id="fn-upper"><code>upper</code></dt>
<dd>Upper case.<br><code class="sig">upper(s String) String
upper(c Char) Char</code></dd>
<dt id="fn-lower"><code>lower</code></dt>
<dd>Lower case.<br><code class="sig">lower(s String) String
lower(c Char) Char</code></dd>
<dt id="fn-trim"><code>trim</code></dt>
<dd>Removes spaces from both ends.<br><code class="sig">trim(s String) String</code></dd>
<dt id="fn-chars"><code>chars</code></dt>
<dd>The characters of a String.<br><code class="sig">chars(s String) Stream[Char]</code></dd>
<dt id="fn-graphemes"><code>graphemes</code></dt>
<dd>The user-perceived characters of a String.<br><code class="sig">graphemes(s String) Stream[String]</code></dd>
<dt id="fn-char_count"><code>char_count</code></dt>
<dd>How many characters.<br><code class="sig">char_count(s String) Int</code></dd>
<dt id="fn-grapheme_count"><code>grapheme_count</code></dt>
<dd>How many user-perceived characters.<br><code class="sig">grapheme_count(s String) Int</code></dd>
<dt id="fn-split"><code>split</code></dt>
<dd>Cuts a String at every separator.<br><code class="sig">split(s String, sep String) List[String]</code></dd>
<dt id="fn-split_once"><code>split_once</code></dt>
<dd>Cuts at the first separator; None if there is none.<br><code class="sig">split_once(s String, sep String) Option[(String, String)]</code></dd>
<dt id="fn-starts_with"><code>starts_with</code></dt>
<dd>True if the text begins with a prefix.<br><code class="sig">starts_with(s String, prefix String) Bool
starts_with(s String, c Char) Bool</code></dd>
<dt id="fn-ends_with"><code>ends_with</code></dt>
<dd>True if the text ends with a suffix.<br><code class="sig">ends_with(s String, suffix String) Bool
ends_with(s String, c Char) Bool</code></dd>
<dt id="fn-strip_prefix"><code>strip_prefix</code></dt>
<dd>The text without a prefix, or None if it doesn't start with it.<br><code class="sig">strip_prefix(s String, prefix String) Option[String]</code></dd>
<dt id="fn-strip_suffix"><code>strip_suffix</code></dt>
<dd>The text without a suffix, or None if it doesn't end with it.<br><code class="sig">strip_suffix(s String, suffix String) Option[String]</code></dd>
<dt id="fn-pad_left"><code>pad_left</code></dt>
<dd>Pads on the left to a width.<br><code class="sig">pad_left(s String, n Int) String
pad_left(s String, n Int, c String) String
pad_left(s String, n Int, c Char) String</code></dd>
<dt id="fn-pad_right"><code>pad_right</code></dt>
<dd>Pads on the right to a width.<br><code class="sig">pad_right(s String, n Int) String
pad_right(s String, n Int, c String) String
pad_right(s String, n Int, c Char) String</code></dd>
<dt id="fn-replace_text"><code>replace_text</code></dt>
<dd>Replaces every occurrence of one piece of text with another.<br><code class="sig">replace_text(s String, from String, to String) String</code></dd>
<dt id="fn-fmt"><code>fmt</code></dt>
<dd>Fills a template of <code>{}</code> slots with values.<br><code class="sig">fmt(template String, args...) String</code></dd>
<dt id="fn-try_fmt"><code>try_fmt</code></dt>
<dd>Like <code>fmt</code>, but gives an Err for a bad template.<br><code class="sig">try_fmt(template String, args...) Result[String, Error]</code></dd>
<dt id="fn-show"><code>show</code></dt>
<dd>The printed form of a value, as a String.<br><code class="sig">show[T](x T) String</code></dd>
</dl>

## Results and options {#f-results-and-options}

Spec <a href="spec.html#s15">§15</a>.

<dl class="ref">
<dt id="fn-is_ok"><code>is_ok</code></dt>
<dd>True for an Ok.<br><code class="sig">is_ok[T, E](r Result[T, E]) Bool</code></dd>
<dt id="fn-is_err"><code>is_err</code></dt>
<dd>True for an Err.<br><code class="sig">is_err[T, E](r Result[T, E]) Bool</code></dd>
<dt id="fn-ok"><code>ok</code></dt>
<dd>Turns a Result into an Option, dropping the error.<br><code class="sig">ok[T, E](r Result[T, E]) Option[T]</code></dd>
<dt id="fn-ok_or"><code>ok_or</code></dt>
<dd>Turns an Option into a Result with a given error.<br><code class="sig">ok_or[T](o Option[T], err Error) Result[T, Error]</code></dd>
<dt id="fn-unwrap"><code>unwrap</code></dt>
<dd>The value of an Ok; aborts on an Err.<br><code class="sig">unwrap[T, E](r Result[T, E]) T</code></dd>
<dt id="fn-map_ok"><code>map_ok</code></dt>
<dd>Changes the value inside an Ok.<br><code class="sig">map_ok[T, U, E](r Result[T, E], f (T) -&gt; U) Result[U, E]</code></dd>
<dt id="fn-map_err"><code>map_err</code></dt>
<dd>Changes the error inside an Err.<br><code class="sig">map_err[T, E, F](r Result[T, E], f (E) -&gt; F) Result[T, F]</code></dd>
<dt id="fn-or_else"><code>or_else</code></dt>
<dd>Tries a recovery function on an Err.<br><code class="sig">or_else[T, E, F](r Result[T, E], f (E) -&gt; Result[T, F]) Result[T, F]</code></dd>
<dt id="fn-recover"><code>recover</code></dt>
<dd>Turns an Err into a value with a function.<br><code class="sig">recover[T, E](r Result[T, E], f (E) -&gt; T) Result[T, E]</code></dd>
<dt id="fn-ensure"><code>ensure</code></dt>
<dd>Ok(()) when a condition holds, else Err(e).<br><code class="sig">ensure[E](ok Bool, e E) Result[Unit, E]</code></dd>
<dt id="fn-guard"><code>guard</code></dt>
<dd>Ok(()) when a condition holds, else an Err with the code MISSING.<br><code class="sig">guard[E](ok Bool) Result[Unit, E]</code></dd>
<dt id="fn-fail"><code>fail</code></dt>
<dd>An Err with a code and optional message.<br><code class="sig">fail[T](code Int) Result[T, Error]
fail[T](code Int, message String) Result[T, Error]</code></dd>
<dt id="fn-traverse"><code>traverse</code></dt>
<dd>Applies a Result-returning function to each item; stops at the first Err.<br><code class="sig">traverse[T, U, E](f (T) -&gt; Result[U, E], xs Seq[T]) Result[List[U], E]</code></dd>
<dt id="fn-sequence"><code>sequence</code></dt>
<dd>Turns Results into one Result of a List; stops at the first Err.<br><code class="sig">sequence[T, E](rs Seq[Result[T, E]]) Result[List[T], E]</code></dd>
<dt id="fn-validate"><code>validate</code></dt>
<dd>Like <code>traverse</code>, but collects every error.<br><code class="sig">validate[T, U, E](f (T) -&gt; Result[U, E], xs Seq[T]) Result[List[U], List[E]]</code></dd>
<dt id="fn-collect_errors"><code>collect_errors</code></dt>
<dd>Ok of all values, or Err of all errors.<br><code class="sig">collect_errors[T, E](rs Seq[Result[T, E]]) Result[List[T], List[E]]</code></dd>
<dt id="fn-partition_results"><code>partition_results</code></dt>
<dd>Splits Results into the values and the errors.<br><code class="sig">partition_results[T, E](rs Seq[Result[T, E]]) (List[T], List[E])</code></dd>
<dt id="fn-map_all"><code>map_all</code></dt>
<dd>Combines two to six Results with a function, collecting all errors.<br><code class="sig">map_all[A, B, R, E](f (A, B) -&gt; R, a Result[A, E], b Result[B, E]) Result[R, List[E]]
map_all[A, B, C, R, E](f (A, B, C) -&gt; R, a Result[A, E], b Result[B, E], c Result[C, E]) Result[R, List[E]]
map_all[A, B, C, D, R, E](f (A, B, C, D) -&gt; R, a Result[A, E], b Result[B, E], c Result[C, E], d Result[D, E]) Result[R, List[E]]
map_all[A, B, C, D, E, R, E](f (A, B, C, D, E) -&gt; R, a Result[A, E], b Result[B, E], c Result[C, E], d Result[D, E], e Result[E, E]) Result[R, List[E]]
map_all[A, B, C, D, E, F, R, E](f (A, B, C, D, E, F) -&gt; R, a Result[A, E], b Result[B, E], c Result[C, E], d Result[D, E], e Result[E, E], f Result[F, E]) Result[R, List[E]]
map_all[A, B, R, X](rs (Result[A, X], Result[B, X]), f (A, B) -&gt; R) Result[R, List[X]]
map_all[A, B, C, R, X](rs (Result[A, X], Result[B, X], Result[C, X]), f (A, B, C) -&gt; R) Result[R, List[X]]
map_all[A, B, C, D, R, X](rs (Result[A, X], Result[B, X], Result[C, X], Result[D, X]), f (A, B, C, D) -&gt; R) Result[R, List[X]]
map_all[A, B, C, D, E, R, X](rs (Result[A, X], Result[B, X], Result[C, X], Result[D, X], Result[E, X]), f (A, B, C, D, E) -&gt; R) Result[R, List[X]]
map_all[A, B, C, D, E, F, R, X](rs (Result[A, X], Result[B, X], Result[C, X], Result[D, X], Result[E, X], Result[F, X]), f (A, B, C, D, E, F) -&gt; R) Result[R, List[X]]</code></dd>
<dt id="fn-par_map_all"><code>par_map_all</code></dt>
<dd>Like <code>map_all</code>, with slow checks run in parallel.<br><code class="sig">par_map_all[A, B, R, X](f (A, B) -&gt; R, c1 () -&gt; Result[A, X], c2 () -&gt; Result[B, X]) Result[R, List[X]]
par_map_all[A, B, C, R, X](f (A, B, C) -&gt; R, c1 () -&gt; Result[A, X], c2 () -&gt; Result[B, X], c3 () -&gt; Result[C, X]) Result[R, List[X]]
par_map_all[A, B, C, D, R, X](f (A, B, C, D) -&gt; R, c1 () -&gt; Result[A, X], c2 () -&gt; Result[B, X], c3 () -&gt; Result[C, X], c4 () -&gt; Result[D, X]) Result[R, List[X]]
par_map_all[A, B, C, D, E, R, X](f (A, B, C, D, E) -&gt; R, c1 () -&gt; Result[A, X], c2 () -&gt; Result[B, X], c3 () -&gt; Result[C, X], c4 () -&gt; Result[D, X], c5 () -&gt; Result[E, X]) Result[R, List[X]]
par_map_all[A, B, C, D, E, F, R, X](f (A, B, C, D, E, F) -&gt; R, c1 () -&gt; Result[A, X], c2 () -&gt; Result[B, X], c3 () -&gt; Result[C, X], c4 () -&gt; Result[D, X], c5 () -&gt; Result[E, X], c6 () -&gt; Result[F, X]) Result[R, List[X]]</code></dd>
<dt id="fn-non_empty"><code>non_empty</code></dt>
<dd>Ok of a NonEmpty from a List, or an Err if it is empty.<br><code class="sig">non_empty[T](xs List[T]) Result[NonEmpty[T], Error]</code></dd>
</dl>

## Functions and combinators {#f-functions-and-combinators}

Spec <a href="spec.html#s23">§23</a>.

<dl class="ref">
<dt id="fn-identity"><code>identity</code></dt>
<dd>Gives its argument back.<br><code class="sig">identity[T](x T) T</code></dd>
<dt id="fn-const"><code>const</code></dt>
<dd>A function that always gives one value.<br><code class="sig">const[A, B](x A) (B) -&gt; A</code></dd>
<dt id="fn-flip"><code>flip</code></dt>
<dd>Swaps the order of a two-parameter function's arguments.<br><code class="sig">flip[A, B, R](f (A, B) -&gt; R) (B, A) -&gt; R</code></dd>
<dt id="fn-tap"><code>tap</code></dt>
<dd>Calls a function on a value for its effect and gives the value back.<br><code class="sig">tap[T, U](x T, f (T) -&gt; U) T</code></dd>
<dt id="fn-fold_all"><code>fold_all</code></dt>
<dd>Combines the items of a collection with their Monoid.<br><code class="sig">fold_all[T Monoid](xs Seq[T]) T</code></dd>
<dt id="fn-fold_map"><code>fold_map</code></dt>
<dd>Maps each item to a Monoid value, then combines them.<br><code class="sig">fold_map[T, M Monoid](f (T) -&gt; M, xs Seq[T]) M</code></dd>
<dt id="fn-hash"><code>hash</code></dt>
<dd>A hash code for a value.<br><code class="sig">hash[T](x T) Int</code></dd>
<dt id="fn-index"><code>index</code></dt>
<dd>The position of an enum case in its declaration.<br><code class="sig">index(x Enum) Int</code></dd>
<dt id="fn-secret_eq"><code>secret_eq</code></dt>
<dd>Compares two secrets in constant time.<br><code class="sig">secret_eq[T](a Secret[T], b Secret[T]) Bool</code></dd>
</dl>

## Concurrency {#f-concurrency}

Spec <a href="spec.html#s17">§17</a>.

<dl class="ref">
<dt id="fn-swap"><code>swap</code></dt>
<dd>Changes an Atom's value with a function and gives the new value.<br><code class="sig">swap[T](a Atom[T], f (T) -&gt; T) T</code></dd>
<dt id="fn-reset"><code>reset</code></dt>
<dd>Sets an Atom's value.<br><code class="sig">reset[T](a Atom[T], v T) T</code></dd>
<dt id="fn-swap_vals"><code>swap_vals</code></dt>
<dd>Like <code>swap</code>, giving (old, new).<br><code class="sig">swap_vals[T](a Atom[T], f (T) -&gt; T) (T, T)</code></dd>
<dt id="fn-reset_vals"><code>reset_vals</code></dt>
<dd>Like <code>reset</code>, giving (old, new).<br><code class="sig">reset_vals[T](a Atom[T], v T) (T, T)</code></dd>
<dt id="fn-try_swap"><code>try_swap</code></dt>
<dd>Like <code>swap</code>, with an Err instead of an abort.<br><code class="sig">try_swap[T](a Atom[T], f (T) -&gt; T) Result[T, Error]</code></dd>
<dt id="fn-try_reset"><code>try_reset</code></dt>
<dd>Like <code>reset</code>, with an Err instead of an abort.<br><code class="sig">try_reset[T](a Atom[T], v T) Result[T, Error]</code></dd>
<dt id="fn-read"><code>read</code></dt>
<dd>Reads the next value from a channel, or waits for a future.<br><code class="sig">read[T](c ChanR[T]) Result[T, Error]
read[T](f FutureR[T]) T</code></dd>
<dt id="fn-write"><code>write</code></dt>
<dd>Sends a value on a channel.<br><code class="sig">write[T, E](w ChanW[T], x T) Result[Unit, E]</code></dd>
<dt id="fn-close"><code>close</code></dt>
<dd>Closes a channel end, file or socket.<br><code class="sig">close[T](x T) Unit</code></dd>
<dt id="fn-resolve"><code>resolve</code></dt>
<dd>Supplies a future's value.<br><code class="sig">resolve[T](w FutureW[T], v T) Unit</code></dd>
<dt id="fn-reject"><code>reject</code></dt>
<dd>Supplies a future's error.<br><code class="sig">reject[T](w FutureW[T], e Error) Unit</code></dd>
<dt id="fn-cancel"><code>cancel</code></dt>
<dd>Sets a cancel token.<br><code class="sig">cancel(c Cancel) Unit</code></dd>
<dt id="fn-after"><code>after</code></dt>
<dd>A timer that fires once after a duration.<br><code class="sig">after(d Duration) Timer</code></dd>
<dt id="fn-arm"><code>arm</code></dt>
<dd>Starts a timer.<br><code class="sig">arm(t Timer, d Duration) Unit</code></dd>
<dt id="fn-arm_every"><code>arm_every</code></dt>
<dd>Starts a timer that fires repeatedly.<br><code class="sig">arm_every(t Timer, d Duration) Unit</code></dd>
<dt id="fn-disarm"><code>disarm</code></dt>
<dd>Stops a timer.<br><code class="sig">disarm(t Timer) Unit</code></dd>
<dt id="fn-sleep"><code>sleep</code></dt>
<dd>Waits for a duration.<br><code class="sig">sleep(d Duration) Unit</code></dd>
<dt id="fn-race"><code>race</code></dt>
<dd>Runs two functions; gives the first result and cancels the other.<br><code class="sig">race[T](f (Cancel) -&gt; T, g (Cancel) -&gt; T) T</code></dd>
<dt id="fn-with_timeout"><code>with_timeout</code></dt>
<dd>Gives a function's result, or Err(TIMED_OUT) if time runs out.<br><code class="sig">with_timeout[T](d Duration, f (Cancel) -&gt; Result[T, Error]) Result[T, Error]</code></dd>
<dt id="fn-par_map"><code>par_map</code></dt>
<dd>Maps in parallel, at most <code>limit</code> at once, keeping order.<br><code class="sig">par_map[T, U](f (T) -&gt; U, xs Seq[T], limit: Int) List[U]</code></dd>
<dt id="fn-par_traverse"><code>par_traverse</code></dt>
<dd>Like <code>par_map</code> for Result-returning functions.<br><code class="sig">par_traverse[T, U, E](f (T) -&gt; Result[U, E], xs Seq[T], limit: Int) Result[List[U], E]</code></dd>
<dt id="fn-retry"><code>retry</code></dt>
<dd>Calls a function up to n times, waiting between tries.<br><code class="sig">retry[T, E](n Int, delay Duration, f () -&gt; Result[T, E]) Result[T, E]</code></dd>
</dl>

## Time {#f-time}

Spec <a href="spec.html#s19e">§19E</a>.

<dl class="ref">
<dt id="fn-now"><code>now</code></dt>
<dd>The current time as a Duration since the epoch.<br><code class="sig">now() Duration</code></dd>
<dt id="fn-monotonic"><code>monotonic</code></dt>
<dd>A steadily increasing clock, for measuring.<br><code class="sig">monotonic() Duration</code></dd>
<dt id="fn-millis"><code>millis</code></dt>
<dd>A Duration in milliseconds.<br><code class="sig">millis(d Duration) Int</code></dd>
<dt id="fn-nanos"><code>nanos</code></dt>
<dd>A Duration in nanoseconds.<br><code class="sig">nanos(d Duration) Int</code></dd>
<dt id="fn-seconds"><code>seconds</code></dt>
<dd>A Duration in seconds.<br><code class="sig">seconds(d Duration) Double</code></dd>
<dt id="fn-weekday"><code>weekday</code></dt>
<dd>1 for Monday to 7 for Sunday.<br><code class="sig">weekday(t DateTime) Int</code></dd>
<dt id="fn-day_of_year"><code>day_of_year</code></dt>
<dd>1 to 366.<br><code class="sig">day_of_year(t DateTime) Int</code></dd>
<dt id="fn-days_in_month"><code>days_in_month</code></dt>
<dd>Days in a month, leap years included.<br><code class="sig">days_in_month(y Int, m Int) Int</code></dd>
<dt id="fn-iso"><code>iso</code></dt>
<dd>A DateTime as ISO 8601 text.<br><code class="sig">iso(t DateTime) String</code></dd>
<dt id="fn-format_time"><code>format_time</code></dt>
<dd>A DateTime as text, from a pattern.<br><code class="sig">format_time(t DateTime, fmt String) String
format_time(t DateTime, fmt String, loc Locale) String</code></dd>
<dt id="fn-parse_iso"><code>parse_iso</code></dt>
<dd>Reads ISO 8601 text.<br><code class="sig">parse_iso[E](s String) Result[DateTime, E]</code></dd>
<dt id="fn-parse_time"><code>parse_time</code></dt>
<dd>Reads text with a pattern.<br><code class="sig">parse_time[E](s String, fmt String) Result[DateTime, E]
parse_time[E](s String, fmt String, loc Locale) Result[DateTime, E]</code></dd>
<dt id="fn-to_instant"><code>to_instant</code></dt>
<dd>A DateTime as a Duration since the epoch.<br><code class="sig">to_instant[E](t DateTime) Result[Duration, E]
to_instant[E](t DateTime, zone String) Result[Duration, E]</code></dd>
<dt id="fn-to_utc"><code>to_utc</code></dt>
<dd>A Duration as a UTC DateTime.<br><code class="sig">to_utc(d Duration) DateTime</code></dd>
<dt id="fn-to_local"><code>to_local</code></dt>
<dd>A Duration as a DateTime in the system's zone.<br><code class="sig">to_local(d Duration) DateTime</code></dd>
<dt id="fn-to_zone"><code>to_zone</code></dt>
<dd>A Duration as a DateTime in a named zone.<br><code class="sig">to_zone[E](d Duration, zone String) Result[DateTime, E]</code></dd>
</dl>

## Files and paths {#f-files-and-paths}

Spec <a href="spec.html#s19c">§19C</a>.

<dl class="ref">
<dt id="fn-read_file"><code>read_file</code></dt>
<dd>A file's text.<br><code class="sig">read_file[E](p String) Result[String, E]</code></dd>
<dt id="fn-write_file"><code>write_file</code></dt>
<dd>Writes text to a file.<br><code class="sig">write_file[E](p String, s String) Result[Unit, E]</code></dd>
<dt id="fn-make_dir"><code>make_dir</code></dt>
<dd>Creates a directory.<br><code class="sig">make_dir[E](p String) Result[Unit, E]</code></dd>
<dt id="fn-remove_file"><code>remove_file</code></dt>
<dd>Deletes a file.<br><code class="sig">remove_file[E](p String) Result[Unit, E]</code></dd>
<dt id="fn-remove_dir"><code>remove_dir</code></dt>
<dd>Deletes a directory.<br><code class="sig">remove_dir[E](p String) Result[Unit, E]</code></dd>
<dt id="fn-rename_path"><code>rename_path</code></dt>
<dd>Renames a file or directory.<br><code class="sig">rename_path[E](a String, b String) Result[Unit, E]</code></dd>
<dt id="fn-list_dir"><code>list_dir</code></dt>
<dd>The sorted names in a directory.<br><code class="sig">list_dir[E](p String) Result[Array[String], E]</code></dd>
<dt id="fn-path_exists"><code>path_exists</code></dt>
<dd>Ok(true) or Ok(false).<br><code class="sig">path_exists[E](p String) Result[Bool, E]</code></dd>
<dt id="fn-file_info"><code>file_info</code></dt>
<dd>A file's kind and size.<br><code class="sig">file_info[E](p String) Result[FileInfo, E]</code></dd>
<dt id="fn-path_join"><code>path_join</code></dt>
<dd>Joins path pieces.<br><code class="sig">path_join(base String, rest String) String</code></dd>
<dt id="fn-path_name"><code>path_name</code></dt>
<dd>The last piece of a path.<br><code class="sig">path_name(p String) String</code></dd>
<dt id="fn-path_parent"><code>path_parent</code></dt>
<dd>A path without its last piece.<br><code class="sig">path_parent(p String) String</code></dd>
<dt id="fn-path_stem"><code>path_stem</code></dt>
<dd>The file name without its extension.<br><code class="sig">path_stem(p String) String</code></dd>
<dt id="fn-path_ext"><code>path_ext</code></dt>
<dd>The file name's extension.<br><code class="sig">path_ext(p String) String</code></dd>
<dt id="fn-cwd"><code>cwd</code></dt>
<dd>The current directory.<br><code class="sig">cwd() String</code></dd>
<dt id="fn-temp_dir"><code>temp_dir</code></dt>
<dd>The temporary directory.<br><code class="sig">temp_dir() String</code></dd>
<dt id="fn-home_dir"><code>home_dir</code></dt>
<dd>The user's home directory.<br><code class="sig">home_dir[E]() Result[String, E]</code></dd>
</dl>

## Input and output {#f-input-and-output}

Spec <a href="spec.html#s19b">§19B</a>.

<dl class="ref">
<dt id="fn-println"><code>println</code></dt>
<dd>Prints a value and a newline.<br><code class="sig">println() Unit
println[T](x T) Unit
println[T](out Io, x T) Unit</code></dd>
<dt id="fn-print"><code>print</code></dt>
<dd>Prints a value.<br><code class="sig">print[T](x T) Unit
print[T](out Io, x T) Unit</code></dd>
<dt id="fn-eprintln"><code>eprintln</code></dt>
<dd>Prints a value and a newline on standard error.<br><code class="sig">eprintln() Unit
eprintln[T](x T) Unit
eprintln[T](out Io, x T) Unit</code></dd>
<dt id="fn-eprint"><code>eprint</code></dt>
<dd>Prints a value on standard error.<br><code class="sig">eprint[T](x T) Unit
eprint[T](out Io, x T) Unit</code></dd>
<dt id="fn-flush"><code>flush</code></dt>
<dd>Sends buffered output on.<br><code class="sig">flush() Unit
flush(out Io) Unit</code></dd>
<dt id="fn-read_line"><code>read_line</code></dt>
<dd>The next line of input; an Err at the end.<br><code class="sig">read_line[E]() Result[String, E]
read_line[E](src Io) Result[String, E]</code></dd>
<dt id="fn-read_all"><code>read_all</code></dt>
<dd>All the rest of the input.<br><code class="sig">read_all[E]() Result[String, E]
read_all[E](src Io) Result[String, E]</code></dd>
<dt id="fn-stdin_lines"><code>stdin_lines</code></dt>
<dd>The lines of standard input, as a stream.<br><code class="sig">stdin_lines() Stream[String]</code></dd>
<dt id="fn-lines"><code>lines</code></dt>
<dd>The lines of a socket or file, as a stream.<br><code class="sig">lines(src Io) Stream[String]</code></dd>
<dt id="fn-read_bytes"><code>read_bytes</code></dt>
<dd>Up to n bytes.<br><code class="sig">read_bytes[E](src Io, n Int) Result[Array[Byte], E]</code></dd>
<dt id="fn-write_bytes"><code>write_bytes</code></dt>
<dd>Writes bytes.<br><code class="sig">write_bytes[E](out Io, data Array[Byte]) Result[Unit, E]</code></dd>
<dt id="fn-with_stdin"><code>with_stdin</code></dt>
<dd>Runs a function with given text as standard input.<br><code class="sig">with_stdin[T](text String, f () -&gt; T) T</code></dd>
<dt id="fn-raw_terminal"><code>raw_terminal</code></dt>
<dd>Puts the terminal in raw mode.<br><code class="sig">raw_terminal[E]() Result[Terminal, E]</code></dd>
<dt id="fn-read_key"><code>read_key</code></dt>
<dd>The next key pressed.<br><code class="sig">read_key[E](t Terminal) Result[Key, E]</code></dd>
</dl>

## Sockets and programs {#f-sockets-and-programs}

Spec <a href="spec.html#s19c">§19C</a>.

<dl class="ref">
<dt id="fn-listen"><code>listen</code></dt>
<dd>Starts listening on a port.<br><code class="sig">listen[E](port Int) Result[Listener, E]</code></dd>
<dt id="fn-accept"><code>accept</code></dt>
<dd>Waits for a connection.<br><code class="sig">accept[E](l Listener) Result[Io, E]</code></dd>
<dt id="fn-connect"><code>connect</code></dt>
<dd>Opens a connection.<br><code class="sig">connect[E](host String, port Int) Result[Io, E]</code></dd>
<dt id="fn-listen_tls"><code>listen_tls</code></dt>
<dd>Like <code>listen</code>, with TLS.<br><code class="sig">listen_tls[E](port Int, cert String, key String) Result[Listener, E]</code></dd>
<dt id="fn-connect_tls"><code>connect_tls</code></dt>
<dd>Like <code>connect</code>, with TLS.<br><code class="sig">connect_tls[E](host String, port Int) Result[Io, E]</code></dd>
<dt id="fn-port_of"><code>port_of</code></dt>
<dd>The port a listener or socket uses.<br><code class="sig">port_of(l Listener) Int
port_of(u Udp) Int</code></dd>
<dt id="fn-bind_udp"><code>bind_udp</code></dt>
<dd>Opens a UDP socket.<br><code class="sig">bind_udp[E](port Int) Result[Udp, E]</code></dd>
<dt id="fn-send_to"><code>send_to</code></dt>
<dd>Sends one UDP datagram.<br><code class="sig">send_to[E](u Udp, host String, port Int, data String) Result[Unit, E]
send_to[E](u Udp, host String, port Int, data Array[Byte]) Result[Unit, E]</code></dd>
<dt id="fn-receive"><code>receive</code></dt>
<dd>Waits for a UDP datagram.<br><code class="sig">receive[E](u Udp) Result[Packet, E]</code></dd>
<dt id="fn-spawn"><code>spawn</code></dt>
<dd>Starts another program.<br><code class="sig">spawn[E](program String) Result[Child, E]
spawn[E](program String, args List[String]) Result[Child, E]</code></dd>
<dt id="fn-wait_child"><code>wait_child</code></dt>
<dd>Waits for it to end.<br><code class="sig">wait_child[E](c Child) Result[Int, E]</code></dd>
<dt id="fn-kill_child"><code>kill_child</code></dt>
<dd>Stops it.<br><code class="sig">kill_child(c Child) Unit</code></dd>
<dt id="fn-run_command"><code>run_command</code></dt>
<dd>Runs another program to the end and gives its output.<br><code class="sig">run_command[E](program String) Result[Output, E]
run_command[E](program String, args List[String]) Result[Output, E]</code></dd>
<dt id="fn-hostname"><code>hostname</code></dt>
<dd>This computer's name.<br><code class="sig">hostname() String</code></dd>
<dt id="fn-os_name"><code>os_name</code></dt>
<dd>The operating system's name.<br><code class="sig">os_name() String</code></dd>
<dt id="fn-wire_pair"><code>wire_pair</code></dt>
<dd>Two connected session endpoints.<br><code class="sig">wire_pair() (Wire, Wire)</code></dd>
<dt id="fn-wire_send"><code>wire_send</code></dt>
<dd>Sends a value on a session endpoint.<br><code class="sig">wire_send[T, E](w Wire, x T) Result[Unit, E]</code></dd>
<dt id="fn-wire_recv"><code>wire_recv</code></dt>
<dd>Receives a value on a session endpoint.<br><code class="sig">wire_recv[T, E](w Wire) Result[T, E]</code></dd>
<dt id="fn-wire_close"><code>wire_close</code></dt>
<dd>Closes a session endpoint.<br><code class="sig">wire_close(w Wire) Unit</code></dd>
</dl>

## Testing and debugging {#f-testing-and-debugging}

Spec <a href="spec.html#s22">§22</a>.

<dl class="ref">
<dt id="fn-assert"><code>assert</code></dt>
<dd>Aborts if a condition is false.<br><code class="sig">assert(ok Bool) Unit
assert(ok Bool, message String) Unit</code></dd>
<dt id="fn-assert_eq"><code>assert_eq</code></dt>
<dd>Aborts if two values differ.<br><code class="sig">assert_eq[T](a T, b T) Unit</code></dd>
<dt id="fn-assert_ne"><code>assert_ne</code></dt>
<dd>Aborts if two values are equal.<br><code class="sig">assert_ne[T](a T, b T) Unit</code></dd>
<dt id="fn-debug_assert"><code>debug_assert</code></dt>
<dd>An <code>assert</code> that a release build leaves out.<br><code class="sig">debug_assert(ok Bool) Unit</code></dd>
<dt id="fn-dbg"><code>dbg</code></dt>
<dd>Prints a value and where it came from, and gives the value back.<br><code class="sig">dbg[T](x T) T</code></dd>
<dt id="fn-trace"><code>trace</code></dt>
<dd>Prints a message with its place.<br><code class="sig">trace[T](x T) Unit</code></dd>
<dt id="fn-gen_int"><code>gen_int</code></dt>
<dd>A generated Int between two bounds.<br><code class="sig">gen_int[T](g Gen, lo T, hi T) T</code></dd>
<dt id="fn-gen_bool"><code>gen_bool</code></dt>
<dd>A generated Bool.<br><code class="sig">gen_bool(g Gen) Bool</code></dd>
<dt id="fn-gen_pick"><code>gen_pick</code></dt>
<dd>A generated pick from a List.<br><code class="sig">gen_pick[T](g Gen, xs List[T]) T</code></dd>
</dl>

