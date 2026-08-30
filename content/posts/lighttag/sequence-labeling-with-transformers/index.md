+++
title = "Sequence Labeling With Transformers"
date = 2020-09-18T00:00:00Z
draft = false
description = "How to align offset annotations with fast-tokenizer output and window long texts for transformer sequence-labeling tasks."

[social]
image = "social.webp"
image_alt = "Archive cover for Sequence Labeling With Transformers."

[share]
disable = false
languages = ["en"]

[original_publication]
site = "LightTag.io"
path = "/blog/sequence-labeling-with-transformers/"
+++
<!-- markdownlint-disable MD028 -->

![Diagram of text annotations aligned with tokenizer output](tokenizer-annotation-alignment.webp)

> Practical NLP operates on long texts, and annotations for sequence-labeling tasks often come in offset format.
> Pre-trained transformer models assume tokenization that annotations must be aligned with, and long texts must be
> segmented consistently with the annotations.
>
> Hugging Face's tokenizers library offers fast tokenizers that return character offsets in the original text, making the
> alignment task easier. When segmenting our text, there is a tradeoff between training speed and model accuracy.
> Our preferred approach is windowing over the aligned tokens and labels.

>Don't want to read? [Code is here](https://github.com/LightTag/sequence-labeling-with-transformers)

Academics ask, "How can we process long texts with transformers."

Practitioners ask, " How can we process long texts with transformers cost-effectively"?

