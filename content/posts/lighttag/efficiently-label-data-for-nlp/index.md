+++
title = "Efficiently Labeling Data for NLP"
date = 2018-11-03T00:00:00Z
draft = false
description = "Three practical ways to collect more useful labeled NLP data with less manual work."
categories = ["NLP", "Labeled Data", "Named Entity Recognition", "Training Data"]

[social]
image = "social.webp"
image_alt = "Archive cover for Efficiently Labeling Data for NLP."

[share]
disable = false
languages = ["en"]

[original_publication]
site = "LightTag.io"
path = "/blog/efficiently-label-data-for-nlp/"
+++
Deep learning applied to NLP has allowed practitioners understand their data less, in exchange for more labeled data. Thus, labeled data has become the bottleneck and cost center of many NLP efforts.

We make the case that by acquiring and leveraging knowledge about your data, you can make annotations more efficient and models more accurate. We share three practical tips to get there.

## Evaluation Data

When labeling a dataset it's important to think what these labels are for. Labels used for evaluation should be crafted and stored like a treasure, they tell you how good your model is and indicate what you need to work on. Most importantly, they give you a first indication of whether your production ready.

We don't want to assist our labelers when they label evaluation data for NLP, as that is likely to introduce biases into the data and we'll forever be doomed to evaluate against a bias instead of (an approximation of) The Truth.

## Training Data

Both industry experience and academic research have shown that given enough training data, a deep model will learn to generalize and provide excellent results despite noisy labels. This is the story of [Google street view](https://techcrunch.com/2012/03/29/google-now-using-recaptcha-to-decode-street-view-addresses/), [advances in Radiology](https://arxiv.org/abs/1806.02121), [CrowdFlower](https://www.figure-eight.com/) and [Appen](https://appen.com/) to name but a few.

Unfortunately, not every company has the reach that Google has, nor can all data be shared with third parties. Often times even if you can share your data with a labeling provider, they don't have enough domain expertise to accurately label it. Put simply, sometimes you can't crowdsource- but, you can still help your in-house labeling team work well and fast.

## Help with what NOT to label

One of the most effective ways to make your labeling team more efficient is by figuring out what doesn't need labeling and then not labeling it. For example, a company dealing with chat data might quickly realize that salutations like "Hi, "How are you" etc. make up 10-20% of the messages they deal with. Not wasting a labelers time on them is a quick win.

## Deduplicate (Zipf's law is your friend)

One thing you shouldn't be labeling is the same thing twice (unless you're doing it intentionally for quality). And as a corollary of Zipf's law, there will be a few examples in your Dataset that repeat a lot. For example, imagine trying to classify the comments of a subreddit as toxic or non-toxic. A good first step would be to check for duplicates and remove them. The alternative is having your labeling team spend hours labeling the same automated message thousands of times

![Top 20 Reddit comments](top-repeated-reddit-comments.webp)

### But don't use active learning

We've discussed [Active Learning](/en/posts/lighttag/active-learning-optimization-is-not-improvement/) before and weren't fans. We discussed the risk that the underlying model will bias the collected data towards its limitations, which is kind of bad when you're trying to collect good labeled data. But don't take our word for it, a recent paper showed that data acquired with [Active Learning](https://arxiv.org/pdf/1807.04801.pdf) does not transfer well to new models.

## Automate the easy stuff

Letting your annotators make simple decisions instead of span annotations will save time. Use your pre-existing knowledge to make those suggestions.

Some things don't need to be labeled and then you shouldn't label them. Some things have to be labeled but should be labeled by "someone else". For example, when collecting labeled data for Named Entity Recognition many entities will be easily detected with a keyword lookup or simple regular expression. For example, when labeling President Trump's Tweets, we could easily detect **Mike Pence** as a Person with a keyword lookup.

If keyword lookup was enough we wouldn't need to label data. We would need someone to tell us that **"@VP"** also refers to a person and to decide of an appearance of the word **Pence** by itself refers to the Vice President or the British word for pennies.

This is super easy with LightTag, you can use our API to upload your suggestions from a regular expression, dictionary or pre-trained model, help your labelers work faster and get feedback about your models' performance.

![Upload your suggestions via LightTag API](example4.webp)

## Wrapping it up

Deep Learning has made the algorithmic side of NLP more accessible but requires copious amounts of labeled data, for both training and evaluation. Labeled datasets for evaluation should be kept pure and bias-free though results from industry and academia have shown that size compensates for noise in training data. With that insight in mind, your labeling efforts can get an easy efficiency boost by doing less work 1) dropping irrelevant data 2) dropping duplicates 3) automating everything that is easy. Using LightTag you can easily display your own suggestions to your annotators
