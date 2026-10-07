# Demonstracja v2: `tools/summarize.py` — 10 SOCZEWEK na jednym dokumencie
*2026-10-07 · ten sam dokument co v1 (Wikipedia „Machine learning”, 9 661 słów treści) · różne są PROMPTY (`--focus`), nie styl.*

## Pomysł
Jedna warstwa *map* (5 notatek, z cache) → **10 różnych finalnych reduce**, każdy z inną dyrektywą `--focus`: od wyciągania faktów, przez instrukcje operacyjne / kroki / komendy, po cztery analizy filozoficzne (ontologiczna, epistemologiczna, logiczna, metodologiczna) + glosariusz i pytania otwarte.

## Werdykt zgodności (to jest wynik!)
`--focus` to **miękki ster**, nie twardy kontrakt. Niezawodnie przełącza **nacisk i reframe kategorialny/akcyjny**; zawodzi przy **abstrakcyjnej meta-analizie i generowaniu pytań** (~3,5k tok kontekstu na 8B → instruction-following siada). Zgodne z prawem projektu *„mechanika deterministyczna, semantyka Jimmy”*.

**Legenda:** ✓ przełączył tryb · ◑ częściowo (treść trafiona, forma nie) · ✗ wrócił do generycznego streszczenia

| # | Soczewka | Słowa | Werdykt |
|---|----------|------:|:------:|
| 01 | Fakty atomowe | 202 | ◑ |
| 02 | Instrukcje operacyjne | 122 | ✓ |
| 03 | Kroki podstawowe | 862 | ✓ |
| 04 | Komendy / checklista | 261 | ◑ |
| 05 | Analiza ontologiczna | 403 | ✓ |
| 06 | Analiza epistemologiczna | 392 | ✗ |
| 07 | Analiza logiczna | 343 | ◑ |
| 08 | Analiza metodologiczna | 276 | ✓ |
| 09 | Glosariusz | 502 | ✓ |
| 10 | Pytania otwarte / luki | 377 | ✗ |

**Bilans:** 5× ✓ · 3× ◑ · 2× ✗

> ⚙️ **Uwagi:** (1) `--style outline` finalny reduce bywa DETERMINISTYCZNIE pusty przy top-k 1 — demo 03/05/07 wymagały top-k 8 (best-of-N ratuje). (2) Prolog „Here is the summary…” ucięty w post-processingu (Jimmy dokleja go uparcie — twarda forma = nasza robota, nie promptu). (3) Jak w v1: map-reduce działa tylko w reżimie „mało dużych chunków + jeden finalny reduce” (domyślny reduce się zapętla).

---

## Demo v01 — Fakty atomowe  ◑
**Prompt (`--focus`):** Extract atomic, self-contained FACTUAL CLAIMS. One verifiable fact per bullet.  
**Słowa:** 202 · **Werdykt:** ◑ — Fakty są, ale forma wciąż „streszczeniowa” — nie rozbił na atomy.

```
• Machine learning is a field of study in artificial intelligence concerned with the development and study of statistical algorithms that can learn from data and generalize to unseen data.
• The term "machine learning" and "artificial intelligence" are often used interchangeably, but they are not synonymous.
• The earliest machine learning program was introduced in the 1950s.
• The "learning machine" was developed by Raytheon Company in the 1960s.
• Tom M. Mitchell provided a widely quoted definition of machine learning.
• The definition is: "A computer program is said to learn from experience E with respect to some class of tasks T and performance measure P if its performance at tasks in T, as measured by P, improves with experience E."
• Machine learning grew out of the quest for artificial intelligence (AI).
• The field changed its goal from achieving artificial intelligence to tackling solvable problems of a practical nature.
• Machine learning and data compression are closely related.
• Machine learning and data mining often employ the same methods and overlap significantly.

Note: The above points are the most important and concise points from the text, and they cover the key concepts and definitions related to machine learning.
```

## Demo v02 — Instrukcje operacyjne  ✓
**Prompt (`--focus`):** Rewrite as OPERATIONAL INSTRUCTIONS: actionable directives, not descriptions.  
**Słowa:** 122 · **Werdykt:** ✓ — Przełączył: „Train models on diverse data… Use… Employ XAI…” — realne dyrektywy.

