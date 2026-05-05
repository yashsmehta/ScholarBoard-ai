---
name: Martin Schrimpf
institution: EPFL
department: School of Life Sciences and School of Computer and Communication Sciences
lab_name: NeuroAI Lab
main_research_area: NeuroAI and computational neuroscience
total_citations: 5030
h_index: 20
---

# Martin Schrimpf

*NeuroAI and computational neuroscience* — EPFL, School of Life Sciences and School of Computer and Communication Sciences, NeuroAI Lab.

## Background

Martin Schrimpf is a Tenure-Track Assistant Professor at EPFL and head of the NeuroAI Lab, where their research integrates machine learning, neuroscience, and cognitive science. Schrimpf is an architect of the Brain-Score platform, an initiative designed to benchmark artificial neural networks against large-scale neural and behavioral datasets to identify brain-like computational architectures. Their work focuses on developing predictive models of the primate visual ventral stream and the human language network to identify the functional principles of natural intelligence. Currently, Schrimpf investigates the use of these brain models for clinical applications, including the development of visual prosthetics and diagnostic tools for neurological disorders.

## Papers

### 2026 — Model-Guided Microstimulation Steers Primate Visual Behavior
*International Conference on Learning Representations (ICLR)*
Authors: Johannes Mehrer, Ben Lonnqvist, Anna Mitola, Abdulkadir Gokce, Paolo Papale, Martin Schrimpf

This research introduces a computational framework designed to causally model and steer neural activity in high-level cortical regions through microstimulation. The framework utilizes Topographic Deep Artificial Neural Networks (TDANNs) to replicate the spatial organization of cortical neurons and incorporates a perturbation module that translates electrical stimulation parameters into localized changes in neural activation. By integrating a mapping procedure to translate model-optimized stimulation coordinates to the macaque ventral visual stream, the authors demonstrate that microstimulation at sites predicted to be functional significantly influences perceptual choices in a visual recognition task. The work establishes that brain-aligned topographic models can effectively guide causal interventions in primates, potentially informing the design of visual prosthetics capable of evoking complex object-level percepts.

### 2026 — Inducing Dyslexia in Vision Language Models
*International Conference on Learning Representations (ICLR)*
Authors: Melika Honarmand, Ayati Sharma, Badr AlKhamissi, Johannes Mehrer, Martin Schrimpf

The authors utilize large-scale vision-language models (VLMs) as computational analogs to investigate the neural basis of developmental dyslexia, a disorder linked to hypoactivation in the visual word form area (VWFA). By employing neuroscientific localization paradigms to identify word-selective units within VLMs, the study evaluates the effects of targeted unit ablation on reading performance. The findings indicate that selective perturbation of these artificial VWFA analogs—but not random units—induces human-like reading deficits, specifically characterized by phonological impairments while preserving general orthographic and cross-modal linguistic processing. The study provides a mechanistic framework for simulating reading disorders and testing causal hypotheses regarding the functional organization of the visual word processing system.

### 2025 — From Language to Cognition: How LLMs Outgrow the Human Language Network
*Conference on Empirical Methods in Natural Language Processing (EMNLP)*
Authors: Badr AlKhamissi, Greta Tuckute, Yingtian Tang, Taha Binhuraib, Antoine Bosselut, Martin Schrimpf

This study benchmarks 34 training checkpoints across diverse model scales to analyze how alignment with the human language network (LN) evolves relative to linguistic competence. The results demonstrate that neural alignment primarily tracks the acquisition of formal linguistic competence—encompassing knowledge of core syntactic and compositional rules—which saturates early in the training trajectory. In contrast, functional competence involving world knowledge and reasoning continues to develop as models reach superhuman next-word prediction performance, leading to a divergence between model representations and biological neural activity. These findings suggest that the human language network primarily encodes formal linguistic structures and that current LLMs outgrow their brain-like processing characteristics as they surpass human-level proficiency.

### 2025 — Scaling Laws for Task-Optimized Models of the Primate Visual Ventral Stream
*International Conference on Machine Learning (ICML)*
Authors: Abdulkadir Gokce, Martin Schrimpf

Evaluating over 600 task-optimized architectures, this research characterizes the scaling laws governing the neural and behavioral alignment of artificial neural networks with the primate visual ventral stream. The authors find that while behavioral alignment with core object recognition performance scales consistently with increased compute, model capacity, and dataset size, neural alignment in visual areas V1 through IT exhibits significant saturation. Parametric power-law fitting suggests that optimal biological alignment is achieved by allocating a higher proportion of compute to dataset scale than to model parameters (approximately a 0.7:0.3 ratio). The results indicate that simple scaling of contemporary vision architectures is insufficient for improving models of internal brain representations, necessitating new strategies for brain-like modeling.

### 2025 — The LLM Language Network: A Neuroscientific Approach for Identifying Causally Task-Relevant Units
*Conference of the Nations of the Americas Chapter of the Association for Computational Linguistics (NAACL)*
Authors: Badr AlKhamissi, Greta Tuckute, Antoine Bosselut, Martin Schrimpf

This paper applies neuroscientific localization methods to large language models to identify functionally specialized, language-selective units analogous to the human core language system. The authors establish the causal necessity of these units for linguistic performance by demonstrating that their targeted ablation significantly degrades language task accuracy, whereas random unit ablation does not. Furthermore, these selective units demonstrate higher representational alignment with human brain recordings than unselected units. The research also investigates the emergence of specialized modules for logical reasoning and social cognition, finding that while specialized units exist across architectures, their functional organization is significantly more heterogeneous than that of the language-selective network.
