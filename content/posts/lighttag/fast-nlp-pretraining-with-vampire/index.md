+++
title = "Fast NLP Model Pretraining With VAMPIRE"
date = 2020-04-26T00:00:00Z
draft = false
description = "VAMPIRE offers fast, domain-specific NLP pretraining when large language models are too expensive or mismatched to the data."

[social]
image = "social.webp"
image_alt = "Archive cover for Fast NLP Model Pretraining With VAMPIRE."

[share]
disable = false
languages = ["en"]

[original_publication]
site = "LightTag.io"
path = "/blog/fast-nlp-pretraining-with-vampire/"
+++
[vampire-paper]: https://arxiv.org/pdf/1906.02242.pdf
[vampire-repo]: https://github.com/allenai/vampire
[allenai]: https://allenai.org/
[huggingface]: https://huggingface.co/
[transformers]: https://github.com/huggingface/transformers
[pre-trained-models-survery]: https://arxiv.org/abs/2003.08271
[cost-of-training]: https://arxiv.org/abs/2004.08900
[transformers-stars]: https://github.com/huggingface/transformers/stargazers
[wildml-nlp]: http://www.wildml.com/2015/11/understanding-convolutional-neural-networks-for-nlp/
[distributional structure]: https://www.tandfonline.com/doi/abs/10.1080/00437956.1954.11659520
[active-learning]: /en/posts/lighttag/active-learning-optimization-is-not-improvement/
[char-level-nlp]: /en/posts/lighttag/character-level-nlp/
[vae-tutorial]: https://arxiv.org/abs/1606.05908
[gensim-lda]: https://radimrehurek.com/gensim/auto_examples/tutorials/run_lda.html

## An Alternative To BERT

[Pre-trained language models][pre-trained-models-survery] are great until you get the [GPU bill][cost-of-training] or have to work on data that the model wasn’t pre-trained on (or worse yet, both).

