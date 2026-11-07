"""map_all: independent Results combined by a function, accumulating every error."""
import sys, subprocess
sys.path.insert(0, ".")
PROG = r'''
tuple User:
  name: String
  email: String
  age: Int

fn check_name(name: String) Result[String, String]:
  when name == "":
    true -> Err("name is empty")
    false -> Ok(name)

fn check_email(e: String) Result[String, String]:
  when e.contains("@"):
    true -> Ok(e)
    false -> Err("bad email ${e}")

fn check_age(a: Int) Result[Int, String]:
  when a < 0:
    true -> Err("negative age")
    false -> Ok(a)

fn create(name: String, email: String, age: Int) Result[User, List[String]]:
  map_all(User, check_name(name), check_email(email), check_age(age))

println(create("ann", "a@b", 3))
println(create("", "nope", -1))
println(create("bob", "nope", 4))
println(map_all((a, b): a + b, Ok(1), Ok(2)))
println(create("", "a@b", 1).is_err())
println((check_name("ann"), check_email("a@b"), check_age(3)) |> map_all(User))
println((check_name(""), check_email("nope")) |> map_all((a, b): a + b))
println((Ok(1), Ok(2)).map_all((a, b): a * 10 + b))
'''
EXPECT = [
  'Ok(User(name: "ann", email: "a@b", age: 3))',
  'Err(List("name is empty", "bad email nope", "negative age"))',
  'Err(List("bad email nope"))',
  'Ok(3)',
  'true',
  'Ok(User(name: "ann", email: "a@b", age: 3))',
  'Err(List("name is empty", "bad email nope"))',
  'Ok(12)',
]
BAD = [
  ("x = map_all((a, b, c): a, Ok(1), Ok(2))\n", "takes 3"),
  ("x = map_all((a): a, Ok(1), Ok(2))\n", "takes 1"),
]
fails = 0
def run(src, *flags):
    open("/tmp/_mapall.mx", "w").write(src)
    return subprocess.run([sys.executable, "-m", "moxie", *flags, "run", "/tmp/_mapall.mx"], capture_output=True, text=True)
for flags in ((), ("--gc",)):
    r = run(PROG, *flags)
    if r.stdout.split("\n")[:-1] != EXPECT:
        fails += 1; print("FAIL good", flags, r.stdout, r.stderr)
    for src, msg in BAD:
        r = run(src, *flags)
        if msg not in r.stdout + r.stderr:
            fails += 1; print("FAIL bad", flags, src, r.stdout, r.stderr)
print("map_all: FAIL" if fails else "map_all: ok")
