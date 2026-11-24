DOCS = {}
def d(name, text, ex=(), shown=()):
    DOCS[name] = (text, list(ex), list(shown))

T = 'p = path_join(temp_dir(), "moxie_ref_demo.txt")\n'
# ---------------------------------------------------------------- files
d("read_file", """Reads a whole text file into a `String`. A file that is missing, unreadable or not valid UTF-8 is an `Err`, never an abort.

**Parameters**

- `p`: the path.

**Returns** `Ok(text)`, or `Err` (code `NOT_FOUND` if there is no such file).""",
 [T + 'write_file(p, "hello")\nprintln(read_file(p))\nremove_file(p)', 'read_file("/no/such/file") |> is_err()'])
d("write_file", """Writes text to a file, replacing whatever was there, and creating the file if needed. The folder must already exist; see `make_dir`.

**Parameters**

- `p`: the path.
- `s`: the text.

**Returns** `Ok(())`, or `Err`.""",
 [T + 'println(write_file(p, "hi"))\nremove_file(p)'])
d("make_dir", """Makes a folder, with any missing folders above it. It is not an error if the folder is already there.

**Parameters**

- `p`: the path.

**Returns** `Ok(())`, or `Err`.""",
 ['q = path_join(temp_dir(), "moxie_ref_dir/a/b")\nprintln(make_dir(q))\nprintln(path_exists(q))\nremove_dir(q)'])
d("remove_file", """Deletes a file. A missing file is an `Err`.

**Parameters**

- `p`: the path.

**Returns** `Ok(())`, or `Err` (code `NOT_FOUND` if there was no such file).""",
 [T + 'write_file(p, "x")\nprintln(remove_file(p))\nprintln(path_exists(p))'])
d("remove_dir", """Deletes a folder. The folder has to be empty; this is deliberate, so one call can't wipe out a tree by mistake.

**Parameters**

- `p`: the path.

**Returns** `Ok(())`, or `Err`.""",
 ['q = path_join(temp_dir(), "moxie_ref_dir2")\nmake_dir(q)\nprintln(remove_dir(q))\nprintln(path_exists(q))'])
d("rename_path", """Renames or moves a file or folder. If the new name already exists as a file, it is replaced.

**Parameters**

- `a`: the current path.
- `b`: the new path.

**Returns** `Ok(())`, or `Err`.""",
 ['a = path_join(temp_dir(), "moxie_ref_a.txt")\nb = path_join(temp_dir(), "moxie_ref_b.txt")\nwrite_file(a, "x")\nprintln(rename_path(a, b))\nprintln(path_exists(a))\nprintln(path_exists(b))\nremove_file(b)'])
d("list_dir", """The names of the items in a folder, sorted, without the folder's own path.

**Parameters**

- `p`: the path of a folder.

**Returns** `Ok(names)` as an `Array[String]`, or `Err`.""",
 ['q = path_join(temp_dir(), "moxie_ref_dir3")\nmake_dir(q)\nwrite_file(path_join(q, "b.txt"), "")\nwrite_file(path_join(q, "a.txt"), "")\nprintln(list_dir(q))\nremove_file(path_join(q, "a.txt"))\nremove_file(path_join(q, "b.txt"))\nremove_dir(q)'])
d("path_exists", """Whether a file or folder is there. Asking can fail, for instance when a folder above it can't be read, which is why the answer is a `Result`.

**Parameters**

- `p`: the path.

**Returns** `Ok(true)`, `Ok(false)`, or `Err`.""",
 ['path_exists("/no/such/file")'])
d("file_info", """Facts about a file or folder: its `kind` (`"file"` or `"dir"`) and its `size` in bytes.

**Parameters**

- `p`: the path.

**Returns** `Ok(FileInfo)`, or `Err` if there is nothing at the path.""",
 [T + 'write_file(p, "hello")\ninfo = file_info(p) |> unwrap()\nprintln(info)\nremove_file(p)'])
