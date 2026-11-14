"""Cases for the stream helpers, clause guards, and `tailrec`. They run in both dialects."""
CASES = [
("distinct", 'xs = List(3, 1, 3, 2, 1, 4)\nprintln("${xs |> to_stream() |> distinct() |> collect()}")\n', ["List(3, 1, 2, 4)"], 0),
("intersperse", 'println("${List("a", "b", "c") |> to_stream() |> intersperse("-") |> collect()}")\n', ['List("a", "-", "b", "-", "c")'], 0),
("flatten", 'println("${List(List(1, 2), List(3), List(4, 5)) |> to_stream() |> flatten() |> collect()}")\n', ["List(1, 2, 3, 4, 5)"], 0),
("cycle", 'println("${List(1, 2, 3) |> to_stream() |> cycle() |> take(7) |> collect()}")\n', ["List(1, 2, 3, 1, 2, 3, 1)"], 0),
("zip_with", 'println("${zip_with(_1 + _2, List(1, 2, 3), List(10, 20, 30)) |> collect()}")\n', ["List(11, 22, 33)"], 0),
("reduce_right", 'println("${List(1, 2, 3, 4) |> to_stream() |> reduce_right(0, (x, acc) -> x - acc)}")\n', ["-2"], 0),
("min_by and max_by", 'ws = List("pear", "fig", "banana")\nprintln("${ws |> to_stream() |> min_by(len)} ${ws |> to_stream() |> max_by(len)}")\n', ['Ok("fig") Ok("banana")'], 0),
("span", '(a, b) = List(1, 2, 5, 1) |> to_stream() |> span(_ < 3)\nprintln("$a $b")\n', ["List(1, 2) List(5, 1)"], 0),
("split_at", '(c, d) = List(1, 2, 3, 4) |> to_stream() |> split_at(1)\nprintln("$c $d")\n', ["List(1) List(2, 3, 4)"], 0),
("guards on function clauses", '''
fn classify(n Int) String if n < 0 = "neg"
fn classify(n) if n == 0 = "zero"
fn classify(n) = "pos"
println("${classify(-1)} ${classify(0)} ${classify(5)}")
''', ["neg zero pos"], 0),
("tailrec accepts a tail call", '''
tailrec fn count(0, acc Int) Int = acc
tailrec fn count(n, acc) = count(n - 1, acc + n)
println("${count(100, 0)}")
''', ["5050"], 0),
("tailrec rejects a call that is not a tail call", '''
tailrec fn fact(0) Int = 1
tailrec fn fact(n) = n * fact(n - 1)
println("${fact(5)}")
''', [], 2),
("an abort in any fiber ends the program", '''
fiber fn bad(tx ChanW[Int]) Unit
  xs = List(1, 2, 3)
  _ = write(tx, xs(len(xs) + 4))
rx, tx = Chan[Int][1]()
_ = run bad(tx)
sleep(1s)
println("still here")
''', [], 1),
("NonEmpty", '''
when non_empty(List(3, 1, 2))
  Ok(x) -> println("${x.to_list()} ${x.len()} ${x.min()} ${x.max()} ${x.reduce1(_1 + _2)} ${x.map(_ * 2)}")
  Err(e) -> println("empty")
println("${non_empty(List())}")
''', ["List(3, 1, 2) 3 1 3 6 NonEmpty(head: 6, tail: List(2, 4))", 'Err(Error(code: 4, message: "empty"))'], 0),
("curry for any arity", '''
fn add7(a Int, b Int, c Int, d Int, e Int, f Int, g Int) Int = a + b + c + d + e + f + g
println("${curry(add7)(1)(2)(3)(4)(5)(6)(7)}")
println("${(curry((a Int, b Int) -> a * b)(6))(7)}")
''', ["28", "42"], 0),
("uncurry for any arity", '''
fn add(a Int, b Int) Int = a + b
fn add4(a Int, b Int, c Int, d Int) Int = a + b + c + d
sums = zip_with(uncurry[2](curry(add)), List(1, 2, 3), List(10, 20, 30)) |> collect()
println("$sums")
println("${uncurry[4](curry(add4))(1, 2, 3, 4)}")
''', ["List(11, 22, 33)", "10"], 0),
("uncurry with the wrong argument count is a compile error", '''
fn add(a Int, b Int) Int = a + b
println("${uncurry[2](curry(add))(1)}")
''', [], 2),
("uncurry with the wrong argument count aborts when the compiler cannot see it", '''
fn add(a Int, b Int) Int = a + b
h = uncurry[2](curry(add))
println("${h(1)}")
''', [], 1),
("curry gives one argument at a time", '''
fn add(a Int, b Int) Int = a + b
println("${curry(add)(1, 2)}")
''', [], 2),
("curry of a one-parameter function is a compile error", '''
fn inc(a Int) Int = a + 1
f = curry(inc)
''', [], 2),
("uncurry needs a constant count of two or more", '''
fn add(a Int, b Int) Int = a + b
f = uncurry[1](curry(add))
''', [], 2),
("a constant failing requires is a compile error", '''
fn half(n Int) Int
  requires n > 0
  n / 2
println(half(0))
''', [], 2),
("a requires that holds is fine, and a variable argument is checked when it runs", '''
fn half(n Int) Int
  requires n > 0
  n / 2
x = 0
println(half(8))
println(half(x))
''', ["4"], 1),
("binary patterns read fields left to right", '''
fn describe(packet Array[Byte]) String
  when packet
    Bin(0xCA, version: bits(4), kind: bits(4), size: u16be, body: bytes(size), rest: bytes) -> "v$version k$kind size $size body ${len(body)} rest ${len(rest)}"
    Bin(a: u8, b: i16le) -> "short $a $b"
    _ -> "no match"
println(describe(b"\\xCA\\x21\\x00\\x02hiXYZ"))
println(describe(b"\\xCA\\x21\\x00\\x09hi"))
println(describe(b"\\x07\\xFE\\xFF"))
println(describe(b"\\x07"))
''', ["v2 k1 size 2 body 2 rest 3", "no match", "short 7 -2", "no match"], 0),
("binary patterns: a byte string literal, a guard, and is", '''
data = b"MZ\\x00\\x10\\x20\\x30"
when data
  Bin(b"MZ", n: u8, _: u8, rest: bytes) if n > 100 -> println("big")
  Bin(b"MZ", n: u8, _: u8, rest: bytes) -> println("MZ $n ${len(rest)}")
  _ -> println("other")
println(data is Bin(b"MZ", _: u8, _: u8, _: u16be))
println(data is Bin(b"PK", rest: bytes))
''', ["MZ 0 2", "true", "false"], 0),
("binary patterns: big and little endian, signed, 32 bits", '''
d = b"\\x01\\x02\\x03\\x04\\xFF\\xFF\\xFF\\xFE"
when d
  Bin(a: u32be, b: i32le) -> println("$a $b")
  _ -> println("no")
''', ["16909060 -16777217"], 0),
("a Bin pattern with bits that do not make whole bytes is a syntax error", '''
when b"ab"
  Bin(a: bits(3), b: u8) -> println("x")
  _ -> println("y")
''', [], 2),
("bytes with no size must be last", '''
when b"ab"
  Bin(a: bytes, b: u8) -> println("x")
  _ -> println("y")
''', [], 2),
("a Bin size must name an earlier field", '''
when b"ab"
  Bin(body: bytes(n), n: u8) -> println("x")
  _ -> println("y")
''', [], 2),
("Bin builds bytes and round-trips with the pattern", '''
p = Bin(0xCA, 2: bits(4), 1: bits(4), 2: u16be, b"hi": bytes(2), -2: i16le, b"XYZ": bytes)
println(p)
when p
  Bin(0xCA, v: bits(4), k: bits(4), n: u16be, body: bytes(n), d: i16le, rest: bytes) -> println("$v $k $n ${len(body)} $d ${len(rest)}")
  _ -> println("no")
''', ["Array(202, 33, 0, 2, 104, 105, 254, 255, 88, 89, 90)", "2 1 2 2 -2 3"], 0),
("Bin builds with a value out of range aborts", '''
n = 300
println(Bin(n: u8))
''', [], 1),
("Bin bits out of range aborts", '''
n = 16
println(Bin(n: bits(4), 0: bits(4)))
''', [], 1),
("Bin arms that cover every length need no wildcard", '''
fn f(x Array[Byte]) Int
  when x
    Bin() -> 0
    Bin(a: u8) -> 1
    Bin(a: u8, b: u8, rest: bytes) -> 2
println(f(b""))
println(f(b"a"))
println(f(b"abc"))
''', ["0", "1", "2"], 0),
("Bin arms that miss a length are a compile error", '''
fn f(x Array[Byte]) Int
  when x
    Bin(a: u8, b: u8) -> 2
    Bin(a: u8, b: u8, c: u8, rest: bytes) -> 3
println(f(b"ab"))
''', [], 2),
("a literal or a guarded Bin arm does not count toward coverage", '''
fn f(x Array[Byte]) Int
  when x
    Bin(0x01, rest: bytes) -> 1
    Bin(rest: bytes) if len(rest) > 3 -> 2
println(f(b"a"))
''', [], 2),
]
