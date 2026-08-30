+++
title = "Character-Level NLP"
date = 2018-12-21T00:00:00Z
draft = false
description = "Character-level models expand usable vocabularies and remove training bottlenecks, with important tradeoffs in sequence length and semantics."

[social]
image = "social.webp"
image_alt = "Archive cover for Character-Level NLP."

[share]
disable = false
languages = ["en"]

[original_publication]
site = "LightTag.io"
path = "/blog/character-level-NLP/"
+++
NLP systems, like life, are about choices and tradeoffs. One such choice is the designation of the smallest unit our models see. Usually, in language, we work with words. This post explores the merits and drawbacks of another, unintuitive, choice, working at the character level.

Character level models give up the semantic information that words have, as well as the plug and play ecosystem of pre-trained word vectors. In exchange, character level deep learning models provide two fundamental advantages. They alleviate vocabulary problems we encounter on the input of our model, and they remove the computational bottleneck at the output of our model.

On the input side, they dramatically increase the vocabulary our models can handle and show resilience in the face of spelling mistakes and rare words. On the output side, character models are computationally cheaper due to the small size of their vocabulary. This attribute makes training techniques (such as cotraining a language model) feasible and fast even under a constrained budget.

This post follows the following structure.  We first illustrate problems we frequently encounter when working at the word level which character level models are set to solve. Since the character level models are counterintuitive, we ask if they can learn anything significant and show a few works that answer that question. We then discuss the advantages and drawbacks of working at the character level and conclude with other techniques that solve the same problem.

## Oil well analytics - a motivating example

