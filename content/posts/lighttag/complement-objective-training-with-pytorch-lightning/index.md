+++
title = "Complement Objective Training With PyTorch Lightning"
date = 2021-06-23T00:00:00Z
draft = false
description = "Complement Objective Training is a simple way to use incorrect-class probabilities and get more from labeled data in PyTorch Lightning."

[social]
image = "social.webp"
image_alt = "Archive cover for Complement Objective Training With PyTorch Lightning."

[share]
disable = false
languages = ["en"]

[original_publication]
site = "LightTag.io"
path = "/blog/complement-objective-training-with-pytorch-lightning/"
+++
Cross-entropy-based training is the standard in deep learning and NLP. During training, we ask our model to maximize the probability of the correct label. But in that paradigm, we're not telling our model to minimize the probabilities of the other, incorrect labels. Can we do better?

Yes.

![Output Probabilities for models trained with and without COT](chart.webp)

[Complement Objective Training](https://arxiv.org/pdf/1903.01182.pdf) (COT) is a simple technique to explicitly train our model to minimize the probabilities of incorrect classes.  COT was presented by Chen et al. at ICLR19 and showed an easy method to improve model performance.
In our own experiments with COT in production settings, we've confirmed those improvements and were particularly pleased with the low cost of implementation.
Using [PyTorch Lightning](https://www.pytorchlightning.ai/) (PL) and the [COT authors' open source code](https://github.com/henry8527/COT), adding COT to our training pipelines took only a few minutes.  The remainder of this post will give an accessible explanation of COT and then show how it can be easily added to your own training loop with PL.

## Cross-Entropy For Humans

Most NLP tasks are trained with cross-entropy. The model makes a prediction such as a document class for classification, a token label for NER, or a plain token for a  translation task.

The model's "prediction" isn't a single label. It's a probability distribution over all possible labels. During training, we know what the correct class is and thus have a "true"  probability distribution over K classes, where the correct class has probability 1, and all the other classes have a probability of 0 in our ground truth distribution.
The Problem With Cross-Entropy
Cross entropy is defined as y^log(y), so when y^ is 0, the cross-entropy is zero, and more importantly, the gradient with respect to y^ is always 0.
If the gradient is always 0 for incorrect classes, we intuitively give up on information that could help train our model.
With standard cross-entropy, we're explicitly rewarding the model for being correct, but we're not giving it explicit feedback for the mistakes it makes because the relevant gradients are 0. This is like training a new employee and praising them when they do something right but never letting them know when they do something wrong.

## Complement Objective Training

COT is a technique to effectively provide explicit negative feedback to our model.  The technique gives us non-zero gradients with respect to incorrect classes, which are used to update the model's parameters.

COT doesn't replace cross-entropy. It's used as a second training step as follows:
We run cross-entropy, and then we do a COT step.
We minimize the cross-entropy between our target distribution. That's equivalent to maximizing the likelihood of the correct class.
During the COT step, we maximize the entropy of the complement distribution. We pretend that the correct class isn't an option and make the remaining classes equally likely.

But, since the true class is an option, and we're training for it explicitly, maximizing the true classes probability and pushing the remaining classes to be equally likely is actually pushing their probabilities to 0 explicitly, which provides explicit gradients to propagate through our model.

## Using COT With PyTorch Lightning

Training a model is like hopping between islands of intellectual joy in a sea of tedious boilerplate. Managing device placement, logging, saving checkpoints, etc., are all effectively undifferentiated heavy lifting that we don't like to do.
For that reason, we adopted PyTorch lightning some time ago. It makes most of the boilerplate go away. When we experimented with COT, we were pleasantly surprised to find that PL made the implementation almost trivial.

COT is implemented as a two-step training procedure.  We make a forward and backward pass for standard cross-entropy and a second forward-backward pass for the COT objective.

While not mentioned in the paper, the authors experimented with training with both losses in a single step but got [consistently worse results](https://openreview.net/forum?id=HyM7AiA5YX¬eId=HJlOtAKta7). The reference implementation goes so far as to use different optimizers for each step (we found this impractical when using Adam on large transformers). Managing multiple training steps with separate objectives, their respective logging and possibly different optimizers sounds like another cruise through the boilerplate options. Luckily, PL stayed true to form and made the boilerplate go away.

When using PL, we implement our model in a LightningModule which is then trained by a trainer. Like a standard torch module, the LightningModule has a forward method, but it has some extra goodies and methods.
The LightningModule also offers a configure_optimizers method, which lets you return a list of optimizers.
When a list is returned, the training_step method is called once for each optimizer with an optimizer_id. In the training_step method, we calculate either the cross-entropy or COT criterion accordingly. Since we wanted to have two steps but use the same optimizer, we returned the same optimizer twice from the configure_optimizers method.

The full implementation took all of 15 minutes which made experimenting with COT a trivial decision. We've noticed faster convergence and a reduction in trivial errors when using models trained with COT. Your mileage may vary, but when using Lightning, it's so easy to implement it's worth a try.

## Code

### The COT Criterion

This is code taken from the paper author's repo. This essentially gives us a loss function

```python
from torch import nn
import torch
from torch.nn import functional as F
class ComplementEntropy(nn.Module):
    device='cuda'
    def __init__(self,num_classes:int):
        super(ComplementEntropy, self).__init__()
        self.num_classes = num_classes

    # here we implemented step by step for corresponding to our formula
    # described in the paper
    def forward(self, yHat, y):
        self.batch_size = len(y)
        self.classes = self.num_classes
        yHat = F.softmax(yHat, dim=1)
        Yg = torch.gather(yHat, 1, torch.unsqueeze(y, 1))
        Yg_ = (1 - Yg) + 1e-7  # avoiding numerical issues (first)
        Px = yHat / Yg_.view(len(yHat), 1)
        Px_log = torch.log(Px + 1e-10)  # avoiding numerical issues (second)
        y_zerohot = torch.ones(self.batch_size, self.classes).scatter_(
            1, y.view(self.batch_size, 1).data.cpu(), 0)
        output = Px.to(self.device) * Px_log.to(self.device) * y_zerohot.to(self.device)
        loss = torch.sum(output)
        loss /= float(self.batch_size)
        loss /= float(self.classes)
        return loss

```

### The PyTorch Lightning Module

Here we show the implementation described above. We use a PyTorch Lightning module that has two training steps
with a shared optimizer. The first step runs a cross entropy loss and the second the COT criterion.

```python
from typing import Any, List, Optional

from torch.optim.lr_scheduler import ReduceLROnPlateau
from transformers import AutoModelForSequenceClassification
import pytorch_lightning as pl
import torch
from torch.nn import functional as F

from pytorch_lightning.metrics import Precision

class CotBert(pl.LightningModule):
    def __init__(
        self,
        num_labels: int,
        model_path: Optional[str] = "distilbert-base-cased",
        use_cot: bool = True,
    ):
        super().__init__()
        self.use_cot = True
        self.bert = AutoModelForSequenceClassification.from_pretrained(
            model_path, num_labels=num_labels
        )
        self.bert.to(self.device)
        self.cot_criterion = ComplementEntropy(num_classes=num_labels)
        self.train_precision = Precision(num_classes=num_labels)
        self.val_precision = Precision(num_classes=num_labels)
        self.log("val_loss", 10000)


    def forward(self,batch):
        output = self.bert(
            input_ids=batch.input_ids.to(self.device),
            attention_mask=batch.attention_masks.to(self.device),
            labels=batch.label_id.to(self.device),
        )
        return output


    def training_step(self, batch, batch_idx: int, optimizer_idx: int):
        output = self.forward(batch)
        train_loss = output["loss"]
        logits = output["logits"]
        cot_loss = self.cot_criterion(logits, batch.label_id.to(self.device),)
        self.log("train_loss", train_loss)
        self.log("cot_loss", cot_loss,prog_bar=True)
        if optimizer_idx == 0:
          return train_loss
        else:
            return cot_loss


    def configure_optimizers(self,):
        """

        Returns
        -------
        We configure two optimizers, one for training and one for COT.

        """
        train_optimizer = torch.optim.Adam(self.parameters(), lr=1e-4)
        train_scheduler = {
            "scheduler": ReduceLROnPlateau(
                optimizer=train_optimizer,
                mode="min",
                factor=0.5,
                patience=50,
                min_lr=5e-6,
            ),
            "interval": "step",
            "frequency": 10,
            "monitor": "train_loss",
        }

        cot_optimizer = torch.optim.Adam(self.parameters(), lr=1e-4)
        cot_scheduler = {
            "scheduler": ReduceLROnPlateau(
                optimizer=cot_optimizer,
                mode="min",
                factor=0.5,
                patience=400,
                min_lr=5e-6,
            ),
            "interval": "step",
            "frequency": 500,
            "monitor": "train_loss",
        }
        return [train_optimizer, train_optimizer],[train_scheduler]


```
