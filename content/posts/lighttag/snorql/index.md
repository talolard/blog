+++
title = "SnorQL: Scaling Weak Supervision With SQL"
date = 2021-02-08T00:00:00Z
draft = false
description = "A SQL-first approach to authoring, running, and analyzing weak-supervision labeling functions at scale."

[social]
image = "social.webp"
image_alt = "Archive cover for SnorQL: Scaling Weak Supervision With SQL."

[share]
disable = false
languages = ["en"]

[original_publication]
site = "LightTag.io"
path = "/blog/snorql/"
+++
<!-- markdownlint-disable MD046 -->

Snorkel promises "Data Programming" - the user writes noisy labeling functions, and Snorkel learns probabilistic labels we can use as training data. No more labeling, yay!

We tried Snorkel to use Snorkel with a dataset comprised of fifteen million Hebrew tweets. Working at that scale out of the box was challenging and took some effort . This article discusses a few tricks that simplified working with Snorkel at a moderate scale.

## How Snorkel Works

Snorkel lets the users define Labeling Functions (LF) such that each labeling function can output one of the k classes or abstain.

Snorkel learns a model by looking at the co-occurrences of labels from different functions. We provide Snorkel with a matrix of empirical co-occurrences, e.g., a statistical summary of our labeling functions.  Snorkel then generates a model that "explains" those co-occurrences.

## A Taxonomy Of Data Representations

Snorkel views the same data in different ways. To make things more readable, let's define what those are.

A **LabelFrame** is a table whose rows correspond to a document, columns correspond to a labeling function, and the value at cell (i,j) is the class_id that labeling function j assigned to document i.

|   doc_id |   func_0 |   func_1 |   func_2 |   func_3 |
|---------:|---------:|---------:|---------:|---------:|
|        0 |        5 |        0 |        3 |        9 |
|        1 |        4 |        2 |        1 |        4 |
|        2 |        6 |        7 |        3 |        1 |
|        3 |        5 |        0 |        1 |        1 |
|        4 |        3 |        9 |        2 |        7 |

The LabelFrame representation isn't convenient for counting co-occurrences of LFs. We'd rather have a flatter representation, such that each column represents an event like "LF i predicted class j," and the values are 0 are 1.

|   doc_id |   e_0 |   e_1 |   e_2 |   e_3 |   e_4 |   e_5 |   e_6 |   e_7 |   e_8 |   e_9 |   e_10 |   e_11 |
|---------:|------:|------:|------:|------:|------:|------:|------:|------:|------:|------:|-------:|-------:|
|        0 |     1 |     0 |     0 |     0 |     0 |     1 |     0 |     1 |     0 |     0 |      1 |      0 |
|        1 |     0 |     0 |     1 |     1 |     0 |     0 |     1 |     0 |     0 |     0 |      0 |      1 |
|        2 |     0 |     1 |     0 |     0 |     0 |     1 |     0 |     0 |     1 |     0 |      1 |      0 |
|        3 |     0 |     1 |     0 |     0 |     0 |     1 |     0 |     0 |     1 |     0 |      1 |      0 |
|        4 |     0 |     1 |     0 |     0 |     1 |     0 |     0 |     0 |     1 |     0 |      0 |      1 |

We'll call each such column an **Event**, and we'll index them so that the Event for function i predicted class j is indexed as i\*num\_labels+j. And the index of events runs from 0 to num_labels\*num_functions

We can convert the LabelFrame to have **Event** columns, and we'll call that the **AugmentedFrame**, and each row as an **AugmentedVector**.

The AugmentedFrame has dimensions (num_docs,num_events). A lucky happenstance of linear algebra tells us that AugmentedFrame.T\*AugmentedFrame is a matrix of size (num_events,num_events) such that cell (i,j) is the number of times that Event i co-occurred with Event j in a document.

We call  AugmentedFrame.T*AugmentedFrame the **ObjectiveMatrix**.

