+++
title = "Which Open-Source NER Model Is Best? Comparing CoreNLP, spaCy, and Flair"
date = 2019-11-20T00:00:00Z
draft = false
description = "A hands-on comparison of CoreNLP, spaCy, and Flair for named-entity recognition across real datasets."

[social]
image = "social.webp"
image_alt = "Archive cover for Which Open-Source NER Model Is Best? Comparing CoreNLP, spaCy, and Flair."

[share]
disable = false
languages = ["en"]

[original_publication]
site = "LightTag.io"
path = "/blog/spacy-vs-stanford/"
+++
[spacy-small]: https://spacy.io/models/en#en_core_web_sm
[spacy-big]: https://spacy.io/models/en#en_core_web_lg
[flair-repo]: https://github.com/zalandoresearch/flair
[corenlp-repo]: https://stanfordnlp.github.io/CoreNLP/
[implementation-repo]:  https://github.com/LightTag/ComparingNERModels
[federal-register]:https://www.federalregister.gov/

## tl;dr

I compared four open-source NLP models by putting their outputs into LightTag and then reviewing their outputs manually. The best model depends on your data and use case, and we'll see how to compare model performance so you can make the best choice for your situation.

![Inter Model Agreement](intermodelagreement.webp)

## Comparing spaCy, CoreNLP and Flair

I wanted to know which [NER](https://en.wikipedia.org/wiki/Named-entity_recognition) library has the best out of the box predictions on the data I'm working with. These days, I'm occupied with two datasets, [Proposed Rules from the Federal Register][federal-register] and tweets from American Politicians.

I tested four different NER models:

- The [Small spaCy Model][spacy-small]
- The [Big spaCy Model][spacy-big]
- [Flair from Zalando][flair-repo]
- [Stanford's Core NLP][corenlp-repo]

It's not straightforward to make an apples-to-apples comparison between these models. Each outputs a slightly different set of tags and makes different assumptions about text [tokenization](/en/posts/lighttag/character-level-nlp/). When I reviewed model outputs, I consolidated the different tags they output and marked a prediction as correct or incorrect based on how useful they were to my use case.

If you'd like to do this yourself, we've published a [repository with the data and code][implementation-repo], and you can sign up for a free LightTag account to do the review.

### Unifying Entity Types (Tags)

spaCy has a tag called GPE - Geo-Political Entity, while Stanford has different tags for Country and State which are more specific instances of GPE. Both of them also make a distinction between a GPE like the United States and a Location such as Mt. Everest. For the tasks I'm working on, those distinctions don't matter so I collapsed all of those tags into GPE.

### Being Strict

That's an example of lenient evaluation, but in some cases, I was also strict. All of these models have a Tag for Misc, but what counts as Misc varies between them. Specifically, spaCy has a Tag called Law which I was very interested in. That means that in cases where one model said Law and the other said Misc, I took Law as correct giving points to spaCy (the only model that outputs Law) and punishing the others.

### Being Specific

As another example, all of the models except Flair output a Date tag, but not every date is relevant to my work. I want explicit dates, such as "24 October 2018". Where a model tagged a phrase like "Today" or "Yesterday" as a date I marked it as wrong.

## How To Compare NER Models

![Comparing NER models in LightTag](reviewmode.webp)

Actually doing the comparison was pretty easy. I loaded my data into LightTag, then ran each model and the data and uploaded the models' output to LightTag. LightTag has a review feature that shows every annotation models made and lets me mark which one is correct or incorrect. After that, I got a nice report and views on individual annotations.

## Findings

### CORENLP Shines on Legal Data

On the federal register dataset, all of the models did quite poorly, with precision hovering around 30% for each of them. I was particularly interested in mentions of GPEs in federal law, and Stanford's CoreNLP really shined in that regard, with an 77% F1 Score (72% Precision, 82% Recall) vs a 67% F1 for the next best model (spaCy's Big)

![Precision Recall for the GPE tag](gpe-prec-rec.webp)

I found that surprising and I used LightTag's drill-down features to look at individual cases to get a sense of why and where Stanford was outperforming. I noticed that Stanford did a superior job of producing useful tokenization.

### Tokenization Preferences Count

For example, in many cases where the phrase "the United States" appeared, spaCy captured the "the" prefix while Stanford did not. That's not to say that spaCy is objectively wrong, but for the use case I had in mind Stanford's tokenization scheme was more suited.

![spaCy capturing the](spacy-fp.webp)

Conversely, Zalando's Flair model consistently made frustratingly bad tokenization choices, such as including trailing punctuation in captured tokens.

![Flair Struggles with tokenization](zalandoerrors.webp)

### Performance Is Dataset Dependent

The situation in the tweets dataset was different. I was primarily interested in finding mentions of People and Companies. Stanford came out ahead again from a metrics perspective, with a 73% F1 Score vs a 50% F1 for the second-best model.

### Bias is Real

One thing that really surprised me was that none of the models were able to identify Nykea Aldridge as a person, though they all identified her as some entity. This would be very important in a downstream application.

![No Person Tag for Nykea Aldridge](nykea.webp)

### What to do with Pronouns ?

CoreNLP's model recognizes pronouns as a Person. Presumably, this is a stepping stone towards their coreference resolution model, but for my use cases, it is just noisy.

![Pronouns Everywhere](pronouns.webp)

## Conclusion

If you were hoping to get a recommendation for which package to pick, I'm afraid you will have to stay disappointed. I hope you do take away from this how you can run your own comparison on your own data and reach the conclusions that are right for your own use case.

In our day and age, out of the box models are a starting point, not a final destination. You'll likely be fine tuning these models to your particular needs. Being able to find gaps in your models performance and identify regressions is still super important and  something you can easily do with LightTag.
