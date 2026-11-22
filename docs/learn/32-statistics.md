---
layout: default
learn: true
title: "Statistics and prediction · Learning Guide moxie"
---
<p><small>Data from outside</small></p>

# 41. Statistics and prediction

The standard `stats` package is a small library for learning how data turns into numbers, and how those numbers turn into predictions. Every function in it is short enough to read (it is `moxie/std/stats.mxi`), and it works on an `Array[Double]`. Write `import stats` and call `stats.mean(xs)`.

It is a teaching library, not a replacement for a numeric toolkit, and being written in moxie it is slow on large data.

## Describing one list of numbers

The **mean** is the average. The **median** is the middle value, so a few extreme values move the mean but barely move the median. The **standard deviation** says how far values typically sit from the mean. A **quantile** is the value below which that fraction of the data falls, from `0.0` (the smallest) to `1.0` (the largest).

```moxie
import stats

scores Array[Double] = (62.0, 71.0, 71.0, 75.0, 80.0, 84.0, 98.0)
println("mean ${stats.mean(scores):.1f}, median ${stats.median(scores):.1f}")
println("spread ${stats.stddev(scores):.2f}")
when stats.quantile(scores, 0.9)
  Ok(q) -> println("90th percentile ${q:.1f}")
  Err(e) -> println("bad quantile")
```
**Output:**

```
mean 77.3, median 75.0
spread 10.69
90th percentile 89.6
```

`variance` and `stddev` treat the values as the whole population and divide by `n`. When the values are a sample of something larger, use `sample_variance` and `sample_stddev`, which divide by `n - 1`.

`quantile` returns a `Result`, because a `q` outside `0.0` to `1.0` has no answer:

```moxie
import stats

xs Array[Double] = (1.0, 2.0, 3.0)
println(stats.quantile(xs, 1.5))
println(stats.sample_stddev(xs))
```
**Output:**

```
Err(Error(code: 1, message: "quantile: q must be between 0.0 and 1.0"))
1.0
```

`z_scores(xs)` gives each value as a number of standard deviations from the mean, and `total` adds them up.

## Predicting with a straight line

**Correlation** runs from `-1.0` to `1.0` and says how closely two lists move along a straight line together. `fit_line(xs, ys)` finds the **least-squares line**, the one with the smallest squared errors in `y`, and returns a `Line` with a `slope`, an `intercept`, and an `r_squared`. `predict(line, x)` reads a prediction off the line.

```moxie
import stats

hours Array[Double] = (1.0, 2.0, 3.0, 4.0, 5.0)
score Array[Double] = (52.0, 58.0, 65.0, 70.0, 78.0)
when stats.fit_line(hours, score)
  Err(e) -> println("cannot fit: ${e.message}")
  Ok(line) ->
    println("each hour adds ${line.slope:.1f} points, starting from ${line.intercept:.1f}")
    println("r squared ${line.r_squared:.3f}")
    println("6 hours predicts ${stats.predict(line, 6.0):.1f}")
    fitted = stats.predict_all(line, hours)
    println("typical error ${stats.rmse(score, fitted):.2f} points")
```
**Output:**

```
each hour adds 6.4 points, starting from 45.4
r squared 0.996
6 hours predicts 83.8
typical error 0.57 points
```

`r_squared` is the share of the variation in `y` that the line explains: `1.0` is a perfect fit, and `0.0` is no better than always guessing the mean of `y`. `rmse` (the typical size of the errors, with big mistakes counting extra) and `mean_absolute_error` (every error counts the same) measure how far predictions are from what really happened.

Two cautions. A prediction far outside the range of the data (60 hours, say) is a guess that the line keeps going, not something the data showed. And a strong correlation says that two things move together, not that one causes the other.

`fit_line` returns an `Err` when there is nothing to fit, as when every `x` is the same:

```moxie
import stats

x Array[Double] = (3.0, 3.0, 3.0)
y Array[Double] = (1.0, 2.0, 3.0)
when stats.fit_line(x, y)
  Err(e) -> println(e.message)
  Ok(line) -> println("fitted")
```
**Output:**

```
fit_line: every x is the same, so there is no line to fit
```

The two arrays given to `covariance`, `correlation`, `fit_line`, `rmse`, and `mean_absolute_error` must have the same number of values. A difference the compiler can see (two arrays of known, different sizes) is a compile error; otherwise the program stops with a failed assertion.

## A series over time

A **moving average** replaces each value by the average of the last few, which smooths out the ups and downs. **Exponential smoothing** keeps a running level that each new value pulls toward itself by `alpha`: a big `alpha` follows the data closely, and a small one changes slowly. The level after the last value is also a forecast for the next one.

```moxie
import stats

sales Array[Double] = (20.0, 24.0, 22.0, 28.0, 27.0, 33.0)
println(stats.moving_average(sales, 3))
println("forecast ${stats.smooth(sales, 0.5):.2f}")
println("slow forecast ${stats.smooth(sales, 0.1):.2f}")
```
**Output:**

```
List(22.0, 24.666666666666668, 25.666666666666668, 29.333333333333332)
forecast 29.50
slow forecast 22.99
```

The slow forecast lags behind a series that is climbing, and that is the trade-off between smoothing the noise and following a real change.

## What to remember

- `import stats`; every function takes an `Array[Double]`.
- `mean`, `median`, `stddev`, `quantile` describe; `fit_line` and `predict` forecast; `moving_average` and `smooth` follow a series.
- `quantile` and `fit_line` return a `Result`.
- Arrays that must pair up have to be the same length.
- A prediction far outside the data is a guess; a high `r_squared` is not proof of cause.

*In the Spec: [23a. Statistics and prediction (the `stats` package)](../spec.html#s23a)*

---

[← Regular expressions](31-regex.html) · [Contents](./) · [Networking, deadlines, and parallel work →](33-networking.html)