d("path_join", """Joins two parts of a path with the right separator. If the second part is an absolute path, it wins.

**Parameters**

- `base`: the first part.
- `rest`: the second part.

**Returns** a `String`.""",
 ['path_join("a", "b.txt")', 'path_join("a/", "b.txt")', 'path_join("a", "/etc/x")'])
d("path_name", """The last part of a path: the file or folder name.

**Parameters**

- `p`: a path.

**Returns** a `String`.""",
 ['path_name("/a/b/c.txt")', 'path_name("c.txt")'])
d("path_parent", """Everything but the last part of a path: the folder that holds it.

**Parameters**

- `p`: a path.

**Returns** a `String`.""",
 ['path_parent("/a/b/c.txt")', 'path_parent("c.txt")'])
d("path_stem", """The file name without its extension.

**Parameters**

- `p`: a path.

**Returns** a `String`.""",
 ['path_stem("/a/b/c.txt")', 'path_stem("archive.tar.gz")'])
d("path_ext", """The extension of the file name, without the dot, or an empty `String` if there is none.

**Parameters**

- `p`: a path.

**Returns** a `String`.""",
 ['path_ext("/a/b/c.txt")', 'path_ext("archive.tar.gz")', 'path_ext("Makefile")'])
d("cwd", """The folder the program was started in.

**Parameters** none.

**Returns** a `String`.""", [], [("cwd()", "\"/home/ada/project\"")])
d("temp_dir", """The folder the system offers for temporary files.

**Parameters** none.

**Returns** a `String`.""", [], [("temp_dir()", "\"/tmp\"")])
d("home_dir", """The current user's home folder.

**Parameters** none.

**Returns** `Ok(path)`, or `Err` if the system doesn't say.""", [], [("home_dir()", "Ok(\"/home/ada\")")])

# ---------------------------------------------------------------- output
d("println", """Writes a value followed by a line end. The value is shown as text the way `show` would, except that a `String` is written without its quotes. With no argument it writes an empty line. With an `Io` first, it writes there, for instance to a network connection.

**Parameters**

- `out` (optional): an `Io` to write to; the default is standard output.
- `x` (optional): the value.

**Returns** nothing.""",
 ['println("hello")\n', "println(42)\n", "println(List(1, 2))\nprintln()\nprintln(\"after a blank line\")\n"])
d("print", """Like `println`, but without the line end, so the next output continues on the same line. Output may be held back until a line end or until `flush`.

**Parameters**

- `out` (optional): an `Io` to write to.
- `x`: the value.

**Returns** nothing.""",
 ['print("a")\nprint("b")\nprintln()'])
d("eprintln", """Like `println`, but to the error stream, which is where messages for the person running the program, as opposed to the program's output, belong.

**Parameters**

- `out` (optional): an `Io`.
- `x` (optional): the value.

**Returns** nothing.""", [], [('eprintln("something went wrong")', "(written to the error stream)")])
d("eprint", """Like `print`, but to the error stream.

**Parameters**

- `out` (optional): an `Io`.
- `x`: the value.

**Returns** nothing.""", [], [('eprint("working...")', "(written to the error stream)")])
d("flush", """Sends held-back output on its way now, which matters for a prompt that doesn't end in a line end, or before the program does something slow.

**Parameters**

- `out` (optional): an `Io`; the default is standard output.

**Returns** nothing.""", ['print("a")\nflush()\nprintln("b")'])
d("read_line", """Reads one line of input, without its line end. It waits, letting other fibers run, until a line arrives.

**Parameters**

- `src` (optional): an `Io` to read from; the default is standard input.

**Returns** `Ok(line)`, or `Err` with code `CLOSED` ("end of input") at the end of the input.""",
 ['fn first() Result[String, Error]\n  read_line()\nprintln(with_stdin("one\\ntwo\\n", first))', 'fn first() Result[String, Error]\n  read_line()\nprintln(is_err(with_stdin("", first)))'])
