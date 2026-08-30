+++
title = "How to Label Data"
date = 2019-06-01T00:00:00Z
draft = false
description = "A complete guide to the seven stages of planning, executing, and scaling a successful NLP labeling project."

[social]
image = "social.webp"
image_alt = "Archive cover for How to Label Data."

[share]
disable = false
languages = ["en"]

[original_publication]
site = "LightTag.io"
path = "/how-to-label-data/"
+++
## 1. Introduction

At LightTag, we create tools to annotate data for natural language processing (NLP). At its core, the process of annotating at scale is a team effort. Managing the annotation process draws on the same principles as managing any other human endeavor. You need to clearly understand what needs to be done, articulate it repeatedly to your team, give them the tools and training to execute effectively, measure their performance against your goals, and help them improve over time.

In this post, we’ll follow the story of Jane, the director of NLP at Automatic Pizza. Automatic Pizza wants to improve its efficiency by letting customers order pizza through a chat interface. They have already implemented the interface, but they currently have employees inputting the information manually into their ordering system. Jane has been tasked with building an NLP system that can read orders as they come in and accurately input them into Automatic Pizza’s ordering system.

Jane knows she needs to be able to analyze a lot of data to build such a system—and lucky for her, Automatic Pizza has over a terabyte of conversation history she can work with. Unlucky for her, no one anticipated the need for the data to be labeled in any way; thus, there are no connections between specific conversations and the pizza that was ordered in that conversation. Jane realizes that if she is to execute this project, she will have to find a way to accurately and rapidly label data.

In this post, we will draw on our experience with various annotation projects to describe the seven distinct stages of an annotation life cycle that Jane will go through. We will explain the purpose of each stage, describe key considerations that should occur during each, and wrap each stage up with the assets you should expect to have at the end.

If you take one thing away from this post, it should be this: Successful annotation projects are always set up so that they continuously improve themselves.

## 2. Definitions

Jane will need to clearly communicate her goals and needs to her team, as well as report progress to her stakeholders. Being an NLP expert, she knows that language can be ambiguous and so sets out to define a few key terms that she’ll use when communicating with her colleagues—terms that we’ll use for this post.

## 2.1. Types of Annotation

Jane is aware of three distinct kinds of annotation that might be relevant for the project: Document classification, entity annotation and relationship annotation.

### 2.1.1. Document Classification

![Document Classification Example](document-classification-example.webp)

Document classification refers to an entire document (message, conversation). For example, when your email client puts things in the spam folder, it classifies them as Spam. Jane might classify messages as either Pizza Orders or Complaints, as we’ll see soon.

### 2.1.2. Entity Annotation

![Entity Annotation Example](entity-annotation-example.webp)

Entity annotation refers to a particular part of the text. For example, in the message “Please send 2 pepperoni pizzas,” pepperoni is a topping and 2 is a quantity. An entity annotation has two attributes: the type of the entity (topping, quantity) and its position in the text.

### 2.1.3. Relationship Annotation

![Drag and Drop Relationship Annotation](relationship-annotation-example.webp)
Sometimes entities relate to each other and we are interested in capturing how they relate. For example, in a message like “I’d like to order two pizzas,” “two” relates to “pizzas” and quantifies that word. For a human, it’s easy to understand that we are talking about two distinct pizzas, and relationship annotations make that understanding explicit.

#### Use Cases For Relationships

Jane was asked to explain the difference between entities and relationships to her colleagues and stakeholders. She consulted Google and searched for “Mother Teresa,” and then for “Mother Teresa’s mother.”
![Relationships in action](relationship-search-example.webp)
In the first search, Google recognizes “Mother Teresa” as an entity of type person. In the second search, it also recognizes Mother Teresa as a person, but also recognizes that “Mother Teresa” relates to “mother” (no pun intended) and that the entity we are really searching for is “Dranafile Bojaxhiu.”

## 2.2. Operational Concepts

Jane established definitions for the kinds of work she will do, but she also needs a vocabulary for how that work will be done.

### 2.2.1. Dataset

A dataset is a collection of examples that need to be annotated. An example might be a single message or an entire conversation. All of Automatic Pizza's data is a dataset, but Jane might want to break it down, for example to a dataset of messages with Orders and another dataset with Complaints.