```
• **Operational Instructions for Practitioners:**
	+ Train machine learning models on diverse and representative data to avoid bias.
	+ Use techniques like data compression and dimensionality reduction to improve model performance.
	+ Employ explainable AI (XAI) methods to ensure transparency and accountability.
	+ Regularly evaluate model accuracy using methods like cross-validation and ROC curves.
	+ Consider using federated learning to maintain user privacy.
	+ Use hardware accelerators like TPUs for efficient deep learning tasks.
	+ Implement techniques like pruning, quantisation, and knowledge distillation for model optimization.
	+ Utilize open-source software like TensorFlow and scikit-learn for machine learning tasks.
	+ Engage with diverse stakeholders to address potential biases and ensure fairness.
	+ Continuously monitor and update models to prevent overfitting and model collapse.
```

## Demo v03 — Kroki podstawowe  ✓
**Prompt (`--focus`):** Decompose into a SEQUENCE OF BASIC STEPS, step by step.  
**Słowa:** 862 · **Werdykt:** ✓ — Ponumerowana sekwencja sekcji (co→historia→typy→…). Outline; top-k 8.

```
1. **What is Machine Learning**
	* Machine learning is a field of study in artificial intelligence concerned with the development and study of statistical algorithms that can learn from data and generalize to unseen data.
	* Advances in deep learning have allowed neural networks, a class of statistical algorithms, to surpass many previous machine learning approaches in performance.

2. **History of Machine Learning**
	* The term "machine learning" was coined in 1959 by Arthur Samuel, an IBM employee and pioneer in the field of computer gaming and artificial intelligence.
	* The earliest machine learning program was introduced in the 1950s, when Samuel invented a computer program that calculated the chance of winning in checkers for each side.
	* The history of machine learning is rooted in decades of efforts to study human cognitive processes.

3. **Types of Machine Learning**
	* Supervised learning: The computer is presented with example inputs and their desired outputs, given by a "teacher".
	* Unsupervised learning: No labels are given to the learning algorithm, leaving it on its own to find structure in its input.
	* Reinforcement learning: A computer program interacts with a dynamic environment in which it must perform a certain goal.
	* Semi-supervised learning: No labels are given to the learning algorithm, but it is given some labelled and unlabelled examples.
```

## Demo v04 — Komendy / checklista  ◑
**Prompt (`--focus`):** Imperative COMMAND CHECKLIST: each item begins with an action verb.  
**Słowa:** 261 · **Werdykt:** ◑ — Pogrubione tezy zamiast czasowników rozkazujących — reframe częściowy.

```
• **Machine learning is a field of study in artificial intelligence concerned with the development and study of statistical algorithms that can learn from data and generalize to unseen data.**
• **The term "machine learning" was coined in 1959 by Arthur Samuel, and the earliest machine learning program was introduced in the 1950s.**
• **Machine learning grew out of the quest for artificial intelligence (AI), and the field has evolved from symbolic approaches to statistical and probabilistic methods.**
• **Supervised learning involves training a model on labeled data to make predictions or classifications, while unsupervised learning involves finding structures in unlabeled data.**
• **Deep learning is a subset of machine learning that uses neural networks to learn complex patterns in data, and has achieved state-of-the-art results in many applications.**
• **Machine learning has been applied to a wide range of fields, including agriculture, healthcare, finance, and more, and has achieved significant improvements in tasks such as image and speech recognition, natural language processing, and decision-making.**
• **The field of machine learning has also been plagued by issues such as overfitting, model collapse, and hallucinations, and has raised concerns about bias, fairness, and transparency.**
• **Explainable AI (XAI) aims to make AI decisions understandable to humans, and has been proposed as a solution to these issues.**
• **Machine learning models can be manipulated or evaded by adversarial attacks, and researchers have demonstrated backdoors in classifying machine learning models.**
• **Tensor Processing Units (TPUs) are hardware accelerators developed by Google for machine learning workloads, and have become a key component of AI infrastructure.**
```

## Demo v05 — Analiza ontologiczna  ✓
**Prompt (`--focus`):** ONTOLOGICAL: entities/categories and relations (is-a, part-of, uses).  
**Słowa:** 403 · **Werdykt:** ✓ — Kategorie: Key Concepts / Key Figures / Techniques / Software. Outline; top-k 8.

```
**Summary**
I. Introduction
* The term "machine learning" was coined in 1959 by Arthur Samuel.
* Machine learning has ties to data mining, statistics, and artificial intelligence.
II. Types of Learning
* Supervised learning: The computer is presented with example inputs and their desired outputs.
	+ Types: Classification, regression, and similarity learning.
* Unsupervised learning: Model identifies patterns or structures in unlabelled data.
	+ Types: Clustering, dimensionality reduction, and density estimation.
* Reinforcement learning: A computer program interacts with a dynamic environment to maximise rewards.
```


