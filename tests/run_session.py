"""Session types (the `session` package): typed conversations over a channel pair.  Run: python3 tests/run_session.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.abspath(__file__)) + "/.."
HEAD = """import session
type alias Client = session.Send[Int, session.Recv[Int, session.End]]
"""
SERVE = """fiber fn serve(e session.Endpoint[session.Peer[Client]]) Result[Unit, Error]
  (n, e2) = session.recv(e)?
  e3 = session.send(e2, n * 2)?
  Ok(session.finish(e3))
"""
CLIENT = """fn client(c session.Endpoint[Client]) Result[Int, Error]
  c2 = session.send(c, 21)?
  (r, c3) = session.recv(c2)?
  session.finish(c3)
  Ok(r)
"""
RUN = "c, s = session.connect[Client]()\n\\run serve(move s)\nprintln(client(c))\n"
CHOICE = """import session
type alias Client = session.Pick[session.Send[Int, session.Send[Int, session.Recv[Int, session.End]]], session.End]

fiber fn serve(e session.Endpoint[session.Peer[Client]]) Result[Unit, Error]
  when session.offer(e)?
    session.Branch.Left(e2) ->
      (a, e3) = session.recv(e2)?
      (b, e4) = session.recv(e3)?
      e5 = session.send(e4, a + b)?
      Ok(session.finish(e5))
    session.Branch.Right(e2) -> Ok(session.finish(e2))

fn client(c session.Endpoint[Client]) Result[Int, Error]
  c2 = session.pick_left(c)?
  c3 = session.send(c2, 20)?
  c4 = session.send(c3, 22)?
  (r, c5) = session.recv(c4)?
  session.finish(c5)
  Ok(r)

c, s = session.connect[Client]()
\\run serve(move s)
println(client(c))
"""
LOOP = """import session
type alias EchoClient = session.Pick[session.Send[Int, session.Recv[Int, EchoClient]], session.End]
type alias EchoServer = session.Offer[session.Recv[Int, session.Send[Int, EchoServer]], session.End]

fn serve(e session.Endpoint[EchoServer]) Result[Unit, Error]
  when session.offer(e)?
    session.Branch.Left(e2) ->
      (n, e3) = session.recv(e2)?
      e4 = session.send(e3, n * 2)?
      serve(e4)
    session.Branch.Right(e2) -> Ok(session.finish(e2))

fn ask(c session.Endpoint[EchoClient], n Int, total Int) Result[Int, Error]
  if n == 0
    c2 = session.pick_right(c)?
    session.finish(c2)
    Ok(total)
  else
    c2 = session.pick_left(c)?
    c3 = session.send(c2, n)?
    (r, c4) = session.recv(c3)?
    ask(c4, n - 1, total + r)

fiber fn server(e session.Endpoint[EchoServer]) Result[Unit, Error]
  serve(e)

c, s = session.connect[EchoClient]()
\\run server(move s)
println(ask(c, 3, 0))
"""
DELEG = """import session
type alias Private = session.Send[Int, session.Recv[Int, session.End]]
type alias Main = session.Send[session.Endpoint[session.Peer[Private]], session.End]

fiber fn worker(e session.Endpoint[session.Peer[Main]]) Result[Unit, Error]
  (line, e2) = session.recv(e)?
  session.finish(e2)
  (n, l2) = session.recv(line)?
  l3 = session.send(l2, n + 100)?
  Ok(session.finish(l3))