| event_id   |   e_0 |   e_1 |   e_2 |   e_3 |   e_4 |   e_5 |   e_6 |   e_7 |   e_8 |   e_9 |   e_10 |   e_11 |
|:-----------|------:|------:|------:|------:|------:|------:|------:|------:|------:|------:|-------:|-------:|
| e_0        |     1 |     0 |     0 |     0 |     0 |     1 |     0 |     1 |     0 |     0 |      1 |      0 |
| e_1        |     0 |     3 |     0 |     0 |     1 |     2 |     0 |     0 |     3 |     0 |      2 |      1 |
| e_2        |     0 |     0 |     1 |     1 |     0 |     0 |     1 |     0 |     0 |     0 |      0 |      1 |
| e_3        |     0 |     0 |     1 |     1 |     0 |     0 |     1 |     0 |     0 |     0 |      0 |      1 |
| e_4        |     0 |     1 |     0 |     0 |     1 |     0 |     0 |     0 |     1 |     0 |      0 |      1 |
| e_5        |     1 |     2 |     0 |     0 |     0 |     3 |     0 |     1 |     2 |     0 |      3 |      0 |
| e_6        |     0 |     0 |     1 |     1 |     0 |     0 |     1 |     0 |     0 |     0 |      0 |      1 |
| e_7        |     1 |     0 |     0 |     0 |     0 |     1 |     0 |     1 |     0 |     0 |      1 |      0 |
| e_8        |     0 |     3 |     0 |     0 |     1 |     2 |     0 |     0 |     3 |     0 |      2 |      1 |
| e_9        |     0 |     0 |     0 |     0 |     0 |     0 |     0 |     0 |     0 |     0 |      0 |      0 |
| e_10       |     1 |     2 |     0 |     0 |     0 |     3 |     0 |     1 |     2 |     0 |      3 |      0 |
| e_11       |     0 |     1 |     1 |     1 |     1 |     0 |     1 |     0 |     1 |     0 |      0 |      2 |

## The Challenges

Snorkels algorithm uses SGD to learn a decomposition of the ObjectiveMatrix. That decomposition gives a mapping from AugmentedVectors to probabilities of the true class, e.g., the noisy probabilistic labels that Snorkel promised.

The first challenge is generating the LabelFrame itself. When the number of documents is large, running multiple functions against each document is slow.

The second challenge is transitioning from the LabelFrame to the ObjectiveMatrix.

The intermediate representation, the AugmentedFrame, is very sparse and very big (num_docs,num_events), consumes a lot of memory, and is slow to generate at scale.

The ObjectiveMatrix is created by multiplying the   AugmentedFrame with its transpose. With millions of documents, the transformations are memory intensive and slow. Slow to the tune of  "my computer locked until the process crashed with an out of memory error." In our neck of the woods, that's a problem.

## The Punchline: We Did Everything In SQL

There are many ways to overcome big data problems, mostly with "big data" tooling. But this isn't really "big data." It's a few gigabytes of text and a lackluster environment for manipulating data in the way we need.

To generate our label functions fast, we wrote them as SQL queries and stored their outputs in a SQL table. What made this fast was a judicial use of SQL indices:

Our labeling functions were based on keyword search and metadata manipulation. Using Postgres trigram indices, we could run regular expression queries over the 15M docs in a second or two.  We generated  10M weak labels via 14 functions in an hour and a half.

Here's an example, we're searching for the Hebrew slang word סמולן in 15M documents in 15ms.

```sql
hebrewtweets=# explain analyze select * from tweets where text ~'סמולן';
```

## QUERY PLAN

     Bitmap Heap Scan on tweets  (cost=64.03..6012.65 rows=1553 width=186) (actual time=11.752..15.600 rows=1281 loops=1)
       Recheck Cond: (text ~ 'סמולן'::text)
       Rows Removed by Index Recheck: 85
       Heap Blocks: exact=1346
       ->  Bitmap Index Scan on trgm_idx  (cost=0.00..63.65 rows=1553 width=0) (actual time=11.590..11.590 rows=1366 loops=1)
             Index Cond: (text ~ 'סמולן'::text)
     Planning Time: 0.942 ms
     Execution Time: 15.705 ms
    (8 rows)

