+++
title = "Postgres Range Aggregation for NLP and Everything Else"
date = 2019-10-18T00:00:00Z
draft = false
description = "A practical PostgreSQL pattern for finding maximal containing spans across overlapping ranges."

[social]
image = "social.webp"
image_alt = "Archive cover for Postgres Range Aggregation for NLP and Everything Else."

[share]
disable = false
languages = ["en"]

[original_publication]
site = "LightTag.io"
path = "/blog/psql-range-aggregation-for-nlp/"
+++
<!-- markdownlint-disable MD060 -->

[Range types](https://www.PostgreSQL.org/docs/9.3/rangetypes.html) are one of our favorite features in Postgres, we use them for NLP to
detect conflicting entity annotations . Doing so requires finding the "Maximal Containing Span" - the union of all of the overlapping spans in a set of spans. Our preference is to do that in the database and this post shows how we do so.

## The Problem We're Trying to Solve

![conflict](conflict.webp)
We often want to find the maximal overlapping range for example:

```text
[0,5] => [0,5]
[0,5], [3,6] => [0,6]
[0,5], [3,6], [5,12] ==> [0,12]
```

Concretely, say we have a table in Postgres that looks like this:

----------------------

| source_id | span |
| :-----------: | :-----: |
| 1 | [0,2) |
| 1 | [3,5) |
| 1 | [4,10) |
| 2 | [11,100) |
| 2 | [25,28) |
| 2 | [50,99) |
| 2 | [98,102) |
| 2 | [101,104) |
| 2 | [103,106) |
| 2 | [110,116) |

And we want to associate every span in a given source to the longest overlapping span it's contained in, like this:

----------------------

| source_id | span | max-span |
| ---------- | ----- | ----------- |
| 1 | [0,2) | [0,2) |
| 1 | [3,5) | [3,10) |
| 1 | [4,10) | [3,10) |
| 2 | [11,100) | [11,106) |
| 2 | [25,28) | [11,106) |
| 2 | [50,99) | [11,106) |
| 2 | [98,102) | [11,106) |
| 2 | [101,104) | [11,106) |
| 2 | [103,106) | [11,106) |
| 2 | [110,116) | [110,116) |

We want to be able to do this in the database, so that we can filter or analyze the data based on additional conditions.

## Prior Art

The best solution we've found on the internet is in the [Postgres Wiki](https://wiki.PostgreSQL.org/wiki/Range_aggregation) and while it works, we weren't happy with it because it decomposes a range into its start and end, which means we can no longer leverage indices and our queries will be slow.

In an ideal world we'd have an aggregate function SUM that would do

```text
SUM( [0,5], [3,6]) => [0,6] # The union operator
SUM ([0,5], [3,6], [5,12]) ==> [0,12]
```

Postgres has no built in union-like aggregation function for ranges out of the box. That's understandable, what would happen in the case of non-overlapping ranges ?

```text
SUM([0,5], [10,20]) => ?????
```

## The Solution

The outline of the solution we're using is as follows:

1. Define a custom aggregation function for range types
2. Use that aggregation function in a Postgres window to calculate "Left-Max Containing Spans"
3. Group by the left point of each "Left-Max Containing Span" and aggregate to get the  "Max Containing Span"
4. Join on the original table to associate each row with it's Max Containing Span

Let's see that in action

### Data

To make the problem more concrete and set up our solution, we'll define the following table:

```sql
create temporary table example
(
  source_id integer, --Where did this range come from ?
  span      int4range
);
insert into example
VALUES (1, '[0,2)'),
       (1, '[3,5)'),
       (1, '[4,10)'),
       (2, '[11,100)'),
       (2, '[25,28)'),
       (2, '[50,99)'),
       (2, '[98,102)'),
       (2, '[101,104)'),
       (2, '[103,106)'),
       (2, '[110,116)');

```

```sql
select * from example
```

----------------------

| source_id | span |
| :-----------: | :-----: |
| 1 | [0,2) |
| 1 | [3,5) |
| 1 | [4,10) |
| 2 | [11,100) |
| 2 | [25,28) |
| 2 | [50,99) |
| 2 | [98,102) |
| 2 | [101,104) |
| 2 | [103,106) |
| 2 | [110,116) |

This table has a collection of ranges from two different sources. In LightTag's case, that might to correspond to a collection of annotations made in different documents (the source_id). Obviously, we don't want to calculate overlapping ranges from different sources.

The result we want looks like this:

| source_id | span | max_span |
| ---------- | ----- | ----------- |
| 1 | [0,2) | [0,2) |
| 1 | [3,5) | [3,10) |
| 1 | [4,10) | [3,10) |
| 2 | [11,100) | [11,106) |
| 2 | [25,28) | [11,106) |
| 2 | [50,99) | [11,106) |
| 2 | [98,102) | [11,106) |
| 2 | [101,104) | [11,106) |
| 2 | [103,106) | [11,106) |
| 2 | [110,116) | [110,116) |

### The wrong way to do windowing

A first step in our solution is to use [window function](https://www.PostgreSQL.org/docs/9.3/tutorial-window.html) to put the previous span next to
the current span, and check if they overlap

```sql
select *,
    lag(span) over w prev,
    lag(span) over w && span overlaps_with_prev
from example
window w as (partition by source_id order by span )
```

| source_id|span|prev|overlaps_with_prev |
|----------|----|----|-------------------|
| 1 | [0,2)||                            |
| 1 | [3,5) | [0,2)|false                |
| 1 | [4,10) | [3,5)|true                |
| 2 | [11,100)||                         |
| 2 | [25,28) | [11,100)|true            |
| 2 | [50,99) | [25,28)|false            |
| 2 | [98,102) | [50,99)|true            |
| 2 | [101,104) | [98,102)|true          |
| 2 | [103,106) | [101,104)|true         |
| 2 | [110,116) | [103,106)|false        |

The thing is, we don't want to know if it overlaps with the previous row, we want to know what the maximal containing range is.

### Writing a Custom Aggregate Function for Postgres

A step forward is to be able to take a rolling union of the spans, like a rolling sum or rolling average. This is tricky, because the union of two non-overlapping ranges is not defined. This is one of those cases where [the obstacle is the way](https://en.wikipedia.org/wiki/The_Obstacle_Is_the_Way).

If we have the spans in a given source sorted by their start position, then two consecutive spans either overlap or define the start of a new maximally containing span. With that in mind, we can write a [User Defined Function](https://www.PostgreSQL.org/docs/12/plpgsql.html) that implements that logic:

```sql
CREATE or REPLACE FUNCTION range_sum(accumulator int4range, current int4range)
  /*
    Utility function for range aggregation. Receives two ranges,
    the accumulator and the current. If they overlap then returns
    their union, otherwise returnsthe current.

    Note, aggreagtes are initialized with the empty range, so on
    first value will always returns current as desired. Thus no
    need for initial value spec   in the aggregate
  */
  returns int4range
  language plpgsql as
'
  begin
    return case
             when accumulator && current then accumulator + current
             else current end;
  end  ';
```

And then use it in a [User Defined Aggregate](https://www.PostgreSQL.org/docs/12/xaggr.html)

```sql
CREATE AGGREGATE range_sum ( int4range ) (
  SFUNC = range_sum,
  STYPE = int4range
  );
```

### Using the new Aggregate Function in a Window

We can use our new aggregate function inside of a window to give us a "rolling window" of range unions. That's a mouthful but the table illustrates it.

```sql
select *,
     range_sum(span) over w left_max_span
from example
window w as (partition by source_id order by span)

### ```
| source_id|span|left_max_span |
|----------|----|----------|
| 1| [0,2) | [0,2)         |
| 1| [3,5) | [3,5)         |
| 1| [4,10) | [3,10)       |
| 2| [11,100) | [11,**100**)   |
| 2| [25,28) | [11,**100**)    |
| 2| [50,99) | [11,**100**)    |
| 2| [98,102) | [11,**102**)   |
| 2| [101,104) | [11,**104**)  |
| 2| [103,106) | [11,**106**)  |
| 2| [110,116) | [110,116) |

Notice that in the column we just calculate, *left_max_span*, we've captured the left edge of a maximal containing span (hence we it's called left_max) but the right edge keeps changing as the window Postgres is running expands. We want the Max Span, so we have an aggregation step ahead of us.

### Aggregating the Left Max Spans to get the Complete Max Spans

If we group by the source_id and left edge of each left_max_span, we can use our aggregate function again to get the Max Span we're looking for.
```sql
  select source_id,
         lower(container) as  left_edge,
         range_sum(container) max_span -- using our aggregate function again, this time in a group by
  from (
         select *,
                range_sum(span) over w container
         from example window w as (partition by source_id order by span)
       ) A
  group by source_id, left_edge
```

### Gives us

| source_id|left_edge|max_span |
|----------|---------|---------|
| 1 | 0 | [0,2)                  |
| 1 | 3 | [3,10)                 |
| 2 | 11 | [11,106)              |
| 2 | 110 | [110,116)            |

## Joining the Max Span on to the Original Table

So now we have our max spans, we just need to join them back onto the original table. The key to this step is to realize that by construction, each span in the original table intersects with exactly one Max Containing Span. So our join condition between the two tables should be on source_id with equality and requiring an intersection between the max_span and the span in the original table.

```sql
select example.*, max_span
from example -- join the original table with the maximal spans
       inner join (
  select source_id,
         lower(container) as  left_edge,
         range_sum(container) max_span -- using our aggregate function again, this time in a group by
  from (
         select *,
                range_sum(span) over w container
         from example window w as (partition by source_id order by span)
       ) A
  group by source_id, left_edge
) B on
    B.source_id = example.source_id
    and B.max_span && example.span -- The example.span overlaps with exactly one max_span by construction
```

### Which gives us

| source_id|span|max_span   |
|----------|----|-----------|
| 1 | [0,2) | [0,2)         |
| 1 | [3,5) | [3,10)        |
| 1 | [4,10) | [3,10)       |
| 2 | [11,100) | [11,106)   |
| 2 | [25,28) | [11,106)    |
| 2 | [50,99) | [11,106)    |
| 2 | [98,102) | [11,106)   |
| 2 | [101,104) | [11,106)  |
| 2 | [103,106) | [11,106)  |
| 2 | [110,116) | [110,116) |

As desired :-)

> **NOTE**
  *We use a subquery here instead of a separate table or CTE for performance reasons. We think subqueries are hard to read, but PG treats them as an   optimization fence ([until version 12 comes out](https://paquier.xyz/PostgreSQL-2/Postgres-12-with-materialize/)). So, if you don't care about      performance or have PG12, you can and should refactor this to a CTE*

## Why do this ?

The guidance counselor at my school would frequently tell me "Just because you can, doesn't mean that you should." I can't say she ever convinced me but it's definitely food for thought when writing software. This particular solution isn't dead obvious and we had a much simpler solution where our app would load the data and calculate these max spans itself. So why add this complexity ?

In our use case this give us better user experience through improved response time (the queries are faster) and new capabilities. The new capabilities part is the what made the case, we can now run deeper queries on these "Max Containing Spans" while leveraging our database structure and functionality. We could do that in our app as well, but it quickly becomes a large project instead of a few additional lines of code.

## The Code

```sql
CREATE or REPLACE FUNCTION range_sum(accumulator int4range, current int4range)
  /*
    Utility function for range aggregation. Receives two ranges,
    the accumulator and the current. If they overlap then returns
    their union, otherwise returnsthe current.

    Note, aggreagtes are initialized with the empty range, so on
    first value will always returns current as desired. Thus no
    need for initial value spec   in the aggregate
  */
  returns int4range
  language plpgsql as
'
  begin
    return case
             when accumulator && current then accumulator + current
             else current end;
  end  ';
CREATE AGGREGATE range_sum ( int4range ) (
  SFUNC = range_sum,
  STYPE = int4range
  );
select *
from your_table
       inner join (
  select lower(cont) as l, range_sum(cont) max_span
  from (
         select *, range_sum(span) over w cont
         from your_table window w as ( order by span)
       ) A
  group by  l
) B on  B.range_sum && example.span
```
