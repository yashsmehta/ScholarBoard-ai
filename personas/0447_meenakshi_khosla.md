---
name: Meenakshi Khosla
institution: University of California, San Diego
department: Department of Cognitive Science
main_research_area: computational neuroscience and artificial intelligence
total_citations: 1381
h_index: 14
---

# Meenakshi Khosla

*computational neuroscience and artificial intelligence* — University of California, San Diego, Department of Cognitive Science.

## Background

Meenakshi Khosla is an Assistant Professor in the Department of Cognitive Science at the University of California, San Diego. Khosla’s research operates at the intersection of artificial intelligence and computational neuroscience, focusing on the development of data-driven models to analyze information processing in the human brain. They use deep neural networks and functional neuroimaging (fMRI) to characterize structured neural representations in the visual cortex, including the identification of food-selective neural populations. Their work also involves building interpretable machine learning tools for large-scale brain mapping across sensory and cognitive domains.

## Papers

### 2026 — Barycentric alignment for instance-level comparison of neural representations
*arXiv preprint*
Authors: Shreya Saha, Zoe Wanying He, Meenakshi Khosla

This work introduces a barycentric framework for representational alignment that explicitly quotients out nuisance symmetries, such as unit reordering and orthogonal transformations, to map neural activations into a universal embedding space. Unlike traditional set-level metrics (e.g., CKA or RSA) that aggregate similarity over entire stimulus distributions, this approach enables instance-level consistency measures to evaluate how individual stimuli cluster across model populations. The authors utilize this stimulus-specific analysis to identify input properties that predict representational convergence in vision and language models and to construct shared spaces for human cortical regions across individuals. The results demonstrate that post-hoc alignment of unimodal models can recover cross-modal semantic judgments comparable to contrastively trained vision-language systems.

### 2026 — Unbalanced Soft-Matching Distance For Neural Representational Comparison With Partial Unit Correspondence
*International Conference on Learning Representations (ICLR)*
Authors: Chaitanya Kapoor, Alex H Williams, Meenakshi Khosla

This paper presents an unbalanced soft-matching metric for comparing neural representations that accounts for partial unit correspondences and varying neuron counts between systems. By extending the soft-matching distance to a partial optimal transport setting, the authors relax strict mass conservation requirements, allowing certain units to remain unmatched. This provides a robust measure of alignment that avoids forced correspondences for low-quality or non-homologous features. The metric is shown to preserve correct matches under outlier noise in synthetic simulations and achieves higher alignment precision across homologous brain areas than standard soft-matching. This ability to partition units by match quality enables the identification of privileged representational axes within specific subpopulations of neurons.

### 2026 — Representational Alignment Across Model Layers and Brain Regions with Hierarchical Optimal Transport
*International Conference on Learning Representations (ICLR)*
Authors: Shaan Shah, Meenakshi Khosla

The authors propose Hierarchical Optimal Transport (HOT), a unified framework for the global alignment of high-dimensional representations in deep neural networks and biological systems. HOT jointly optimizes for soft, globally consistent layer-to-layer couplings and neuron-level transport plans, permitting representational mass from a source layer to be distributed across multiple target layers to handle architectural depth mismatches. This method produces a symmetric global alignment score and reveals smooth hierarchical correspondences across vision models, large language models, and human visual cortex recordings. By incorporating the global activation structure of the entire network, HOT provides more stable and interpretable comparisons than greedy or layer-independent matching techniques.

### 2025 — Bridging Critical Gaps in Convergent Learning: How Representational Alignment Evolves Across Layers, Training, and Distribution Shifts
*Advances in Neural Information Processing Systems (NeurIPS)*
Authors: Chaitanya Kapoor, Sudhanshu Srivastava, Meenakshi Khosla

This research presents a large-scale systematic audit of representational convergence across dozens of vision models, evaluating alignment through affine-invariant linear regression, rotation-invariant orthogonal Procrustes, and unit-order-invariant soft-matching. The study demonstrates that representational convergence is primarily driven by shared input statistics and architectural biases, with alignment crystallizing within the first training epoch prior to task-performance plateaus. Furthermore, while early layers maintain tight alignment across out-of-distribution (OOD) shifts, deeper layers diverge in proportion to the severity of the distribution shift. These findings elucidate the evolution of representational universality during task optimization and have significant implications for the design of brain-like artificial systems.

### 2025 — Modeling the language cortex with form-independent and enriched representations of sentence meaning reveals remarkable semantic abstractness
*arXiv preprint*
Authors: Shreya Saha, Shurui Li, Greta Tuckute, Yuanning Li, Ru-Yuan Zhang, Leila Wehbe, Evelina Fedorenko, Meenakshi Khosla

This research investigates the semantic abstractness of the human language system by modeling neural responses to sentences using cross-modal and form-independent representations. The authors utilize vision foundation models to extract embeddings from synthetic images generated from sentence prompts, demonstrating that aggregating these vision-based representations rival large language models (LLMs) in predicting language cortex activity. Enhancing neural predictivity through the use of multiple paraphrases and the enrichment of sentence prompts with implicit commonsense context further improves encoding performance. These findings suggest that the human language cortex maintains highly abstract, form-independent meaning representations that transcend specific sensory modalities or linguistic surface forms.