## Demo v06 — Analiza epistemologiczna  ✗
**Prompt (`--focus`):** EPISTEMOLOGICAL: how is knowledge acquired, justified, validated?  
**Słowa:** 392 · **Werdykt:** ✗ — Wróciło do streszczenia (dodało skale „Importance: 9/10”, nie epistemologię).

```
• **Machine learning is a field of study in artificial intelligence concerned with the development and study of statistical algorithms that can learn from data and generalize to unseen data.** (Importance: 9/10)
• **The term "machine learning" and "artificial intelligence" are often used interchangeably, but they are not synonymous.** (Importance: 8.5/10)
• **The history of machine learning is rooted in decades of efforts to study human cognitive processes, with the Hebbian theory of neuron interaction setting the groundwork for how many machine learning algorithms work.** (Importance: 8/10)
• **Machine learning grew out of the quest for artificial intelligence (AI), with researchers attempting to approach the problem with various symbolic methods, as well as what were then termed "neural networks".** (Importance: 8/10)
• **The field of machine learning has shifted focus away from symbolic approaches inherited from AI, and toward methods and models borrowed from statistics, fuzzy logic, and probability theory.** (Importance: 8/10)
• **Deep learning is a subset of machine learning, and advances in deep learning have allowed neural networks to surpass many previous machine learning approaches in performance.** (Importance: 8/10)
• **Machine learning and data mining often employ the same methods and overlap significantly, but machine learning focuses on prediction based on known properties learned from the training data, while data mining focuses on the discovery of previously unknown properties in the data.** (Importance: 8/10)
• **The field of machine learning has intimate ties to optimization, with many learning problems formulated as minimization of some loss function on a training set of examples.** (Importance: 8/10)
• **The computational analysis of machine learning algorithms and their performance is a branch of theoretical computer science known as computational learning theory.** (Importance: 8/10)
• **Machine learning has been applied to a wide range of fields, including agriculture, anatomy, adaptive website, affective computing, astronomy, automated decision-making, banking, behaviorism, bioinformatics, brain–machine interfaces, cheminformatics, citizen science, climate science, computer networks, computer vision, credit-card fraud detection, data quality, DNA sequence classification, economics, financial data analysis, general game playing, handwriting recognition, healthcare, information retrieval, insurance, internet fraud detection, investment management, knowledge graph embedding, linguistics, machine learning control, machine perception, machine translation, material engineering, mathematics, marketing, medical diagnosis, natural language processing, natural language understanding, online advertising, optimization, recommender systems, robot locomotion, search engines, sentiment analysis, sequence mining, software engineering, speech recognition, structural health monitoring, syntactic pattern recognition, telecommunications.** (Importance: 7.5/10)
```


## Demo v07 — Analiza logiczna  ◑
**Prompt (`--focus`):** LOGICAL: definitions, premises, inferential dependencies.  
**Słowa:** 343 · **Werdykt:** ◑ — Struktura hierarchiczna, ale bez jawnych zależności wnioskowania. Outline; top-k 8.

```
**Machine Learning**

*   **History of Machine Learning**
    *   Introduced in 1959 by Arthur Samuel
    *   First machine learning program in the 1950s
    *   Probabilistic reasoning used in early AI
    *   Machine learning grew out of AI quest for learning from data
*   **Types of Machine Learning**
    *   Supervised learning: builds a model of a set of data with both inputs and outputs
    *   Unsupervised learning: finds structures in unlabelled data
    *   Reinforcement learning: takes actions in an environment to maximise cumulative reward
    *   Semi-supervised learning: combines supervised and unsupervised learning
*   **Machine Learning Goals**
    *   Predictions based on known properties learned from training data
```

## Demo v08 — Analiza metodologiczna  ✓
**Prompt (`--focus`):** METHODOLOGICAL: methods, procedures, evaluation, assumptions.  
**Słowa:** 276 · **Werdykt:** ✓ — Prowadzi terminami-metodami (Deep/Supervised/Unsupervised) z mechanizmem.

