---
layout: default
learn: true
title: "Networking, deadlines, and parallel work · Learning Guide moxie"
---
<p><small>Data from outside</small></p>

# 42. Networking, deadlines, and parallel work

This lesson covers talking over a network, waiting with a deadline, racing two jobs against each other, and spreading work across fibers. Everything here uses `localhost`, so each example is a complete program that runs on its own.

## Sockets

A network connection is the same kind of value as a file, an `Io`, so code that reads lines doesn't care which it was given. `listen(port)` gives a `Listener` (port `0` picks a free one, and `port_of` says which). `accept` waits for a client, and `connect(host, port)` is the client side.

A server and a client can run as two fibers of one program, because `accept` and `read_line` park only their own fiber:

```moxie
fiber fn server(tx ChanW[Int]) Result[Unit, Error]
  l = listen(0)?
  \write(tx, port_of(l))
  c = accept(l)?
  println(c, "hello from server")
  close(c)
  close(l)
  Ok(())

rx, tx = Chan[Int][1]()
go server(tx)
c = connect("127.0.0.1", read(rx)?)?
println(read_line(c)?)
close(c)
```
**Output:**

```
hello from server
```

The server reports its port through a channel (lesson 28), the client connects to it, and the line the server wrote comes out of `read_line`. `connect` returns a `Result`, since a connection can fail.

Other kinds of connection exist, and they use the same `Io` functions:

- `connect_tls(host, port)` is `connect` over TLS, the protocol behind `https`. The certificate is checked against the system's trusted authorities and against the name you gave, and one that fails is an `Err`, never a connection with a warning. `listen_tls(port, cert_file, key_file)` is the server side.
- `bind_udp(port)` gives a `Udp` socket for separate datagrams: each `send_to` is one packet and each `receive` gets one packet, and packets may arrive out of order, twice, or not at all.

These need a peer or a certificate, so the examples are shown but not run:

```moxie
c = connect_tls("example.com", 443)?
println(c, "GET / HTTP/1.0\r\nHost: example.com\r\n")
println(read_line(c)?)
close(c)

sock = bind_udp(5300)?
p = receive(sock, timeout: 2s)?
println("${p.host}:${p.port} sent ${len(p.data)} bytes")
\send_to(sock, p.host, p.port, p.data)
close(sock)
```

## HTTP

`import http` gives a small HTTP client and server for plain jobs, with text bodies and one request per connection. A server is a function from a `Request` to a `Response`, and `http.serve` calls it for each connection:

```moxie
import http

fn handle(req http.Request) http.Response
  if req.method == "POST"
    http.text(200, "you said: ${req.body}")
  elif req.path == "/hello"
    http.text(200, "hello, mixer")
  else
    http.text(404, "nothing at ${req.path}")

fiber fn server(l Listener, count Int) Unit
  http.serve_n(l, count, handle)

l = listen(0)?
port = port_of(l)
go server(l, 3)
a = http.get("localhost", port, "/hello")?
println("${a.status} ${a.body}")
b = http.post("localhost", port, "/echo", "hello")?
println("${b.status} ${b.body}")
c = http.get("localhost", port, "/nope")?
println("${c.status} ${c.body}")
```
**Output:**

```
200 hello, mixer
200 you said: hello
404 nothing at /nope
```

`serve_n` handles a fixed number of connections and returns; `http.serve(l, handle)` goes on forever. The client calls return a `Result`, so `?` hands a failed connection back to the caller. Headers are a list of `Header(name, value)`; `http.header_value(headers, "Content-Type")` finds one without regard to case, and `http.request(host, port, method, path, headers, body)` is the general form behind `get` and `post`.

There is no TLS and no chunked body in this package, and the body is text. Both ends need the `net.connect` or `net.listen` permission.

## Waiting with a deadline

Every call that can wait on the outside world takes `timeout:`, a `Duration`: `read(ch, timeout: d)`, `accept`, `connect`, `receive`, `wait_child`, `run_command`, and `read_line` on a socket. When the time passes with nothing to show, the call returns an `Err` with the reserved code `TIMED_OUT`, so a timeout is never confused with a dropped connection (`IO_ERROR`), and `retry` treats it as worth another try.