SQL also made the transformations simple.  We stored each weak label in a SQL table and used a sequence of aggregations to generate the various representations. SQL was a good fit because the data is extremely sparse, and SQL natively stores and operates on only the "non-sparse rows."  Again, judicial use of indices and materialized views made this fast.

Yes, we could have used sparse matrices (and indeed we tried), but loading the sparse data from SQL and converting it to a sparse matrix was slow. More importantly, we figured out an orders of magnitude performance improvement at inference using SQL (more below).

## The Orders Of Magnitude Faster Inference Trick

Let's recap how we train Snorkel. We convert the LabelFrame to the AugmentedFrame and then derive the ObjectiveMatrix from the AugmentedFrame. We train Snorkel to find a decomposition of the ObjectiveMatrix, which gives us a mapping from an AugmentedVectors to a noisy, probabilistic approximation of the true label.

So at inference, Snorkel's input is an AugmentedVector. Now, while we have millions of documents and millions of possible AugmentedVectors, we realized that the number of distinct AugmentedVectors that our LFs induces was small. Our experiment had 15 million documents, 4,782,969 possible AugmentedVectors, but only 384 distinct AugmentedVectors induced by the labeling functions.

That means that instead of running inference on 15 million different items, we could run inference once for the 384 distinct AugmentedVectors, store the results in a table and associate them to the corresponding documents with a join.
That's a 39,000X decrease in compute needs. A win!

## But We Had To Write Python as Well :-(

The open source Snorkel library does many things and tries to keep life simple for the average user (Generating an opportunity to monetize the advanced user).
The code that trains the underlying Snorkel model is built around transforming LabelFrames to AugmentedFrames. It also has a lot of scaffolding for features that weren't implemented.

Our approach essentially replaced Snorkel's data processing with our own, and we ended up having to reimplement (e.g. copy paste just the relevant parts).

## Enough bragging, show me that beautiful SQL

So in this part I'll walk you through the high level SQL we used.

### Table Setup

```sql
CREATE EXTENSION pg_trgm
create table tweets (
    text text,
    tweet_id bigint ,
    created_at timestamp,
    user_name text,
    user_screen_name text,
    user_id bigint
);
alter table tweets add constraint unique_tweet_id UNIQUE (tweet_id);
create index on tweets (used_id,tweet_id);
create table label (
    id serial primary key deferrable initially deferred,
    name text not null unique
);
create table function (
    name text not null primary key ,
    query text not null,
    id serial
);
create table prediction (
    funcname text not null ,
    tweet_id bigint not null ,
    label_name text not null ,
    primary key (funcname,tweet_id)
) ;
create index tweet_label_ix on prediction (label_name,tweet_id);
```

### Adding A Label Function

```sql
INSERT INTO prediction
select distinct on (tweet_id) 'ראש הממשלה' as funcname,tweet_id,'right'
from tweets
 where text ~'ראש הממשלה'

```

### Adding A Fancy Label Function

After we did a few label functions based on the tweet content, we wanted to use the information we gathered to make noisy labels based on the tweet user. Here's an example, that assigns a label to all tweets from a user if the majority of the users tweets were noisily labeled as left or right

```sql
with x as (
    select used_id, label_name, count(*) c
    from prediction
             inner join tweets t using (tweet_id)
    where label_name <> 'noise'
    group by used_id, label_name
    order by c desc
),
ratios as (
    select *
   ,   l.c::float /r.c ratio from x l inner join x r using (used_id)
    where l.label_name='left' and r.label_name='right'
    ),
preds as (

    select 'ratio' as funcname,
    tweet_id,
    case
    when ratio>2 then 'right'
    when ratio <0.5 then 'left'
    end
    as label_name
    from ratios
    inner join tweets using (used_id)

    )
insert into prediction
select * from preds where label_name is not null
on conflict do nothing;

```

