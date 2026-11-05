// Manual check of the Try moxie page under a real Pyodide, headless.  Needs Node with playwright, and a local Pyodide core:
//   curl -L -o core.tar.bz2 https://github.com/pyodide/pyodide/releases/download/0.26.4/pyodide-core-0.26.4.tar.bz2 && tar xjf core.tar.bz2
//   mkdir site && cp -r docs/. site/ && ln -s $PWD/pyodide site/pyodide && (cd site && python3 -m http.server 8765 &)
//   NODE_PATH=$(npm root -g) node tests/try_page.js
// (try.html takes ?pyodide=/pyodide/ to use the local copy).  It prints each program's output for you to read.
const { chromium } = require('playwright');
const progs = {
  hello: 'println("hello from the page")\n',
  clock: 't0 = monotonic()\nsleep(50ms)\nprintln((monotonic() - t0).millis() >= 50)\nprintln(now().seconds() > 1.7e9)\n',
  random: 'println(random_int(3, 3))\nprintln(len(random_bytes(8)))\ng = seeded(5)\nprintln(gen_int(g, 0, 9) == gen_int(seeded(5), 0, 9))\n',
  osname: 'println(os_name())\nprintln(is_terminal(stdout))\nprintln(is_err(terminal_size()))\n',
  host: 'println(len(cwd()) > 0)\nprintln(len(hostname()) > 0)\nprintln(len(temp_dir()) > 0)\nprintln(is_ok(home_dir()) or is_err(home_dir()))\n',
  temp: 'p = make_temp_file("t-")?\nprintln(path_exists(p))\nremove_file(p)?\nwrite_file("a.txt", "hi")?\nprintln(read_file("a.txt")?)\n',
  dates: 'println(iso(to_utc(1700000000s)))\nprintln(format_time(DateTime(2026, 11, 4, 16, 5), "%A %B %e"))\nprintln(parse_iso("2026-02-30"))\nprintln(to_zone(1700000000s, "America/Los_Angeles"))\nprintln(iso(to_local(0s)))\n',
  exit3: 'println("before")\nexit(3)\n',
  signals: 'rx = signals()\nprintln("x")\n',
  net: 'println(connect("example.com", 80))\n',
  dns: 'println(lookup_host("localhost"))\n',
  proc: 'println(run_command("echo", List("hi")))\n',
  prop: 'test "t":\n  forall xs: List[Int]:\n    assert(len(xs) < 3, "long")\n',
};
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const logs = [];
  page.on('console', m => logs.push('console: ' + m.text()));
  page.on('pageerror', e => logs.push('pageerror: ' + e.message));
  await page.goto('http://localhost:8765/try.html?pyodide=/pyodide/');
  await page.waitForFunction(() => !document.getElementById('run').disabled, null, { timeout: 120000 });
  console.log('status:', await page.textContent('#status'));
  for (const [name, src] of Object.entries(progs)) {
    await page.fill('#src', src);
    const mode = name === 'prop' ? 'test' : 'run';
    await page.click('#' + mode);
    await page.waitForFunction(() => !document.getElementById('run').disabled, null, { timeout: 60000 }).catch(() => {});
    await page.waitForTimeout(400);
    const out = (await page.textContent('#out')).trim();
    console.log(`== ${name}\n${out.slice(0, 500)}`);
  }
  console.log(logs.slice(0, 10).join('\n'));
  await browser.close();
})();
