---
title: Convolutional Methods for Text
tags: ['NLP', 'convolutions', 'deep learning', 'rnn']
draft: false
date: '2017-05-22'

---


### tl;dr

* RNNs funktionieren großartig für Text, aber Convolutions können es schneller
* Jeder Teil eines Satzes kann die Semantik eines Wortes beeinflussen. Deshalb wollen wir, dass unser Netzwerk die gesamte Eingabe auf einmal sieht
* Ein so großes rezeptives Feld zu bekommen, kann Gradienten verschwinden lassen und unsere Netzwerke scheitern lassen
* Das Vanishing-Gradient-Problem können wir mit DenseNets oder dilatierten Convolutions lösen
* Manchmal müssen wir Text generieren. Wir können „Deconvolutions“ verwenden, um Ausgaben beliebiger Länge zu erzeugen.

### Intro

In den letzten drei Jahren hat das Feld des NLP dank Deep Learning eine enorme Revolution erlebt. Der Anführer dieser Revolution war das rekurrente neuronale Netzwerk und insbesondere seine Ausprägung als LSTM. Parallel dazu wurde das Feld des Computer Vision durch Convolutional Neural Networks umgeformt. Dieser Post untersucht, was wir „Text-Leute“ von unseren Freunden lernen können, die Vision machen.

### Häufige NLP-Aufgaben

Um die Bühne zu bereiten und uns auf ein Vokabular zu einigen, möchte ich ein paar der gängigeren Aufgaben in NLP vorstellen. Der Konsistenz halber nehme ich an, dass alle Eingaben unseres Modells Zeichen sind und dass unsere „Beobachtungseinheit“ ein Satz ist. Beide Annahmen sind nur der Bequemlichkeit halber, und du kannst Zeichen durch Wörter und Sätze durch Dokumente ersetzen, wenn du möchtest.

#### Klassifikation

Vielleicht der älteste Trick im Buch: Oft wollen wir einen Satz klassifizieren. Zum Beispiel möchten wir eine E-Mail-Betreffzeile als Hinweis auf Spam klassifizieren, die Stimmung einer Produktrezension erraten oder einem Dokument ein Thema zuweisen.

Der naheliegendste Weg, diese Art von Aufgabe mit einem RNN zu handhaben, ist, den gesamten Satz Zeichen für Zeichen einzuspeisen und dann den finalen Hidden State des RNN zu beobachten.

#### Sequenz-Labeling

