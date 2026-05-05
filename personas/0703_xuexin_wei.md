---
name: Xuexin Wei
institution: University of Texas at Austin
department: Department of Neuroscience
lab_name: B-B-C Lab (brain-behavior-computation lab)
main_research_area: Computational and theoretical neuroscience
total_citations: 3172
h_index: 18
---

# Xuexin Wei

*Computational and theoretical neuroscience* — University of Texas at Austin, Department of Neuroscience, B-B-C Lab (brain-behavior-computation lab).

## Background

Xuexin Wei is a computational and theoretical neuroscientist who investigates the neural mechanisms underlying adaptive and intelligent behavior. By integrating normative modeling with bottom-up analysis of large-scale experimental data, Wei develops theories on sensory adaptation, perceptual biases, and neural manifold geometry. Wei's research applies the principle of efficient computation to understand how environmental structures and task demands shape neural representations in the domains of vision and navigation. Currently, Wei's lab focuses on bridging biological neural coding with deep learning to explore generalization and probabilistic inference in both brain and artificial systems.

## Papers

### 2025 — Split-trial analysis reveals the information capacity of neural population codes
*bioRxiv (Preprint)*
Authors: Dylan Le, Xue-Xin Wei

This research presents 'split-trial analysis,' a novel computational method designed to quantify information-limiting noise in neural populations without requiring the estimation of high-dimensional noise covariance matrices. By partitioning individual-trial population responses into multiple repeated virtual measurements, the technique disentangles noise shared across the entire population (the information-limiting component) from private, non-limiting noise. Extensive numerical simulations demonstrate that this approach significantly outperforms existing methods in terms of sample efficiency, accuracy, and robustness. The authors apply the method to diverse neurophysiological datasets, identifying substantial information-limiting noise in the mouse head-direction system, minimal limiting noise in the mouse V1 orientation code, and highly stable temporal structures of information limits in the macaque prefrontal cortex during saccadic tasks.

### 2025 — Quantifying Task-relevant Similarities in Representations Using Decision Variable Correlations
*Advances in Neural Information Processing Systems (NeurIPS 2025)*
Authors: Yu (Eric) Qian, Wilson S. Geisler, Xue-Xin Wei

This paper introduces Decision Variable Correlation (DVC) as a principled metric for characterizing the similarity of decision strategies between biological neural systems and deep neural networks (DNNs). Grounded in signal detection theory, DVC quantifies image-by-image correlations between decoded decisions derived from internal neural representations in classification tasks, thereby isolating task-relevant information structure from general representational alignment. Analysis of monkey V4/IT electrophysiological recordings and DNNs reveals that while model-to-model similarity is high, model-to-monkey similarity is consistently lower and unexpectedly decreases as ImageNet-1k classification performance improves. Furthermore, the results show that neither adversarial training nor pre-training on larger datasets improves brain-alignment in these critical task-relevant dimensions, suggesting a fundamental divergence between biological vision and current image classification models.

### 2025 — Identifiability of Bayesian Models of Cognition
*bioRxiv (Preprint)*
Authors: Michael Hahn, Entang Wang, Xue-Xin Wei

This study addresses the critical problem of parameter identifiability when inferring Bayesian observer models from behavioral data. The authors analytically investigate whether the fundamental components of these models—prior beliefs, likelihood functions (constrained by encoding noise), and loss functions—can be uniquely recovered from experimental observations. They prove that under broadly applicable conditions, these components are identifiable without a priori knowledge, provided that behavioral measurements are collected across multiple levels of sensory noise. The theoretical framework is validated through simulations and applications to human orientation perception datasets, providing rigorous guiding principles for experimental design and the interpretation of normative models in cognitive science and neuroscience.

### 2024 — Cognitive maps from predictive vision
*Nature Machine Intelligence*
Authors: Margaret von Ebers, Xue-Xin Wei

This study explores the computational link between predictive processing in the visual hierarchy and the emergence of spatial representations in the hippocampal-entorhinal system. By training self-supervised neural networks to predict future visual states or inputs within simulated environments, the authors demonstrate that hexagonal grid-like activity patterns naturally emerge in the model's latent units. This findings suggests that the 'canonical' grid cell representations used for spatial navigation can be derived from a more general objective of optimizing predictive accuracy in dynamic visual environments. The research provides a unifying perspective on how the brain's internal models of the world may be constructed through self-supervised learning on visual sequences.

### 2024 — A unifying theory explains seemingly contradictory biases in perceptual estimation
*Nature Neuroscience*
Authors: Michael Hahn, Xue-Xin Wei

Perceptual biases are often interpreted as evidence for disparate computational strategies, such as Bayesian attraction to priors or efficient coding-driven repulsion. This paper presents a normative Bayesian framework that reconciles these seemingly contradictory phenomena via an additive decomposition of perceptual bias into three distinct components: attraction to a prior, repulsion from regions with high encoding precision (Fisher information), and regression away from stimulus boundaries. The theory reveals a universal rule for predicting the direction and magnitude of biases based on limited neural resources and environmental statistics. This unified account is validated across multiple sensory domains, including the perception of orientation, color, and magnitude, offering a singular explanation for diverse behavioral regularities in human perception.
