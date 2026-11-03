"""Cases for the stream helpers, clause guards, and `tailrec`. They run in both dialects."""
CASES = [
("distinct", 'xs = List(3, 1, 3, 2, 1, 4)\nprintln("${xs |> to_stream() |> distinct() |> collect()}")\n', ["List(3, 1, 2, 4)"], 0),
("intersperse", 'println("${List("a", "b", "c") |> to_stream() |> intersperse("-") |> collect()}")\n', ['List("a", "-", "b", "-", "c")'], 0),
("flatten", 'println("${List(List(1, 2), List(3), List(4, 5)) |> to_stream() |> flatten() |> collect()}")\n', ["List(1, 2, 3, 4, 5)"], 0),
("cycle", 'println("${List(1, 2, 3) |> to_stream() |> cycle() |> take(7) |> collect()}")\n', ["List(1, 2, 3, 1, 2, 3, 1)"], 0),
("zip_with", 'println("${zip_with(_1 + _2, List(1, 2, 3), List(10, 20, 30)) |> collect()}")\n', ["List(11, 22, 33)"], 0),
("reduce_right", 'println("${List(1, 2, 3, 4) |> to_stream() |> reduce_right(0, fn (x, acc): x - acc)}")\n', ["-2"], 0),
("min_by and max_by", 'ws = List("pear", "fig", "banana")\nprintln("${ws |> to_stream() |> min_by(len)} ${ws |> to_stream() |> max_by(len)}")\n', ['Ok("fig") Ok("banana")'], 0),
("span", '(a, b) = List(1, 2, 5, 1) |> to_stream() |> span(_ < 3)\nprintln("$a $b")\n', ["List(1, 2) List(5, 1)"], 0),
("split_at", '(c, d) = List(1, 2, 3, 4) |> to_stream() |> split_at(1)\nprintln("$c $d")\n', ["List(1) List(2, 3, 4)"], 0),
("guards on function clauses", '''
fn classify(n: Int) String if n < 0: "neg"
fn classify(n) if n == 0: "zero"
fn classify(n): "pos"
println("${classify(-1)} ${classify(0)} ${classify(5)}")
''', ["neg zero pos"], 0),
("tailrec accepts a tail call", '''
tailrec fn count(0, acc: Int) Int: acc
tailrec fn count(n, acc): count(n - 1, acc + n)
println("${count(100, 0)}")
''', ["5050"], 0),
("tailrec rejects a call that is not a tail call", '''
tailrec fn fact(0) Int: 1
tailrec fn fact(n): n * fact(n - 1)
println("${fact(5)}")
''', [], 2),
("an abort in any fiber ends the program", '''
fiber fn bad(tx: ChanW[Int]) Unit:
  xs = List(1, 2, 3)
  _ = write(tx, xs(7))
rx, tx = Chan[Int][1]()
_ = run bad(tx)
sleep(1s)
println("still here")
''', [], 1),
("NonEmpty", '''
when non_empty(List(3, 1, 2)):
  Ok(x) -> println("${x.to_list()} ${x.len()} ${x.min()} ${x.max()} ${x.reduce1(_1 + _2)} ${x.map(_ * 2)}")
  Err(e) -> println("empty")
println("${non_empty(List())}")
''', ["List(3, 1, 2) 3 1 3 6 NonEmpty(head: 6, tail: List(2, 4))", 'Err(Error(code: 4, message: "empty"))'], 0),
("curry for any arity", '''
fn add7(a: Int, b: Int, c: Int, d: Int, e: Int, f: Int, g: Int) Int: a + b + c + d + e + f + g
println("${curry(add7)(1)(2)(3)(4)(5)(6)(7)}")
println("${(curry(fn (a: Int, b: Int): a * b)(6))(7)}")
''', ["28", "42"], 0),
]