mc, ms = session.connect[Main]()
pc, ps = session.connect[Private]()
\\run worker(move ms)
mc2 = session.send(mc, ps)?
session.finish(mc2)
pc2 = session.send(pc, 5)?
(r, pc3) = session.recv(pc2)?
session.finish(pc3)
println(r)
"""
RUNS = [
 ("a request and a reply between two fibers", HEAD + SERVE + CLIENT + RUN, "Ok(42)"),
 ("a choice between two branches", CHOICE, "Ok(42)"),
 ("a loop until the client stops", LOOP, "Ok(12)"),
 ("an endpoint sent over another session", DELEG, "105"),
]
CHECKS = [
 ("receiving before sending", HEAD + "fn f(c session.Endpoint[Client]) Result[Int, Error]\n  (r, c2) = session.recv(c)?\n  Ok(r)\n", "expected `session.Endpoint[session.Recv[T, S]]`"),
 ("sending the wrong type", HEAD + 'fn f(c session.Endpoint[Client]) Result[Unit, Error]\n  c2 = session.send(c, "no")?\n  Ok(())\n', "needs one type for `T`"),
 ("using an endpoint twice", HEAD + "fn f(c session.Endpoint[Client]) Result[Unit, Error]\n  c2 = session.send(c, 1)?\n  c3 = session.send(c, 2)?\n  Ok(())\n", "use of moved value `c`"),
 ("dropping an endpoint mid-conversation", HEAD + "fn f(c session.Endpoint[Client]) Result[Unit, Error]\n  c2 = session.send(c, 1)?\n  Ok(())\n", "dropped before its protocol is finished"),
 ("reaching End without finishing", HEAD + "fn f(c session.Endpoint[Client]) Result[Int, Error]\n  c2 = session.send(c, 1)?\n  (r, c3) = session.recv(c2)?\n  Ok(r)\n", "never finished"),
 ("handing a function the wrong end", HEAD + SERVE + "c, s = session.connect[Client]()\n\\run serve(move c)\n", "mismatched types"),
 ("sending on the receiving end", HEAD + "c, s = session.connect[Client]()\nx = session.send(s, 1)\n", "expected `session.Endpoint[session.Send[T, S]]`"),
 ("reusing an endpoint after sending it", HEAD.replace("session.Send[Int,", "session.Send[Int,") + "type alias Main = session.Send[session.Endpoint[Client], session.End]\nfn f(mc session.Endpoint[Main], p session.Endpoint[Client]) Result[Unit, Error]\n  mc2 = session.send(mc, p)?\n  session.finish(mc2)\n  p2 = session.send(p, 1)?\n  Ok(())\n", "use of moved value `p`"),
 ("a correct function checks clean", HEAD + SERVE + CLIENT, None),
]
RUNS.append(("a case pattern qualified by the package", CHOICE.replace("session.Branch.Left", "session.Left").replace("session.Branch.Right", "session.Right"), "Ok(42)"))
BR = """import session
type alias C = session.Pick[session.Send[Int, session.End], session.End]
"""
CHECKS += [
 ("every branch finishes the conversation", BR + "fn f(c session.Endpoint[C], b Bool) Result[Unit, Error]\n  if b\n    c2 = session.pick_left(c)?\n    c3 = session.send(c2, 1)?\n    Ok(session.finish(c3))\n  else\n    c2 = session.pick_right(c)?\n    Ok(session.finish(c2))\n", None),
 ("a branch that leaves the conversation open", BR + "fn f(c session.Endpoint[C], b Bool) Result[Unit, Error]\n  if b\n    c2 = session.pick_right(c)?\n    session.finish(c2)\n  Ok(())\n", "dropped before its protocol is finished"),
 ("using an endpoint after branches that consumed it", BR + "fn f(c session.Endpoint[C], b Bool) Result[Unit, Error]\n  if b\n    c2 = session.pick_right(c)?\n    session.finish(c2)\n  else\n    c3 = session.pick_right(c)?\n    session.finish(c3)\n  c4 = session.pick_right(c)?\n  Ok(session.finish(c4))\n", "use of moved value `c`"),
 ("a helper that takes over an endpoint uses it up", BR + "fn helper(c session.Endpoint[C]) Result[Unit, Error]\n  c2 = session.pick_right(c)?\n  Ok(session.finish(c2))\nfn f(c session.Endpoint[C]) Result[Unit, Error]\n  r = helper(c)\n  helper(c)\n", "use of moved value `c`"),
 ("a helper handed an endpoint without move", BR + "fn helper(c session.Endpoint[C]) Result[Unit, Error]\n  c2 = session.pick_right(c)?\n  Ok(session.finish(c2))\nfn f(c session.Endpoint[C]) Result[Unit, Error]\n  helper(c)\n", None),
 ("a helper handed an endpoint with move", BR + "fn helper(c session.Endpoint[C]) Result[Unit, Error]\n  c2 = session.pick_right(c)?\n  Ok(session.finish(c2))\nfn f(c session.Endpoint[C]) Result[Unit, Error]\n  helper(move c)\n", None),
]
fails = []
def run_in(src, cmd, gc):
    with tempfile.TemporaryDirectory() as d:
        open(os.path.join(d, "main.mxi"), "w").write(src)
        r = subprocess.run([sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + [cmd, os.path.join(d, "main.mxi")], cwd=ROOT, capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()
for name, src, want in RUNS:
    for gc in (False, True):
        rc, o = run_in(src, "run", gc)
        ok = rc == 0 and o == want
        print(("ok    " if ok else "FAIL  ") + name + (" (gc)" if gc else "") + ("" if ok else f"  -> rc={rc} {o[:300]}"))
        if not ok: fails.append(name)
for name, src, word in CHECKS:
    for gc in (False, True):
        rc, o = run_in(src, "check", gc)
        ok = (rc != 0 and word in o) if word else rc == 0
        print(("ok    " if ok else "FAIL  ") + name + (" (gc)" if gc else "") + ("" if ok else f"  -> rc={rc} {o[:300]}"))
        if not ok: fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
