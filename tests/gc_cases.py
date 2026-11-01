"""moxie/gc cases: programs that rely on the collector's rules. Each is (name, source, expected output lines, expected exit)."""
CASES = [
("closures in a list, branches return different closures", '''
fn pick(flag: Bool, k: Int) (Int) -> Int:
  when flag:
    true -> fn (n): n + k
    false -> fn (n): n * k
fns = List(pick(true, 3), pick(false, 3))
println("${fns(0)(10)} ${fns(1)(10)}")
''', ["13 30"], 0),
("capturing closures stored in a Dict", '''
fn make(k: Int) (Int) -> Int:
  fn (n): n + k
table = Dict[String, (Int) -> Int]()
table(a) = make(1)
table(b) = make(10)
table(c) = make(100)
when table(b):
  Ok(f) -> println("${f(5)} ${len(table)}")
  Err(e) -> println("missing")
''', ["15 3"], 0),
("closure in a tuple field and in an Atom", '''
tuple Op:
  apply: (Int) -> Int
k = 7
op = Op(apply: fn (n): n * k)
a = Atom[(Int) -> Int](fn (n): n + k)
f = @a
println("${op.apply(6)} ${f(1)}")
''', ["42 8"], 0),
("collections grow past a hint", '''
d = Dict[String, Int][2]()
d(a) = 1
d(b) = 2
d(c) = 3
l = List[Int][2]()
l = l + 1
l = l + 2
l = l + 3
s = Set[Int][1]()
s = s + 1
s = s + 2
println("${len(d)} ${len(l)} ${len(s)}")
''', ["3 3 2"], 0),
("put returns the updated Dict", '''
d = Dict[String, Int]()
d2 = put(d, "z", 9)
d3 = put(d2, "y", 8)
println("${len(d)} ${len(d3)} ${d3("z").get_or(0)}")
''', ["0 2 9"], 0),
("variadic is a List", '''
fn total(base: Int, numbers: ...Int) Int:
  numbers |> to_stream() |> reduce(base, _1 + _2)
vs = List(10, 20, 30, 40, 50)
println("${total(100, 10, 20, 30)} ${total(100, ...vs)} ${total(100)}")
''', ["160 250 100"], 0),
("channel capacity from a variable, and unbounded", '''
n = 3
rx, tx = Chan[Int][n + 1]()
_ = write(tx, 1)
_ = write(tx, 2)
u, w = Chan[Int][#unbounded]()
for i in 1..=100:
  _ = write(w, i)
println("${read(rx).get_or(0)} ${read(u).get_or(0)}")
''', ["1 1"], 0),
("clone inside a loop", '''
fiber fn worker(id: Int, out: ChanW[Int]) Unit:
  _ = write(out, id * 10)
rx, tx = Chan[Int][8]()
for i in 1..=5:
  _ = run worker(i, clone(tx))
drop = move tx
total = Range(1..=5, 1) |> reduce(0, fn (acc, _): acc + read(rx).get_or(0))
println("$total")
''', ["150"], 0),
("a stream can be returned", '''
fn evens(xs: List[Int]) Stream[Int]:
  xs |> to_stream() |> filter(_ % 2 == 0)
for x in evens(List(1, 2, 3, 4, 5, 6)):
  println("$x")
''', ["2", "4", "6"], 0),
("string slice can be returned", '''
fn tail(s: String) String:
  s(2..)
println(tail("Python"))
''', ["thon"], 0),
("recursive value stored in a Dict and an Atom", '''
enum Tree:
  Leaf,
  Node(left: Tree, value: Int, right: Tree)
fn size(t: Tree) Int:
  when t:
    Leaf -> 0
    Node(l, _, r) -> size(l) + 1 + size(r)
t = Tree.Node(left: Node(left: Leaf, value: 1, right: Leaf), value: 2, right: Leaf)
d = Dict[String, Tree]()
d(t1) = t
a = Atom[Tree](t)
println("${size(d("t1").get_or(Leaf))} ${size(@a)}")
''', ["2 2"], 0),
("dead names hold nothing: a big list summed", '''
xs: List[Int] = Range(1..=100000, 1) |> to_stream() |> collect()
total = xs |> to_stream() |> reduce(0, _1 + _2)
println("$total")
''', ["5000050000"], 0),
("the Atom that keeps everything", '''
log = Atom[List[String]](List())
fn note(msg: String) Unit:
  _ = swap(log, _ + msg)
for i in 1..=50:
  note("m$i")
println("${len(@log)}")
''', ["50"], 0),
("copy does not exist", '''
s = "Python"
t = copy(s(2..))
println(t)
''', [], 1),
]
