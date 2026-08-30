+++
title = "The Joy of IndexedDB for NLP"
date = 2019-07-08T00:00:00Z
draft = false
description = "How browser-native full-text search can give domain experts fast access to text without a search cluster or operational burden."

[social]
image = "social.webp"
image_alt = "Archive cover for The Joy of IndexedDB for NLP."

[share]
disable = false
languages = ["en"]

[original_publication]
site = "LightTag.io"
path = "/blog/indexeddb-for-nlp/"
+++
## tl;dr
>
> - Textual search is the easiest way to apply domain expertise to a corpus of text
> - You think you need a server to power your text, but you are wrong.
> - You can do full text search in the browser.
> - That means there is no need for ops and engineering to start analyzing text.
> - [Here's an open source implementation](https://github.com/lighttag/ylabel)

As the CEO of LightTag, I don't get to do as much tech as I used too, much less talk about it in any depth. But today is a new day and today I'd like to share what I think about the browser, and how it's changing the way we do NLP.

## How We Look for Things in Text

 The power of the modern the browser is kind of stunning and it's worth stopping to think about what we can do with the browser today that we couldn't before. We'll get there, but let me talk about me for a minute. I've been working with text for the bulk of my career, and I've probably spent half that time running regular expressions in SQL, provisioning Elasticsearch clusters and waiting for Excel files to load, all so that I could look at the text I have and make sense of it, and if I was lucky, figure out what to do with it.

That trinity of Excel, SQL, and Elasticsearch actually outline the three things I needed when figuring out what my raw materials are. Excel provides an interface to view and comment on the data. SQL and Elasticsearch both provide two pillars, storage & persistence on the one hand, and large(ish) scale search on the other.

As I've progressed in my career I still work with text a lot, but I've come to realize that I understand SQL and Elasticsearch, I don't understand what's written in legal documents, patient records, Bloomberg chats or oil well drilling comments. The plus side is that other people do, lawyers can read contracts, doctors can read patient records, traders can read Bloomberg chats and people who drill for oil can read drilling comments. They, on the other hand, can't set up Elasticsearch and don't have the time to configure proper indexing in SQL. My job is to enable them.

Here's the thing, even though we are complementary, there are many of them and only one of me.

![One vs Many](oldboy-fight-scene.webp)

## I'm a bottleneck and so are you

 Sometimes I want to hire more of me, but I'm expensive and it only makes sense to hire more of me if the potential payoff is really big or at least really certain. At the onset of the project that's almost never the case, text analytics usually starts off with "here's a bunch of text what can we do with it" and a 1GB CSV file that crashes your computer when you load it in Excel (Don't worry, of course, I use VIM but Excel serves the narrative)

 Under those terms, a domain expert will try to load the file once or twice and then give up on the project before anything has even happened. Conversely, my doppelgänger is going to spend a week figuring out the latest and greatest in Elasticsearch and another two weeks getting a cluster up in Kubernetes because he can't understand the text but he gets paid for being a great engineer.

So, if you zoom in on this problem, it actually turns out that **engineering and ops stand between your domain experts and their text**. Of course, of course, *your* organization has great ops and everyone can access data easily, but a lot of other people and companies are suffering because **the lead time to saying something intelligent about a piece of text is governed by DevOps** and can be measured in weeks with no loss in accuracy.

## Maybe those frontend people are on to something

If you're "[a real systems programmer](https://www.usenix.org/system/files/1311_05-08_mickens.pdf)" or backend engineer you've spent some time looking down at those frontend people with their CSS and callback hell and months spent reconciling IE with Firefox. Maybe, just maybe, in your heart of hearts when you were in a dark mood, you thought less of them. Maybe you feel this way because the browser is basically an obstacle between the end user and your total genius. While *they* were busy aligning boxes to fit a mobile screen just right, you unleashed your genius to write a new version of [malloc](http://goog-perftools.sourceforge.net/doc/tcmalloc.html) so that you could multiply matrices even faster.

So even though the browser is the obstacle, it turns out that **you** are the bottleneck, and no one really cares about your fancy malloc. Just get out of the way as fast as you can so that people can do their job empowered by the tools you gave them. I know that you love inversion of control and I happen to love inversions in yoga, so let's stand this problem of ours on its head so to speak.

## Instead of being the bottleneck be the catalyst

## Instead of the browser being the obstacle, let it be the way

It turns out that the modern browser and it's lingua franca - JavaScript have come a long way since that one time you tried to make a sortable table on a web page in 2008. JavaScript is [fast](https://nodesource.com/blog/why-the-new-v8-is-so-damn-fast/), the browser has [threads](https://developer.mozilla.org/en-US/docs/Web/API/Web_Workers_API/Using_web_workers) and a [Key-Value database](https://developer.mozilla.org/en-US/docs/Web/API/IndexedDB_API) that feels like the [nice parts of DynamoDB](https://developer.mozilla.org/en-US/docs/Web/API/IndexedDB_API).

I'll tell you in a moment why this is great for your users, those doctors and lawyers we talked about before, but it's worth pointing out that with this stuff, you can geek out and look down on "front end developers" while becoming one yourself. Who knows, maybe you'll start [fighting about CSS-in-JS](https://gist.github.com/threepointone/731b0c47e78d8350ae4e105c1a83867d).

## A Full Text Search Engine in the Browser

Using IndexedDB, that key value database I mentioned, you can build an inverted index and start doing full-text search. Here is a [naive implementation](https://github.com/dfahlander/Dexie.js/blob/master/samples/full-text-search/FullTextSearch.js) in 80 lines of code, an in [depth paper](https://cs.uwaterloo.ca/~jimmylin/publications/Lin_ICTIR2015.pdf) about the idea and our own open source implementation with a UI called [YLabel](https://github.com/lighttag/ylabel). Before we go into the details, take a minute to clear your mind of deep NLP nonsense and comprehend what this means. You can give anyone you know full-text search and interaction with their data without doing any ops work, you go from being a bottleneck to being a catalyst.

In a nutshell, full-text search works like this: You take a bunch of documents, extract all their tokens, then hold a map between tokens and the list of documents that contain them. That's called a posting list or an inverted index. You can get pretty fancy with this, for example storing the position of a token alongside the document it appeared in which enables phrase searches or storing how frequent particular tokens are in the corpus to assist with ranking results.

![A postings list](postingslist.webp)

Querying a postings list is simple, take all the tokens in your query, do the lookup to get containing document ids for each token, then take the intersection. What you are left with is the list of documents that contain the tokens you searched for. And it's crazy fast

You used to think that getting text search to work fast meant having a big cluster, complex analyzers, and the patience to set up and tune Elasticsearch and Postgres' Full-Text Index. But that's just wrong, you can let anyone in your organization search over thousands of documents **with no-ops**. You know what they say, the only thing better than DevOps is NoOps and its a matter of fact that when you have no servers and dependencies you have no ops. Not to repeat myself, but that means that the people who will actually use this stuff will be able to do so without you. You're free. And it's thanks to the browser.

## So why search?

If you made it this far I've either angered you (sorry) or you need to help your team search through text. Typically, you're doing this to classify it. Maybe you want to find toxic comments in Wikipedia, learn to detect diagnoses in radiological reports or identify suspicious activity in your organizations chat. Either way, *you* probably don't understand the domain well enough, but *you* do need to empower the people who do. Search is an interface that lets experts apply their expertise to data efficiently and you can have it for free.

One way to think about industrial applications of machine learning and AI is as leverage for a company's internal expertise. There are a few people where you work who understand something better than anyone else. With ML, sometimes, you can scale that understanding so that it feels like you have an infinite amount of these experts always on call. In an industrial setting, NLPs role is the transferring of that expertise from the experts head into a model, e.g. to create that leverage. In the last few years, the automation side has become very accessible if not easy, and the challenge is in getting the domain experts to apply their knowledge to the data effectively.

**Search** should be one of the first tools in our toolbox but it's traditionally been hard to carry out because of the operational burden associated with deploying a "search engine". It turns out that the modern browser can easily be set up to be a search engine, without any operational needs or engineering support. You might want to add [active learning](/en/posts/lighttag/active-learning-optimization-is-not-improvement/) to your pipeline, and you can do that in the browser as well (stay tuned). So if you've been avoiding the JavaScript ecosystem and you need to empower people working with text, I recommend you take another look.