A timeout gives up *waiting*; it undoes nothing. A `run_command` that times out has had its program killed, and a `read` that times out has taken nothing from the channel.

```moxie
rx, tx = Chan[Int][1]()
println(read(rx, timeout: 50ms))
\write(tx, 7)
println(read(rx, timeout: 50ms))

fn try_read() Result[Int, Error]
  read(rx, timeout: 10ms)

println(retry(3, 10ms, try_read))
close(tx)
```
**Output:**

```
Err(Error(code: 12, message: "read: timed out"))
Ok(7)
Err(Error(code: 12, message: "read: timed out"))
```

## Racing and time limits

`timeout:` covers calls that wait on the outside world. For your own work, `race(f, g)` runs two functions at once and gives the result of whichever finishes first, and `with_timeout(d, f)` runs `f` and gives `Err` with `TIMED_OUT` if it is still going after `d`.

Each function takes a `Cancel` token, because in moxie stopping is a request: when `race` has a winner it sets the other's token, and when `with_timeout` runs out of time it sets the token. The other function ends only if it looks (`is_cancelled(c)`, or `cancelled(c) ->` in a `select`, lesson 29). Both are structured: they wait for the slower function to end before they return, so none outlives its call.

```moxie
fn polite(c Cancel) Result[Int, Error]
  for true
    select
      cancelled(c) ->
        return Err(Error(CLOSED, "cancelled"))

      else
        sleep(5ms)
  Ok(0)

fn quick(c Cancel) Result[Int, Error]
  sleep(10ms)
  Ok(42)

println(race(polite, quick))
println(with_timeout(1s, quick))
println(with_timeout(50ms, polite))
```
**Output:**

```
Ok(42)
Ok(42)
Err(Error(code: 12, message: "with_timeout: timed out"))
```

`race` gives whatever finished first, an `Err` included, and the two functions must have the same result type. `with_timeout` takes a function that gives `Result[T, Error]` and gives the same type back, so `TIMED_OUT` joins the reserved errors you already handle. Each call site counts against the program's fibers: 2 for `race`, 1 for `with_timeout`.

## Doing the work in parallel

`par_map(f, xs, limit: n)` calls `f` on every item, at most `n` at a time, each call in its own fiber, and gives the results as a `List` in the order of the input, however the calls finish. It pays off when `f` mostly waits (a network call, a file, a program) or when the work spreads across cores; for a quick calculation, plain `map` is faster, because starting a fiber costs more than the work.

`limit:` must be a number the compiler can see (a literal or a top-level constant), the same rule as a channel's capacity, for the same reason: fibers are counted before the program runs.

`par_traverse(f, xs, limit: n)` is `traverse` for the same job, for an `f` that gives a `Result`. When an item fails it stops starting new items, lets the running ones finish, and gives the `Err` of the earliest failing item, so the answer doesn't depend on timing.

```moxie
fn slow_double(n Int) Int
  sleep((6 - n) * 10ms)
  n * 2

fn check(n Int) Result[Int, String]
  sleep((6 - n) * 10ms)
  when n % 2 == 0
    true -> Err("even ${n}")
    false -> Ok(n)

println(List(1, 2, 3, 4, 5) |> par_map(slow_double, limit: 3))
println(par_traverse(check, List(1, 3, 5), limit: 2))
println(par_traverse(check, List(1, 2, 3, 4, 5), limit: 5))
```
**Output:**

```
List(2, 4, 6, 8, 10)
Ok(List(1, 3, 5))
Err("even 2")
```

The order of any output the calls themselves print is up to the scheduler, but the *results* come back in input order. The items and whatever `f` uses must be plain data: a resource is owned by one fiber.

## What to remember

- A socket is an `Io`; `connect` and `accept` return a `Result`, and park only their own fiber.
- `import http`: a server is a function from `Request` to `Response`.
- `timeout:` turns a wait into an `Err` with code `TIMED_OUT`.
- `race` and `with_timeout` stop work by *asking*, through a `Cancel` token.
- `par_map` and `par_traverse` give results in input order, with a compile-time `limit:`.

---

[← Statistics and prediction](32-statistics.html) · [Contents](./) · [Units of measure →](34-units.html)