Sequenz-Labeling-Aufgaben sind Aufgaben, die für jede Eingabe eine Ausgabe zurückgeben. Beispiele sind Part-of-Speech-Tagging oder Entity-Recognition-Aufgaben. Während das Bare-Bones-LSTM-Modell weit vom State of the Art entfernt ist, ist es leicht zu implementieren und liefert überzeugende Ergebnisse. Siehe [dieses Paper](https://arxiv.org/pdf/1508.01991.pdf) für eine ausgefeiltere Architektur

![Bidirektionale LSTM-Architektur für Sequenz-Labeling](./bilstm-ner-sequence-labeling.webp)

#### Sequenzgenerierung

Vermutlich die beeindruckendsten Ergebnisse im modernen NLP gab es bei der Übersetzung. Übersetzung ist eine Abbildung von einer Sequenz auf eine andere, ohne Garantien für die Länge des Ausgabesatzes. Zum Beispiel ist die Übersetzung der ersten Worte der Bibel von Hebräisch nach Englisch: בראשית = „In the Beginning“.

Im Zentrum dieses Erfolgs steht das Sequence-to-Sequence- (aka Encoder-Decoder-)Framework, eine Methodik, eine Sequenz in einen Code zu „komprimieren“ und sie dann in eine andere Sequenz zu dekodieren. Bemerkenswerte Beispiele sind Übersetzung (Hebräisch encodieren und nach Englisch decodieren), Bildbeschreibung (ein Bild encodieren und eine textuelle Beschreibung seines Inhalts decodieren)

![Pipeline für Bildbeschreibung mit CNN-Features, die einen Attention-LSTM-Decoder speisen](./cnn-attention-image-captioning.webp)

Der grundlegende Encoder-Schritt ist ähnlich zu dem Schema, das wir für Klassifikation beschrieben haben. Das Erstaunliche ist, dass wir einen Decoder bauen können, der lernt, Ausgaben beliebiger Länge zu generieren.

Die beiden Beispiele oben sind eigentlich beide Übersetzung, aber Sequenzgenerierung ist etwas breiter als das. OpenAI hat kürzlich [ein Paper veröffentlicht](https://blog.openai.com/unsupervised-sentiment-neuron/), in dem sie lernen, „Amazon Reviews“ zu generieren, während sie die Sentiment-Ausrichtung der Ausgabe steuern

![Generierte Amazon-Reviews mit Sentiment auf positiv oder negativ beschränkt](./sentiment-controlled-examples.webp)

Ein weiterer persönlicher Favorit ist das Paper [Generating Sentences from a Continuous Space](https://arxiv.org/pdf/1511.06349.pdf). In diesem Paper trainierten sie einen Variational Autoencoder auf Text, was zur Fähigkeit führte, zwischen zwei Sätzen zu interpolieren und kohärente Ergebnisse zu erhalten.

![Beispiele für Satzinterpolation aus einem Variational Autoencoder](./sentence-interpolation-samples.webp)

### Anforderungen an eine NLP-Architektur

Was alle Implementierungen, die wir uns angesehen haben, gemeinsam haben, ist, dass sie eine rekurrente Architektur verwenden, normalerweise ein LSTM (Falls du nicht sicher bist, was das ist: [hier](http://karpathy.github.io/2015/05/21/rnn-effectiveness/) ist eine großartige Einführung). Bemerkenswert ist, dass keine der Aufgaben „rekurrent“ im Namen hatte und keine LSTMs erwähnte. Vor diesem Hintergrund lass uns einen Moment darüber nachdenken, was RNNs und insbesondere LSTMs liefern, das sie so allgegenwärtig im NLP macht.

#### Beliebige Eingabegröße

Ein Standard-Feedforward-Neuronales-Netzwerk hat einen Parameter für jede Eingabe. Das wird problematisch, wenn man mit Text oder Bildern arbeitet, aus ein paar Gründen.

1. Es schränkt die Eingabegröße ein, die wir handhaben können. Unser Netzwerk wird eine endliche Anzahl an Eingabeknoten haben und nicht darüber hinaus wachsen können.
2. Wir verlieren eine Menge gemeinsamer Information. Betrachte die Sätze „I like to drink beer a lot“ und „I like to drink a lot of beer“. Ein Feedforward-Netzwerk müsste das Konzept von „a lot“ zweimal lernen, da es jedes Mal in unterschiedlichen Eingabeknoten erscheint.

Rekurrente neuronale Netzwerke lösen dieses Problem. Statt einen Knoten pro Eingabe zu haben, haben wir eine große „Box“ von Knoten, die wir immer wieder auf die Eingabe anwenden. Die „Box“ lernt eine Art Übergangsfunktion, was bedeutet, dass die Ausgaben einer Rekurrenzrelation folgen, daher der Name.

Erinnere dich daran, dass die _Vision-Leute_ einen sehr ähnlichen Effekt für Bilder mit Convolutions bekommen haben. Das heißt: Statt einen Eingabeknoten pro Pixel zu haben, erlaubten Convolutions die Wiederverwendung desselben kleinen Parametersatzes über das gesamte Bild.

#### Langzeitabhängigkeiten

Das Versprechen von RNNs ist ihre Fähigkeit, Langzeitabhängigkeiten implizit zu modellieren. Das Bild unten stammt von OpenAI. Sie trainierten ein Modell, das am Ende Sentiment erkannte, und färbten den Text Zeichen für Zeichen mit der Ausgabe des Modells ein. Beachte, wie das Modell das Wort „best“ sieht und ein positives Sentiment auslöst, das es über mehr als 100 Zeichen mit sich trägt. Das ist das Erfassen einer weitreichenden Abhängigkeit.

![Heatmap der Aktivierung eines Sentiment-Neurons über Review-Text](./sentiment-heatmap.webp)

Die Theorie der RNNs verspricht uns Langzeitabhängigkeiten out of the box. In der Praxis ist es etwas schwieriger. Wenn wir via Backpropagation lernen, müssen wir das Signal durch die gesamte Rekurrenzrelation propagieren. Das Ding ist: Bei jedem Schritt multiplizieren wir am Ende mit einer Zahl. Wenn diese Zahlen im Allgemeinen kleiner als 1 sind, geht unser Signal schnell gegen 0. Wenn sie größer als 1 sind, explodiert unser Signal.

Diese Probleme nennt man Vanishing und Exploding Gradient und sie werden im Allgemeinen durch LSTMs und ein paar clevere Tricks gelöst. Ich erwähne sie jetzt, weil wir diesen Problemen mit Convolutions wieder begegnen werden und einen anderen Weg brauchen, sie zu adressieren.

### Vorteile von Convolutions

Bisher haben wir gesehen, wie großartig LSTMs sind, aber dieser Post handelt von Convolutions. Im Sinne von _don’t fix what ain’t broken_ müssen wir uns fragen, warum wir überhaupt Convolutions verwenden wollen würden.

Eine Antwort ist: „Weil wir es können“.

Aber es gibt zwei andere überzeugende Gründe, Convolutions zu verwenden: Geschwindigkeit und Kontext.

#### Parallelisierung

RNNs arbeiten sequenziell: Die Ausgabe für die zweite Eingabe hängt von der ersten ab, und so können wir ein RNN nicht parallelisieren. Convolutions haben dieses Problem nicht; jeder „Patch“, auf dem ein Convolutional Kernel arbeitet, ist unabhängig von den anderen, was bedeutet, dass wir über die gesamte Eingabeschicht gleichzeitig gehen können.

Dafür gibt es einen Preis: Wie wir sehen werden, müssen wir Convolutions zu tiefen Schichten stapeln, um die gesamte Eingabe zu sehen, und jede dieser Schichten wird sequenziell berechnet. Aber die Berechnungen in jeder Schicht passieren gleichzeitig und jede einzelne Berechnung ist klein (im Vergleich zu einem LSTM), sodass wir in der Praxis eine große Beschleunigung bekommen.

Als ich anfing, das zu schreiben, hatte ich nur meine eigene Erfahrung und Googles ByteNet, um diese Behauptung zu stützen. Gerade diese Woche hat Facebook ihr vollständig convolutionales Übersetzungsmodell veröffentlicht und eine 9-fache Beschleunigung gegenüber LSTM-basierten Modellen berichtet.

#### Die gesamte Eingabe auf einmal sehen

LSTMs lesen ihre Eingabe von links nach rechts (oder von rechts nach links), aber manchmal möchten wir, dass der Kontext vom Ende des Satzes die Gedanken des Netzwerks über den Anfang beeinflusst. Zum Beispiel könnten wir einen Satz haben wie „I’d love to buy your product. Not!“ und wir möchten, dass diese Negation am Ende den gesamten Satz beeinflusst.

Mit LSTMs erreichen wir das, indem wir zwei LSTMs laufen lassen: eines von links nach rechts und das andere von rechts nach links, und ihre Ausgaben konkatenieren. Das funktioniert in der Praxis gut, verdoppelt aber unsere Rechenlast.

Convolutions dagegen bekommen ein größeres „rezeptives Feld“, wenn wir mehr und mehr Schichten stapeln. Das bedeutet, dass standardmäßig jeder „Schritt“ in der Darstellung der Convolution die gesamte Eingabe in seinem rezeptiven Feld sieht, von davor und danach. Mir ist kein definitives Argument bekannt, dass dies inhärent besser ist als ein LSTM, aber es gibt uns den gewünschten Effekt auf kontrollierbare Weise und mit geringer Rechenkosten.

Bisher haben wir unser Problemfeld abgesteckt und ein wenig über die konzeptuellen Vorteile von Convolutions für NLP gesprochen. Ab hier möchte ich diese Konzepte in praktische Methoden übersetzen, die wir verwenden können, um unsere Netzwerke zu analysieren und zu konstruieren.

### Praktische Convolutions für Text

![Animierte Visualisierung eines Convolutional Kernels, der über ein Bild gleitet](./convolution-animation.webp)

Du hast wahrscheinlich eine Animation wie die oben gesehen, die illustriert, was eine Convolution macht. Unten ist ein Eingabebild, oben ist das Ergebnis, und der graue Schatten ist der Convolutional Kernel, der wiederholt angewendet wird.

Das ergibt alles perfekt Sinn, außer dass die in dem Bild beschriebene Eingabe ein Bild ist, mit zwei räumlichen Dimensionen (Höhe und Breite). Wir sprechen über Text, der nur eine Dimension hat, und die ist temporal, nicht räumlich.

Für alle praktischen Zwecke macht das keinen Unterschied. Wir müssen nur an unseren Text als ein Bild mit Breite _n_ und Höhe 1 denken. Tensorflow bietet dafür eine conv1d-Funktion, aber sie stellt andere convolutionale Operationen nicht in ihrer 1d-Version bereit.

Um die Idee „Text = ein Bild der Höhe 1“ konkret zu machen, schauen wir uns an, wie wir den 2d-Convolution-Op in Tensorflow auf eine Sequenz eingebetteter Tokens anwenden würden.

Was wir hier tun, ist die Form der Eingabe mit tf.expand\_dims zu ändern, sodass sie zu einem „Bild der Höhe 1“ wird. Nachdem wir den 2d-Convolution-Operator ausgeführt haben, drücken wir die zusätzliche Dimension wieder weg.

### Hierarchie und rezeptive Felder

![Hierarchie von CNN-Filtern, die von Kanten zu Gesichtern fortschreitet](./cnn-receptive-hierarchy.webp)

Viele von uns haben Bilder wie das oben gesehen. Es zeigt grob die Hierarchie von Abstraktionen, die ein CNN auf Bildern lernt. In der ersten Schicht lernt das Netzwerk grundlegende Kanten. In der nächsten Schicht kombiniert es diese Kanten, um abstraktere Konzepte wie Augen und Nasen zu lernen. Schließlich kombiniert es diese, um einzelne Gesichter zu erkennen.

Mit Blick darauf müssen wir uns daran erinnern, dass jede Schicht nicht nur abstraktere Kombinationen der vorherigen Schicht lernt. Aufeinanderfolgende Schichten sehen, implizit oder explizit, mehr von der Eingabe.

![Baum des rezeptiven Feldes, der schichtweise Aggregation über Eingaben zeigt](./hierarchical-receptive-field-tree.webp)

#### Rezeptives Feld vergrößern

Bei Vision wollen wir oft, dass das Netzwerk ein oder mehrere Objekte im Bild identifiziert und andere ignoriert. Das heißt, wir interessieren uns für ein lokales Phänomen, aber nicht für eine Beziehung, die sich über die gesamte Eingabe erstreckt.

![Hotdog-Klassifikations-App, die Hotdog- und Schuh-Fotos vergleicht](./hotdog-classifier-example.webp)

Text ist subtiler, da wir oft wollen, dass Zwischenrepräsentationen unserer Daten so viel Kontext über ihre Umgebung wie möglich tragen. Mit anderen Worten: Wir wollen ein möglichst großes rezeptives Feld haben. Es gibt ein paar Wege, das zu erreichen.

#### Größere Filter

Der erste, offensichtlichste Weg ist, die Filtergröße zu erhöhen, also eine \[1x5\]-Convolution statt einer \[1x3\]. In meiner Arbeit mit Text habe ich damit keine großartigen Ergebnisse erzielt, und ich werde meine Spekulationen dazu anbieten, warum.

In meinem Bereich arbeite ich meist mit Eingaben auf Zeichenebene und mit Texten, die morphologisch sehr reich sind. Ich denke an (zumindest die ersten) Convolution-Schichten als das Lernen von n-Grammen, sodass die Breite des Filters Bigrams, Trigrams usw. entspricht. Wenn das Netzwerk früh größere n-Gramme lernt, sieht es weniger Beispiele, da es in einem Text mehr Vorkommen von „ab“ als von „abb“ gibt.

Ich habe diese Interpretation nie bewiesen, aber ich habe konsistent schlechtere Ergebnisse mit Filterbreiten größer als 3 bekommen.

#### Schichten hinzufügen

Wie wir im Bild oben gesehen haben, erhöht das Hinzufügen weiterer Schichten das rezeptive Feld. [Dang Ha The Hien](https://medium.com/u/b04dc6044cc) schrieb einen [großartigen Guide](https://medium.com/@nikasa1889/a-guide-to-receptive-field-arithmetic-for-convolutional-neural-networks-e0f514068807) zur Berechnung des rezeptiven Feldes in jeder Schicht, den ich dir empfehle zu lesen.

Schichten hinzuzufügen hat zwei unterschiedliche, aber zusammenhängende Effekte. Der eine, der oft herumgeworfen wird, ist, dass das Modell lernt, höherstufige Abstraktionen über die Eingaben zu bilden, die es bekommt (Pixels =>Edges => Eyes => Face). Der andere ist, dass das rezeptive Feld bei jedem Schritt wächst.

Das bedeutet, dass unser Netzwerk bei genügend Tiefe die gesamte Eingabeschicht betrachten könnte, wenn auch vielleicht durch einen Schleier von Abstraktionen. Leider kann hier das Vanishing-Gradient-Problem sein hässliches Haupt erheben.

#### Der Gradient-/Rezeptives-Feld-Trade-off

Neuronale Netze sind Netze, durch die Information fließt. Im Forward Pass fließt unsere Eingabe und transformiert sich, hoffentlich zu einer Repräsentation werdend, die besser zu unserer Aufgabe passt. Während der Back Phase propagieren wir ein Signal, den Gradienten, zurück durch das Netzwerk. Genau wie in Vanilla-RNNs wird dieses Signal häufig multipliziert, und wenn es durch eine Reihe von Zahlen geht, die kleiner als 1 sind, dann wird es gegen 0 verblassen. Das bedeutet, dass unser Netzwerk am Ende sehr wenig Signal hat, aus dem es lernen kann.

Damit bleiben wir mit einem gewissen Trade-off zurück. Einerseits möchten wir so viel Kontext wie möglich aufnehmen können. Andererseits riskieren wir, wenn wir versuchen, unsere rezeptiven Felder durch das Stapeln von Schichten zu vergrößern, verschwindende Gradienten und ein Scheitern daran, überhaupt etwas zu lernen.

### Zwei Lösungen für das Vanishing-Gradient-Problem

Glücklicherweise haben viele kluge Menschen über diese Probleme nachgedacht. Noch glücklicher: Das sind keine Probleme, die einzigartig für Text sind; auch die _Vision-Leute_ wollen größere rezeptive Felder und gradientenreiche Signale. Schauen wir uns ein paar ihrer verrückten Ideen an und nutzen sie, um unseren eigenen textuellen Ruhm zu mehren.

#### Residual Connections

2016 war ein weiteres großartiges Jahr für die _Vision-Leute_, mit mindestens zwei sehr populären Architekturen, die entstanden sind: [ResNets](https://arxiv.org/abs/1512.03385) und [DenseNets](https://arxiv.org/abs/1608.06993) (Das DenseNet-Paper ist insbesondere außergewöhnlich gut geschrieben und sehr lesenswert). Beide adressieren dasselbe Problem: „Wie mache ich mein Netzwerk sehr tief, ohne das Gradientensignal zu verlieren?“

[Arthur Juliani](https://medium.com/u/18dfe63fa7f0) schrieb eine fantastische Übersicht über [Resnet, DenseNets und Highway Networks](https://chatbotslife.com/resnets-highwaynets-and-densenets-oh-my-9bb15918ee32) für diejenigen unter euch, die Details und Vergleiche suchen. Ich werde kurz DenseNets anreißen, die das Kernkonzept ins Extrem treiben.

![DenseNet-Block mit dicht verbundenen Convolution-Schichten](./densenet-connections.webp)

Die allgemeine Idee ist, die Distanz zwischen dem Signal, das vom Loss des Netzwerks kommt, und jeder einzelnen Schicht zu reduzieren. Das wird erreicht, indem eine Residual-/Direktverbindung zwischen jeder Schicht und ihren Vorgängern hinzugefügt wird. Dadurch kann der Gradient von jeder Schicht direkt zu ihren Vorgängern fließen.

DenseNets machen das auf eine besonders interessante Weise. Sie konkatenieren die Ausgabe jeder Schicht mit ihrer Eingabe, sodass:

1. Wir beginnen mit einem Embedding unserer Eingaben, sagen wir der Dimension 10.
2. Unsere erste Schicht berechnet 10 Feature Maps. Sie gibt die 10 Feature Maps aus, konkateniert mit dem ursprünglichen Embedding.
3. Die zweite Schicht bekommt als Eingabe 20-dimensionale Vektoren (10 aus der Eingabe und 10 aus der vorherigen Schicht) und berechnet weitere 10 Feature Maps. Somit gibt sie 30-dimensionale Vektoren aus.

Und so weiter und so weiter, für so viele Schichten, wie du möchtest. Das Paper beschreibt eine Menge Tricks, um Dinge handhabbar und effizient zu machen, aber das ist die grundlegende Prämisse, und das Vanishing-Gradient-Problem ist gelöst.

Es gibt zwei weitere Dinge, die ich hervorheben möchte.

1. Ich erwähnte zuvor, dass obere Schichten eine Sicht auf die ursprüngliche Eingabe haben können, die durch Schichten von Abstraktionen vernebelt ist. Einer der Highlights des Konkatenierens der Ausgaben jeder Schicht ist, dass das ursprüngliche Signal die folgenden Schichten intakt erreicht, sodass alle Schichten eine direkte Sicht auf niedrigstufige Features haben, was im Wesentlichen einen Teil dieses Nebels entfernt.
2. Der Residual-Connection-Trick erfordert, dass alle unsere Schichten dieselbe Form haben. Das bedeutet, dass wir jede Schicht so padden müssen, dass ihre Eingabe- und Ausgabedimensionen im Raum gleich sind \[1Xwidth\]. Das bedeutet, dass diese Art Architektur für sich genommen für Sequence-Labeling-Aufgaben funktioniert (bei denen Eingabe und Ausgabe dieselben räumlichen Dimensionen haben), aber mehr Arbeit für Encoding- und Klassifikationsaufgaben benötigt (bei denen wir die Eingabe auf einen Vektor fester Größe oder ein Set von Vektoren reduzieren müssen). Das DenseNet-Paper behandelt das tatsächlich, da ihr Ziel Klassifikation ist, und wir werden diesen Punkt später weiter ausführen.

#### Dilatierte Convolutions

Dilatierte Convolutions aka _atrous_ Convolutions aka Convolutions mit Löchern sind eine weitere Methode, das rezeptive Feld zu vergrößern, ohne die Gradientengötter zu verärgern. Als wir uns bisher das Stapeln von Schichten angesehen haben, sahen wir, dass das rezeptive Feld linear mit der Tiefe wächst. Dilatierte Convolutions lassen uns das rezeptive Feld exponentiell mit der Tiefe wachsen.

Du findest eine fast zugängliche Erklärung von dilatierten Convolutions im Paper [Multi scale context aggregation by dilated convolutions](https://arxiv.org/pdf/1511.07122.pdf), das sie für Vision nutzt. Obwohl konzeptionell einfach, hat es eine Weile gedauert, bis ich genau verstand, was sie tun, und ich könnte es immer noch nicht ganz richtig verstanden haben.

Die Grundidee ist, „Löcher“ in jeden Filter einzuführen, sodass er nicht auf benachbarten Teilen der Eingabe arbeitet, sondern sie überspringt zu weiter entfernten Teilen. Beachte, dass das anders ist als eine Convolution mit Stride > 1 anzuwenden. Wenn wir einen Filter striden, überspringen wir Teile der Eingabe zwischen Anwendungen der Convolution. Bei dilatierten Convolutions überspringen wir Teile der Eingabe innerhalb einer einzelnen Anwendung der Convolution. Indem wir clever wachsende Dilatationen anordnen, können wir das versprochene exponentielle Wachstum der rezeptiven Felder erreichen.

Wir haben bisher viel Theorie besprochen, aber wir sind endlich an einem Punkt, an dem wir dieses Zeug in Aktion sehen können!

Ein persönliches Lieblingspaper ist [Neural Machine Translation in Linear Time](https://arxiv.org/pdf/1610.10099.pdf). Es folgt der Encoder-Decoder-Struktur, über die wir am Anfang gesprochen haben. Wir haben noch nicht alle Werkzeuge, um über den Decoder zu sprechen, aber wir können den Encoder in Aktion sehen.

![Encoder mit dilatierten Convolutions und expandierenden rezeptiven Feldern über eine Sequenz](./dilated-convolution-receptive-field.webp)

Und hier ist eine englische Eingabe

> Director Jon Favreau, who is currently working on Disney’s forthcoming Jungle Book film, told the website Hollywood Reporter: “I think times are changing.”

Und ihre Übersetzung, präsentiert von dilatierten Convolutions

> Regisseur Jon Favreau, der zur Zeit an Disneys kommendem Jungle Book Film arbeitet, hat der Website Hollywood Reporter gesagt: “Ich denke, die Zeiten andern sich”.

Und als Bonus: Denk daran, dass Sound genau wie Text ist, in dem Sinne, dass er nur eine räumliche/temporale Dimension hat. Schau dir DeepMinds [Wavenet](https://deepmind.com/blog/wavenet-generative-model-raw-audio/) an, das dilatierte Convolutions (und eine Menge anderer Magie) nutzt, um [menschlich klingende Sprache](https://storage.googleapis.com/deepmind-media/pixie/knowing-what-to-say/second-list/speaker-1.wav) und [Klaviermusik](https://storage.googleapis.com/deepmind-media/pixie/making-music/sample_4.wav) zu generieren.

### Etwas aus deinem Netzwerk herausbekommen

Als wir DenseNets besprochen haben, erwähnte ich, dass der Einsatz von Residual Connections uns dazu zwingt, Eingabe- und Ausgabelänge unserer Sequenz gleich zu halten, was durch Padding erreicht wird. Das ist großartig für Aufgaben, bei denen wir jedes Element in unserer Sequenz labeln müssen, zum Beispiel:

* Beim Part-of-Speech-Tagging, wo jedes Wort eine Wortart ist.
* Bei Entity Recognition, wo wir Person, Company und Other für alles andere labeln könnten

Andere Male möchten wir unsere Eingabesequenz auf eine Vektorrepräsentation reduzieren und diese nutzen, um etwas über den gesamten Satz vorherzusagen.

* Wir könnten eine E-Mail als Spam labeln basierend auf ihrem Inhalt und/oder Betreff
* Vorhersagen, ob ein bestimmter Satz sarkastisch ist oder nicht

In diesen Fällen können wir den traditionellen Ansätzen der _Vision-Leute_ folgen und unser Netzwerk mit Convolution-Schichten abschließen, die kein Padding haben, und/oder Pooling-Operationen verwenden.

Aber manchmal wollen wir dem Seq2Seq-Paradigma folgen, was [Matthew Honnibal](https://medium.com/u/42936aed59d2) prägnant [_Embed, encode, attend, predict_](https://explosion.ai/blog/deep-learning-formula-nlp)_._ genannt hat. In diesem Fall reduzieren wir unsere Eingabe auf eine Vektorrepräsentation, müssen diesen Vektor aber irgendwie wieder zu einer Sequenz der richtigen Länge hochsampeln.

Diese Aufgabe bringt zwei Probleme mit sich

* Wie machen wir Upsampling mit Convolutions?
* Wie machen wir genau die richtige Menge an Upsampling?

Ich habe die Antwort auf die zweite Frage noch nicht gefunden oder zumindest noch nicht verstanden. In der Praxis hat es mir genügt, irgendeine obere Schranke für die maximale Länge der Ausgabe anzunehmen und dann bis zu diesem Punkt hochzusampeln. Ich vermute, Facebooks neues [Translation-Paper](https://s3.amazonaws.com/fairseq/papers/convolutional-sequence-to-sequence-learning.pdf) adressiert das, aber ich habe es noch nicht tief genug gelesen, um es zu kommentieren.

#### Upsampling mit Deconvolutions

Deconvolutions sind unser Werkzeug für Upsampling. Am einfachsten (für mich) ist zu verstehen, was sie tun, durch Visualisierungen. Glücklicherweise haben ein paar kluge Leute einen [großartigen Post über Deconvolutions](http://distill.pub/2016/deconv-checkerboard/) bei Distill veröffentlicht und ein paar spaßige Visualizer eingebaut. Lass uns damit anfangen.

![Diagramm einer gestrideten Convolution, das zeigt, wie der Kernel Eingaben abdeckt](./strided-convolution-diagram.webp)

Betrachte das Bild oben. Wenn wir die untere Schicht als Eingabe nehmen, haben wir eine Standard-Convolution mit Stride 1 und Breite 3. _Aber,_ wir können auch von oben nach unten gehen, also die obere Schicht als Eingabe behandeln und die etwas größere untere Schicht erhalten.

Wenn du darüber eine Sekunde nachdenkst: Diese „Top-down“-Operation passiert bereits in deinen Convolutional Networks, wenn du Backpropagation machst, da die Gradientensignale genau so propagieren müssen, wie im Bild gezeigt. Noch besser: Es stellt sich heraus, dass diese Operation einfach die Transponierte der Convolution-Operation ist, daher der andere verbreitete (und technisch korrekte) Name für diese Operation: Transposed Convolution.

Jetzt wird’s spannend. Wir können unsere Convolutions striden, um unsere Eingabe zu verkleinern. Also können wir unsere Deconvolutions striden, um unsere Eingabe zu vergrößern. Ich denke, der einfachste Weg zu verstehen, wie Strides mit Deconvolutions funktionieren, ist, sich die folgenden Bilder anzusehen.

![Diagramm einer gestrideten Convolution, das zeigt, wie der Kernel Eingaben abdeckt](./strided-convolution-diagram.webp)
![Transposed Convolution mit überlappender Abdeckung der Ausgaben](./transposed-convolution-overlap.webp)

Das obere haben wir schon gesehen. Beachte, dass jede Eingabe (die obere Schicht) drei der Ausgaben speist und jede der Ausgaben von drei Eingaben gespeist wird (außer an den Rändern).

![Abstand einer dilatierten Convolution mit Lücken, die das rezeptive Feld erweitern](./dilated-convolution-spacing.webp)

Im zweiten Bild platzieren wir imaginäre Löcher in unseren Eingaben. Beachte, dass nun jede Ausgabe von höchstens zwei Eingaben gespeist wird.

![Transposed Convolution, die eine Sequenzlänge hochskaliert](./transposed-convolution-upscaling.webp)

Im dritten Bild haben wir zwei imaginäre Löcher in unsere Eingabeschicht eingefügt, und so wird jede Ausgabe von genau einer Eingabe gespeist. Das verdreifacht am Ende die Sequenzlänge unserer Ausgabe im Verhältnis zur Sequenzlänge unserer Eingabe.

Schließlich können wir mehrere Deconvolution-Schichten stapeln, um unsere Ausgabeschicht schrittweise auf die gewünschte Größe anwachsen zu lassen.

Ein paar Dinge, über die es sich lohnt nachzudenken

1. Wenn du diese Zeichnungen von unten nach oben betrachtest, sind es am Ende Standard-Strided-Convolutions, bei denen wir einfach imaginäre Löcher in den Ausgabeschichten hinzugefügt haben (die weißen Blöcke)
2. In der Praxis ist jede „Eingabe“ keine einzelne Zahl, sondern ein Vektor. In der Bildwelt könnte das ein 3-dimensionaler RGB-Wert sein. In Text könnte es ein 300-dimensionales Word Embedding sein. Wenn du in der Mitte deines Netzwerks (de)convolvierst, wäre jeder Punkt ein Vektor in der Größe, die aus der letzten Schicht herauskam.
3. Ich erwähne das, um dich davon zu überzeugen, dass genug Information in der Eingabeschicht einer Deconvolution steckt, um sich über ein paar Punkte in der Ausgabe zu verteilen.
4. In der Praxis hatte ich Erfolg damit, nach einer Deconvolution ein paar Convolutions mit längenerhaltendem Padding auszuführen. Ich stelle mir vor (habe es aber nicht bewiesen), dass das wie eine Umverteilung von Information wirkt. Ich denke daran wie daran, ein Steak nach dem Grillen ruhen zu lassen, damit sich die Säfte neu verteilen.

![Vergleich von Steak ohne Ruhezeit versus mit Ruhezeit, um Umverteilung von Information zu veranschaulichen](./steak-resting-comparison.webp)

### Zusammenfassung

Der Hauptgrund, warum du Convolutions in deiner Arbeit in Betracht ziehen solltest, ist, dass sie schnell sind. Ich denke, das ist wichtig, um Forschung und Exploration schneller und effizienter zu machen. Schnellere Netzwerke verkürzen unsere Feedback-Zyklen.

Die meisten Aufgaben, denen ich mit Text begegnet bin, haben am Ende dieselbe Anforderung an die Architektur: das rezeptive Feld zu maximieren, während ein ausreichender Fluss von Gradienten erhalten bleibt. Wir haben den Einsatz sowohl von DenseNets als auch von dilatierten Convolutions gesehen, um das zu erreichen.

Schließlich wollen wir manchmal eine Sequenz oder einen Vektor zu einer größeren Sequenz erweitern. Wir haben Deconvolutions als eine Methode betrachtet, um „Upsampling“ auf Text zu machen, und als Bonus das Hinzufügen einer Convolution danach mit dem Ruhenlassen eines Steaks verglichen, damit es seine Säfte neu verteilt.

Ich würde gerne mehr über deine Gedanken und Erfahrungen mit diesen Arten von Modellen erfahren. Teile sie in den Kommentaren oder ping mich auf Twitter [@thetalperry](https://twitter.com/thetalperry)