d("read_all", """Reads everything that is left of the input, as one `String`.

**Parameters**

- `src` (optional): an `Io`; the default is standard input.

**Returns** `Ok(text)`, or `Err`.""", ['fn everything() Result[String, Error]\n  read_all()\nprintln(with_stdin("one\\ntwo\\n", everything))'])
d("stdin_lines", """The lines of standard input, one at a time, until the input ends. It is meant for `for` and pipelines.

**Parameters** none.

**Returns** a `Stream[String]`.""",
 ['fn gather() List[String]\n  stdin_lines() |> collect()\nprintln(with_stdin("a\\nb\\nc\\n", gather))'])
d("lines", """The lines of an `Io`, one at a time, until it ends.

**Parameters**

- `src`: an `Io`, such as a connection.

**Returns** a `Stream[String]`.""", [], [("for line in lines(conn)", "runs once for each line the other side sends")])
d("read_bytes", """Reads up to `n` bytes from an `Io`. At the end of the input you get fewer than `n`, or none.

**Parameters**

- `src`: an `Io`.
- `n`: how many bytes at most.

**Returns** `Ok(bytes)` as an `Array[Byte]`, or `Err`.""", [], [("read_bytes(conn, 4)", "Ok(Array(1, 2, 3, 4))")])
d("write_bytes", """Writes raw bytes to an `Io`.

**Parameters**

- `out`: an `Io`.
- `data`: an `Array[Byte]`.

**Returns** `Ok(())`, or `Err`.""", [], [("write_bytes(conn, Array(1, 2, 3))", "Ok(())")])
d("with_stdin", """Runs a function with standard input replaced by some text. It is how a program that reads input is tested without a keyboard.

**Parameters**

- `text`: what the input will contain.
- `f`: the function to run.

**Returns** whatever `f` returns.""",
 ['fn first() Result[String, Error]\n  read_line()\nprintln(with_stdin("5\\n", first))'])
d("raw_terminal", """Puts the terminal into raw mode, so single key presses arrive at once instead of whole lines, as a game or editor needs. The terminal is put back when the `Terminal` is closed or the program ends.

**Parameters** none.

**Returns** `Ok(Terminal)`, or `Err` when there is no terminal (for instance when input is piped).""", [], [("raw_terminal()", "Ok(Terminal())")])
d("read_key", """Waits for one key press on a raw terminal.

**Parameters**

- `t`: a `Terminal` from `raw_terminal`.

**Returns** `Ok(Key)`, or `Err`.""", [], [("read_key(t)", "Ok(Key.Char('q'))")])

# ---------------------------------------------------------------- network
d("listen", """Starts accepting network connections on a port. Port 0 asks the system to pick a free one; `port_of` tells you which.

**Parameters**

- `port`: the TCP port number.

**Returns** `Ok(Listener)`, or `Err` if the port can't be used.""",
 ['l = listen(0) |> unwrap()\nprintln(port_of(l) > 0)\nclose(l)'])
d("accept", """Waits for the next incoming connection on a `Listener`. Other fibers run while it waits.

**Parameters**

- `l`: a `Listener`.

**Returns** `Ok(Io)` for the new connection, or `Err`.""", [], [("accept(l)", "Ok(Io())  (when a client connects)")])
d("connect", """Opens a TCP connection to a host and port. The name is looked up, which is why this can take a while and why other fibers run meanwhile.

**Parameters**

- `host`: a name or address.
- `port`: the port number.

**Returns** `Ok(Io)`, or `Err` if the connection fails.""",
 ['l = listen(0) |> unwrap()\nc = connect("127.0.0.1", port_of(l)) |> unwrap()\nprintln(is_ok(write_bytes(c, Array(1))))\nclose(c)\nclose(l)'])