[WellLine](https://wellline.com/) provides "AI-Driven Well Timelines for Well Optimization" and were one of LightTags first customers. Part of their work is applying natural language processing to the human written logs each oil well produces.

![Annotating Oil Well Logs](wellline.webp)

WellLine's domain is almost a subdialect of English. Many of the words are in English, but many are not, there are abbreviations and jargon that only a domain expert could understand. Since this domain isn't abundant on the internet, common pre-trained NLP solutions such as word vectors don't have a vocabulary that fits WellLine's.

In WellLine's case, measurements and units are important, but tokenizing them before applying a model can lead to trouble. Consider the term *9 7/8" BHA* that is annotated as Rig Equipment. A standard tokenizer, that is - a standard assumption of what a word is, would separate the numbers giving us [9,7,/,8,"]. A more accurate tokenizer would require significant domain expertise and engineering effort to produce.

Many NLP use cases in industry follow a similar pattern. While the language of the texts in question is English, they tend to have unique words, abbreviations and use of punctuation or emoji that challenge conventional views of what a token is. Using off the shelf solutions that assume a standard tokenization is often counterproductive, as we saw above. However, the time and money required to build a domain-specific tokenizer might be very high.

These are cases where we thing character level models make a lot of sense. They come up more often than you might expect, whether dealing with financial chats, political tweets, biological or pharmaceutical text or morphologically rich languages such as Hebrew or Arabic. Often, we don't care about the tokenization or the semantics of the entire vocabulary. We just care about finding the information we need in those texts.

In these cases, character level models make a compelling case. By definition to excuse us from tokenizing, are able to handle vocabularies of arbitrary size and are computationally cheap, which facilitates pretraining and cotraining techniques without a TPU pod.

## Do Character Level models work?

However promising they might sound, character level models do run against intuition. Words have semantic meaning, characters don't and a priori it's not obvious we can expect a model to learn anything about the semantic contents of a piece of text by going over the characters. Luckily, we can stand on the shoulders of giants and look at a few works that show that they do.

### Character level models can learn non-trivial syntax

Back in 2015, Andrej Karpathy published [The Unreasonable Effectiveness of Recurrent Neural Networks](http://karpathy.github.io/2015/05/21/rnn-effectiveness/) in which he trained a recurrent neural network to write almost sensible C code. Here is an example (copy pasted from his post)

```c
/*
 * Increment the size file of the new incorrect UI_FILTER group information
 * of the size generatively.
 */
static int indicate_policy(void)
{
  int error;
  if (fd == MARN_EPT) {
    /*
     * The kernel blank will coeld it to userspace.
     */
    if (ss->segment < mem_total)
      unblock_graph_and_set_blocked();
    else
      ret = 1;
    goto bail;
  }
  segaddr = in_SB(in.addr);
  selector = seg / 16;
  setup_works = true;
  for (i = 0; i < blocks; i++) {
    seq = buf[i++];
    bpf = bd->bd.next + i * search;
    if (fd) {
      current = blocked;
    }
  }
  rw->name = "Getjbbregs";
  bprm_self_clearl(&iv->version);
  regs->new = blocks[(BPF_STATS << info->historidac)] | PFMR_CLOBATHINC_SECONDS << 12;
  return segtable;
}
```

Yoav Goldberg wrote a follow up to Karpathy's blog and said
>Impressive stuff, huh? How could the network learn to imitate the input like that? Indeed. I was quite impressed as well.
However, it feels to me that most readers of the post are impressed by the **wrong reasons**. This is because they are not familiar with unsmoothed maximum-likelihood character level language models and their unreasonable effectiveness at generating rather convincing natural language outputs.
>...
>Generating English a character at a time -- not so impressive in my view. The RNN needs to learn the previous nn letters, for a rather small nn, and that's it.
>
>However, the **code-generation example is very impressive**. Why? **because of the context awareness**. Note that in all of the posted examples, the code is well indented, the braces and brackets are correctly nested, and even the comments start and end correctly. This is not something that can be achieved by simply looking at the previous nn letters.

In that sense, Karpathy demonstrated that we can reasonably expect a character level model to pick up on "deep" structures of language and leverage them. Karpathy trained a language model, which by itself is not particularly useful, but we'll come back to why we think this illustrates the compelling power of character level models for applied NLP.

### Character level models can "understand" sentiment

In 2017, OpenAI released [a blog post](https://blog.openai.com/unsupervised-sentiment-neuron/) and [paper](https://arxiv.org/abs/1704.01444) where they trained a character level language model on Amazon reviews and discovered that the model learned to pick up on sentiment, by itself.
![OpenAI Neural Sentiment](openai-neural-sentiment.webp)
Some of the details of the experiment make it sound a bit impractical
> We first trained a multiplicative LSTM with 4,096 units on a corpus of 82 million Amazon reviews to predict the next character in a chunk of text. Training took one month across four NVIDIA Pascal GPUs, with our model processing 12,500 characters per second.

Still, the paper illustrates that character level models can capture the semantic properties of text, essentially from first principles.

### Character level models can translate

DeepMind's [Neural Machine Translation in Linear Time](https://arxiv.org/abs/1610.10099) and Lee et al. [Fully Character-Level Neural Machine Translation Without Explicit Segmentation](http://aclweb.org/anthology/Q17-1026) both demonstrated translation done at the character level. These are particularly compelling results, as the task of translation strongly captures the semantic understanding of the underlying text.
![Overcoming common problems with a char model](character-model-problems.webp)

DeepMind's paper is doubly interesting, as its model uses convolutions instead of the common RNN/LSTM. In practical terms, this makes training much faster, allowing iteration and exploration without a large compute budget or TPU cluster.

## The advantages of working at the character level

Having a sense that character level models work, we should consider what advantages they bring to the table and why we might want to use them.
We encounter the choice between characters and words in two places, at the model's input and the model's output.
On the input side, we get a much more permissive vocabulary and pay with longer sequences (more compute) and reduced semantic information. On the output side, we stand to gain a significant improvement in compute performance, which we'll elaborate on in a moment.

### Character level models allow for an open vocabulary

Consider the following sentence from the maintenance log of a deep sea oil rig (yes they have logs)
> Set 10 3/4" csg slips w/ 50K LBS.

Does it say "Set ten three-quarter inch ..." or "Set ten three-quarter inch ..."

The *s* suffix on *slips* gives us a strong clue that *10* quantifies the 3/4" slip and that the second reading is correct. One could expect a word level model to figure this out easily, however, we'd need to ask ourselves, what tokens exactly will our model see?

When we work at the word level, we have to choose a vocabulary up front. The list of words our model can handle is fixed, and all others are mapped to UNK. A lenient model usually has the 10–30K most frequent words in its vocabulary.

Word vectors trained on Google News don't contain the tokens 10, 3/4", CSV w/, or 50K.

Further, the nearest words to *slips* are slip, fall, etc., indicating that the model thinks slip is a verb and slips is an inflection of the verb. In other words, our model would see the sentence

> Set 10 3/4" csg slips w/ 50K LBS.

as

<!-- vale off -->
> Set UNK UNK UNK falls UNK UNK Location_Based
<!-- vale on -->

If we were trying to use NLP to understand what is happening on our drilling wells, using word vectors (naively) would get us nowhere fast. Character level models, on the other hand, are effectively unrestricted in their vocabulary and would see the input "as-is". Recalling Goldberg's comment about context, it's not hard to imagine that a character level model would be able to make the connection between that pluralizing *s* suffix and the 10 to "understand" that the 10 is a quantifier.

This advantage isn't limited to oil well analytics. It's common to apply NLP to user-generated text, which is rich with spelling mistakes, emojis, abbreviations, slang, domain-specific jargon, and grammar. On top of that, language evolves, and new words and symbols are added constantly. While character-level models don't solve all of the problems of human text, they do set up our models to process such text more robustly.

Which brings us to the advantages in output

### Character level models remove the bottleneck in training tasks

The more common problems in applied NLP /Text Mining are finding and disambiguating entities in the text, like the 10 above. That is, we don't often need to generate text. However, it's been well established that cotraining or pretraining our models on a language modeling task help by 1) facilitating generalization 2) reducing the number of labels needed for a given validation accuracy.

A language model aims to predict the next token given the previous tokens. As is standard, the final layer computes a softmax over every token in the vocabulary. With a large vocabulary, the softmax step and associated gradient calculations become the performance bottleneck in training a language model.

Character level models overcome this implicitly by having a small vocabulary to begin with. This opens the door to quickly pretraining or cotraining a language model alongside our main objective. While it's true that you can overcome this bottleneck by throwing more budget, hardware, and engineering at it, that drives up both the development and deployment costs of your model. The fact is that business engages in applied NLP to see ROI, preferably fast, and there is a limit to how much money can be thrown at a given problem.

## The disadvantages of character level NLP models

Character level models are not a panacea and come with their own set of drawbacks. The two most glaring ones are the lack of semantic content of the input (characters are meaningless) and the growth in the length of our inputs. The average English word has five characters meaning that dependent on architecture, we can expect a 5X increase in compute requirements.

### Characters are  Semantically Void

Giving up on the semantic content of words is a non-trivial decision and not one you see frequently in state of the art systems. At the time of writing, Googles [BERT](https://arxiv.org/abs/1810.04805) models set state of the art, and come pre-trained on a 100 languages. Not many organizations have the compute capacity to run BERT pretraining so forgoing these models is a non-trivial decision. Having said that, it is interesting to note that the [BERT model for Asian languages effectively works at the character level](https://github.com/google-research/bert/blob/master/multilingual.md#tokenization).

### Longer sequences increase Computational expense

Working at the character level effectively multiplies the length of your sequence by the average number of characters in a word. In English, that's five e.g. you pay a five-fold increase in compute, assuming you process your input sequentially. Seeing that one of the compelling reasons to use character level models is the fact that they computationally cheap, this seems to be rather counter-productive.

This is a valid and oft-frustrating drawback but one that only holds if you process your input sequentially. If you are willing and able to use either convolutions (like the Bytenet paper) or Transformers (like BERT) then the model's inherent parallelism effectively nullifies the cost of long sequences. It's still a tradeoff, essentially reaping the most benefit out of character level models (mildly) restricts your choice of architecture.

### You don't care about characters

If you are doing a sequence tagging task such as named entity recognition, you probably don't care about individual characters. Your model should tell you if a particular word is an entity or not and be measured on that output. Using a character level model means you'll get character level output which leaves you with more work to be done.

It gets worse. Character level models aren't obligated to any tokenization scheme and certainly not the one that you chose to judge your model under. A priori, there is nothing stopping your model from making predictions on subwords or disagreeing with your tokenization (such as splitting contractions where you'd keep them as one token). This effectively introduces a new class of error that you need to account for when evaluating your model.

There are solutions/patches to this problem. Applying a B-I-O scheme to your model helps, as it encourages the model to implicitly learn word boundaries. Learning a linear CRF, or using a beam decoder also helps alleviate this problem.

## Other solutions to the problems character level models solve

As we've said before, choosing characters or words is a tradeoff and its also a continuum. There are methods that capture the best of both worlds, although they come with their own drawbacks. In this section, we'll look at a few of them and discuss their relative advantages and drawbacks.

### Consuming large vocabularies

On the input side of things, the main issue that character level models solve is the ability to handle an arbitrarily large vocabulary, including resilience to spelling mistakes and other anachronisms of human text. There exist two other commonly used approaches, and likely a few we aren't aware of.

#### Subword Embeddings

These are a class of embedding techniques that account for subword units during embedding pretraining. One of the first papers that made use of these was [Neural Machine Translation of Rare Words with Subword Units](http://www.aclweb.org/anthology/P16-1162) which opens with:
> Neural machine translation (NMT) models
typically operate with a fixed vocabulary,
but translation is an open-vocabulary
problem. .... In this paper,
we introduce a simpler and more effective
approach, making the NMT model
capable of open-vocabulary translation by
**encoding rare and unknown words as sequences
of subword units**. This is based on
the intuition that various word classes are
translatable via smaller units than words,
for instance names (via character copying
or transliteration), compounds (via compositional
translation), and cognates and
loanwords (via phonological and morphological
transformations).

 Systems in this genre include Facebook's [fastText](https://arxiv.org/abs/1607.04606), Google's [SentencePiece](https://github.com/google/sentencepiece), and spaCy's HashEmbed, which relies on Bloom Embedding.

 In our internal work, we've found these to be frustrating. We often work with languages that have rich morphologies or domains where individual characters can change the meaning of a sentence dramatically. In these cases, subword embeddings leave something to be desired.

 Leonard Apeltsin of Primer.ai wrote a post about [Russian NLP](https://primer.ai/blog/Russian-Natural-Language-Processing/). In it, he looked at the nearest words to Vodka in the embedding space formed by [RusVectors](http://rusvectores.org/en/models/), which were built with knowledge of Russian morphology, versus those found by fastText. The results are amusing.

##### RusVectors nearest neighbors to Vodka

 ![RusVectors nearest neighbors to Vodka](rusvectors-vodka-neighbors.webp)

##### fastText Nearest Neighbors to Vodka

![fastText nearest words to Vodka](fasttext-vodka-neighbors.webp)

##### fastText Nearest Neighbors to Vodka (lemmatized)

![fastText nearest words to Vodka after lemmatization](fasttext-lemmatized-vodka-neighbors.webp)

### Combining word embeddings with character representations

Another approach that's gaining significant traction is to input both word embeddings and process the characters of each word, then concatenate the result of processing with the corresponding words vector.

![Character and word level representation](cnnlstm.webp)

This method seems to be an improvement over subword units as far as morphology is concerned. Since there is no a priori commitment to what the subword units are the model is free to learn what the optimal representation of a "word" is.

#### Characters and Words Combined From [Named Entity Recognition With Bidirectional LSTM-CNNs](https://www.aclweb.org/anthology/Q16-1026)

### Reducing the cost of the softmax

None of these methods on their own alleviate the problem of a large softmax layer, which as we've seen is often the performance bottleneck in a network. Often our core NLP task doesn't require a large softmax, but we do want to cotrain or pretrain a language model to improve our models' performance and data efficiency.

The solutions to this problem break down into two classes, the first class approximates the softmax in some more computationally friendly way. Sebastian Ruder gave an excellent rundown of [Softmax approximation methods](http://ruder.io/word-embeddings-softmax/) his blog.

The second circumvents the softmax by finding an alternative target. Matt Honnibal from spaCy has been working on adding something like this to the spaCy library. In the relevant [GitHub issue](https://github.com/explosion/spaCy/pull/2931), he writes
> My solution is to instead load in a pre-trained vectors file, and use the vector-space as the objective. This means we only need to predict a 300d vector for each word, instead of trying to softmax over 10,000 IDs or whatever. It also means the vocabulary we can learn is very large, which is quite satisfying.

Unfortunately, this technique has so far yielded a negative result, as Matt documents in his [spaCy pretraining experiment](https://github.com/honnibal/spacy-pretrain-polyaxon#experiment-2-ontonotes-ner-fasttext-vectors).

Another interesting work in this field is the recent [Semi-Supervised Sequence Modeling with Cross-View Training](https://arxiv.org/pdf/1809.08370.pdf).
> We, therefore, propose Cross-View
Training (CVT), a semi-supervised learning
algorithm that improves the representations of
a Bi-LSTM sentence encoder using a mix of
labeled and unlabeled data. On labeled examples,
standard supervised learning is used. On
unlabeled examples, CVT teaches auxiliary
prediction modules that see restricted views
of the input (e.g., only part of a sentence) to
match the predictions of the full model seeing
the whole input. Since the auxiliary modules
and the full model share intermediate
representations, this in turn improves the full
model.

![Cross-view training architecture](cross-view-training.webp)
In simpler terms, this technique assumes you have some labeled data and lots of unlabeled data. You switch between batches of labeled and unlabeled. On labeled batches the network as trained as usual. On Unlabeled batches, "auxiliary networks" that are exposed to only part of the input try to predict what the entire model predicted given the entire input. Since each auxiliary network sees a different slice of the input, each one has to learn to compensate for the missing piece. But since the weights are shared between the auxiliary and primary networks, the overall model gains from this. Crucially, from a "softmax perspective" the loss that is calculated on the auxiliary steps is the KL divergence of each networks predictions (a small softmax) instead of over the entire vocabulary.

## Summary

It's been a long journey but here's what we've seen in a nutshell.
Character level models tackle a few of the problems that word level models have. Notably, they allow us to consume an essentially arbitrarily large vocabulary and make the cost of pre/cotraining a language model affordable. Despite those promises, it wasn't clear that they are bound to work in practice. We saw Andrej Karpathy and OpenAI's work on character level language models as well as DeepMind's character level translation system. These showed that character level models can understand semantics in text.

We reviewed some of the drawbacks of character level models including the multiplicative growth in effective sequence size, the lack of inherent meaning in a character and the distance they have from the actual language goals we want to achieve.

Finally, we looked at alternatives to character models and saw that there are a number of embedding methods that take subword units into account, as well as model architectures that make up for their shortcomings. We also saw attempts to circumvent the costs of language modeling with a softmax, either by approximating the softmax itself or changing the language modeling task slightly.

At LightTag character models serve us well, in the sense that they are adaptable to multiple language domains, are easy and fast to train and don't come with external dependencies that need to be managed. Like all things in life, choosing the atomic unit your model sees is a tradeoff, and if you've made it this far we hope you've gotten an extra view with which you can judge that tradeoff for your use case. Want to talk about, or need help labeling data? Write to us

## References

1. [Fully Character-Level Neural Machine Translation without Explicit Segmentation](http://aclweb.org/anthology/Q17-1026)
2. [Neural Machine Translation in Linear Time](https://arxiv.org/abs/1610.10099)
3. [Russian Natural Language Processing](https://primer.ai/blog/Russian-Natural-Language-Processing/)
4. [Enriching Word Vectors with Subword Information](https://arxiv.org/abs/1607.04606)
5. [Unsupervised Sentiment Neuron](https://blog.openai.com/unsupervised-sentiment-neuron/)
6. [Learning to Generate Reviews and Discovering Sentiment](https://arxiv.org/abs/1704.01444)
7. [BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding](https://arxiv.org/abs/1810.04805)
8. [Named Entity Recognition with Bidirectional LSTM-CNNs](https://www.aclweb.org/anthology/Q16-1026)
9. [On word embeddings - Part 2: Approximating the Softmax](http://ruder.io/word-embeddings-softmax/)
10. [Semi-Supervised Sequence Modeling with Cross-View Training](https://arxiv.org/pdf/1809.08370.pdf)
