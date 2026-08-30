+++
title = "Understanding the TensorFlow Estimator API"
date = 2018-12-03T00:00:00Z
draft = false
description = "The motivation behind TensorFlow's Estimator API, the abstractions it provides, and how its pieces fit together."

[social]
image = "social.webp"
image_alt = "Archive cover for Understanding the TensorFlow Estimator API."

[share]
disable = false
languages = ["en"]

[original_publication]
site = "LightTag.io"
path = "/blog/tensorflow-estimator-api/"
+++
TensorFlow's [Estimator API](https://www.tensorflow.org/guide/estimators) makes the engineering and operational aspects of deep/machine learning simpler. We've found it immensely valuable for reducing the complexity of our model training and production deployments. The learning curve for the Estimator API is non-trivial, and when we were figuring it out we felt there was a lack of conceptual motivation in the available documentation. This post walks you through the core concepts and motivations of the API and should be read alongside the documentation and examples.

## LightTag's Use Case

At LightTag we provide tools to annotate text, most of our customers use LightTag to gather training data for their own machine learning models. As users annotate text we train models that suggest more annotations. Users can accept or reject annotations which further inform our models as well as provide human validation of the model.

We don't share data between customers yet need to support each customer's unique datasets, languages and prediction targets such as different entities and or document classifications. Additionally, most of our customers have sensitive data and run our products on their own premise. Thus we can't expect to do training or prediction in the cloud.

These constraints add up to become an operational and engineering pain which the Estimator API has helped alleviate.

## Deploying a model is as much software engineering as it is data science

Putting a model intro production follows four steps

1. We define the model - the operations it performs on our data
2. We train the model - exposing it to examples and updating its parameters
3. We evaluate the model - and scratch our heads why it doesn't work.
4. We serve the model - we expose it to the world or internal systems and serve its predictions.

Each of steps 2-4 impose subtleties on how we engage with our model - and these subtleties become software engineering tasks. During training and evaluation we'll have ground truth labels we'll compare the model too. During training, we'll use those labels to update parameters while in evaluation we'll be calculating the model's performance. During prediction, we'll be running the model on data without labels and from a source, we may not completely understand.

Furthermore, we'd often like to have different operational behavior during each of these stages. During training, we'd like to save checkpoints of our models progress, while evaluation has no such requirement. We might be interested in the model's accuracy score on evaluation data, but don't want to waste compute cycles calculating it during training. Often we'd like to preprocess our data during training or apply dropout but usually, don't want to do so during evaluation and prediction.

Said concisely, getting a model into production is as much software engineering as it is data science. We encounter different requirements and concerns at each of these stages and want to leverage separation of concerns to write maintainable and reusable code. The Estimator API is a (sub) framework that enables this.