```
• **Machine learning** is a field of study in artificial intelligence concerned with the development and study of statistical algorithms that can learn from data and generalize to unseen data.
• **Deep learning** is a subset of machine learning that uses neural networks, a class of statistical algorithms, to surpass many previous machine learning approaches in performance.
• **Probabilistic reasoning** was also employed in early AI research, especially in automated medical diagnosis, but was later abandoned due to theoretical and practical problems with data acquisition and representation.
• **Supervised learning** involves training a model on labeled data to learn a function that can be used to predict the output associated with new inputs.
• **Unsupervised learning** involves finding structures in unlabeled data without any external guidance, and is used for tasks like clustering, dimensionality reduction, and density estimation.
• **Reinforcement learning** involves a computer program interacting with a dynamic environment to perform a certain goal, and is used for tasks like game playing and robotics.
• **Machine learning and statistics** are closely related fields in terms of methods, but distinct in their principal goal, with machine learning finding generalizable predictive patterns and statistics drawing population inferences from a sample.
• **Computational learning theory** is a branch of theoretical computer science that studies the performance of machine learning algorithms, including probabilistic bounds on performance and time complexity.
• **Explainable AI (XAI)** aims to make AI decisions understandable to humans, addressing concerns about algorithmic biases, fairness, accountability, transparency, privacy, and regulation.
• **Tensor Processing Units (TPUs)** are hardware accelerators developed by Google for machine learning workloads, optimized for tensor computations and widely used in large-scale machine learning models.
```

## Demo v09 — Glosariusz  ✓
**Prompt (`--focus`):** Glossary STRICTLY 'TERM — definition', one per line.  
**Słowa:** 502 · **Werdykt:** ✓ — Zadziałał PO eskalacji (prose + twardy format): „Gaussian process — …”. top-k 8.

```
Machine learning — A field of study in artificial intelligence concerned with the development and study of statistical algorithms that can learn from data and generalize to unseen data.
Decision tree learning — A type of machine learning that builds a model using a tree-like structure.
Reinforcement learning — A type of machine learning in which a computer program interacts with a dynamic environment to maximise cumulative reward.
Rule-based machine learning — A branch of machine learning that automatically discovers and learns rules from data.
Artificial neural networks — Computing systems vaguely inspired by the biological neural networks that constitute animal brains.
Support-vector machines — A type of supervised learning method used for classification and regression.
Gaussian process — A stochastic process in which every finite collection of the random variables in the process has a multivariate normal distribution.
```

## Demo v10 — Pytania otwarte / luki  ✗
**Prompt (`--focus`):** OPEN QUESTIONS ending in '?' — unresolved/debated/unknown.  
**Słowa:** 377 · **Werdykt:** ✗ — Uparcie zwraca fakty, nie pytania — nawet po eskalacji. Realny limit.

```
• Machine learning is a field of study in artificial intelligence concerned with the development and study of statistical algorithms that can learn from data and generalize to unseen data.
• The field of machine learning has its roots in decades of efforts to study human cognitive processes, with the Hebbian theory of neuron interaction setting the groundwork for many machine learning algorithms.
• Machine learning has grown out of the quest for artificial intelligence, with the term "machine learning" coined in 1959 by Arthur Samuel.
• The field has evolved from a focus on symbolic approaches to a focus on statistical and probabilistic methods, with deep learning being a subset of machine learning.
• Machine learning has applications in various fields, including agriculture, anatomy, adaptive website, affective computing, astronomy, automated decision-making, banking, behaviorism, bioinformatics, brain–machine interfaces, cheminformatics, citizen science, climate science, computer networks, computer vision, credit-card fraud detection, data quality, DNA sequence classification, economics, financial data analysis, general game playing, handwriting recognition, healthcare, information retrieval, insurance, internet fraud detection, investment management, knowledge graph embedding, linguistics, machine learning control, machine perception, machine translation, material engineering, mathematics, marketing, medical diagnosis, natural language processing, natural language understanding, online advertising, optimisation, recommender systems, robot locomotion, search engines, sentiment analysis, sequence mining, software engineering, speech recognition, structural health monitoring, syntactic pattern recognition, telecommunications.
• Machine learning approaches can suffer from data biases, which can be picked up from human-made data, and the field has a long way to go in addressing these issues.
• The field of machine learning has seen significant advancements in recent years, with the introduction of Tensor Processing Units (TPUs) and other hardware accelerators, as well as the development of new software frameworks such as TensorFlow and PyTorch.
• Machine learning has been applied to various real-world problems, including predicting the 2008 financial crisis, aiding in the development of a cure for COVID-19, and optimizing smartphone performance and thermal behavior.
• The field of machine learning has also seen significant advancements in explainability, with the development of techniques such as Explainable AI (XAI) to make AI decisions understandable to humans.
• Machine learning has also been applied to various fields such as healthcare, finance, and education, with applications including predictive policing, credit-card fraud detection, and personalized medicine.
```