d("listen_tls", """Like `listen`, but the connections are encrypted with TLS, using a certificate and key you give.

**Parameters**

- `port`: the TCP port.
- `cert`: the path of the certificate file.
- `key`: the path of the key file.

**Returns** `Ok(Listener)`, or `Err` (for instance if a file can't be read).""", [], [('listen_tls(8443, "cert.pem", "key.pem")', "Ok(Listener())")])
d("connect_tls", """Like `connect`, but encrypted with TLS. The server's certificate is checked against the system's trusted ones, and a certificate that doesn't match the host name is an `Err`.

**Parameters**

- `host`: a name; it is used to check the certificate.
- `port`: the port.

**Returns** `Ok(Io)`, or `Err`.""", [], [('connect_tls("example.com", 443)', "Ok(Io())")])
d("port_of", """The port a `Listener` or a `Udp` socket is using, which is how you find out the port the system picked when you asked for 0.

**Parameters**

- `l`: a `Listener` or a `Udp`.

**Returns** an `Int`.""", ['port_of(listen(0) |> unwrap()) > 0'])
d("bind_udp", """Opens a UDP socket on a port, to send and receive single packets. Port 0 means any free port.

**Parameters**

- `port`: the port.

**Returns** `Ok(Udp)`, or `Err`.""", ['u = bind_udp(0) |> unwrap()\nprintln(port_of(u) > 0)\nclose(u)'])
d("send_to", """Sends one UDP packet.

**Parameters**

- `u`: a `Udp`.
- `host`, `port`: where to send it.
- `data`: a `String` or an `Array[Byte]`.

**Returns** `Ok(())`, or `Err`. Success doesn't mean the packet arrived: UDP doesn't promise that.""",
 ['a = bind_udp(0) |> unwrap()\nb = bind_udp(0) |> unwrap()\nprintln(send_to(a, "127.0.0.1", port_of(b), "ping"))\nclose(a)\nclose(b)'])
d("receive", """Waits for one UDP packet.

**Parameters**

- `u`: a `Udp`.

**Returns** `Ok(Packet)`, with the data and where it came from, or `Err`.""", [], [("receive(u)", "Ok(Packet(...))")])
d("spawn", """Starts another program and returns at once, leaving it running. You can then wait for it or stop it.

**Parameters**

- `program`: the program to run.
- `args` (optional): a `List[String]` of arguments.

**Returns** `Ok(Child)`, or `Err` if it can't be started.""", [], [('spawn("sleep", List("5"))', "Ok(Child())")])
d("wait_child", """Waits for a program started with `spawn` to finish. Other fibers run meanwhile.

**Parameters**

- `c`: a `Child`.

**Returns** `Ok(exit code)`, or `Err`.""", [], [("wait_child(c)", "Ok(0)")])
d("kill_child", """Stops a program started with `spawn`.

**Parameters**

- `c`: a `Child`.

**Returns** nothing.""", [], [("kill_child(c)", "the program is stopped")])
d("run_command", """Runs a program, waits for it to end, and gathers what it printed.

**Parameters**

- `program`: the program to run.
- `args` (optional): a `List[String]` of arguments.

**Returns** `Ok(Output)` with the exit code and the text of its standard output and error, or `Err` if it can't be started.""",
 ['run_command("echo", List("hi")) |> map_ok((o) -> o.stdout)'])