> *We present a framework for specifying, training, evaluating, and
deploying machine learning models. Our focus is on simplifying
cutting-edge machine learning for practitioners in order to bring
such technologies into production.* -[Estimator API white paper](https://arxiv.org/pdf/1708.02637.pdf)

## What Problem does the Estimator API Solve?

The Estimator API guides us towards software engineering best practices on our route to deploying a model to production. Its implicit assumption about the world is that a model is distinct from the process that trains it, and both are distinct from the procedures that evaluate or serve it. This may sound like a tautology but a quick glance at models on GitHub, and likely introspection into your own deep learning journey reveals that many models and implementations don't separate these as conveniently as one might like.

## Should you use the Estimator API?

There is no such thing as a free lunch and the price you pay for using the estimator API is a non-trivial learning curve.
> *Because our
the framework is built on TensorFlow, we inherit a number of common
design patterns: there is a preference for functions and closures
over objects, wherever such closures are sufficient; callbacks are
common* -[Estimator API white paper](https://arxiv.org/pdf/1708.02637.pdf)

Our experience with TensorFlow prior to using the Estimator API didn't really involve closures and we all carry trauma from callbacks due to the dark days of jQuery. In other words, when we set out to try the estimator API it didn't feel familiar or intuitive and it took us on average two hours of grokking code and reading docs to get comfortable with it.

Whether that's a valuable investment or not depends on your use case. If you aren't aiming for a production release of a model, or are mostly focused on figuring out a trick or a particular method then this might not be worth your time. But if you need to get to production or are working on reusable components for your DL stack like we are then it's worth the investment.

## The Core Concepts of the Estimator API

The Gateway to the Estimator API is the [Estimator](https://www.tensorflow.org/api_docs/python/tf/estimator/Estimator) class. If you can successfully instantiate the class then you'll get an object with **train**, **evaluate** and **predict**.  Each of these accepts an **input function** which we will come back to, and then do exactly what you'd expect they would do.

Then the question becomes how do we instantiate an Estimator?

At a bear but sufficient minimum, we need to [instantiate the estimator](https://www.tensorflow.org/api_docs/python/tf/estimator/Estimator#__init__) API with a model function. That sounds simple at first, but if you think about it it's an overly simplistic and this is where things get a little confusing.

### The Model Functions EstimatorSpec

The model function that we pass to the Estimator returns an [EstimatorSpec](https://www.tensorflow.org/api_docs/python/tf/estimator/EstimatorSpec) instance.
 We'll get back to the model functions gory details, but for now, just recall that the Estimator uses the EstimatorSpec to decide what to do. Since this seems convoluted at first glance it's worthwhile to stop and appreciate the motivation for doing so.

Since TensorFlow is (still) a static graph framework, we needed to construct new graphs for our train/eval/predict steps or write expansive models that exposed an array of ops, which we'd call depending on the stage we were in. Both of these are mediocre and error-prone software engineering, the first leads to code duplication and subtle errors, while the latter leads to bloated unmaintainable model code.

The Estimator API solves this by calling the input function with a mode parameter. When you write your model function, you can tell it to do different things based on the mode, such as use a different data source, collect different metrics or not run your optimizer on your evaluation data.

### The Model Function

So, the model function is passed as a parameter to the Estimators constructor and returns an EstimatorSpec. We know that the Estimator calls the model function with a parameter *mode* that tells it if it's in training/eval/prediction. But what else does the estimator call the model function with?

The model function gets three crucial parameters. **features**, **labels** and **mode**.

**mode** Is simply the name of the method we called on the Estimator, train, evaluate or predict and we can use it to alter the model's behavior

**features** and **labels** are a bit weird. They themselves are the output of the *input function* that we call Estimator.train/evaluate/predict with, again, we'll come back to that function in a moment. What we've found useful is the fact that each of these can be a dictionary of tensors, which makes it easy to pass the data for multi-task learning.

The model functions job is to create an Estimator spec from these inputs. The docs have a good example (which we've added comments too)

```python
def my_model_fn(features, labels, mode):
  if (mode == tf.estimator.ModeKeys.TRAIN or
      mode == tf.estimator.ModeKeys.EVAL):
    loss = ... # Calculate the loss if we are in training or eval
  else:
    loss = None #In prediction their is no loss
  if mode == tf.estimator.ModeKeys.TRAIN:
    train_op = ... # If we are in training mode define a training op
  else:
    train_op = None #Otherwise we don't need one
  if mode == tf.estimator.ModeKeys.PREDICT:
    predictions = ... # If we are predicting calculate the predictions
  else:
    predictions = None

  return tf.estimator.EstimatorSpec( # Retrun an Estimatorspec
      mode=mode, # The mode tell's the spec which ops to use
      predictions=predictions, # The predictions (only called if mode==PREDICT)
      loss=loss, # Only used if mode!=PREDICT
      train_op=train_op # Only used if mode==TRAIN
      )
```

Something of note here is that in this example there is no explicit mention of a model. You're free to define a model in whatever way you want. It could be inline in this function, you could make a separate class or a series of functions, as you see fit. What you are required to produce are the ops for each mode.

* For mode == ModeKeys.TRAIN: required fields are loss and train_op.
* For mode == ModeKeys.EVAL: required field is loss.
* For mode == ModeKeys.PREDICT: required fields are predictions.

### The Input Function

We mentioned a mysterious input function a few times. Recall that once you have an instance of an Estimator, you can call it's *train*, *evaluate* or *predict* methods and each of these require an *input_function* as an argument.

You can use the input function in a few ways, but we'll describe the way we do it. In our use cases, we return a [Dataset](https://www.tensorflow.org/api_docs/python/tf/data/Dataset) object. You can read our [guide to getting text into TensorFlow](https://medium.com/@TalPerry/getting-text-into-tensorflow-with-the-dataset-api-ffb832c8bec6), but in a nutshell, you want it to return a tuple (features, labels) where each of features and labels is a dictionary of tensors

```python
def generator_function(params):
    #Generates data, returns a triple of ids, length, value
    while True:
        d = createNum2WordDict(size=100, high=params['max_num'])
        for value, word in d.items():
            if value == 0:
                continue
            ids = [vocab[char] for char in word]
            length = len(word)
            yield (ids, length, value)


def input_fn(params):
    generator = lambda: generator_function(params) #instantiate the generator with params and make it callabale
    dataset = tf.data.Dataset.from_generator( #Build a tensorflow dataset from the generator
        generator=generator,
        output_types=(tf.int64, tf.int64, tf.double),
        output_shapes=(tf.TensorShape([None]), tf.TensorShape([]), tf.TensorShape([]))
        #Output is (List of ints, single int, single double)
    )
    dataset = dataset.padded_batch(
        params['batch_size'], #Make the dataset a batch and pad all sequences to same length)
        padded_shapes=(tf.TensorShape([None]), tf.TensorShape([]), tf.TensorShape([]))
    )

    dataset = dataset.map(lambda x, y, z: ({"sequences": x, "lengths": y}, z %2))
    # Converted the dataset of tuples into a dataset that returns a tuple of (dict of tensors, Tensor)
    return dataset

```

### Putting it all together

To recap, here's what we've seen

1. You can instantiate an Estimator instance by providing it with a model function
2. The Estimator exposes train, evaluate and predict methods that do what they say.
3. The model function you provide to the Estimator returns an EstimatorSpec. It runs the relevant ops for the mode you are in
4. The train, evaluate and predict methods each take an input function as an argument. The input function provides features and labels ( unless you are in predict mode)

We figured this out by grokking through Google's [Transformer Model](https://github.com/tensorflow/models/blob/master/official/transformer/transformer_main.py). That code base exemplifies everything we mentioned here and shows how the concepts can be used very effectively. Reading that code in light of this post should be a good next step.

## Summary

The Estimator API provides a framework for consistently managing and executing the lifecycle of a model from training to prediction in production. It relies on callbacks and closures, making the learning curve a bit steep (in our opinion). It makes separation of concerns, code reuse and deployment much simpler and as such we see it as a software engineering tool much more than a data science tool. In that light, if you're just getting started with TensorFlow it might not be the place to start. However, if you are concerned with simplifying the engineering and operational aspects of machine learning, it is an invaluable tool.
