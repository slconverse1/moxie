"""Observed resource use (the run-time counterpart of the compiler's pool tally, Spec section 19).

The reference interpreter has no compiler tally yet, so `moxie --pools run FILE` reports the
highest number of each kind of resource that was open at once.  The compiler's static tally must
be at least this large for any run.
"""


class Pools:
    def __init__(self):
        self.open = {}
        self.peak = {}
        self.total = {}

    def acquire(self, kind):
        n = self.open.get(kind, 0) + 1
        self.open[kind] = n
        self.total[kind] = self.total.get(kind, 0) + 1
        if n > self.peak.get(kind, 0):
            self.peak[kind] = n

    def release(self, kind):
        self.open[kind] = max(0, self.open.get(kind, 0) - 1)

    def report(self):
        if not self.peak:
            return "pool report: nothing counted was created\n"
        w = max(len(k) for k in self.peak)
        out = ["pool report (observed): kind, most open at once, total opened"]
        for k in sorted(self.peak):
            out.append(f"  {k.ljust(w)}  {self.peak[k]:>4}  {self.total[k]:>6}")
        out.append("  (a resource that goes out of scope without being closed or dropped counts as open until its fiber or the program ends;")
        out.append("   Timers and Atoms are never released)")
        return "\n".join(out) + "\n"
