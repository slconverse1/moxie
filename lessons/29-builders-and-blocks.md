# Builders: a DSL without macros

Some programs read best when the code looks like the thing it builds: a page of markup, a menu, a configuration. Many languages add macros for this. Moxie has none, and doesn't need them. A builder is an ordinary set of functions, and nesting is nested calls. Types keep the nesting honest.

## Nested calls

Give each kind of node its own tuple type, so that only the right children fit in the right parents:

```moxie
tuple Html deriving show
  text String

tuple Li deriving show
  text String

fn h1(text String) Html
  Html(text: "<h1>${text}</h1>")

fn li(text String) Li
  Li(text: "<li>${text}</li>")

fn ul(items ...Li) Html
  inner = items |> map(_.text) |> reduce("", _1 + _2)
  Html(text: "<ul>${inner}</ul>")

fn body(children ...Html) Html
  inner = children |> map(_.text) |> reduce("", _1 + _2)
  Html(text: "<body>${inner}</body>")

fn html(child Html) String
  "<html>${child.text}</html>"

page = html(
  body(
    h1("Welcome to moxie"),
    ul(
      li("fast"),
      li("small")
    )
  )
)
println(page)
```
```output
<html><body><h1>Welcome to moxie</h1><ul><li>fast</li><li>small</li></ul></body></html>
```

The calls are indented so that they look like the page. `ul` takes `Li` items only, so `ul(h1("x"))` is a compile error: a heading cannot sit in a list.

```moxie
tuple Html deriving show
  text String

tuple Li deriving show
  text String

fn h1(text String) Html
  Html(text: "<h1>${text}</h1>")

fn ul(items ...Li) Html
  Html(text: "<ul></ul>")

println(ul(h1("x")).text)
```
```error
error: mismatched types: expected `Li`, found `Html`
```

## Children as an indented block

Nested calls with commas work, but a block reads more like the page it makes. A parameter marked `block` receives the indented lines under the call, as a `List`:

```moxie
tuple Item deriving show
  text String

fn item(text String) Item
  Item(text: "<li>${text}</li>")

fn menu(name String, block items List[Item]) String
  inner = items |> map(_.text) |> reduce("", _1 + _2)
  "<ul id=${name}>${inner}</ul>"

page = menu("nav")
  item("Start")
  item("Docs")
println(page)
```
```output
<ul id=nav><li>Start</li><li>Docs</li></ul>
```

Each line of the block is a child. A call with no block gets an empty list:

```moxie
tuple Item deriving show
  text String

fn item(text String) Item
  Item(text: "<li>${text}</li>")

fn menu(name String, block items List[Item]) String
  inner = items |> map(_.text) |> reduce("", _1 + _2)
  "<ul id=${name}>${inner}</ul>"

println(menu("empty"))
```
```output
<ul id=empty></ul>
```

### Conditions and loops inside a block

A block is ordinary code that builds one list, so it can decide what goes in:

- an `if` (with `elif` and `else`) adds children only when its condition holds;
- a `for` adds the children of every iteration;
- `...list` adds every element of a list;
- a binding, such as `label = "x"`, adds nothing; it is just a name for later lines.

```moxie
tuple Item deriving show
  text String

fn item(text String) Item
  Item(text: "<li>${text}</li>")

fn menu(name String, block items List[Item]) String
  inner = items |> map(_.text) |> reduce("", _1 + _2)
  "<ul id=${name}>${inner}</ul>"

admin = true
pages = List("Home", "About")
extra = List(item("Help"), item("Contact"))

page = menu("nav")
  item("Start")
  if admin
    item("Admin")
  for p in pages
    item(p)
  ...extra
println(page)

guest = menu("guest")
  item("Start")
  if not admin
    item("Admin")
  else
    item("Dashboard")
println(guest)
```
```output
<ul id=nav><li>Start</li><li>Admin</li><li>Home</li><li>About</li><li>Help</li><li>Contact</li></ul>
<ul id=guest><li>Start</li><li>Dashboard</li></ul>
```

A `when` is not allowed in a block; use `if` / `elif` / `else`.

### The children are checked

The block's lines are checked against the `block` parameter's `List` type, so a child of the wrong type is a compile error, and a call to a function that has no `block` parameter can't take a block at all:

```moxie
tuple Item deriving show
  text String

fn item(text String) Item
  Item(text: "<li>${text}</li>")

fn plain(name String) String
  name

result = plain("x")
  item("oops")
println(result)
```
```error
error: `plain` has no `block` parameter, so it can't take an indented block of children (declare one: `fn plain(.., block items List[T])`)
```

## Builders that nest

Because a block's children come from ordinary calls, builders nest as deeply as you like. Here is a small document builder with sections that hold paragraphs:

```moxie
tuple Para deriving show
  text String

tuple Section deriving show
  text String

fn para(text String) Para
  Para(text: "  ${text}\n")

fn section(title String, block paras List[Para]) Section
  inner = paras |> map(_.text) |> reduce("", _1 + _2)
  Section(text: "${title}\n${inner}")

fn document(block sections List[Section]) String
  sections |> map(_.text) |> reduce("", _1 + _2)

doc = document()
  section("Intro")
    para("Moxie is small.")
    para("It has no macros.")
  section("Why")
    for reason in List("types", "values", "fibers")
      para("Because of ${reason}.")
print(doc)
```
```output
Intro
  Moxie is small.
  It has no macros.
Why
  Because of types.
  Because of values.
  Because of fibers.
```

Every level is a function, every list is typed, and the whole page is a value you can pass around, test, and store.

## What to remember

- A builder is plain functions; the nesting is nested calls.
- Give each node its own tuple type so the compiler rejects a child in the wrong place.
- A `block` parameter takes the indented lines under a call as a `List`, in order.
- Inside a block, `if`, `for`, and `...list` choose the children; a binding adds none.
- A mistake in the children is a compile error, not a surprise at run time.
