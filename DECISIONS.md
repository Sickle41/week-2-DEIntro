# DECISIONS.md

> Day 3 deliverable. Real data engineers leave a trail of *why*, not just *what*.
> Keep this short and honest — a few sentences per question. You're defending the
> calls you made, including the tools you reached for.

## 1. Dedup: which row wins, and how did you pick it?

`raw_orders` had the same `order_id` more than once. How did you decide which
copy to keep, and what would break if you'd kept the wrong one?

_Your answer:_

## 2. The NULL customer_id orders — what did you do with them?

Some orders have no `customer_id`. They survive `clean_orders` but fall out of
`customer_order_summary`. Was that the right call? Where did that revenue go, and
how would you report it to someone who asked "do our customer totals add up?"

_Your answer:_

## 3. Dates: how did you handle the three formats?

`order_date` arrived as `05-Jan-2024`, `2024-02-11`, and `03/02/2024`. What did
your parsing look like, and how did you make sure none came out NULL?

_Your answer:_

## 4. SQL vs. Polars: why was `tag_revenue` the one you moved?

You did every other transform in SQL and `tag_revenue` in Polars. Why that one?
What made it a better fit for a DataFrame — and, just as important, why did you
NOT move the others? (The point of the week is *choosing*, not switching.)

_Your answer:_

## 5. Parameter binding: why not just f-string it?

`customer_order_summary` takes `min_orders` as a bound parameter. What's the
argument for binding over building the SQL string yourself with an f-string?

_Your answer:_

## 6. If this were 100x bigger

One thing in your pipeline you'd reconsider if `orders` were 3 billion rows
instead of 30 thousand:

_Your answer:_
