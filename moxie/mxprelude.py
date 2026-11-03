"""Parts of the prelude that are written in moxie itself (no compiler support needed)."""

SRC = '''
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
'''


def install(I):
    from .parser import parse_program
    prog = parse_program(SRC, "<prelude>")

    def setup():
        return (yield from I.exec_stmts(prog.stmts, I.prelude))
    I.sched.run_main(setup())