### 2.2.2. Class

A class is a particular classification option. A document can be **Positive** or **Negative** and email can be **Spam** or **Ham**. There can be more than two classes, for example Salty, Sweet, Sour, Bitter and Umami. And sometimes one document can have more than one class—for example “Interesting” and “Positive.”

### 2.2.3. Tag

A tag is a nicer name for an entity type. Jane already defined an entity as something that has a type and a position in the document, but using the term “tag” is clearer than type. Examples of tags are **Person** (Jane), **Country** (Madagascar), **Topping** (Pepperoni) and **Emotion** (Fascinated).

### 2.2.4. Schema

Jane knows she’ll be asking people to *annotate* her *datasets* with *tags* and *classes*. But, she doesn’t want each annotator to pick and choose their own tags and classes; she wants everyone to use the same collection of tags and classes. She calls that collection a **schema**. We use schemas in real life all the time — for example, the colors on a traffic light are a schema—and it’s very important that we all understand and use the same schema when driving through an intersection. Jane wonders what she’d do if one day the traffic light at the end of her street changed from green to deep purple.

## 3. The Exploration Stage

## 3.1. Stage Purpose

Jane’s first step in annotating is understanding what data she has and what kinds of annotations her team will need to do, and what the schema - the tags and classes, will be. Answering those questions is the purpose of the exploration stage.

## 3.2. Key Considerations

Jane’s project begins with a terabyte of text and a high level goal, - “extract all of the components of a Pizza order from a conversation”. She knows that she’ll need to extract entities such as **Toppings**, **Addresses** and **Delivery times**, though she probably will need other concepts as well. Let’s follow her journey as she begins to explore the data.

### 3.2.1. Differentiating Relevant and Irrelevant Data

Jane opens up the data and the first example she sees looks like this:

```text
“Your pizza is the worst ever. It came cold, the order was wrong and you delivered to my neighbor. Never again!”
```

Another example reads

```text
“Are you a bot? Is this even human? What’s your name.”
```

Finally, Jane finds an example that looks like a real pizza order.

```text
“For tomorrow at 4 PM please send 2 pepperoni pizzas one with extra cheese and one with no sauce.
Also 2 garlic bread, two cokes a sprite and a big smile.
Please deliver to 49 LightTag Blvd, White Plains New York.
Our number for questions is 555-555-5555.”
```

Quickly it becomes clear that before she can begin labeling all the orders in the chatbot logs, she has to separate the data into relevant and irrelevant categories. This is a document classification task and Jane now knows she’ll have to classify her texts into at least two classes: Order and Not-Order.

### 3.2.2. Unanticipated Tags

Having found an order, Jane applies her schema to it, annotating the delivery time, address and toppings. After looking at the data she realizes she’ll need a few more tags.

* ``` *tomorrow at 4 PM* ```
  * Jane realizes she’ll need distinct tags for dates and time.
  * Jane also makes a note that she’ll need to normalize phrases like Tomorrow to an actual date.

* ```2 pepperoni pizzas one with extra cheese and one with no sauce```
  * Jane notices that the word Pizza is used once, but she’ll need to capture two different Pizzas.
  * Jane isn't sure yet if *“no sauce”* would be tagged as a **topping** or a **modification**.
  * Jane needs a tag that captures quantities such as  “2” and “one,”

* ```Also 2 garlic bread```
  * Garlic Bread is a new tag, which Jane calls “Side Dish.”

* ```two cokes```
  * Coke is yet another new tag, Coke needs to be labeled as a drink.

* ```a sprite```
  * “A” is a quantifier; Sprite is a drink.

* ```Please deliver to 49 LightTag Blvd, White Plains New York.```
  * This is an address, but Jane wonders if it should be broken down to Street, City, State.

* ```Our number for questions is 555-555-5555```
  * It’s important to capture the phone number, so a new entity type is required.

### 3.2.3. Relationships between entities

One phrase that stands out to Jane is ```2 pepperoni pizzas one with extra cheese and one with no sauce.```
As she thinks about it further, she realizes that “pepperoni pizza” is said once, but represents two separate pizzas: one with extra cheese and the other with no sauce. The way to annotate this is through a relationship structure, like this:
![Pizza Relation Annotation](pizza-relationship-annotation.webp)
While this is correct, Jane wonders whether it’s the right thing to do for her organization, which we’ll discuss in the next stage.

