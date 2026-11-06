"""Signatures of prelude functions for the checker (check.py), written as moxie declarations in the order the arguments really
go (a stage takes its function first and its source last: `map(f, xs)`).  A name may have several: the checker uses an overload
only when exactly one fits the argument types it knows, so a call with an unknown argument is left unknown.  `Seq[T]` stands for
any source of T values: a List, an Array, a Set, a Ring, or a Stream.  The bodies are placeholders; only the headers are read.
"""

SRC = '''
fn map[T, U](f: (T) -> U, xs: Seq[T]) Stream[U]: 0
fn map[T, U, E](f: (T) -> U, r: Result[T, E]) Result[U, E]: 0
fn filter[T](f: (T) -> Bool, xs: Seq[T]) Stream[T]: 0
fn take[T](n: Int, xs: Seq[T]) Stream[T]: 0
fn drop[T](n: Int, xs: Seq[T]) Stream[T]: 0
fn take_while[T](f: (T) -> Bool, xs: Seq[T]) Stream[T]: 0
fn drop_while[T](f: (T) -> Bool, xs: Seq[T]) Stream[T]: 0
fn enumerate[T](xs: Seq[T]) Stream[(Int, T)]: 0
fn zip[A, B](a: Seq[A], b: Seq[B]) Stream[(A, B)]: 0
fn sort[T](xs: Seq[T]) Stream[T]: 0
fn sort_by[T, K](f: (T) -> K, xs: Seq[T]) Stream[T]: 0
fn reverse[T](xs: Seq[T]) Stream[T]: 0
fn reduce[T, A](init: A, f: (A, T) -> A, xs: Seq[T]) A: 0
fn collect[T](xs: Seq[T]) List[T]: 0
fn sum[T](xs: Seq[T]) T: 0
fn product[T](xs: Seq[T]) T: 0
fn count[T](xs: Seq[T]) Int: 0
fn any[T](f: (T) -> Bool, xs: Seq[T]) Bool: 0
fn all[T](f: (T) -> Bool, xs: Seq[T]) Bool: 0
fn find[T, E](f: (T) -> Bool, xs: Seq[T]) Result[T, E]: 0
fn first[T, E](xs: Seq[T]) Result[T, E]: 0
fn last[T, E](xs: Seq[T]) Result[T, E]: 0
fn partition[T](f: (T) -> Bool, xs: Seq[T]) (List[T], List[T]): 0
fn unzip[A, B](xs: Seq[(A, B)]) (List[A], List[B]): 0
fn upper(s: String) String: 0
fn upper(c: Char) Char: 0
fn lower(s: String) String: 0
fn lower(c: Char) Char: 0
fn abs(n: Int) Int: 0
fn abs(x: Double) Double: 0
'''
