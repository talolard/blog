+++
title = "Code to Align Annotations with Hugging Face Tokenizers"
date = 2020-09-20T00:00:00Z
draft = false
description = "An end-to-end implementation for aligning span annotations with Hugging Face tokenizers, windowing them, and batching them in PyTorch."

[social]
image = "social.webp"
image_alt = "Archive cover for Code to Align Annotations with Hugging Face Tokenizers."

[share]
disable = false
languages = ["en"]

[original_publication]
site = "LightTag.io"
path = "/blog/sequence-labeling-with-transformers/example"
+++
<!-- markdownlint-disable MD024 MD046 -->

>*This post [comes with a repo](https://github.com/LightTag/sequence-labeling-with-transformers)*

Our previous post on
[aligning span annotations to Hugging Face's tokenizer outputs](/en/posts/lighttag/sequence-labeling-with-transformers/)
discussed the various tradeoffs one needs to consider, and concluded that a windowing strategy over the tokenized text
and labels is optimal for our use cases.

This post demonstrates an end to end implementation of token alignment and windowing. We'll start by implementing
utility classes that make programming a little easier, then implement the alignment functionality which aligns offset
annotations to the out of a tokenizer. Finally we'll implement a PyTorch Dataset that stores our aligned tokens and
labels as windows, a Collator to implement batching and a simple DataLoader to be used in training.

We'll show and end to end flow on the DDI Corpus, recognizing pharmacological entities with BERT.

## Utility Classes For Convenient APIs

We'll start by defining some types and utility classes that will make our work more convenient

```python
from typing_extensions import TypedDict
from typing import List,Any
IntList = List[int] # A list of token_ids
IntListList = List[IntList] # A List of List of token_ids, e.g. a Batch
```

## The Alignment Algorithm

### FastTokenizers Simplify Alignment

Recent versions of Hugging Face's tokenizers library include variants of Tokenizers that end with Fast and inherit
from [PreTrainedTokenizerFast](https://huggingface.co/transformers/main_classes/tokenizer.html#transformers.PreTrainedTokenizerFast)
such as [BertTokenizerFast](https://huggingface.co/transformers/model_doc/bert.html#berttokenizerfast)
and [GPT2TokenizerFast](https://huggingface.co/transformers/model_doc/gpt2.html#gpt2tokenizerfast).

Per the tokenizer's documentation
> When the tokenizer is a “Fast” tokenizer (i.e., backed by HuggingFace tokenizers library), [the output] provides in addition several advanced alignment methods which can be used to map between the original string (character and words) and the token space (e.g., getting the index of the token comprising a given character or the span of characters corresponding to a given token).

Notably, the output provides the methods
[token_to_chars](https://huggingface.co/transformers/main_classes/tokenizer.html#transformers.BatchEncoding.token_to_chars)
and [char_to_token](https://huggingface.co/transformers/main_classes/tokenizer.html#transformers.BatchEncoding.char_to_token)
which do exactly what their name implies, provide mappings between tokens and character offsets in the original text.
That's exactly what we need to align annotations in offset format with tokens.

## A warmup implementation

Our final implementation will use the BIOUL scheme we mentioned before. But before we do that, let's try a simple
alignment to see what it feels like

```python
text = "I am Tal Perry, founder of LightTag"
annotations = [
    dict(start=5,end=14,text="Tal Perry",label="Person"),
    dict(start=16,end=23,text="founder",label="Title"),
    dict(start=27,end=35,text="LightTag",label="Org"),

              ]
for anno in annotations:
    # Show our annotations
    print (text[anno['start']:anno['end']],anno['label'])


```

    Tal Perry Person
    founder Title
    LightTag Org

```python
from transformers import BertTokenizerFast,  BatchEncoding
from tokenizers import Encoding
tokenizer = BertTokenizerFast.from_pretrained('bert-base-cased') # Load a pre-trained tokenizer
tokenized_batch : BatchEncoding = tokenizer(text)
tokenized_text :Encoding  =tokenized_batch[0]


```

```python
tokens = tokenized_text.tokens
aligned_labels = ["O"]*len(tokens) # Make a list to store our labels the same length as our tokens
for anno in (annotations):
    for char_ix in range(anno['start'],anno['end']):
        token_ix = tokenized_text.char_to_token(char_ix)
        if token_ix is not None: # White spaces have no token and will return None
            aligned_labels[token_ix] = anno['label']
for token,label in zip(tokens,aligned_labels):
    print (token,"-",label)
```

    [CLS] - O
    I - O
    am - O
    Ta - Person
    ##l - Person
    Perry - Person
    , - O
    founder - Title
    of - O
    Light - Org
    ##T - Org
    ##ag - Org
    [SEP] - O

### Accounting For Multi Token Annotations

In the above example, some of our annotations spanned multiple tokens.
For instance "Tal Perry" spanned "Ta", "##l" and "Perry". Clearly by themselves none of those tokens are a Person, and
so our current alignment scheme isn't as useful as it could be.
To overcome that, we'll use the previously mentioned BIOLU scheme, which will indicate if a token is the beginning,
inside, last token in an annotation or if it is not part of an annotation or if it is perfectly aligned with an annotation.

```python
def align_tokens_and_annotations_bilou(tokenized: Encoding, annotations):
    tokens = tokenized.tokens
    aligned_labels = ["O"] * len(
        tokens
    )  # Make a list to store our labels the same length as our tokens
    for anno in annotations:
        annotation_token_ix_set = (
            set()
        )  # A set that stores the token indices of the annotation
        for char_ix in range(anno["start"], anno["end"]):

            token_ix = tokenized.char_to_token(char_ix)
            if token_ix is not None:
                annotation_token_ix_set.add(token_ix)
        if len(annotation_token_ix_set) == 1:
            # If there is only one token
            token_ix = annotation_token_ix_set.pop()
            prefix = (
                "U"  # This annotation spans one token so is prefixed with U for unique
            )
            aligned_labels[token_ix] = f"{prefix}-{anno['label']}"

        else:

            last_token_in_anno_ix = len(annotation_token_ix_set) - 1
            for num, token_ix in enumerate(sorted(annotation_token_ix_set)):
                if num == 0:
                    prefix = "B"
                elif num == last_token_in_anno_ix:
                    prefix = "L"  # Its the last token
                else:
                    prefix = "I"  # We're inside of a multi token annotation
                aligned_labels[token_ix] = f"{prefix}-{anno['label']}"
    return aligned_labels


labels = align_tokens_and_annotations_bilou(tokenized_text, annotations)
for token, label in zip(tokens, labels):
    print(token, "-", label)
```

    [CLS] - O
    I - O
    am - O
    Ta - B-Person
    ##l - I-Person
    Perry - L-Person
    , - O
    founder - U-Title
    of - O
    Light - B-Org
    ##T - I-Org
    ##ag - L-Org
    [SEP] - O

Notice how **founder** above has a **U** prefix and the other annotations now follow a BIL scheme.

### Mapping Labels To Ids

It's great that we have our annotations aligned, but we need the labels as integer ids for training.
During inference, we'll also need a way to map predicted ids back to labels.
I'm going to make a custom class that handles that, called a LabelSet.

```python
import itertools


class LabelSet:
    def __init__(self, labels: List[str]):
        self.labels_to_id = {}
        self.ids_to_label = {}
        self.labels_to_id["O"] = 0
        self.ids_to_label[0] = "O"
        num = 0  # in case there are no labels
        # Writing BILU will give us incremntal ids for the labels
        for _num, (label, s) in enumerate(itertools.product(labels, "BILU")):
            num = _num + 1  # skip 0
            l = f"{s}-{label}"
            self.labels_to_id[l] = num
            self.ids_to_label[num] = l
        # Add the OUTSIDE label - no label for the token

    def get_aligned_label_ids_from_annotations(self, tokenized_text, annotations):
        raw_labels = align_tokens_and_annotations_bilou(tokenized_text, annotations)
        return list(map(self.labels_to_id.get, raw_labels))


example_label_set = LabelSet(labels=["Person", "Org", "Title"])
aligned_label_ids = example_label_set.get_aligned_label_ids_from_annotations(
    tokenized_text, annotations
)

for token, label in zip(tokens, aligned_label_ids):
    print(token, "-", label)
```

    [CLS] - 0
    I - 0
    am - 0
    Ta - 1
    ##l - 2
    Perry - 3
    , - 0
    founder - 12
    of - 0
    Light - 5
    ##T - 6
    ##ag - 7
    [SEP] - 0

## Batching

Now that we have alignment logic in place, we need to figure out how to load, batch and pad the data. We also need
to handle the case where our text is longer than we can feed our model. Below we show an implementation of a
particular strategy, windowing over uniform length segments of the text. This isn't the only strategy, or even
necessarily the best, but it fits our use case well. You can read more about
read [why we use windowing when training NER models with BERT](/en/posts/lighttag/sequence-labeling-with-transformers/).
Below we'll just show how to do that.

## The Raw Dataset

We'll be using the [DDI Corpus](https://www.sciencedirect.com/science/article/pii/S1532046413001123). You can download
a JSON version from the [DDI Corpus repository](https://github.com/LightTag/DDICorpus).
Let's take a quick look at the data

```python
import json
from pprint import pprint

raw = json.load(open("./ddi_train.json"))
for example in raw:
    # our simple implementation expects the label to be called label, so we adjust the original data
    for anno in example["annotations"]:
        anno["label"] = anno["tag"]
pprint(raw[2])
```

    {'annotations': [{'end': 58, 'label': 'drug', 'start': 47, 'tag': 'drug'},
                     {'end': 75, 'label': 'drug', 'start': 62, 'tag': 'drug'},
                     {'end': 135, 'label': 'drug', 'start': 124, 'tag': 'drug'},
                     {'end': 164, 'label': 'drug', 'start': 152, 'tag': 'drug'}],
     'content': 'Pharmacokinetic studies have demonstrated that omeprazole and '
                'erythromycin significantly increased the systemic exposure of '
                'cilostazol and/or its major metabolites.',
     'metadata': {'original_id': 'DrugDDI.d452.s1'}}

Let's take a look at that tokenized and aligned

```python
example = raw[2]
tokenized_batch = tokenizer(example["content"])
tokenized_text = tokenized_batch[0]
labels = align_tokens_and_annotations_bilou(tokenized_text, example["annotations"])
for token, label in zip(tokenized_text.tokens, labels):
    print(token, "-", label)
```

    [CLS] - O
    Ph - O
    ##arma - O
    ##co - O
    ##kin - O
    ##etic - O
    studies - O
    have - O
    demonstrated - O
    that - O
    o - B-drug
    ##me - I-drug
    ##pra - I-drug
    ##zo - I-drug
    ##le - L-drug
    and - O
    er - B-drug
    ##yt - I-drug
    ##hr - I-drug
    ##omy - I-drug
    ##cin - L-drug
    significantly - O
    increased - O
    the - O
    systemic - O
    exposure - O
    of - O
    c - B-drug
    ##ilo - I-drug
    ##sta - I-drug
    ##zo - I-drug
    ##l - L-drug
    and - O
    / - O
    or - O
    its - O
    major - O
    meta - B-drug
    ##bol - I-drug
    ##ites - I-drug
    . - L-drug
    [SEP] - O

## Padding and Windowing in a Dataset

Our dataset is conveniently split into sentences. We still need to batch it and pad the examples.
More commonly, data is not split into sentences, and so we will window over fixed sized parts of it.
The windowing, padding, and alignment logic will be done in a PyTorch Dataset, and we'll get to batching in a moment.

```python
from dataclasses import dataclass
from torch.utils.data import Dataset
from transformers import PreTrainedTokenizerFast
```

```python
@dataclass
class TrainingExample:
    input_ids: IntList
    attention_masks: IntList
    labels: IntList


class TraingDataset(Dataset):
    def __init__(
        self,
        data: Any,
        label_set: LabelSet,
        tokenizer: PreTrainedTokenizerFast,
        tokens_per_batch=32,
        window_stride=None,
    ):
        self.label_set = label_set
        if window_stride is None:
            self.window_stride = tokens_per_batch
        self.tokenizer = tokenizer
        for example in data:
            # changes tag key to label
            for a in example["annotations"]:
                a["label"] = a["tag"]
        self.texts = []
        self.annotations = []

        for example in data:
            self.texts.append(example["content"])
            self.annotations.append(example["annotations"])
        ###TOKENIZE All THE DATA
        tokenized_batch = self.tokenizer(self.texts, add_special_tokens=False)
        ###ALIGN LABELS ONE EXAMPLE AT A TIME
        aligned_labels = []
        for ix in range(len(tokenized_batch.encodings)):
            encoding = tokenized_batch.encodings[ix]
            raw_annotations = self.annotations[ix]
            aligned = label_set.get_aligned_label_ids_from_annotations(
                encoding, raw_annotations
            )
            aligned_labels.append(aligned)
        ###END OF LABEL ALIGNMENT

        ###MAKE A LIST OF TRAINING EXAMPLES. (This is where we add padding)
        self.training_examples: List[TrainingExample] = []
        empty_label_id = "O"
        for encoding, label in zip(tokenized_batch.encodings, aligned_labels):
            length = len(label)  # How long is this sequence
            for start in range(0, length, self.window_stride):

                end = min(start + tokens_per_batch, length)

                # How much padding do we need ?
                padding_to_add = max(0, tokens_per_batch - end + start)
                self.training_examples.append(
                    TrainingExample(
                        # Record the tokens
                        input_ids=encoding.ids[start:end]  # The ids of the tokens
                        + [self.tokenizer.pad_token_id]
                        * padding_to_add,  # padding if needed
                        labels=(
                            label[start:end]
                            + [-100] * padding_to_add  # padding if needed
                        ),  # -100 is a special token for padding of labels,
                        attention_masks=(
                            encoding.attention_mask[start:end]
                            + [0]
                            * padding_to_add  # 0'd attenetion masks where we added padding
                        ),
                    )
                )

    def __len__(self):
        return len(self.training_examples)

    def __getitem__(self, idx) -> TrainingExample:

        return self.training_examples[idx]
```

### Let's See what comes out

Below we'll create a dataset instance.
We first create a label_set, in this case there is only one label, **drug**.
We then instantiate our Dataset by passing the raw data, the tokenizer and the label_set.
We get back **TrainingExample** instances with the windowed and padded  input_ids and label_ids as well as attention_masks.

```python
label_set = LabelSet(labels=["drug"])
ds = TraingDataset(
    data=raw, tokenizer=tokenizer, label_set=label_set, tokens_per_batch=16
)
ex = ds[10]
pprint(ex)
```

    TrainingExample(input_ids=[1233, 1621, 4420, 18061, 5165, 1114, 4267, 6066, 1465, 3171, 1306, 117, 1126, 27558, 1104, 140], attention_masks=[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], labels=[3, 0, 0, 0, 0, 0, 1, 2, 2, 2, 2, 3, 0, 0, 0, 0])

### Batching

We still need a way batch these examples. We can't feed a list of TraingExamples to a model, we need to make tensors
out of the input_ids and labels. This is easily achieved with a collating function. A collating function gets a list
of items from our dataset (in our case a list of TraingExamples) and returns  batched tensors.

We'll simplify things, by making a **TraingBatch** class whose constructor is the collating function

```python
import torch


class TraingingBatch:
    def __getitem__(self, item):
        return getattr(self, item)

    def __init__(self, examples: List[TrainingExample]):
        self.input_ids: torch.Tensor
        self.attention_masks: torch.Tensor
        self.labels: torch.Tensor
        input_ids: IntListList = []
        masks: IntListList = []
        labels: IntListList = []
        for ex in examples:
            input_ids.append(ex.input_ids)
            masks.append(ex.attention_masks)
            labels.append(ex.labels)
        self.input_ids = torch.LongTensor(input_ids)
        self.attention_masks = torch.LongTensor(masks)
        self.labels = torch.LongTensor(labels)
```

## Training Our Model

With our batching ready, let's use a pre-trained model and show how to fine-tune it on our new dataset.

```python
from torch.utils.data.dataloader import DataLoader
from transformers import BertForTokenClassification, AdamW

model = BertForTokenClassification.from_pretrained(
    "bert-base-cased", num_labels=len(ds.label_set.ids_to_label.values())
)
optimizer = AdamW(model.parameters(), lr=5e-6)

dataloader = DataLoader(
    ds,
    collate_fn=TraingingBatch,
    batch_size=4,
    shuffle=True,
)
for num, batch in enumerate(dataloader):
    loss, logits = model(
        input_ids=batch.input_ids,
        attention_mask=batch.attention_masks,
        labels=batch.labels,
    )
    loss.backward()
    optimizer.step()
    print(loss)

```

    tensor(1.6987, grad_fn=<NllLossBackward>)
    tensor(1.6388, grad_fn=<NllLossBackward>)
    tensor(1.6135, grad_fn=<NllLossBackward>)
    ...

## The End

This is where this post ends. Check back soon for the follow up
where we'll share examples and tips for training sequence labeling models from pretrained transformers.

This post showed an implementation of the ideas in our previous post
on  [Sequence Labeling With Transformers](/en/posts/lighttag/sequence-labeling-with-transformers/).
You can find this post as a [notebook with some additional utilities here](https://github.com/LightTag/sequence-labeling-with-transformers).
Follow [us on twitter](https://twitter.com/LabeledData) for updates and share this post if you liked it.