## 3.3. Stage Products

Having gone through the exploration stage, Jane has understood that she needs to carry out  a classification task to recognize Orders and an entity annotation task to recognize the details that comprise a Pizza order. She now knows what kind of work will need to be done, as well as what her Schemas look like.
Remember that Jane started with a terabyte of text, which made up her original dataset. Labeling so much text is not feasible, and Jane decides to break that dataset into a number of smaller datasets which her team will work on separately.

## 4. Feasibility and Value Analysis Stage

![Feasibility Analysis](dilbert-feasibility-analysis.webp)

## 4.1. Stage Purpose

Automatic Pizza Co doesn’t want labeled data, they want automated ordering of Pizzas through a chat interface. Having completed the exploration phase, Jane and her stakeholders can now have a discussion about the overall project feasibility, it’s likely impact and possible limitations.
The purpose of this stage is to carry out those conversations on the basis of the knowledge gained during exploration and ensure that the proposed labeling schema aligns with the business goals.

## 4.2. Key Considerations

### 4.2.1. Document Classification Serves the Business

One of the first things Jane realized was that her team would have to build a classifier, which could determine which messages were orders and which were something else, such as a customer complaint. During a discussion with stakeholders from the business, it is concluded that such a classifier is useful in and of itself, as the business can use it to route customer inquiries to the right person.
Jane’s team is confident they can build such a classifier and the business is pleased to see that the project can return value at low risk.

### 4.2.2. Accuracy Requirements

In the same discussion with business, the concept of performance metrics comes up. It’s quickly realized that all of the entities must be captured, and they can’t be misclassified. In data science parlance, the recall must be nearly 100 percent—that is, all of the concepts in an order need to be captured for the process to be completely automated.

Jane, being one to underpromise and overdeliver, says that 100 percent recall isn’t very likely and nearly sentences the project to doom. But Bob, an engineer on the chat interface team, points out that they can add a flow where the user validates the information that was captured, alleviating the risk of a misplaced order.

This reframes the conversation around performance requirements, from having a goal of full automation to one of ensuring the user has a great experience. The right metrics aren’t clear, but the team set a goal of 80 percent precision and 80 percent recall on each of the entity types and decide to test how users respond.

### 4.2.3. Handling Relationships

Jane previously realized that there is a relationship structure in some of the orders and that a perfect annotation of the documents would include those structures. However, no one on her team has ever worked with relationship extraction and the expertise isn’t available. This calls into question the value of annotating those relationships.

The business asks for how often those structures come up as a necessity to achieve the project’s goals. Having run over a few hundred examples during the evaluation, Jane estimates that 80 percent of messages don’t need to be parsed with relation structures.

It’s decided that if the project can deliver on 80 percent of the value without opening up a major research front, relationships will not be annotated or extracted with a willingness to modify this if it becomes crucial.

## 4.3. Stage Value

People and companies don’t label data for fun; they label data to achieve a business goal. What needs to be labeled, and how, are functions of that goal. Sometimes you’ll discover “peripheral” annotation tasks that drive business value, such as the classification stage above.
Other times, you’ll discover that the organization doesn’t have the resources or expertise to leverage annotations, and in those cases, you’ll either modify the project goals or go back to the drawing board.
In either case, these are important conversations to have prior to annotating at scale as they keep the data team and key stakeholders aligned.

## 5. Guideline Development Stage

![Standards](xkcd-standards.webp)

## 5.1. Stage Purpose

With clear goals and buy-in from her stakeholders, Jane can start building a team of annotators. But how will she tell them what to do and what exactly does she need to tell them? The purpose of this stage is to answer those questions, by establishing guidelines that will be shared with the annotating team.

## 5.2. This Is Extremely Important

At the outset of this guide, we said that “You need to clearly understand what you are trying to do, articulate it repeatedly to your team, measure their performance against your goals and give them the tools and training to improve and execute effectively.”

Guidelines are the first step in the process—articulating what you are trying to do and telling that to your team. Without guidelines, no one will know exactly what to do, and when you measure and get bad results it will be your own fault.

## 5.3. Key Considerations