### What Our Prediction Table Looked Like

So after populating predictions from label functions, we get a table that looks like this:

    hebrewtweets=#  select * from prediction order by tweet_id limit 5;
     funcname |      tweet_id      | label_name
    ----------+--------------------+------------
     ratio    | 972148187900399622 | right
     ratio    | 972148195143946240 | left
     short    | 972148216245440512 | noise
     ratio    | 972148222822109184 | right
     ratio    | 972148223342252032 | right

Or, joining on the function and label tables:

    hebrewtweets=# select tweet_id,function.id as function_id,l.id as label_id from prediction
    hebrewtweets-#          inner join function on funcname = name
    hebrewtweets-#          inner join label l on prediction.label_name = l.name
    hebrewtweets-# order by tweet_id
    hebrewtweets-# limit 5;
          tweet_id      | function_id | label_id
    --------------------+-------------+----------
     972148187900399622 |           8 |        3
     972148195143946240 |           8 |        2
     972148216245440512 |           7 |        1
     972148222822109184 |           8 |        3
     972148223342252032 |           8 |        3

## Creating The Statistics For Snorkel

So to make the AugmentedFrame, we can do the following query. We put it into a materialized view for fast access, and added an index on it.

### Mapping predictions to Events

```sql
create materialized view  augmented_frame as
(
with base as (
    select tweet_id, label.id as label_id, f.id as func_id
    from prediction
             inner join label on label_name = label.name
             inner join function f on funcname = f.name
),
     lnum as (
         select count(*) numlabels
         from label
         where id > -1
     ),
     composed as (
         select (func_id * (numlabels - 1)) + label_id event_id, tweet_id
         from base,
              lnum
     ),
     co_oc as (
         select tweet_id, array_agg(event_id order by event_id) co
         from composed
         group by tweet_id
     )
select *
from co_oc
    );

```

So this gives us the AugmentedVector for each tweet.

    hebrewtweets=# select * from augmented_frame where array_length(co,1) >2 limit 10;
          tweet_id      |     co
    --------------------+------------
     972368366546702336 | {20,27,39}
     972380011910127616 | {14,20,27}
     972397589130809344 | {6,27,41}
     972400137967407104 | {9,27,33}
     972400203239182336 | {20,27,36}
     972440476480688129 | {20,27,39}
     972447234418724865 | {27,33,39}
     972451277111250945 | {20,27,39}
     972451749574438912 | {14,20,27}
     972459339293261824 | {20,27,39}

### Generating The Objective Matrix

So to generate our objective matrix, the thing that Snorkel is optimizing on, we just need to take a count of the co column

```sql
create view objective_matrix as (
select co, count(*) frequency
from augmented_frame
group by co
);
```

    select * from objective_matrix limit 10;
          co      | frequency
    --------------+-----------
     {2}          |       726
     {2,6,27}     |         1
     {2,11}       |         1
     {2,11,20,27} |         1
     {2,20}       |         6
     {2,20,26}    |         1
     {2,20,27}    |        36
     {2,20,27,39} |         1
     {2,26}       |        56
     {2,26,33}    |         2

And all we have left is to load it into Python and feed it to Snorkel

```python
    num_docs = 9413449
    num_funcs=14
    num_classes = 3
    num_events = num_funcs*num_classes

    objective = np.zeros((num_events,num_events))
    from sqlalchemy import create_engine
    engine = create_engine('postgresql://***:****@localhost:5432/hebrewtweets')

    with engine.connect() as connection:
        result = connection.execute("select * from objective_matrix")
        for num,row in enumerate(result):
            co_oc_array = row['co']
            frequency = row['frequency']
            for i in co_oc_array:
                for j in co_oc_array:
                    objective[i,j] += frequency
                    objective[j, i] += frequency
    model = train_model(num_funcs,num_classes,objective/num_docs)

```

## Conclusion

So that's the bulk of the story. Let us know in the discussions if you liked it, and we'll keep posting about our work with Weak Supervision and Snorkel.
