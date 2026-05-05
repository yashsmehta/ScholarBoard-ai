---
name: Eero P. Simoncelli
institution: New York University
department: Center for Neural Science
lab_name: Laboratory for Computational Vision
main_research_area: computational neuroscience and vision science
total_citations: 132974
h_index: 101
---

# Eero P. Simoncelli

*computational neuroscience and vision science* — New York University, Center for Neural Science, Laboratory for Computational Vision.

## Background

Eero P. Simoncelli is a Silver Professor at New York University and the director of the Center for Computational Neuroscience at the Flatiron Institute. Simoncelli develops computational models at the intersection of mathematics, engineering, and neuroscience to characterize the representation of visual information in biological and artificial systems. Their work includes research on natural image statistics, multiscale image transforms such as the steerable pyramid, and the SSIM index for image quality assessment. Currently, Simoncelli investigates the geometric structure of neural representations and population coding principles to analyze how the brain processes complex visual scenes.

## Papers

### 2026 — Blind denoising diffusion models and the blessings of dimensionality
*arXiv (Preprint)*
Authors: Zahra Kadkhodaie, Aram-Alexandre Pooladian, Sinho Chewi, Eero P. Simoncelli

This work provides a rigorous theoretical and empirical analysis of generative diffusion models using blind denoisers that lack explicit noise amplitude conditioning. The authors prove that these blind denoising diffusion models (BDDMs) automatically track an implicit noise schedule during the reverse process, provided the data distribution possesses low intrinsic dimensionality. They demonstrate that BDDMs can accurately sample from the target distribution in polynomial time relative to the intrinsic dimension. Empirically, BDDMs are shown to produce higher-quality samples than non-blind models by correcting the mismatch between true image noise residuals and pre-defined noise schedules.

### 2026 — Learning a distance measure from the information-estimation geometry of data
*International Conference on Learning Representations (ICLR)*
Authors: Guy Ohayon, Pierre-Etienne H. Fiquet, Florentin Guth, Jona Ballé, Eero P. Simoncelli

The authors introduce the Information-Estimation Metric (IEM), an unsupervised distance measure derived from the geometric structure of signal probability densities. Grounded in the I-MMSE relationship and Tweedie’s formula, the IEM relates log-probability to the errors of an optimal denoiser across varying noise scales. Geometrically, the metric compares score vector fields of blurred signal densities. The paper proves that the IEM is a valid global distance metric and derives a local Riemannian second-order approximation. When learned on ImageNet, the IEM achieves performance competitive with supervised perceptual metrics in predicting human quality judgments.

### 2025 — Learning normalized image densities via dual score matching
*Advances in Neural Information Processing Systems (NeurIPS)*
Authors: Florentin Guth, Zahra Kadkhodaie, Eero P. Simoncelli

This paper presents a framework for learning normalized energy-based models (EBMs) by modifying score-network architectures to compute scalar energies while retaining inductive biases. While standard score-matching optimizes the gradient of the log-density with respect to the input, it does not constrain the absolute density level. The authors introduce a secondary objective based on the gradient with respect to the noise level, ensuring the learned energy is consistent and normalized. This dual-matching approach enables exact density estimation and reveals that natural image manifolds possess significant geometric regularities beyond simple dimensionality reduction.

### 2025 — Discriminating image representations with principal distortions
*International Conference on Learning Representations (ICLR)*
Authors: Jenelle Feather, David Lipshutz, Sarah E. Harvey, Alex H. Williams, Eero P. Simoncelli

This research introduces a framework for comparing neural and artificial image representations by analyzing their local geometries through the Fisher Information Matrix (FIM). The FIM serves as a substrate for characterizing representational sensitivity to local stimulus perturbations. The authors define 'principal distortions'—orthogonal stimulus changes that maximize model response variance—to differentiate representations that exhibit similar global structures. This methodology allows for the identification of specific visual features where models diverge, providing a high-resolution metric for evaluating how well computational models align with biological visual representations.

### 2024 — Learning predictable and robust neural representations by straightening image sequences
*Advances in Neural Information Processing Systems (NeurIPS)*
Authors: Xueyan Niu, Cristina Savin, Eero P. Simoncelli

Inspired by the observation that the primate visual system 'straightens' temporal trajectories of natural videos, the authors propose a self-supervised learning objective that incentivizes representational straightness. The objective promotes neural embeddings that follow linear paths over time, allowing for prediction via linear extrapolation. The authors demonstrate that these straightened representations effectively factorize geometric, photometric, and semantic attributes. Furthermore, representations learned through this straightening principle exhibit significantly greater robustness to noise and adversarial perturbations compared to standard self-supervised methods optimized for augmentation invariance.
