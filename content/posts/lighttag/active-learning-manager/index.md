+++
title = "ALMa: Active Learning (Data) Manager"
date = 2020-05-10T00:00:00Z
draft = false
description = "ALMa makes active learning easier by abstracting away the bookkeeping of labeled and unlabeled data."
categories = ["NLP", "ML", "Active Learning"]

[social]
image = "social.webp"
image_alt = "Archive cover for ALMa: Active Learning (Data) Manager."

[share]
disable = false
languages = ["en"]

[original_publication]
site = "LightTag.io"
path = "/blog/active-learning-manager/"
+++
<!-- markdownlint-disable MD046 -->

Active Learning is a popular technique to reduce annotation costs by using AI to decide what to label next.
The subtle bookkeeping involved in keeping track of what has been labeled is tedious and error-prone. We need to train our learner on **Labeled** data, but sample new examples to label from **Unlabeled** data. As we label data, it moves between the two subsets of our **Dataset**, making the bookkeeping a chore that should be abstracted away.

Today we're happy to [open-source ALMa](https://github.com/LightTag/ALMa) the **Active Learning Manager** that abstracts away the bookkeeping. Whereas most implementations modify the data array in place, ALMa maintains views of **Labeled** and **Unlabeled** subsets of the original **Dataset**.

## The Problem ALMa Solves

In a typical active learning setup we start with an Array **Dataset** of examples which naturally divides into two disjoint subsets **U**labeled data and **Labeled** data. When we work with our **Unlabeled** data as an array, its indices don't correspond to the indices of our **Dataset** and they change every time we add new labeled data.

### Active Learning without ALMa involves confusing Bookkeeping

In the example below, taken from the [ModAL](https://modal-python.readthedocs.io/en/latest/content/examples/pool-based_sampling.html) library, the original dataset is constantly modified with hard-to-read NumPy code. While it is short, it is difficult to grok and harder still to ensure correctness.

```python
for index in range(N_QUERIES):
  query_index, query_instance = learner.query(X_pool)
  #What is this reshape stuff doing ?
  X, y = X_pool[query_index].reshape(1, -1), y_pool[query_index].reshape(1, )
  learner.teach(X=X, y=y)

  #Confusing np.delete
  X_pool, y_pool = np.delete(X_pool, query_index, axis=0), np.delete(y_pool, query_index)
```

## Active Learning with ALMa is easy

Here's the same code using ALMa, it has a few more lines, but the bookkeeping has effectively been abstracted away.

```python
for index in range(N_QUERIES):
    index_to_label, query_instance = learner.query(manager.unlabeld)
    original_ix = manager.get_original_index_from_unlabeled_index(index_to_label)
    y = original_labels_train[original_ix]
    label = (index_to_label, y)
    manager.add_labels(labels)
    learner.teach(X=manager.labeled, y=manager.labels)

```

## ALMa's solution: Simpler Bookkeeping with Views and Offsets

ALMa uses NumPy's fancy indexing to maintain views of the **Dataset** which minimizes and simplifies the bookkeeping that needs to be done. ALMa relies on two NumPy features to manage the bookkeeping, [fancy indexing](https://docs.scipy.org/doc/NumPy/reference/arrays.indexing.html#advanced-indexing) with _mask index arrays_ to create views of the data, and the _nonzero_ method to calculate index offsets for new labeled data (which comes in indexed relative to the **Unlabeled** subset)

### Maintaining Views of the Labeled and Unlabeled data

ALMa uses NumPy's [mask index arrays](https://docs.scipy.org/doc/NumPy/user/basics.indexing.html#boolean-or-mask-index-arrays) to create "views" of **Data** that correspond to our **Labeled** and **Unlabeled** data.

When we initialize an ActiveLearningManager it creates a boolean array whose indices are True if the corresponding feature has been labeled, and False otherwise.

```python
# Create a boolean array with the same length as features
self.labeled_mask = np.zeros(self.features.shape[0], dtype=bool)
```

This makes getting the **Unlabeled** indices simple

```python
def unlabeled_mask(self):
    return np.logical_not(self.labeled_mask)
```

We can then expose the views on the ActiveLearningManager as follows:

```python
    @property
    def labeled(self):
        return self.features[self.labeled_mask]

    @property
    def unlabeld(self):
        return self.features[self.unlabeled_mask]
```

### Adding New Labels

With our views in place our active learning process boils down to:

- Sample some data from the **Unlabeled** subset
- Have the annotator label them and update ALMa
- Train the learner on the updated **Labeled** subset
- repeat

But, when we sample from the **Unlabeled**, the examples are not indexed relative to the original dataset and so we need a way to recover to correct indices.

This would be easily solved if we had an array whose indices were the same as our **Unlabeled** data and values were the corresponding indices in the **Dataset**.

#### Mapping offsets with NumPy's nonzero method

This is actually easier done than said, NumPy provides a [nonzero()](https://docs.scipy.org/doc/NumPy/reference/generated/NumPy.nonzero.html#NumPy.nonzero) method that gives us exactly that.

```python
import numpy as np
a = np.zeros(10,dtype=np.bool)
a.nonzero()[0]
```

    array([], dtype=int64) #Empty array

```python
a[3] =True
a.nonzero()[0]
```

    array([3]) # Maps the first true value to its index in the original array

```python
a[7] = True
a.nonzero()[0]
```

```python
array([3, 7]) # Maps both True values to their correct place in the original array
```

#### Adding Labels With NumPy's nonzero method

ALMa holds a boolean array _labeled_mask_ whose values are True when we already have a label for the example at the index. We calculate _unlabeled_mask_ by taking the logical _not_ of _labeled_mask_. So calling _nonzero()_ on our _unlabeled_mask_ gives us a new array whose indices are the indices of our **Unlabeled** data and values are the indices of that example in our **Dataset**.

Armed with that, calculating the correct offsets is simple:

```python
    def _offset_new_labels(self, labels_for_unlabeled_dataset: LabelList):

        if len(self._labels) == 0:
            # Nothing to correct in this case
            return labels_for_unlabeled_dataset
        labels_for_dataset: LabelList = []
        unlabeled_indices_map = self.unlabeled_mask.nonzero()[0]

        for label in labels_for_unlabeled_dataset:
            index_in_unlabeled, annotation = label
            index_in_dataset = unlabeled_indices_map[index_in_unlabeled]
            new_label: Label = (index_in_dataset, annotation)
            labels_for_dataset.append(new_label)
        return labels_for_dataset

```

And when we add one or more new labels ALMa does

```python
    def add_labels(self, labels: LabelList, offset_to_unlabeled=True):
        if isinstance(labels, tuple):  # if this is a single example
            labels: LabelList = [labels]
        elif isinstance(labels, list):
            pass
        else:
            raise Exception(
                "Malformed input. Please add either a tuple (ix,label) or a list [(ix,label),..]"
            )
        if offset_to_unlabeled:
            labels = self._offset_new_labes(labels)
        self._update_masks(labels)
        for label in labels:
            self._labels[label[0]] = label[1]
```

## Final Thoughts

Managing state is generally difficult and error prone, and this is true for active learning as well. By minimizing the state being mutated and working with views of the data we can simplify the end users experience. We hope that using ALMa will help you focus on your research or production models by freeing you up from bookkeeping. [Clone ALMa here](https://github.com/LightTag/ALMa)
