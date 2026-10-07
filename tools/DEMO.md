# Demonstracja: tools/summarize.py na artykule Wikipedii „Machine learning”
*Wygenerowano: 2026-10-07 · narzędzie 100% oparte na Jimmym (llama3.1-8B @ chatjimmy.ai)*

## Źródło i metoda
- **Źródło:** Wikipedia EN „Machine learning”, pobrane jako PDF (REST API) → `pdftotext`.
- **Rozmiar surowy (PDF→tekst):** 16,864 słów. Po odcięciu przypisów/bibliografii/linków: **9,661 słów treści** (~12,5k tokenów) — to wejście podawane narzędziu.
- **Konfiguracja wspólna:** `--chunk-words 2400 --reduce-words 100000 --batch-size 100 --top-k 1 --cache` → 5 chunków → 5 notatek *map* (policzone RAZ, współdzielone przez wszystkie demo) → jeden finalny *reduce*.
- **Współczynnik redukcji** = 9,661 słów ÷ (słowa streszczenia).

> ⚙️ **Uwaga techniczna (uczciwie):** przy domyślnym `--chunk-words 300` hierarchiczny *reduce* **nie zbiega** na tym dokumencie — partie N→N w nieskończoność (bug niezbieżności: `REDUCE_MID` nie kompresuje własnego wejścia). Zadziałał reżim „mało dużych chunków + jeden finalny reduce”, gdzie suma notatek mieści się pod sufitem kontekstu ~6k tokenów. To realne ograniczenie alfa-narzędzia.

## Tabela zbiorcza
| # | Tryb | Długość (słowa) | Redukcja |
|---|------|----------------:|---------:|
| 01 | Domyślny — punkty (bullets) | 242 | **39.9×** |
| 02 | TL;DR (jedno-dwa zdania) | 84 | **115.0×** |
| 03 | Proza ~200 słów | 216 | **44.7×** |
| 04 | Outline (hierarchia) — top-k 8 | 712 | **13.6×** |
| 05 | Fokus: daty / osoby / liczby | 283 | **34.1×** |
| 06 | Fokus: ograniczenia / ryzyka / biasy | 253 | **38.2×** |
| 07 | Proza ultra-krótka ~40 słów | 53 | **182.3×** |
| 08 | Wyjście po polsku | 362 | **26.7×** |
| 09 | Proza ~120 słów | 120 | **80.5×** |
| 10 | Map-only — pełne notatki | 4,033 | **2.4×** |

---

## Demo 01 — Domyślny — punkty (bullets)
**Flagi:** `--style bullets`  
**Długość:** 242 słów · **Redukcja: 39.9×**  
**Po co:** Tryb bazowy: zwięzłe punkty, domyślny cel ~250 słów.

```
Here are 10 concise bullet points summarizing the key points from the provided text:

• Machine learning is a field of study in artificial intelligence concerned with the development and study of statistical algorithms that can learn from data and generalize to unseen data.
• The term "machine learning" and "artificial intelligence" are often used interchangeably, but they are not synonymous.
• The history of machine learning is rooted in decades of efforts to study human cognitive processes.
• The Hebbian theory of neuron interaction set the groundwork for how many machine learning algorithms work.
• Machine learning grew out of the quest for artificial intelligence (AI) as an academic discipline.
• The field changed its goal from achieving artificial intelligence to tackling solvable problems of a practical nature.
• Deep learning is a subset of machine learning that has achieved substantial improvements in performance.
• Machine learning and data compression are closely related, with a system that predicts the posterior probabilities of a sequence given its entire history being used for optimal data compression.
• The bias–variance decomposition is one way to quantify generalisation error, with the complexity of the hypothesis matching the complexity of the function underlying the data for best performance.
• Machine learning approaches can suffer from data biases, which can be picked up from human-made data, and the lack of participation and representation of minority populations in the field is blamed for machine learning's vulnerability to biases.
```

## Demo 02 — TL;DR (jedno-dwa zdania)
**Flagi:** `--style tldr --max-words 60`  
**Długość:** 84 słów · **Redukcja: 115.0×**  
**Po co:** Maksymalna kompresja: esencja w kilku zdaniach.

```
Here is a 60-word summary of the provided text:

Machine learning is a field of study that combines statistics and mathematical optimization methods to enable computers to learn from data and make predictions or classifications. It has its roots in the 1950s and 1960s, with early researchers such as Donald Hebb and Walter Pitts and Warren McCulloch contributing to the development of neural networks. The field has since grown and evolved, with advances in deep learning and the introduction of new algorithms and techniques.
```

