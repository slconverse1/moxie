"""Parts of the prelude that are written in moxie itself (no compiler support needed)."""

SRC = '''
enum FileMode:
  ReadOnly
  Create
  Append
  ReadWrite

tuple FileInfo:
  kind: String
  size: Int

impl FileInfo:
  fn is_file(self) Bool: self.kind == "file"
  fn is_dir(self) Bool: self.kind == "dir"

tuple Packet:
  host: String
  port: Int
  data: Array[Byte]

tuple DateTime:
  year: Int
  month: Int
  day: Int
  hour: Int = 0
  minute: Int = 0
  second: Int = 0
  nano: Int = 0

enum Key:
  Typed(c: Char)
  Ctrl(c: Char)
  Alt(c: Char)
  Fn(n: Int)
  Enter
  Tab
  Backspace
  Delete
  Escape
  Up
  Down
  Left
  Right
  Home
  End
  PageUp
  PageDown
  Insert
  Other

tuple FileChange:
  path: String
  kind: Keyword

tuple Output:
  code: Int
  stdout: String
  stderr: String

interface Semigroup:
  fn combine(self, other: Self) Self

interface Monoid:
  Semigroup
  static fn empty() Self

impl Semigroup for String:
  fn combine(self, other: String) String: self + other

impl Monoid for String:
  static fn empty() String: ""

impl[T] Semigroup for List[T]:
  fn combine(self, other: List[T]) List[T]: self + other

impl[T] Monoid for List[T]:
  static fn empty() List[T]: List()

tuple Sum[T]:
  value: T

impl[T: Addable] Semigroup for Sum[T]:
  fn combine(self, other: Sum[T]) Sum[T]: Sum(self.value + other.value)

impl[T: Addable] Monoid for Sum[T]:
  static fn empty() Sum[T]: Sum(0)

tuple Product[T]:
  value: T

impl[T: Numeric] Semigroup for Product[T]:
  fn combine(self, other: Product[T]) Product[T]: Product(self.value * other.value)

impl[T: Numeric] Monoid for Product[T]:
  static fn empty() Product[T]: Product(1)

tuple All:
  value: Bool

impl Semigroup for All:
  fn combine(self, other: All) All: All(self.value and other.value)

impl Monoid for All:
  static fn empty() All: All(true)

tuple Any:
  value: Bool

impl Semigroup for Any:
  fn combine(self, other: Any) Any: Any(self.value or other.value)

impl Monoid for Any:
  static fn empty() Any: Any(false)

tuple Min[T]:
  value: T

impl[T: Ordered] Semigroup for Min[T]:
  fn combine(self, other: Min[T]) Min[T]: Min(min(self.value, other.value))

tuple Max[T]:
  value: T

impl[T: Ordered] Semigroup for Max[T]:
  fn combine(self, other: Max[T]) Max[T]: Max(max(self.value, other.value))

fn fold_all[T: Monoid](xs) T:
  items = xs |> to_stream() |> collect()
  when items:
    List(h, ...t) -> t |> to_stream() |> reduce(h, (acc, x): acc.combine(x))
    _ -> T.empty()

fn fold_map[T, M: Monoid](f, xs) M:
  fold_all[M](xs |> to_stream() |> map(f) |> collect())

tuple NonEmpty[T]:
  head: T
  tail: List[T]

fn non_empty[T](l: List[T]) Result[NonEmpty[T], Error]:
  when l:
    List(h, ...t) -> Ok(NonEmpty(h, t))
    _ -> Err(Error(MISSING, "empty"))

impl NonEmpty[T]:
  fn to_list(self) List[T]: List(self.head) + self.tail
  fn len(self) Int: 1 + len(self.tail)
  fn to_stream(self): to_stream(List(self.head) + self.tail)
  fn map(self, f): NonEmpty(f(self.head), self.tail |> to_stream() |> map(f) |> collect())
  fn reduce1(self, f): self.tail |> to_stream() |> reduce(self.head, f)
  fn min(self): self.tail |> to_stream() |> reduce(self.head, min)
  fn max(self): self.tail |> to_stream() |> reduce(self.head, max)
enum Option[T] deriving eq, show, read:
  Some(value: T)
  None

impl Monad[Option]:
  fn map[A, B](self: Option[A], f: (A) -> B) Option[B]:
    when self:
      Some(v) -> Option.Some(f(v))
      None -> Option.None
  static fn pure[A](a: A) Option[A]:
    Option.Some(a)
  fn ap[A, B](self: Option[(A) -> B], x: Option[A]) Option[B]:
    when self:
      Some(g) -> x.map(g)
      None -> Option.None
  fn flat_map[A, B](self: Option[A], f: (A) -> Option[B]) Option[B]:
    when self:
      Some(v) -> f(v)
      None -> Option.None
fn is_some[T](o: Option[T]) Bool:
  when o:
    Some(_) -> true
    None -> false

fn is_none[T](o: Option[T]) Bool:
  not is_some(o)
'''

from .locales import tuple_source
SRC = SRC + tuple_source()


GC_SRC = '''
impl Monad[List[_]]:
  fn map[A, B](self: List[A], f: (A) -> B) List[B]:
    self.reduce(List(), (acc, a): acc + List(f(a)))
  static fn pure[A](a: A) List[A]:
    List(a)
  fn ap[A, B](self: List[(A) -> B], x: List[A]) List[B]:
    self.flat_map((g): x.map(g))
  fn flat_map[A, B](self: List[A], f: (A) -> List[B]) List[B]:
    self.reduce(List(), (acc, a): acc + f(a))
'''


def install(I):
    from .parser import parse_program
    from .values import GC
    prog = parse_program(SRC + (GC_SRC if GC[0] else ""), "<prelude>")

    def setup():
        return (yield from I.exec_stmts(prog.stmts, I.prelude))
    I.sched.run_main(setup())
    from . import locales
    from .values import TupleV, ListV
    I.locales = {}
    for name in locales.VALUES:
        d = locales.full(name)
        I.locales[name] = TupleV([_val(d[k]) for k in locales.ORDER], list(locales.ORDER), "Locale")


def _val(x):
    from .values import ListV
    if isinstance(x, list):
        return ListV([_val(i) for i in x])
    return x