In the wild, outside academia, text is arbitrarily long, and sequence labeling annotations
come in offset format, with start and end offsets of the annotation relative to the
annotated string. In the wild, practitioners want to leverage pre-trained transformer-based
models like BERT.
[Hugging Face's Transformers library](https://huggingface.co/transformers/) has made getting started with pre-trained transformers
easy. But, in the wild, one question remains, how to [align sequence offsets to Hugging Face
Tokenizer tokens](https://github.com/huggingface/transformers/issues/7019)?

## Should I Read This?

This post discusses the *considerations* and tradeoffs regarding aligning span annotations
to transformer tokenizer's tokens. It doesn't give code. You should read it if you want to use pre-trained
transformer models with the transformers library for NER like tasks (sequence labeling).
If you're looking for a quick "how-to," read our "how to align offset annotations
for BERT" post.

### Why would I want to know how to align transformer tokens with span annotations?

Custom sequence labeling tasks, such as recognizing clauses in contracts or drugs
in medical records, are widespread in applied NLP. While the supervised learning
paradigm has made these tasks achievable, practitioners continuously seek ways to
lower the cost of annotation and time to market of a sequence labeling pipeline.

Pre-trained, transformer-based models such as BERT promise to reduce the annotation
cost and time to market of a sequence labeling pipeline. Hugging Face's transformers
library is the most accessible way to use pre-trained models, thus defining part
of the ecosystem and tools a practitioner uses.

Understanding the nuance and techniques of inputting span based annotations into
a transformer-based pipeline promises quick set-up, easy debugging, and faster time
to market at less cost.

This post continues with a high-level recipe for alignment and batch preparation,
and then presents the considerations that were taken in when deriving that recipe.

## How To Align Offset Annotations with Tokenizers?

1. Load the text and annotations in a [PyTorch Dataset](https://pytorch.org/tutorials/beginner/data_loading_tutorial.html)

2. Tokenize all of the texts in one batch with a [Fast tokenizer](https://huggingface.co/transformers/model_doc/bert.html#berttokenizerfast). **Don't** apply [padding
or truncation](https://huggingface.co/transformers/preprocessing.html#everything-you-always-wanted-to-know-about-padding-and-truncation).

3. Align the annotations of each text with its tokenized representation. You'll
have a list of tokens and a list of labels, both of the same length.

4. Iterate over the token, label pairs with a window of size N. Each such window
will be an item in your dataset. Ensure that all windows are padded to length N.

5. Use a PyTorch Dataloader to create batches from your dataset.

The rest of this post describes the considerations that brought us to this method.

## Properties And Assumptions Of the Transformers Ecosystem

We can make several observations about pre-trained transformer models that will inform
the strategy and implementation of data preparation for sequence labeling tasks with
transformers.

### Tokenization Reduces String Length by a factor of 2-4

![Shrink](shrink.webp)
The tokenizers used for transformer models map whole words or parts of them to a
single token, resulting in tokenized sequences that are 2-4 times shorter than the
text's character length. For example, the average tweet is 120 characters long and
30-40 tokens, depending on the tokenizer used.

### The Most Important Context is Often Nearby

A complimentary observation is that the context that most influences a span's meaning
is typically local to it, within 100 or so characters. While this is a heuristic
and not a fact, when coupled with the observation that tokenized sequences are 2-4
times shorter than their character level counterparts, we can consider segmenting
raw text by windows of length 50 -100 tokens and assume that these windows will hold
sufficient semantic context for training our model.

### Span Annotations Don't Align Neatly With Windows

However, segmenting the text by equal-sized windows does not respect the boundaries
of our annotations. An annotation may cross two distinct windows. Worse still, an
annotation that spans two windows would have its first part at the end of the first
window, and its later part at the beginning of the second window. Thus the first
part of the annotation would miss its right context, and the latter part would not
see its left context.

### Transformers are not sensitive to array indices

Self-attention modules, the "workhorse" of transformers, process each pair of tokens
independently. The self-attention module is not spatially aware; it does not consider
a particular token position in the tensor. Instead, transformers receive spatial
information via positional embeddings.

Armed with this observation, we can identify and mitigate the following risk. Positional
embeddings for later points in a sequence will not be trained when using short windows.
Thus our model won't be prepared for inference on full-length sequences.

We can mitigate this problem by explicitly specifying which positional embeddings
to use during training. By default, Hugging Face's transformers library matches the
position of a token to the natural positional embedding. However, we can manually
specify a different range of positions and train a segment as if it appeared in any
span to which our model can attend.

### BIO-Like Scheme for subword tokens

Academic NER datasets are typically annotated with a [BIO (Beginning, Inside Other)](https://en.wikipedia.org/wiki/Inside%E2%80%93outside%E2%80%93beginning_%28tagging%29)
-like scheme, which indicates when an entity consists of multiple tokens. BIO-like
schemes help distinguish adjacent tokens with one contiguous annotation from adjacent
tokens with adjacent but distinct annotations.

The same benefits apply when working with transformers. And one other benefit accrues.
BIO-like schemas can hint to our model that an annotation is split at the start or
end of a window, as the window will start or end without part of the scheme.

We've used a BIOUL scheme, where U(nit) is an annotation that spans a single token,
and L(ast) indicates the last token of a multi-token annotation. This gives the opportunity
to introduce more inductive bias to the model through a CRF. [AllenNLP's CRF implementation](https://github.com/allenai/allennlp/blob/master/allennlp/modules/conditional_random_field.py)
allows specifying forbidden transitions (O-&gt;L is forbidden), which results in
faster training of more accurate models.

## Long Sequences when working with transformers for NER

Academics ask, "How can we process long texts with transformers." Practitioners ask,
" How can we process long texts with transformers cost-effectively"?

Time is money, not only in terms of cloud computing costs but in overall productivity.
The faster a single experiment can be run, the sooner a team can converge on a solution.
The quicker a model can be trained, the earlier it can go to market. And as the total
cost of development drops, user-specific models can be deployed at more accessible
price points.

So for practitioners, a lot is riding on processing long texts fast right now.

As opposed to classification, truncation is out of the question for NER like tasks
because an annotation can appear anywhere in the original text, including the potentially
truncated part. So the practitioner needs to carefully consider working with long
sequences when solving sequence labeling tasks.

### Sequence Length and the Accuracy / Cost Tradeoff

There is a tradeoff between model accuracy and the cost, in time and money, of training
a new sequence labeling model. Because the semantics of real-world texts don't come
with a natural segmentation, we expect that exposing the model to more extended contexts
will improve its accuracy. However, as our training sequence length grows, so do
the wall clock time and compute training costs. A practitioner needs to balance between
the assumed accuracy provided by longer sequences and the benefits of shortened training
cycles reaped from short sequences.

### Segmentation Is A Necessity

Texts in the wild are longer than 512 tokens; thus, we must segment them, but don't
have a natural and usable segmentation unit. When we segment our texts, we need to
maintain consistency with the segment bounds implied by annotations, which may not
align with the model's tokenization of the text or its segments.

### Sentences Are Bad For Business

The obvious, yet devious, solution is to split long texts into sentences and treat
sentences as our segmentation unit. Sentences are great. They make sense, and almost
any annotation, even in the wild, will fall into a sentence.

But there are two problems with sentences. First, [it's not that easy to split any
random text into a sentence](https://github.com/explosion/spaCy/issues/5268), which means we'll use senseless and hard to trace partitions
of our text.

Second, sentences come in many shapes and sizes, which means that we'll frequently
be padding batches. When working with transformers, we pay quadratically for each
additional token, padding or not, and sentences force us to pay that price.

### Dynamic Segmentation Implies Slower Training

Instead of sentences, we could segment our texts based on the annotations. That's
a tempting option with several drawbacks. First, an annotation doesn't indicate how
much left and right context are needed to determine it, and so we don't know what
an optimal segment length for an annotation is.

Moreover, as in the case of sentences, a dynamic segmentation strategy will give
us variable-length sequences, which we'll have to pad before feeding the sequences
to the model. Recall that padding increases sequence length, and our compute cost
and wall clock time grow quadratically with sequence length.

## Hugging Face Transformers were not designed for Sequence Labeling

Hugging Face's Transformers library is the goto library for using pre-trained language
models. It offers the model implementations, loading pre-trained models in one line,
and a fast and robust tokenization utility. However, as the library's [philosophy
page](https://huggingface.co/transformers/philosophy.html) mentions:
>"this library is NOT a modular toolbox of building blocks for neural
nets. If you want to extend/build-upon the library, just use regular Python/PyTorch/TensorFlow/Keras
".

In other words, Transformers' goal is not to solve data engineering problems that
are particular to sequence labeling.

That's not a shortcoming of the library in any way. It is a fact that engineers need
to consider to decide which parts of the library to use and what tasks need to be
solved by other means.

As their name implies, transformers tokenizer modules can tokenize text into the
tokenization scheme a particular model expects. They can also do more, such as calculate
the span offsets of a token in the original text, automate the application of padding
and truncate the tokens to comply with a model's limitations. Those features are
where the perimeter of usability becomes murky because the library's goals are not
related to the specific concerns of sequence labeling for long texts.

Getting back the span offsets of a token is invaluable for alignment. On the other
hand, automated padding becomes a nuisance, and truncation is irrelevant.

Transformers offer a few beautiful utilities such as a built-in Trainer that encapsulates
many of the finer details of training and evaluation. In practice, we've found that
the API constraints it places make rolling your own trainer a compelling alternative
for sequence labeling tasks.

## How to align span annotations to Hugging Face Tokenizer tokens - The Details

### A Minimal Partition

Consider the tokenization of a text as a partitioning of it. Additionally, a set
of span annotations is also a partitioning of the text. The tokenization is the finest
partition that our model will accept, and as such. That means that when aligning
annotations to tokens, we must adhere to the partitioning those tokens imply. We
can't make up a smaller token.

Until recently, the alignment of annotations and tokenizer tokens was difficult as
it was done by iterating over tokens and annotations and then matching substrings.

Hugging Face introduced FastTokenizers, which, among other things, return the characters
offsets of a token. With the newer FastTokenizers, alignment is as simple as checking
if an annotation's span overlaps with a token's.

Since an annotation, my span more than one token, a more sophisticated alignment
variant includes a BIO-like schema, such that the resulting labels produced from
annotations indicate if they are the beginning, end, or middle of the annotation
concerning the tokens they span.

### Implications of Span Annotation Alignment For Evaluation

There are two edge cases that annotation-token alignment leaves open. The finest
partition of the text our model operates on is the token, but annotations come from
a finer partition, the character level start-end. We need to be cognizant of this
fact during evaluation because if any annotation in the evaluation set is inconsistent
with the tokenization scheme, a model will never be able to predict it perfectly.

This phenomenon's notable cause is annotations that (accidentally) have leading or
trailing white spaces, which will entail a span different from what our model operates
on.

### Spans That Don't Align With Tokens

A second edge case is an annotation that starts or ends in the middle of a token.
In standard English, this is rarely a problem but can happen in morphologically rich
languages. As a (contrived) English example, the BERT tokenizer tokenizes "pedometer"
into "pe", "\#\#dom"," \#\#eter". Annotation for the substring "meter" would start
at the "\#\#do**m**" token but obviously, "do" is not part of the annotation.

## The Windowing Strategy for Span Alignment with Tokens

The above alignment procedure produces two equal length lists, one of the tokens
and one of their corresponding labels. It's desirable to batch multiple examples
during training, which requires that all sequences have a uniform length. Additionally,
the sequence length must be smaller than the models' sequence length limit, and the
entire batch must fit in GPU memory.

A strategy to satisfy all of these constraints can be created with some combination
of padding, truncation, windowing, and strides. Padding will extend all sequences
to a uniform length; truncation will ensure they are shorter than a model's maximal
length.

As we alluded to before, combing padding and truncation will increase our costs and
inadvertently remove data from our training set.

An alternative is windowing: processing fixed-sized chunks of the tokenized and aligned
token, label pairs. Windowing has an advantage that most windows won't need padding
at all and provides us a way to process the entire text regardless of its length
and without risk of truncating useful information.

However, an annotation may span two windows, and it's defining context may fall outside
of a particular window. Striding in small steps mitigates this by showing the same
annotation inside and outside a window and in varying contexts. Using a BIO-like
schema during label alignment reduces the harm of training on split annotations.

## Conclusion

Practical NLP operates on long texts and annotations for sequence labeling tasks often come in offset format.
Pre-trained transformer models assume tokenization that annotations must be aligned with, and long texts must be
segmented consistently with the annotations.

Hugging Face's tokenizers library offers FastTokenizers that return character offsets in the original text, making the
alignment task easier. When segmenting our text, there is a tradeoff between training speed and model accuracy.
Our preferred approach is windowing over the aligned tokens and labels.