The simplest guidelines are: “Here are the documents to label, and here are the classes and entities to capture. Good luck.” Guidelines should be more extensive than that, at a minimum describing the tags and entities and showing an example or two for each. For example, Jane might write:
“Topping—describes something that goes on a pizza, for example pepperoni or extra cheese.”
While this is a good start, the secret to writing good guidelines is to anticipate common errors and describe their resolution explicitly.

### 5.3.1. Where do errors come from?

While Jane has a perfectly clear understanding of what she expects, language is fickle and it’s not guaranteed that everyone else understands things in the same way. For example, “extra cheese” might be considered a topping in the USA but a modification to a non-native speaker. It’s important to discover these cases early and establish them in the guidelines.

#### 5.3.1.1. Syntactic Errors

A common source of error is ambiguity in the syntactic specifications. That’s a fancy way of saying that some of your annotators will capture trailing white spaces and others won’t; some will include commas in their annotations and others won’t. At the end of the day, you need one annotation, and need to decide how to annotate these cases and say so to your team.

#### 5.3.1.2. Semantic Classification Errors

Sometimes your team won’t agree on what something is. For example:

```text
I ordered a large chease pizza and a coke to Somehwere Blvd an hour ago! It still isn't here!!!!
What gives ?! Can you call me with an update ?
555-555-5556
```

Jane reads this and thinks it’s **not an order** because the customer says the order has already been placed. Bob, who is on her team, classifies this as **an order** because it has all of the information an order would have.

Both Jane and Bob have compelling arguments, and the right answer depends on what the downstream task is. In this case, Jane’s team wants to build a classifier that recognizes orders, and so Jane is correct.

#### 5.3.1.3. More Syntactic Errors

Sometimes your team won’t comprehend the fine differences between your various classes and entities. A ```large pepperoni pizza with pineapple``` is a **pizza** after all, so why not label the whole phrase as **pizza**?  Consider this set of annotations that Jane produced:
![Jane](janes-annotations.webp)
And compare it with Bob’s:
![Bob](bobs-annotations.webp)

Bob isn’t “wrong”—a ```large cheese pizza``` is a **pizza** after all—but the annotations he created don’t align with the project’s goals.

#### 5.3.1.4 Intent-Based Errors

When combining entity tags and document classification, you’ll often give your annotators an opportunity to think about whether they should annotate. For example, Alice, who also thought this was a complaint, did not annotate any entities because this was not an order:

![Alice](alices-annotations.webp)

### 5.3.2. Pro-Tip

Consider carefully whether to combine classification and entity annotation in the same task. By doing so you are giving your annotators more room for choice, and choice leads to ambiguity. While for the sake of efficiency it is tempting to do both at once, it does require clear guidelines to be put in place.

## 5.4. Stage Value

Setting clear guidelines for your annotators and making them easily accessible will help your team produce more consistent and reliable annotations. Establishing early on what errors are likely to occur will help you formulate clearer guidelines that address those situations and remediate them.

## 6. Establish a Golden Source

## 6.1. Stage Purpose

With guidelines in hand, Jane is ready to bring in a team of annotators, but she still needs a way to quickly review their work and gauge the performance of new team members. She realizes the team will need a gold-standard dataset to evaluate new team members against, and will use it to recognize errors and gaps in the guidelines.

## 6.2. Key Considerations

### 6.2.1. Using Agreement Metrics

The fastest way to establish a golden source of data is to have three or more people annotate the same set of documents, and then consider all annotations with a majority or unanimous vote. This is fast because it does not require manual review, but it can lead to gaps in the data.

### 6.2.2. Manual Review

A slower but more accurate way of establishing a golden set of data is to submit the annotations for manual review. To make this process effective, it is important to avoid re-annotating the document, but rather show individual annotations and let the reviewer accept or reject each one. Where there are conflicts, the reviewer should be shown all of them and should select the correct annotations.
![Conflicting annotations ready for manual review](conflicting-annotations.webp)

This kind of interface lends itself to simple binary decisions (Yes/No) and reduces the action space and cognitive load on the reviewer. In turn, the manual review process becomes much faster while remaining more accurate than aggregating by agreement.

### 6.2.3. Stage Value

Having a small golden source of data enables the team to track the accuracy of new members as they join, recognize gaps in the guidelines and quickly fix problems before they spread.

