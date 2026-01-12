+++
title = 'Fünf praktische Lektionen für das Serving von Modellen mit Triton Inference Server'
date = 2025-12-15T10:00:00+02:00
draft = false
tags = ['machine-learning', 'mlops', 'inference', 'triton']
+++

Triton Inference Server ist zu einer beliebten Wahl für das produktive Serving von Modellen geworden – und das aus gutem Grund: Er ist schnell, flexibel und leistungsstark. Trotzdem erfordert der effektive Einsatz von Triton ein Verständnis dafür, wo er glänzt – und wo er ganz klar nicht glänzt. Dieser Beitrag sammelt fünf praktische Lektionen aus dem Betrieb von Triton in Production, die ich mir früher gewünscht hätte verinnerlicht zu haben.

## Die richtige Serving-Schicht wählen

Nicht alle Modelle gehören auf Triton. **Nutze vLLM für generative Modelle; nutze Triton für eher traditionelle Inferenz-Workloads.**

LLMs sind gerade überall, und Triton bietet Integrationen sowohl mit TensorRT-LLM als auch mit vLLM. Auf den ersten Blick lässt Triton dadurch wie ein One-Stop-Shop wirken, um alles zu serven – von Bildklassifikatoren bis hin zu Large Language Models.

In der Praxis habe ich festgestellt, dass Triton im Vergleich zu einem „rohen“ vLLM-Deployment nur sehr wenig zusätzlichen Nutzen bringt. Das ist kein Vorwurf an Triton – es ist ein Spiegelbild dessen, wie unterschiedlich generative Workloads im Vergleich zur klassischen Inferenz sind. Viele von Tritons besten Features lassen sich schlicht nicht sauber auf die Art abbilden, wie LLMs serviert werden.

Ein paar konkrete Beispiele machen das deutlich:

- **Dynamisches Batching → Kontinuierliches Batching**
  Tritons dynamischer Batcher wartet kurz, um ganze Requests zu gruppieren, und führt sie dann gemeinsam aus. Das funktioniert extrem gut für Inferenz mit fester Shape. LLM-Serving hingegen profitiert von kontinuierlichem Batching, bei dem neue Requests in einen aktiven Batch eingefügt werden, während andere mit dem Generieren von Tokens fertig werden. Zwar ist das technisch über Tritons vLLM-Backend möglich, aber es ist weder einfach noch naheliegend zu betreiben.

{{< img src="dynamic-vs-continuous-batching.png" alt="Dynamisches Batching vs kontinuierliches Batching" class="article-image" resize="1200x" >}}

- **Model Packing → Model Sharding**
  Triton macht es leicht, mehrere Modelle auf einer einzelnen GPU zu packen, um die Auslastung zu verbessern. LLMs passen selten in dieses Modell. Selbst eher moderate Modelle belegen oft eine ganze GPU, und größere erfordern Sharding über GPUs oder sogar Nodes hinweg. Triton verhindert das nicht, aber es hilft dabei auch nicht in nennenswertem Maße.

{{< img src="model-sharding-vs-packing.png" alt="Model Sharding vs Model Packing" class="article-image" resize="1200x" >}}

- **Request-Caching → Prefix-Caching**
  Tritons eingebauter Cache funktioniert, indem er Request–Response-Paare speichert, was für deterministische Workloads sehr effektiv ist. Generative Modelle profitieren stattdessen vom Caching von Zwischenzustand, etwa KV-Caches, die über gemeinsame Prompt-Präfixe indiziert sind. Das ist ein grundsätzlich anderes Problem – und eines, das LLM-native Serving-Systeme deutlich natürlicher lösen.

Kurz gesagt: Ich habe es durchgehend als deutlich einfacher empfunden, vLLM direkt zu deployen und sofort von kontinuierlichem Batching, Sharding und Prefix-Caching zu profitieren, als Triton darüber zu legen und mich mit Konfiguration herumzuschlagen, um ein ähnliches Verhalten zu erreichen.

## Latenz mit serverseitigen Timeouts schützen

Dynamisches Batching ist Tritons Killer-Feature. Indem Requests für ein kurzes, konfigurierbares Zeitfenster gepuffert und dann im Batch ausgeführt werden, verbessert Triton die Hardware-Auslastung und eliminiert eine große Menge clientseitiger Komplexität.

Es gibt jedoch eine wichtige Stolperfalle: Standardmäßig wird Triton keine Requests aus der Warteschlange verwerfen.

Unter Last ist es durchaus möglich, dass Triton einen Rückstau aufbaut, während Clients timeouten und weiterziehen. Wenn `max_queue_delay_microseconds` nicht konfiguriert ist, können diese aufgegebenen Requests in der Queue liegen bleiben und später doch ausgeführt werden, wodurch Ressourcen verbraucht werden, während neuere Requests auf ihre Reihe warten.

Das Ergebnis ist pervers, aber häufig:

- Triton verbringt Zeit damit, Requests zu verarbeiten, die der Client bereits aufgegeben hat.
- Die Latenz steigt, während die Queue veraltete Arbeit abarbeitet.

Dieses Problem ist besonders ausgeprägt beim Python-Backend. Während einige native Backends Client-Abbrüche erkennen können, überlässt das Python-Backend diese Verantwortung weitgehend dem User-Code. Sobald ein Request deine `execute()`-Methode erreicht, läuft er in der Regel bis zum Ende, sofern du nicht explizit auf Cancellation prüfst.

Wenn dir Latenz wichtig ist – und das ist sie mit an Sicherheit grenzender Wahrscheinlichkeit – sind serverseitige Queue-Timeouts nicht optional.

## Client-Bibliotheken minimal halten

Triton erfordert, dass Clients Modelnamen, Tensor-Namen, Shapes und Datentypen kennen. Das direkt an Application-Entwickler:innen weiterzugeben ist unangenehm, daher lohnt sich ein kleiner Client-Wrapper in der Regel.

Problematisch wird es, wenn dieser Wrapper Ambitionen entwickelt.

Ich habe (und gebaut) Client-Bibliotheken gesehen, die hilfreich sein wollen, indem sie Retries, Backoff oder andere Resilience-Features hinzufügen. In der Praxis geht das oft nach hinten los. Requests erneut zu senden, die wegen Overload oder ungültiger Inputs fehlgeschlagen sind, kann den Traffic genau dann verstärken, wenn das System ohnehin schon kämpft – und aus einer vorübergehenden Verlangsamung ein selbstverschuldetes Denial-of-Service machen.

Das heißt nicht, dass man keine Retries verwenden sollte, sondern dass man sie nicht unsichtbar machen sollte – und dass Callers identifizieren können sollten und identifizierbar sein sollten, wenn Retry-Logik überarbeitet werden muss.

Meine Empfehlung ist einfach: Halte Client-Bibliotheken langweilig. Lass sie die Request-Konstruktion erledigen und sonst nichts. Implementiere Retries und Error-Handling am Call-Site, wo die Anwendung den nötigen Kontext und die Observability hat, um das Richtige zu tun.

## Tritons eingebauten Cache nutzen

Tritons Request–Response-Cache ist leicht zu übersehen, kann aber überraschend effektiv sein – besonders in Cloud-Umgebungen. GPU-Instanzen bringen oft deutlich mehr Systemspeicher mit, als sonst genutzt wird, und ein paar zusätzliche Gigabytes fürs Caching können deiner GPU eine beträchtliche Menge redundanter Arbeit ersparen.

Das ist keine pauschale Empfehlung – viele Workloads werden nicht profitieren –, aber es lohnt sich zu experimentieren. Cache-Hit-Rates zusammen mit Queue-Depth zu beobachten, kann dir schnell zeigen, ob Caching hilft und ob ein bestimmter Client unnötigen, doppelten Traffic erzeugt.

## ThreadPoolExecutor für clientseitige Parallelität bevorzugen

Auf der Client-Seite habe ich festgestellt, dass der einfachste Weg, parallele Inferenz-Requests abzusetzen, auch der beste ist: Verwende einen Thread-Pool.

In CPython gibt Socket-I/O den GIL frei. Da Tritons HTTP-Client primär I/O-bound ist, ist `ThreadPoolExecutor` damit eine effektive und unkomplizierte Wahl:

```python
def infer(inputs):
    return model_client.infer(inputs=inputs)

with ThreadPoolExecutor(max_workers=8) as pool:
    results = list(pool.map(infer, batch_of_requests))
```

Dieser Ansatz hat ein paar schöne Eigenschaften:

1. Der Client muss keine Batching-Logik implementieren.
2. Tritons dynamischer Batcher kann Requests über Threads hinweg und sogar über Clients hinweg aggregieren.
3. Nebenläufigkeit ist natürlich begrenzt und liefert damit eine Form von Backpressure.

Jegliche Python-Arbeit innerhalb von `infer` bleibt serialisiert, was sich als Feature statt Bug herausstellt: Es verhindert, dass der Client den Server überrollt, während effizientes paralleles I/O weiterhin möglich bleibt.

## Fazit

Triton ist ein mächtiges Serving-System, aber es ist auch meinungsstark. Es funktioniert am besten, wenn seine Abstraktionen zu dem Workload passen, den du serven willst.

Für klassische Inferenz-Workloads sind Tritons Batching, Scheduling und Caching schwer zu schlagen. Für LLMs und andere generative Modelle passen speziell dafür gebaute Systeme wie vLLM oft besser. Diese Unterscheidung zu verstehen – und Triton defensiv zu konfigurieren, wenn du es einsetzt – hilft erheblich dabei, zuverlässige Inferenzsysteme mit niedriger Latenz zu bauen.