## Demo 03 — Proza ~200 słów
**Flagi:** `--style prose --max-words 200`  
**Długość:** 216 słów · **Redukcja: 44.7×**  
**Po co:** Płynny akapit zamiast punktów — do wklejenia w tekst.

```
Here is a summary of the provided text in 200 words or less:

Machine learning is a field of study that focuses on developing and studying algorithms that can learn from data and generalize to unseen data. It is a subset of artificial intelligence that uses statistical and mathematical methods to analyze and make predictions or decisions. The field has a long history, dating back to the 1950s, and has evolved from a quest for artificial intelligence to a practical approach to solving real-world problems. Machine learning has applications in various fields, including agriculture, healthcare, finance, and more.

There are different types of machine learning, including supervised, unsupervised, and reinforcement learning. Supervised learning involves training a model on labeled data to make predictions or classifications. Unsupervised learning involves finding patterns in unlabeled data. Reinforcement learning involves training a model to make decisions based on rewards or penalties.

Machine learning models can be trained on large datasets using various algorithms, including neural networks, decision trees, and support vector machines. The field has seen significant advancements in recent years, with the development of deep learning algorithms and the use of GPUs to accelerate computations. However, machine learning models can also suffer from biases and errors, and there is a need for more transparency and explainability in AI decision-making.
```

## Demo 04 — Outline (hierarchia) — top-k 8
**Flagi:** `--style outline --max-bullets 12 --top-k 8`  
**Długość:** 712 słów · **Redukcja: 13.6×**  
**Po co:** Struktura zagnieżdżona. Przy top-k 1 reduce zwracał DETERMINISTYCZNĄ pustkę (cicha porażka); top-k 8 odblokował poprawny wynik za pierwszym razem.

*Fragment (pełny wynik 712 słów):*

```
Here is a summary of the document in a hierarchical outline format with 12 top-level items:

I. **History of Machine Learning**

* A. The term "machine learning" was coined in 1959 by Arthur Samuel
* B. The earliest machine learning program was introduced in the 1950s by Samuel
* C. Machine learning has its roots in decades of research on human cognitive processes
* D. Researchers studied human cognitive processes, including Walter Pitts and Warren McCulloch, who proposed the first mathematical model of neural networks

II. **Types of Machine Learning**

* A. Supervised learning: A computer is presented with example inputs and their desired outputs
* B. Unsupervised learning: No labels are given to the learning algorithm, leaving it to find structure in its input
* C. Reinforcement learning: A computer program interacts with a dynamic environment to perform a certain goal
* D. Semi-supervised learning: A combination of supervised and unsupervised learning

III. **Machine Learning Applications**

* A. Machine learning models can be used for computer vision, speech recognition, natural language processing, and decision-making
* B. Machine learning has applications in agriculture, anatomy, astronomy, automated decision-making, banking, and more

IV. **Machine Learning Models**

* A. A machine learning model is a type of mathematical model that can be used to make predictions or classifications on new data
* B. Machine learning models require a high quantity of reliable data to perform accurate predictions
* C. Trained models derived from biased or non-evaluated data can result in skewed or undesired predictions
* D. Algorithmic bias is a potential result of data not being fully prepared for training

V. **Machine Learning Ethics**

...
```

## Demo 05 — Fokus: daty / osoby / liczby
**Flagi:** `--style bullets --focus [key dates, people, named systems, numbers]`  
**Długość:** 283 słów · **Redukcja: 34.1×**  
**Po co:** Sterowanie uwagą: to samo źródło, soczewka na fakty twarde.