> Holy crap: It costs $245,000 to train the XLNet model (the one that's beating BERT on NLP tasks: 512 TPU v3 chips × 2.5 days × $8 a TPU). — Elliot Turner (@eturner303), June 24, 2019

The [VAMPIRE paper][vampire-paper] came out in 2019 from a team at [AllenAI][allenai] with an [accompanying repo][vampire-repo] and caught our attention for its promise of fast, lightweight pre-training that adapts to any domain. In this blog post, we’ll discuss the core ideas behind Vampire as we (at LightTag) understand them and enumerate the tradeoffs of choosing Vampire over more traditional pre-trained models.

## Motivation

### Pre-trained Language Models

Pre-trained language models allow us to delegate a large chunk of NLP modeling work to a pre-trained model with a promise that we’ll only need a small amount of labeled data to fine-tune the model to our particular task. The [popularity][transformers-stars] of these models is a testament to how consistently they do deliver on their promise.

Pre-trained language models deliver by encapsulating knowledge about language and (possibly) about the world in a black box. As end-users, this saves us from having to craft these features ourselves or training a model that will figure them out on its own.

![Delegation](delegation.webp)

Notably, these models are trained on a vast quantity of data that would normally be outside of our compute budget and thus have learned about a large swath of human language. The size of the data is complemented by the typical size of a pre-trained model, which has millions to billions of parameters.

The applicability of a pre-trained language model depends on two factors:

1. Do we have enough compute budget to run large models?
2. Was the pre-trained language model trained on a language and domain that is similar to our task at hand ?

Put simply, sometimes the cost of putting a BERT like model into production isn’t justifiable.

### Limits on the Applicability of the Pre-Trained Models

Sometimes the factors that drive the success of pre-trained language models are the same factors that restrict their usability for a specific task:

1. If our data is very domain-specific or in a language that a pre-trained model isn’t available for, the pre-training will not have contributed significantly to our task.
2. Because of the generally large size of pre-trained models, they are expensive to fine-tune and to deploy to production.

With an infinite budget, that problem goes away, but most of us live in a resource-constrained world where shipping fast and cost-effectively is important. When resources are a factor to consider pre-trained language models can be prohibitively expensive.

## Seq2Vec and Bag Of Words

In the pre-deep learning days, we didn’t have many options to model sequences, and indeed the majority of NLP work used a [bag of words representations][distributional structure] to classify things. Deep Learning brought us convenient APIs to work with sequences, the LSTM, the [1-d Convolution][wildml-nlp], and the Transformer.

![Bag Of Words](bagofwords.webp)

The Deep Learning paradigm for document classification became embedding with one of the above structures to generate a vector representation of our text, and use that representation to make a prediction. This is the Seq2Vec paradigm - How do we convert an arbitrary sequence into a fixed-size vector.

![Seq2Vec](seq2vec.webp)

One of the nice features of this paradigm is that we got an end-to-end model and process with few moving parts. Simply put a sequence in, train with labels and get predictions.

Pre-trained language models leveraged that goodness. The pre-training phase initialized the parameters of the model to produce high-quality useful representations and the “end-to-end” nature of these models allowed fine-tuning them by simply adding a “head” at the top.

Vampire’s key insight is that pre-training on sequences is computationally expensive and that we can get useful representations at a fraction of the cost by pre-training on word counts instead. Doing so naively puts us back in the bag-of-words paradigm and forgoes the advantages of deep learning.

To regain the advantages of the Seq2Vec paradigm, Vampire pre-trains its embeddings and then has us concatenate them to a Seq2Vec model (e.g. an LSTM), fine-tuning the two together to generate our final prediction (See the tradeoffs section for a full discussion of the tradeoffs )

## Augmenting Seq2Vec with Bag of Words

The pre-training phase of Vampire is essentially forming a topic model, similar to LDA (but simpler). The assumption is that documents are a mixture of topics, and each topic defines high likely (e.g. frequent) words are. If we knew what words belong to a topic, and what topics a document was made of, we could generate documents accordingly. If we knew that, we could represent a document as a distribution over the topics (e.g. a mixture) which would be a vector representation of the document with a semantic interpretation.

![Topic Model Words](topicmodelwords.webp)
But, we don’t know what topics we have, how words are distributed in each topic, and certainly and not what topics our documents are comprised of. Enter the pre-training step of Vampire which aims to answer exactly that by training a variational auto-encoder. You can read more on [variational autoencoders here][vae-tutorial] , but for our purposes suffice to say that the VAE takes the count of each word and “embeds” the document in a space that corresponds to latent topics in our corpus.
![Topic Model Words](topicmodeltopics.webp)
This is useful but not much different from just training [LDA with Gensim][gensim-lda]. The innovation is that Vampire has us then take the latent representation of the document and concatenate it to the output of a regular Seq2Vec model, then fine-tune them together. This gives us the advantages of a Seq2Vec model, notably the ability to process arbitrary sequences and fine-tune the Seq2Vec component and the pre-training component together.

## The Vampire Pre-Training Processes

![Vampire Architecture](vampirearchitecture.webp)

Using Vampire can be reduced to the following recipe:

- **Pretokenize** and vectorize your training data + Save the Vectorizer
- **Train Vampire** a Variational Autoencoder on the token frequencies of each document
- **Seq2Vec** Use a Seq2Vec model of your choice
- **Concatenate** The output of your Seq2Vec model with the Vampire representation
- **Predict** your target class using the concatenated vector
- **Fine Tune** your joint model using standard methods

## Advantages and Drawbacks

Everything in life is a tradeoff and using Vampire is no exception. When you choose the use it, here’s what you're giving up a few obvious and not so obvious things.

### Drawbacks

First, you’re giving up the sheer breadth of “knowledge” that large pre-trained language models have. That’s a lot to give up on and you should only do so if you have a good reason.

Second, you're giving up on an entire ecosystem. [Hugging Face’s][huggingface] [transformers][transformers] library is a de-facto, well-maintained implementation of many pre-trained models, with a large community. Stack overflow is full of answers and there are many people you can reach out to for help. On the other hand, Vampire is research code, while the authors are nice enough to answer emails, the ecosystem around this technique is much smaller.

That also means that you don’t have as much certainty that it will work for you. One of the nice things about BERT is that people have used it for more or less any problem, and someone has probably succeeded in doing what you’re doing already. The confidence that gives in knowing that what you’re doing should work is very valuable.
![Someone Did It Before](bert-autocomplete.webp)

Finally, using Vampire is a two-stage process, you need to build two models and glue them together. Gluing things together (in this case the Vampire VAE and your Seq2Vec Model) is an easy way to make mistakes and bugs and is a big forfeiture in terms of developer productivity. The relative impact of this might be quite low, as modern transformer-based models have their own set of baggage to carry (e.g. [custom tokenizers][char-level-nlp]).

### Advantages

Having said all that, we didn’t write about Vampire because it’s bad, we wrote about it because it’s quite great. There are two good reasons we’ve found to use Vampire, and when applicable we’ve found them to be very good reasons to try it out. First, experimentation is much faster because models can run on CPUs in a few minutes. Second, it’s easy to ensure the model is adapted to the exact domain we’re working in, regardless of language or obscurity of the domain

One place where Vampire particularly shines is in [Active Learning][active-learning]. Active Learning with large pre-trained models is hard because the training steps are too slow to give an “Active feeling” to the user. Vampire allows keeping the model light enough to do near-real-time training steps and never have the end-user wait on a model run to complete.

Another challenge with Active Learning that vampire helps resolve is diversity sampling. In traditional active learning, it’s hard to ensure we sample diverse samples, but using a VAE this becomes easier because of the natural geometric structure of the data the VAE imparts.

![Diversity](diversity.webp)

## Final Thoughts

We’ve been experimenting with Vampire at LightTag to help our users' label data faster. Being a SaaS company, we needed a cost-effective way to fine-tune models to our customers' data, without sharing data between them and remaining adaptive to the multitude of domains and languages our customers use. Vampire has been a great way to give our customers the solutions they need while keeping our own compute costs manageable.

We think that the long tail of natural language processing is in niche applications in narrow domains. That means that the typical NLP project is worth doing, but won’t reach the scale of Google Translate like service and accordingly has a limit to the returns it can generate. While the (well-justified) hype around pre-trained language models makes them the obvious first choice, solutions like Vampire can make more sense when viewed from a business (instead of a data science) perspective.

On a related note, techniques like these that are “nimble” and cheap to run mean that we can leverage ML and NLP on a more ad-hoc basis with a broader user base and thus people who see benefit from it.
