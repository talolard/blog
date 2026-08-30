+++
title = "Context Is King! Why Deep Learning Matters for NLP"
date = 2019-11-19T00:00:00Z
draft = false
description = "Language is ambiguous at every scale; this essay explains why context is the central problem that deep NLP models address."

[social]
image = "social.webp"
image_alt = "Archive cover for Context Is King! Why Deep Learning Matters for NLP."

[share]
disable = false
languages = ["en"]

[original_publication]
site = "LightTag.io"
path = "/blog/context-is-king/"
+++
> What has four letters, sometimes has nine letters but never has five letters.

If you can't think of an answer, it's because the preceding sentence was not a question; it was a statement, as indicated by the period at the end. This goes to show that the meaning of a word depends on its context, and sometimes the dependency is very distant.

Check out this sentence in Hebrew that has four different meanings:

> יש בבית הספר מורה לספרות

1. There is a male literature teacher at the school
2. There is a female literature teacher at the school
3. There is a male barbering teacher at the school
4. There is a female barbering teacher at the school

The ambiguity arises from the fact that מורה and ספרות are homonyms, and while this is a valid sentence, it does not contain enough information to decide which sense of the word is correct.

Even a human couldn't look at that sentence in isolation and know which meaning the author intended. We call such a sentence "underspecified" and while underspecified sentences are ubiquitous in the written world, we barely notice, because we don't read sentences on their own.

A pattern emerges here. A word's meaning can depend on the context it appears in. A sentence's meaning can also depend on its surrounding sentences. Sometimes we need the broad meaning of a sentence to understand the meaning of a certain word in it, which in turn informs the meaning of the sentence.

If you think these are edge cases you're right, they are. But human language is full of edge cases, and if they weren't we'd be solving all of NLP with regular expressions and a few if statements.

The evolution in architecture for deep NLP has been about handling the structure of language and the edge cases that structure invokes.

- **RNN**s have helped us deal with the sequential nature of language.
- **LSTM**s have helped us deal with long-range dependencies, such as the period at the end of the first example.
- **Bidirectional** RNNs and LSTMs have helped us deal with contextual dependencies from the future as well as the past. The meaning of the word "What" in our first example depended on the period that came after it.
- **Transformers and self-attention** help us deal with non-linear contextual dependencies. If the teacher was holding a comb, we would assume they are a barber, and if she was wearing a dress, we would assume she was a woman.

As you uncover errors in your text annotation and NLP models, leverage tools like LightTag's analytics to review individual cases and notice if the context that defines the meaning of a word is more involved than your current model can handle.