```
Here is the final summary of the provided text in 10 concise bullet points, ordered by importance:

• **Machine learning is a field of study in artificial intelligence concerned with the development and study of statistical algorithms that can learn from data and generalize to unseen data.** (Key concept)
• **The term "machine learning" and "artificial intelligence" are often used interchangeably, but they are not synonymous.** (Key concept)
• **The Hebbian theory of neuron interaction set the groundwork for how many machine learning algorithms work, introduced by Donald Hebb in 1949.** (Historical context)
• **The first mathematical model of neural networks was proposed by Walter Pitts and Warren McCulloch in the 1950s.** (Historical context)
• **Tom M. Mitchell provided a widely quoted definition of machine learning in 1998: "A computer program is said to learn from experience E with respect to some class of tasks T and performance measure P if its performance at tasks in T, as measured by P, improves with experience E."** (Definition)
• **Deep learning is a subset of machine learning that has achieved significant improvements in performance.** (Key concept)
• **Machine learning and data mining often employ the same methods, but with different goals: machine learning focuses on prediction, while data mining focuses on discovery.** (Key concept)
• **The computational analysis of machine learning algorithms and their performance is a branch of theoretical computer science known as computational learning theory.** (Key concept)
• **Machine learning models can be used for a wide range of applications, including agriculture, healthcare, finance, and more.** (Key concept)
• **Explainable AI (XAI) aims to make AI decisions understandable to humans, addressing concerns about algorithmic biases, fairness, accountability, transparency, privacy, and regulation.** (Key concept)
```

## Demo 06 — Fokus: ograniczenia / ryzyka / biasy
**Flagi:** `--style bullets --focus [limitations, risks, bias, criticism, failure modes]`  
**Długość:** 253 słów · **Redukcja: 38.2×**  
**Po co:** To samo źródło, inna soczewka — krytyka i słabości ML.

```
Here are the 10 most important points from the document:

• Machine learning is a field of study in artificial intelligence concerned with the development and study of statistical algorithms that can learn from data and generalize to unseen data.
• The term "machine learning" and "artificial intelligence" are often used interchangeably, but they are not synonymous.
• The history of machine learning is rooted in decades of efforts to study human cognitive processes, with the Hebbian theory of neuron interaction setting the groundwork for many machine learning algorithms.
• Machine learning grew out of the quest for artificial intelligence, with researchers attempting to approach the problem with various symbolic methods and neural networks.
• The field changed its goal from achieving artificial intelligence to tackling solvable problems of a practical nature in the 1990s.
• Machine learning and statistics are closely related fields in terms of methods, but distinct in their principal goal.
• The more variables (input) used to train the model, the more accurate the ultimate model will be.
• The computational analysis of machine learning algorithms and their performance is a branch of theoretical computer science known as computational learning theory.
• Machine learning approaches can suffer from data biases, which can be picked up from human-made data, and the lack of participation and representation of minority populations in the field of AI is blamed for machine learning's vulnerability to biases.

Note: These points cover the most important and relevant information from the document, and are ordered by importance.
```

## Demo 07 — Proza ultra-krótka ~40 słów
**Flagi:** `--style prose --max-words 40`  
**Długość:** 53 słów · **Redukcja: 182.3×**  
**Po co:** Abstrakt jednoakapitowy — najkrótszy sensowny opis.

```
Here is a summary of the provided text in 40 words or less:

Machine learning is a field of study that uses statistical algorithms to learn from data and make predictions or classifications. It has its roots in the 1950s and 1960s, with early work by researchers like Donald Hebb and Walter Pitts.
```

## Demo 08 — Wyjście po polsku
**Flagi:** `--style bullets --language polish`  
**Długość:** 362 słów · **Redukcja: 26.7×**  
**Po co:** Wejście angielskie → streszczenie polskie (tłumaczenie w locie na etapie reduce).

```
Here is the summary of the provided text in 10 concise bullet points, ordered by importance:

• Machine learning is a field of study in artificial intelligence concerned with the development and study of statistical algorithms that can learn from data and generalize to unseen data.
• The field of machine learning has its roots in decades of efforts to study human cognitive processes, and the Hebbian theory of neuron interaction set the groundwork for many machine learning algorithms.
• The term "machine learning" was coined in 1959 by Arthur Samuel, and the earliest machine learning program was introduced in the 1950s.
• Machine learning grew out of the quest for artificial intelligence (AI), and the field has evolved from symbolic approaches to statistical and probabilistic methods.
• The field of machine learning has intimate ties to optimization, and many learning problems are formulated as minimization of some loss function on a training set of examples.
• Machine learning has been applied to various fields, including agriculture, anatomy, astronomy, automated decision-making, banking, bioinformatics, brain–machine interfaces, cheminformatics, citizen science, climate science, computer networks, computer vision, credit-card fraud detection, data quality, DNA sequence classification, economics, financial data analysis, general game playing, handwriting recognition, healthcare, information retrieval, insurance, internet fraud detection, investment management, knowledge graph embedding, linguistics, machine learning control, machine perception, machine translation, material engineering, mathematics, marketing, medical diagnosis, natural language processing, natural language understanding, online advertising, optimization, recommender systems, robot locomotion, search engines, sentiment analysis, sequence mining, software engineering, speech recognition, structural health monitoring, syntactic pattern recognition, telecommunications.
• Machine learning approaches can suffer from data biases, which can be picked up from human-made data, and the lack of participation and representation of minority populations in the field of AI is blamed for machine learning's vulnerability to biases.
• Machine learning has been used to aid in developing a cure for COVID-19, predict pro-environmental behavior of travellers, optimize smartphone performance and thermal behavior based on user interaction, and predict stock returns without overfitting.
• Machine learning has been applied to study fine art paintings and reveal previously unrecognised influences among artists, and has been used to investigate and predict evacuation decision-making in disasters.
```

