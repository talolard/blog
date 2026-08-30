+++
title = "When Should You Use Machine in the Loop?"
date = 2019-02-05T00:00:00Z
draft = false
description = "Machine-in-the-loop labeling can reduce annotation cost while introducing bias; here is how to reason about the tradeoff."

[social]
image = "social.webp"
image_alt = "Archive cover for When Should You Use Machine in the Loop?."

[share]
disable = false
languages = ["en"]

[original_publication]
site = "LightTag.io"
path = "/blog/when-to-use-machine-in-the-loop/"
+++
Like any new technology, AI can be used to reduce costs by optimizing existing processes or unleash value by enabling new processes and products. For example, [Facebook is trying](https://motherboard.vice.com/en_us/article/xwk9zd/how-facebook-content-moderation-works) to reduce it's reputational costs and risks by applying AI to monitor suspicious content. Meanwhile, Goldcorp famously [used AI to recognize many potential gold mines](https://www.ideaconnection.com/open-innovation-success/Open-Innovation-Goldcorp-Challenge-00031.html) that humans had missed thus becoming one of the most valuable mining companies in the world.

Whether used to reduce costs or increase revenue, [AI is not magic](https://www.technologyreview.com/s/612394/ai-is-not-magic-dust-for-your-company-says-googles-cloud-ai-boss/). To the degree that a machine can do something that seems magical, it's because a human told it how to do so, either directly - by hard-coding rules, or by showing it examples from which the machine learned.

![XKCD comic about a machine-learning system](xkcd-machine-learning.webp)

## AI's Bottleneck is Labeled Data

If and when AI outperforms the manual writing of rules, its success is due to the fact that experts that can write the rules are rare, expensive and sometimes wrong, whereas the data never lies (if collected well).
Thus, for a business, striving to deliver results, it is often cheaper and more reliable to collect labeled data from which an  AI system can learn than it is to write a series of rules.

For this reason, labeled data has become the bottleneck of  AI initiatives that businesses are deploying. This bottleneck has become so significant and ubiquitous that an entire industry has formed to solve it. Companies such as [Figure-Eight](https://www.figure-eight.com/) and [Appen](https://appen.com/) provide outsourced labeling services to those companies whose data is simple enough to be labeled by outsiders. For those with legal barriers around their data or a need to deploy in-house experts, LightTag offers tools to label data in-house with your own team.

## Machine In The Loop Systems - There Is No Free Lunch

A natural progression of the data labeling industry is to use AI to improve the efficiencies of data labeling. This idea goes by a few different names such as human-in-the-loop, machine-in-the-loop, and [active learning](/en/posts/lighttag/active-learning-optimization-is-not-improvement/).
While the different names have different implementation details, the premise is consistent. Have the human and the machine interact, to maximize the accuracy of the machine while minimizing the effort of the humans.

While at first glance this sounds like a winning proposition, it's important to remember that there is no such thing as a free lunch. Utilizing an external model introduces new and unknown biases into your annotation project. That is to say that while automation will certainly reduce the cost of producing a new annotation, it will also decrease the value of each annotation produced.

It's the data teams job to evaluate whether that tradeoff is acceptable. As a rule of thumb, when generating "gold standard" data for evaluation, the organization should strive to maximize the quality of the data collected. Gold standard data tends to define the metrics the data team  will be optimizing for, thus errors in the data used for evaluation tend to compound for the duration of the project.

Training data, on the other hand, can be more forgiving of moderate bias if there is enough of it present and techniques are chosen that account for the presence of bias and noise.

LightTag's annotation platform includes a machine in the loop interface that learns from your annotators. We've found that once our model reaches an accuracy of roughly 60%, annotator throughput roughly doubles. The reason for this disproportionate lift might surprise you. It's much faster to accept or reject a machine suggestion than it is to initiate an annotation.

## Protecting Your Data From Bias

An effective methodology our customers put in place is collecting an unbiased gold standard dataset with no machine in the loop while using a model for training data. Thus, customers can and do compare the distribution of the annotation classes generated with and without a model in the loop, and can thus quickly identify and adjust for significant bias introduced by the model.
![Diagram showing bias introduced by machine-in-the-loop labeling](bias.webp)

Ultimately, the choice of using the machine in the loop techniques is one of risk and reward. Introducing a machine into the labeling process will introduce some bias. However, you may double your annotator throughput or halve the need for labeled data. The best guiding principle we can offer is to consider how frequently and how often you'll be labeling. Short-lived projects that will collect less than 50K annotations will probably not see a significant drop in costs and can expect to see projects end a few days faster.
Longer-lived and large scale annotation projects have more to gain. Doubling annotator throughput over a period of time amounts to a significant cost saving, while a larger sample reduces the risk of biasing towards a particular model.

Another compelling feature of the machine in the loop model is that when you're done with the loop you can keep the machine. Since your team of labelers has validated the output of the machine, you know exactly how good the machine is and can deploy it to production with no further adjustments. Where this is feasible it is often very cost-effective since building a model tends to be as or more expensive than labeling data.
LightTag makes this particularly easy, you can call the models LightTag trains as an API without any complicated deployments.

## The Punchline

To summarize, labeled data is often the bottleneck in new and continuing AI projects. Where possible, companies minimize the operational costs of labeling by outsourcing the entire project. However, for companies with sensitive data, or annotations that require expertise, annotations must be executed in house.
Naturally, annotation projects introduce labor costs and since we often need copious amounts of labeled data, those costs can be significant. Human in the loop techniques help alleviate those costs by increasing annotator throughput. There is no such thing as a free lunch, and these techniques introduce some bias into the data. It is up to the data team to decide when to use these techniques and how to track and adjust for resulting bias.