## 7. Automation Stage

![Automation Of Annotation](annotation-suggestions.webp)

## 7.1. Stage Purpose

Jane realizes that many of the concepts she needs to annotate are simple and can be annotated by a machine. For example, pepperoni will almost always be a topping. She can increase her team’s efficiency by “pre-annotating” the text with existing models, dictionaries, etc., to help her team work faster. In a pre-annotation setting, the annotators are shown suggestions, which they accept or reject before adding new annotations. This reduces the work they need to do on low-value “simple” annotations, freeing them up to work on the harder cases.

## 7.2. Key Considerations

### 7.2.1. Pre-annotation with Dictionaries

Automatic Pizza Co. has a list of all toppings on its menu, as well as a list of the drinks they sell. Jane realizes that she can use this list to create pre-annotations and show them to her annotators. Jane has a fairly large dictionary, since Automatic Pizza Co. has many toppings, and the scale of her data is quite large. She is concerned that using native “find” commands in her programming language might be too slow. She remembers hearing about clever string-matching algorithms back in school that make this much faster, and after some Google foo she finds a great string matching library like [FlashText](https://github.com/vi3k6i5/flashtext) to quickly pre-annotate her dataset.

### 7.2.2. Pre-annotation with Regular Expressions

Jane knows she needs to capture telephone numbers from the text and writes a quick regular expression for telephone numbers. Other common regular expressions include monetary values, email addresses, and dates.

### 7.2.3. External Models and Libraries

Other entity types can be captured by more specific models and programs. Jane needs to capture delivery addresses from orders, which don’t fit neatly into string-matching algorithms, but extracting addresses from text has been done many times before. Jane can take an open source implementation or build her own and use the output of that software to pre-annotate addresses or other domain-specific entity types.

## 7.3. Stage Value

Introducing automation has two main values. The first is that it increases annotator productivity by reducing the amount of work they have to do. We typically see a **doubling in annotation throughput** when automation is used.

The second value is that your annotators are implicitly validating the models you’ve used to pre-annotate. This can help you quickly discover classes and entities that you’ve already solved, reducing the modeling work you’ll need to do downstream. In Jane’s case, she finds that her Telephone regex and address model are perfect, but recognizing toppings needs work to accommodate for spelling mistakes.

## 8. Annotate

## 8.1. Stage Purpose

At this point, you’re ready to annotate.

## 8.2. Key Considerations

### 8.2.1. Workforce Management

Scaling an annotation project is really an exercise in workforce management. You’ll have one or more datasets consisting of examples that need to be labeled, and a team of labelers to do the work. Your job at this point is to make sure that the right labeler is doing the right work at the right time.

How you allocate work to your team and track who did what is paramount. A poor method will lead to duplicate work in some areas and missing labels in others. For smaller projects, this can be handled using Excel, but for larger tasks with more data and annotators, a specialized tool is often helpful.
![Make A Task](create-annotation-task.webp)

### 8.2.2. Is work pushed or pulled?

Jane has a team of annotators, a collection of data and a set of tags and classes to apply to that data. How does an annotator know what piece of data to label and with which tags? Older annotation systems had the annotator pull work, by browsing through a list of documents and selecting the collection of tags.
A more efficient tool will schedule work for annotators dynamically, and push the right job at the right time to the right person.

### 8.2.3. Tracking Performance

Typically, you’ll want to have a portion of your data labeled by more than one person, so that you can measure agreement on an ongoing basis. As you scale, your team will encounter phenomena you hadn’t anticipated and so agreement numbers should vary.

Measuring this is an important way of tracking down these phenomena and accommodate them in your data. In Jane’s case, perhaps the term “gluten free” is inconsistently annotated or skipped, because the schema she initially provided didn’t accommodate a tag for it, or the guidelines didn’t express them.

## 8.3. Stage Value

Managing a large annotation project is an exercise in resource allocation and routing. Pushing work toward your team instead of having them pull it saves labelers time, eliminates scheduling errors and reduces the managerial overhead involved in running an annotation project.

## 9. Final Review

## 9.1. Stage Purpose

This stage serves two goals: first, as a final confirmation of data quality, and second, to prepare your data for downstream uses. The majority of algorithms in use expect one label per input, so if you have multiple annotations you need to merge them (in case of agreement) or resolve conflicts if those exist. This stage is essentially a larger-scale version of establishing a golden source, and the same considerations apply.

## 9.2. Key Considerations

### 9.2.1. Manual vs. Automatic Review

In the section on establishing Golden Source, we said that a manual review process was more accurate. When reviewing a large dataset, with hundreds of thousands or millions of annotations, a manual review may not be feasible.
While it is recommended that at least some of the data is validated manually, a number of automated options may make sense

### 9.2.2. Using a Denoising Model

A project like [Snorkel](https://hazyresearch.github.io/snorkel/) is designed to take as input multiple conflicting and overlapping annotations and output a new model that is “more accurate” than its inputs. Snorkel does this by modeling the conflicts and overlaps in the annotations and learning a model of the “noise,” which it then subtracts.

## 9.3. Stage Value

Final Review ensures your data is of high quality and in a format that your downstream applications can consume (e.g., one output for each input). Where possible, a manual review process is preferred, but in light of the scale of some annotation projects, the use automated methods may be necessary.

## 10. Key Takeaways

## 10.1. Not a Linear Process

While we described this as a linear process, that’s not necessarily the case. With an ongoing review, you can spot errors and provide feedback to your annotators. The result should be a plot of your agreement (such as Fleiss’ kappa) that goes up and to the right.
Further, as your dataset grows, you might use it to train models that provide new and more accurate and more varied suggestions to your annotators, thereby increasing your team’s velocity and validating the model concurrently.

## 10.2. An effort with compounding returns

Labeling data is a lot of work, and this process seems to make more work. While that is true, it is worth it: everything you do downstream depends on the quality of the data you use, and the effects of data quality compound. High-quality data means high-quality models, easy debugging and faster iterations. Low-quality data means models that fail in production with no reliable means of analysis.

## 10.3. Communication is Key

Measuring your results is crucial for knowing what is going on, but that’s only half the battle. High-quality data comes from consistent communication between project managers and annotators, in a two-way dialogue.

## 11. Jane’s Big Promotion

Jane was originally daunted at the scope of her annotation project. She hadn’t anticipated it would be so much work and was concerned at all the things that could go wrong. Luckily, she followed the seven stages.

Using LightTag’s Exploration Mode, she was able to figure out exactly what was needed, articulate that to the business and set realistic targets. Crucially, she was able to identify what was not feasible or cost-effective and articulate that to the business with real data.

Jane leveraged LightTag’s built-in support for multiple datasets and schemas, to first discover what kinds of annotation her team needed to do, and then iterate on a schema with a small team. Using LightTag’s analytics, she was quickly able to discover what was going wrong, resolve her schema and sharpen her guidelines.

With her schema established, Jane leveraged LightTag’s workforce management features, which made it easy to bring in a large team of labelers from Automatic Pizza Co. LightTag helped her bring on board many people from across the business, even when most of them only worked for a few minutes. LightTag’s ability to show annotators the guidelines made communicating with them easy—even those team members in different time zones.

As the project progressed, Jane saw annotation throughput nearly double as LightTag’s AI learned from her team and made suggestions. She added even more speed by using LightTag’s API to upload pre-annotations for addresses and phone numbers.

Throughout the project, Jane was able to update her stakeholders about the project’s throughput and data quality by using LightTag’s analytics and dashboards. Doing so kept the business engaged while helping Jane ensure that her team was performing well and the labels being produced were accurate.

When it came time to produce a golden set from the annotations, Jane found that her efforts thus far had paid off. Agreement on annotations was consistently high thanks to the effective guidelines she had written and her ongoing monitoring. Using LightTag’s review mode, she was able to quickly validate the hundreds of thousands of annotations made, and resolve conflicting annotations when they did appear.

Jane’s journey is great, but what she, her team and her stakeholders care about are results. The model that was built on the back of the annotations worked in production. Automatic Pizza Co.’s customers were thrilled they could order pizza faster, and the business was thrilled they sold more pizzas at lower cost. The powers that be noticed Jane’s results, as well as her effective management of the team (thanks LightTag) and relevant and accurate communication with her stakeholders. She was promptly promoted to Head of Data for Automatic Pizza and we’re looking forward to seeing what she does next.
