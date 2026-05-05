---
name: Heiko H. Schütt
institution: University of Luxembourg
department: Department of Behavioural and Cognitive Sciences
lab_name: Psychophysics Lab
main_research_area: computational cognitive science
total_citations: 2385
h_index: 16
---

# Heiko H. Schütt

*computational cognitive science* — University of Luxembourg, Department of Behavioural and Cognitive Sciences, Psychophysics Lab.

## Background

Heiko H. Schütt is an Associate Professor at the University of Luxembourg specializing in the development of mechanistic models for visual perception and cognitive behavior. Their research integrates deep neural networks, Bayesian inference, and efficient coding to explain human visual processing, particularly regarding eye movements and object recognition in natural scenes. Schütt developed open-source computational toolboxes, including Psignifit 4 for psychometric function fitting and the rsatoolbox for representational similarity analysis. Their work focuses on creating models that bridge behavioral and neurophysiological data while advancing statistical methods for evaluating representational geometries.

## Papers

### 2025 — A Python Toolbox for Representational Similarity Analysis
*eLife*
Authors: Jasper J. F. van den Bosch, Tal Golan, Benjamin Peters, JohnMark Taylor, Mahdiyar Shahbazi, Baihan Lin, Ian Charest, Jörn Diedrichsen, Nikolaus Kriegeskorte, Marieke Mur, Heiko H. Schütt

This work introduces rsatoolbox, an open-source Python implementation for Representational Similarity Analysis (RSA) designed to relate high-dimensional neural activity patterns to computational models. The toolbox incorporates a suite of recent methodological advances, including the use of cross-validated Mahalanobis distances (crossnobis) to provide unbiased estimates of representational dissimilarity matrices (RDMs) in the presence of noise. It further integrates advanced RDM comparators and rigorous statistical inference procedures, such as condition- and subject-level bootstrapping, to evaluate model-to-brain alignment. The software facilitates the evaluation of deep neural networks and other hierarchical models against multivariate data from fMRI, EEG/MEG, and large-scale electrophysiology.

### 2025 — Disentangling signal and noise in neural responses through generative modeling
*PLOS Computational Biology*
Authors: Kendrick Kay, Jacob S. Prince, Thomas Gebhart, Greta Tuckute, Jingyang Zhou, Thomas Naselaris, Heiko H. Schütt

In this paper, we propose the Generative Modeling of Signal and Noise (GSN) framework to solve the problem of separating condition-related signal covariance from trial-to-trial noise covariance in multivariate neural measurements. While traditional analyses rely on trial averaging, GSN explicitly models measured responses as the sum of samples from latent multivariate signal and noise distributions. By applying shrinkage estimators to the data covariance, GSN allows for more accurate characterization of the population-level representational geometry even in regimes with high noise or limited trials. We demonstrate that GSN provides superior estimates of signal distribution and improves the reliability of inferences regarding neural representations in both simulated and empirical fMRI datasets.

### 2025 — Bayesian Comparisons Between Representations
*arXiv*
Authors: Heiko H. Schütt

This paper presents a formal Bayesian framework for quantifying the similarity between neural network representations based on the predictive distributions of linear readouts. It is argued that the prior predictive distribution serves as a comprehensive description of a model's inductive bias and generalization capability. By employing information-theoretic metrics such as the Jensen-Shannon distance or total variation distance between these distributions, the method induces pseudo-metrics for representations that account for uncertainty. This approach establishes a theoretical unification between disparate representational similarity metrics, connecting task-based linear probing with kernel-based measures like centered kernel alignment (CKA) and representational similarity analysis (RSA).

### 2025 — High Error Margin Loss: Improving Robustness and Generalisation by Overcoming Training Issues of Margin-Based Losses
*arXiv*
Authors: Michael W. Spratling, Heiko H. Schütt

This study proposes the High Error Margin (HEM) loss as a robust alternative to the standard cross-entropy (CE) loss for training deep neural network classifiers. CE loss is susceptible to overconfidence and continues to update weights for well-classified samples, which can negatively impact adversarial robustness and out-of-distribution generalization. HEM loss is a variant of multi-class margin loss that avoids premature termination of gradient updates while curbing overconfidence. Extensive benchmarking across multiple architectures shows that HEM loss significantly improves performance in unknown class rejection, adversarial defense, and continual learning, while remaining competitive with CE on clean accuracy.

### 2024 — Integrating Vision: From Neuroscience to Artificial Intelligence
*Applied and Computational Engineering*
Authors: Haoshan Ye, Heiko H. Schütt

This review synthesizes the current state of knowledge regarding the biological foundations of vision—spanning the retina, lateral geniculate nucleus, and cortical areas V1 through V6—with modern advancements in artificial neural networks (ANNs). We evaluate the extent to which deep neural networks serve as effective models for biological vision by analyzing their ability to predict human error patterns and multivariate neural signals. The article outlines a research program where failures in model-to-brain alignment drive the development of more biologically plausible architectures, such as those incorporating feedback connections and multisensory integration, to bridge the performance gap between artificial systems and the complexity of human perception.