d("hostname", """The name of this computer.

**Parameters** none.

**Returns** a `String`.""", [], [("hostname()", "\"ada-laptop\"")])
d("os_name", """The name of the operating system: `"linux"`, `"macos"` or `"windows"`.

**Parameters** none.

**Returns** a `String`.""", ['os_name() == "linux" or os_name() == "macos" or os_name() == "windows"'])
d("wire_pair", """Makes a connected pair of `Wire`s, ends of a channel that can carry whole values between programs or between a program and a foreign library. What is written to one is read from the other.

**Parameters** none.

**Returns** a pair of `Wire`s.""", ['(a, b) = wire_pair()\nwire_send(a, 5)\nprintln(wire_recv[Int](b))'])
d("wire_send", """Sends a value over a `Wire`. The value must be plain data (numbers, text, tuples, lists), not a resource.

**Parameters**

- `w`: a `Wire`.
- `x`: the value.

**Returns** `Ok(())`, or `Err` if the wire is closed.""", ['(a, b) = wire_pair()\nprintln(wire_send(a, "hi"))'])
d("wire_recv", """Waits for a value from a `Wire`. The type you expect is written in brackets; it must be the type that was sent.

**Parameters**

- `T` (in brackets): the type expected.
- `w`: a `Wire`.

**Returns** `Ok(value)`, or `Err` if the wire is closed.""", ['(a, b) = wire_pair()\nwire_send(a, 5)\nprintln(wire_recv[Int](b))'])
d("wire_close", """Closes a `Wire`. The other end can still read what was already sent, and then gets an `Err`.

**Parameters**

- `w`: a `Wire`.

**Returns** nothing.""", ['(a, b) = wire_pair()\nwire_send(a, 1)\nwire_close(a)\nprintln(wire_recv[Int](b))\nprintln(is_err(wire_recv[Int](b)))'])

# ---------------------------------------------------------------- testing
d("assert", """Stops the program with a message if a condition is false. In a `test`, a failed assertion fails the test and the other tests go on. An optional message says what was expected.

**Parameters**

- `ok`: the condition that must hold.
- `message` (optional): what to report if it doesn't.

**Returns** nothing.""", ["assert(1 < 2)\nprintln(\"fine\")"], [('assert(1 > 2, "one is not bigger")', "aborts: assertion failed: one is not bigger")])
d("assert_eq", """Checks that two values are equal and, if they are not, reports both so you can see the difference.

**Parameters**

- `a`, `b`: two values of one type.

**Returns** nothing.""", ["assert_eq(1 + 1, 2)\nprintln(\"fine\")"], [("assert_eq(1 + 1, 3)", "aborts, showing 2 and 3")])
d("assert_ne", """Checks that two values are different.

**Parameters**

- `a`, `b`: two values of one type.

**Returns** nothing.""", ["assert_ne(1, 2)\nprintln(\"fine\")"], [("assert_ne(1, 1)", "aborts")])
d("debug_assert", """Like `assert`, but only checked when the program is run in debug mode; in a release build it costs nothing. Use it for checks that are too slow to leave on, and never for checks that guard against bad input.

**Parameters**

- `ok`: the condition that must hold.

**Returns** nothing.""", ["debug_assert(1 < 2)\nprintln(\"fine\")"])
d("dbg", """Prints a value, with the line it is on, to the error stream, and returns it unchanged, so you can drop it into the middle of an expression to see what is going on. It is allowed anywhere, whatever the effects of the surrounding code.

**Parameters**

- `x`: any value.

**Returns** `x`.""", ["dbg(2 + 3) * 10"])
d("trace", """Writes a value to the trace, a log for finding out what a program did, which can be turned on and off from outside. Like `dbg`, it is allowed anywhere.

**Parameters**

- `x`: any value.

**Returns** nothing.""", ["trace(\"step one\")\nprintln(\"done\")"])
d("gen_int", """A random whole number between two bounds, both included, for a property test. The generator `g` is handed to the test by `moxie test`, which prints the seed when a test fails, so the failure can be replayed.

**Parameters**

- `g`: the `Gen`.
- `lo`, `hi`: the bounds.

**Returns** an integer in the range.""", [], [("gen_int(g, 0, 100)", "37  (a different number each run, same for a given seed)")])
d("gen_bool", """A random `true` or `false` for a property test.

**Parameters**

- `g`: the `Gen`.

**Returns** a `Bool`.""", [], [("gen_bool(g)", "true")])
d("gen_pick", """A random item of a list, for a property test.

**Parameters**

- `g`: the `Gen`.
- `xs`: a non-empty `List`.

**Returns** one of its items.""", [], [("gen_pick(g, List(\"a\", \"b\", \"c\"))", "\"b\"")])
