---
layout: default
dialect: gc
learn: true
title: "Machine learning, lite · Moxie/gc Mixer’s Guide"
---
# 75. Machine learning, lite

The `ml` package is a small set of machine-learning methods that you can read in an afternoon. It works on one number per example, so it teaches the ideas: a model learns a rule from examples, and then it predicts a label for something new. It is not a deep-learning toolkit, and it isn't meant for large data. Import it with `import ml`.

## Learning a rule from labelled examples

A *classifier* learns from examples whose label is known. Here each example is one number, and its label is 0.0 or 1.0. `fit` trains a logistic model by gradient descent: it nudges the weight and bias a little downhill on the average error, many times over.

```moxie
import ml
xs Array[Double] = (0.0, 1.0, 2.0, 3.0)
ys Array[Double] = (0.0, 0.0, 1.0, 1.0)
when ml.fit(xs, ys, 0.5, 2000)
  Err(e) -> println("no model: ${e.message}")
  Ok(m) -> println("${ml.classify(m, 0.5)} ${ml.classify(m, 2.5)}")
```
**Output:**

```
0.0 1.0
```

`fit` returns a `Result`, because bad input is an `Err` rather than a surprise. Its rules are the ones a reader would expect: the labels must be 0.0 or 1.0, the number of steps must not be negative, and there must be at least one example. A label outside those values is caught when the program runs.

```moxie
import ml
xs Array[Double] = (0.0, 1.0)
bad Array[Double] = (0.0, 2.0)
when ml.fit(xs, bad, 0.5, 10)
  Err(e) -> println(e.message)
  Ok(m) -> println("trained")
```
**Output:**

```
fit: labels must be 0.0 or 1.0
```

Two arrays of *known, different* sizes are a compile error instead, because the compiler can see the mismatch before the program runs.

```moxie
xs Array[Double] = (0.0, 1.0)
ys Array[Double] = (0.0, 1.0, 1.0)
println(ml.fit(xs, ys, 0.5, 10))
```

## What the model says

A `Model` holds a weight and a bias. `probability` gives the chance that an example is in class 1, and `classify` picks the class with the higher chance, which is 1.0 at a probability of one half or more.

```moxie
import ml
m = ml.Model(weight: 2.0, bias: -4.0)
println(ml.probability(m, 2.0))
println(ml.classify(m, 1.0))
println(ml.classify(m, 3.0))
```
**Output:**

```
0.5
0.0
1.0
```

## Learning from a neighbour

The nearest-neighbour rule needs no training at all. To label a new number, take the example whose value is closest to it and copy its label. Ties go to the first example in the list.

```moxie
import ml
xs Array[Double] = (0.0, 1.0, 2.0, 3.0)
ys Array[Double] = (0.0, 0.0, 1.0, 1.0)
when ml.nearest_label(xs, ys, 2.4)
  Err(e) -> println("no neighbour")
  Ok(label) -> println(label)
```
**Output:**

```
1.0
```

## Finding two groups

Clustering finds structure without labels. `two_means` splits the numbers into two groups. Its two centres start at the smallest and the largest value, and each step gives every number to its nearer centre and then moves each centre to the average of its group. A few steps are enough for well-separated groups.

```moxie
import ml
when ml.two_means((1.0, 2.0, 10.0, 11.0), 5)
  Err(e) -> println(e.message)
  Ok(centres) -> println(centres)
```
**Output:**

```
(1.5, 10.5)
```

## What to remember

- A model learns from examples, and the labels tell it what right looks like.
- Every function in `ml` is a few lines you can read. Read `one_gradient_step` in `moxie/std/ml.mxi` to see the whole method.
- Bad input comes back as an `Err`, and mismatched sizes that the compiler can see are compile errors.
- Real machine learning uses far more data, features and methods than this package does. The point here is the shape of the ideas.

---

[← Unifying tuples and parameter lists](75-unifying-tuples-and-parameters.html) · [Contents](./) · [Where to go next →](64-where-to-go-next.html)