## Demo 09 — Proza ~120 słów
**Flagi:** `--style prose --max-words 120`  
**Długość:** 120 słów · **Redukcja: 80.5×**  
**Po co:** Punkt środkowy krzywej długość - kompresja.

```
Here is a summary of 120 words or less:

Machine learning is a field of study in artificial intelligence concerned with developing and studying statistical algorithms that can learn from data and generalize to unseen data. It draws from statistics and mathematical optimization methods. The term "machine learning" and "artificial intelligence" are often used interchangeably, but they are not synonymous. The field has a rich history, dating back to the 1950s, with early researchers such as Donald Hebb and Walter Pitts and Warren McCulloch contributing to the development of neural networks. Machine learning has grown out of the quest for artificial intelligence, and has become a distinct field with its own goals and methods, including supervised, unsupervised, and reinforcement learning.
```

## Demo 10 — Map-only — pełne notatki
**Flagi:** `--map-only`  
**Długość:** 4,033 słów · **Redukcja: 2.4×**  
**Po co:** Bez etapu reduce: połączone notatki per-chunk. Maksymalne POKRYCIE, minimalna kompresja — kontrapunkt dla reszty.

*Pełne notatki: 4,033 słów, 5 sekcji (po jednej na chunk). Fragment:*

```
### Część 1
• Machine learning is a field of study in artificial intelligence concerned with the development and study of statistical algorithms that can learn from data and generalize to unseen data.
• Statistics and mathematical optimization methods compose the foundations of machine learning.
• Data mining is a related field of study, focusing on exploratory data analysis (EDA) through unsupervised learning.
• Probably approximately correct learning provides a mathematical and statistical framework for describing machine learning.
• Advances in deep learning have allowed neural networks, a class of statistical algorithms, to surpass many previous machine learning approaches in performance.
• The term "machine learning" and "artificial intelligence" are often used interchangeably, but they are not synonymous.
• The term machine learning was coined in 1959 by Arthur Samuel.
• The earliest machine learning program was introduced in the 1950s.
• The history of machine learning is rooted in decades of efforts to study human cognitive processes.
• The Hebbian theory of neuron interaction set the groundwork for how many machine learning algorithms work.
• The Hebbian theory was introduced by Donald Hebb in 1949.
• The Hebbian theory was later developed by Walter Pitts and Warren McCulloch.
• The first mathematical model of neural networks was proposed by Walter Pitts and Warren McCulloch.
• The first experimental "learning machine" was developed by Raytheon Company in the 1960s.
• The "learning machine" was called Cybertron.
• The "learning machine" was used to analyze sonar signals, electrocardiograms, and speech patterns.
• The "learning machine" was repetitively "trained" by a human operator/teacher.
• The "learning machine" was equipped with a "goof" button to cause it to reevaluate incorrect decisions.
• Tom M. Mitchell provided a widely quoted definition of machine learning.
• The definition is: "A computer program is said to learn from experience E with respect to some class of tasks T and performance measure P if its performance at tasks in T, as measured by P, improves with experience E."
• The definition is fundamentally operational rather than defining the field in cognitive terms.
• The definition follows Alan Turing's proposal in his paper "Computing Machinery and Intelligence".
• The question "Can machines think?" is replaced by asking whether machines can convincingly imitate a human in its responses to human-posed questions.
• AlexNet, developed by Alex Krizhevsky, Ilya Sutskever, and Geoffrey Hinton, achieved substantially improved results in the ImageNet image recognition competition.
• AlexNet contributed to the wider adoption of deep neural networks.
• In 2012, AlexNet was developed.
• In 2013, Tomas Mikolov and colleagues introduced word2vec, techniques for efficiently learning distributed vector representations of words from large text corpora.
...
```
