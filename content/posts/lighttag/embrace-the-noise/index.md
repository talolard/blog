+++
title = "Embrace the Noise: A Case Study of Text Annotation for Medical Imaging"
date = 2018-11-03T00:00:00Z
draft = false
description = "What an NLP pipeline for chest X-rays teaches about weak labels, selective annotation, and practical training-data design."
categories = ["NLP", "Labeled Data", "Named Entity Recognition", "Training Data"]

[social]
image = "social.webp"
image_alt = "Archive cover for Embrace the Noise: A Case Study of Text Annotation for Medical Imaging."

[share]
disable = false
languages = ["en"]

[original_publication]
site = "LightTag.io"
path = "/blog/embrace-the-noise/"
+++
<!-- markdownlint-disable MD024 -->

In this post we'll discuss the recent paper [TextRay: Mining Clinical Reports to Gain a Broad Understanding of Chest X-rays](https://arxiv.org/abs/1806.02121) focusing on the best practices the paper exemplifies with regards to labeling text data for NLP.

## What is TextRay ?

![TextRay architecture](architecture.webp)

TextRay was written by a team from [Zebra Medical Vision](https://www.zebra-med.com/), a for-profit company that applies deep learning to medical imaging. One of the core challenges of the medical imaging space is acquiring the **labeled** images (such as X-rays) to train their models with.
The TextRay paper expands a core insight from a paper called  [ChestX-ray8](https://arxiv.org/abs/1705.02315) by the NIH. The theme common to both is the realization that most medical images are already labeled, in the sense that a radiologist has already reviewed them and written a report. Said simply, it's smart to extract the information from the reports and less smart to have another radiologist label the images again.

![Chest X-Ray examples](xrays.webp)

We think that the TextRay paper contains a number of **best practices for labeling text**, especially for NLP teams that strive to be ROI positive. The rest of this post will enumerate a few of those practices, explain why they matter, how they go wrong and what the TextRay paper got right.
Dr. Laserson, the lead author of the paper was kind of to correspond with us about the paper. His insights are shared within, including a number of direct quotes, and we are very appreciative of the time and effort he took in answering our questions.

## Understand the risk-reward profile of your labeling project

### Why it matters

Any large-scale labeling project is expensive, especially when the labelers are domain experts. Moreover, it's an uncertain investment, in that you don't know a priori that you'll be able to convert labels into a satisfactory model.

For example, the TextRay paper started with 2.1M X-rays. Assuming it takes a radiologist two minutes to decipher an X-ray, and we pay a radiologist $100 an hour, this amounts to $7M and 8 Radiologist-years. Even if they made such an investment, they'd still need to develop a model that would get FDA approval, no small or certain feat.

On the other hand, there is a great shortage of expert radiologists and thus a lack of access to high quality, fast, error-free X-ray interpretation. For Zebra Medical Vision, the potential reward is solving a major gap in modern healthcare and seizing the business opportunity that comes with it.

### How companies get this wrong?

One of the largest struggles of the NLP team is getting stakeholders to commit the financial and expert resources required to execute an annotation project. Often data scientist pitch their needs as "We need labeled data to do our work", which is true, but gives stakeholders no clear reasons to allocate expensive resources to them (They're probably making money somewhere else).

What data science teams do wrong is what they don't do, that is provide a clear indication of the costs of an annotation project as well as the value it will generate. Without these metrics, it's hard for any stakeholder to commit resources nor gauge if a project is on track. This results in the familiar lack of devoted labeling experts and sporadic reallocation of the few resources that are assigned.

### What TextRay got right

We asked Dr. Laserson, TextRay's lead author, about the expense of the project to which he replied: "compared to tasks that require actually looking at images, which we give constantly to our radiologists, the cost was not high."

In that sense, the TextRay team was quite fortunate to work in a context where expensive labeled data was the norm ( A medical imaging company), stakeholders were likely used to such expenditures.

A back of the envelope estimation puts the cost of the TextRay project at around $300–500K while a conservative estimate of the cost of the corresponding image labels is $7M. In other words, at a success likelihood of more than 10%, the project would have a positive expected value. Those are metrics stakeholders can get behind.

## Have a clear purpose for your labels

### Why it matters

The enemy of a successful labeling project is ambiguity. Having a clear use case for the labeled data reduces ambiguity.
How companies get this wrong

Often, in the name of reducing costs, project managers will have their labeling team go over the data once and label everything.

When an ambiguous term is encountered a new, more specific label is added. Because everything is "important" annotators either miss things or become overwhelmed with the task at hand, thus losing their ability to think globally about the data.

### What TextRay got right

The purpose of the TextRay text labels was to generate labels for computer vision. Thus the team realized that they should only use findings that describe things that are visually detectable.

> In making the final ontology[the labels applied to the text], we focused on visual findings rather than clinical  interpretations or diagnoses.

We mentioned that a lack of purpose results in either ambiguity or a plethora of specific tags, but the paper shows the opposite phenomena when a clear purpose is preserved:

> We chose to merge… bronchial markings into interstitial markings, since it is often impossible to differentiate these based on the image alone"

## Start with a coarse ontology

### Why it matters
>
> one thing that made it easier is that we built [the ontology] bottom-up, rather than top-down. There are very complex "official" x-ray ontologies online with tons of findings, which some people urged me to use, and I'm happy I didn't" - Dr. Laserson

It's often tempting to come to a dataset with a fully formed schema/ontology and begin labeling. But often its preferable to start with a very coarse ontology, something perhaps as simple as "relevant/ irrelevant".

The main advantage of starting with a coarse topology is the reduction in cognitive load, and thus the increased opportunity to get to know your dataset. As we'll see, an intimate familiarity with your data allows you to truly clarify what matters, and eliminate the work on everything else. There is no better way to reduce costs then by eliminating them entirely.

### How companies get this wrong?

Perhaps the most common practice(sin?)  we see is a project or product manager define a detailed ontology based on product requirements and send the labelers to label it.

The people defining the schema should absolutely by labeling the data with it. Defining a schema for annotation is imposing a mental model on the world, and it's crucial to get feedback on that model, not only from the annotators who you force to use it but from the data you are trying to impose the model on.

Failing to do so often leads to data that is inconsistently labeled and thus not very useful for evaluation or training of models.

### How TextRay got it right

Dr. Laserson was kind of enough to share the process they went through in detail,
> It took a while for the team to converge on the right schema. We knew there would be positive, negative and neutral sentences from the start (neutral = sentences unrelated to the image). Another category, which I called "context", emerged shortly after (context = sentence describing the type of scan taken, i.e. "Lateral Chest with contrast", but not any finding). After tagging a few thousand sentences we added the "generally abnormal" category (=there is clearly something wrong, but you can't tell exactly what just by reading the text). …
The first big milestone took 2 weeks, and we had a few correction iterations later.
Most of the work (tagging 20k sentences) was done by two medical students
`

## Find what you don't need to do, then don't do it

### Why it matters

If you've defined a clear purpose for your labels there is no point in doing something that doesn't serve that purpose. The best way to lower the cost of annotations is by reducing the number of things that need to be annotated.

In most domains where NLP is applied, there is a near infinite amount of text, but only a small amount of it really matters. Being able to define what really matters (or what doesn't) lets you focus on the things that count instead of wasting time on the things that don't.

### How companies get this wrong?

As before, in the name of reducing costs, project managers will have labelers label everything, under the assumption that it is cheaper to do the whole thing once then come back to it sporadically. The fallacy comes to light since most things don't matter, so labeling everything ends up being mostly a waste.

### How TextRay got it right

Using the coarse ontology they built before, and the insight that only sentences that corresponded to a visual finding were important the team was able to:

1. Designate every sentence that was neutral or negative (had no finding) as irrelevant and throw it away
2. Treat each report as a set of positive sentences
3. Reduce their labeling effort from labeling millions of reports to labeling 20K sentences.

#### That's a 100X Reduction in Workload

> First, a sentence boundary detection algorithm was applied to the 2.1M reports, yielding a pool of 827k unique sentences… it was possible to fully cover 826k reports using just the 20k most prevalent positive sentences

![The number of reports (y) that were fully covered by the top (x) most common sentences.](covering.webp)

That is, having realized that they only cared about the meaning of positive sentences they realized they could strip away neutrals and negatives. At that point, the number of things to label become the number of positive sentences (within the 20k)  in the corpus, which was comparatively small. "

## Embrace the Noise

*This section holds true for training data but does not apply to evaluation data.*

You may have noticed that the methodologies described above will work "most of the time" but will have the occasional error. Perhaps the most important and yet subtle points of the paper are that it's better to have a tremendous but noisy training set rather than a large and perfect one.

The TextRay team was able to use the 20K labeled sentences to assign labels to images. If a report contained sentence X and sentence Y, then the image was labeled with X and Y.

When all positive sentences in a  report came from the 20K labeled ones, they called it fully covered.
Some reports were only partially covered, that is, they contained sentences that were outside of the 20K but were also not negative or neutral sentences.

 Using these exampled added a few hundred thousand images to the training set but
[ Using these reports introduces] risk that some of them also mention abnormalities that would be mislabeled as negatives. … Additionally, many radiologists will omit mention of normal structures in favor of brevity, thereby implying a negative label … this omission bias introduces noise into the labeling process.

The somewhat surprising result is that a model trained on the noisier partially-covered training set consistently outperformed the model trained on the more accurate fully covered data set, where performance was measured by comparing the model to a group of expert radiologists.

## Summary

We took a look at some of the best practices for labeling data exhibited in the TextRay paper and looked at why organizations sometimes get them wrong. Notably, we saw that

* Understanding and communicating the risk-reward profile of a labeling project is paramount to getting stakeholder buy-in.
* Defining a clear purpose for the labels reduces ambiguity
* Starting with a coarse ontology enables attaining an intimate familiarity of the dataset fast and the emergence of the best ontology for the job
* If you take the time the find what you don't need to do, you can save a lot of time by not doing it.
* Empirically, deep neural models can compensate for noisy training data, embrace the noise.
