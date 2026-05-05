---
name: Talia Konkle
institution: Harvard University
department: Department of Psychology and Center for Brain Science
lab_name: Cognitive and Neural Organization Lab
main_research_area: cognitive and neural organization of vision
total_citations: 9579
h_index: 37
---

# Talia Konkle

*cognitive and neural organization of vision* — Harvard University, Department of Psychology and Center for Brain Science, Cognitive and Neural Organization Lab.

## Background

Talia Konkle is a Professor of Psychology at Harvard University and an associate faculty member at the Kempner Institute, specializing in the functional architecture of the human visual system. Konkle’s research uses behavioral psychophysics, functional MRI, and computational modeling to map the representational geometry of high-level visual experiences onto the cortical surface. Their work investigates the large-scale topographic organization of object knowledge, specifically the roles of real-world size and animacy in shaping neural responses. Konkle also bridges biological and artificial intelligence by using deep neural networks to study the computational pressures that drive representation learning and cortical specialization.

## Papers

### 2025 — Archetypal SAE: Adaptive and Stable Dictionary Learning for Concept Extraction in Large Vision Models
*International Conference on Machine Learning (ICML)*
Authors: Thomas Fel, Ekdeep Singh Lubana, Jacob S. Prince, Matthew Kowal, Victor Boutin, Isabel Papadimitriou, Binxu Wang, Martin Wattenberg, Demba E. Ba, Talia Konkle

This study addresses the inherent instability in Sparse Autoencoders (SAEs) used for mechanistic interpretability, where stochastic training factors frequently result in inconsistent dictionary atoms. The authors propose Archetypal SAEs (A-SAE), a framework that constrains dictionary elements to reside within the convex hull of the activation data, thereby anchoring the learned features to the empirical distribution. This geometric constraint significantly enhances both the stability and semantic plausibility of extracted concepts. Evaluations utilizing novel metrics for identifiability and plausibility across diverse vision backbones demonstrate that a relaxed variant (RA-SAE) preserves state-of-the-art reconstruction fidelity while uncovering more robust and interpretable feature sets in large-scale vision models.

### 2024 — A large-scale examination of inductive biases shaping high-level visual representation in brains and machines
*Nature Communications*
Authors: Colin Conwell, Jacob S. Prince, Kendrick N. Kay, George A. Alvarez, Talia Konkle

In an extensive computational benchmarking effort involving over 1.8 billion regressions and 50,000 representational similarity analyses, this research evaluates how various model architectures and training objectives influence alignment with the human visual system. By comparing 224 diverse deep neural networks, including CNNs and Vision Transformers, against large-scale fMRI data from the Natural Scenes Dataset, the authors find that qualitatively distinct architectures and task objectives (e.g., contrastive vision vs. vision-language alignment) achieve surprisingly similar levels of brain predictivity when other parameters are controlled. These findings suggest that the emergent representational geometry of high-level visual cortex is shaped more by the broad statistics of natural image diets than by specific architectural constraints or downstream task demands.

### 2024 — Contrastive learning explains the emergence and function of visual category-selective regions
*Science Advances*
Authors: Jacob S. Prince, George A. Alvarez, Talia Konkle

This work reconciles modular and distributed coding accounts of human ventral stream organization using a contrastive self-supervised learning framework. The authors demonstrate that training deep convolutional neural networks with instance-level contrastive objectives on natural image datasets leads to the spontaneous emergence of units selective for faces, bodies, scenes, and words, even in the absence of explicit category supervision. Using a novel sparse positive encoding procedure, they show that these emergent model units accurately predict neural responses in corresponding category-selective regions (e.g., FFA, PPA, EBA). Furthermore, virtual lesions to these model units result in specific, dissociable deficits in categorization performance, providing a computational account of how domain-general contrastive pressures drive functional specialization in the primate visual system.

### 2024 — Immersive scene representation in human visual cortex with ultra-wide angle neuroimaging
*Nature Communications*
Authors: Jeongho Park, Edward Soucy, Jennifer Segawa, Ross Mair, Talia Konkle

Traditional fMRI studies typically present visual stimuli within the central 10-15° of the visual field, failing to capture the panoramic 220° experience of natural vision. This study employs a custom-engineered ultra-wide angle display system capable of a 175° unobstructed view to investigate cortical representation under immersive conditions. Results indicate that scene-selective regions (PPA, RSC/MPA, and OPA) maintain their category preferences and spatial tuning even when central vision is occluded by an artificial scotoma, whereas face-selective regions (FFA) show distinct modulation patterns. The findings provide evidence that high-level scene areas are not merely driven by foveal biases but are fundamentally organized to integrate peripheral information for immersive environmental representation.

### 2024 — Manipulating dropout reveals an optimal balance of efficiency and robustness in biological and machine visual systems
*International Conference on Learning Representations (ICLR)*
Authors: Jacob S. Prince, Gabriel Fajardo, George A. Alvarez, Talia Konkle

Applying the efficient coding hypothesis to the human visual hierarchy, the researchers investigate the tradeoff between high-dimensional informational efficiency and representational robustness. By parametrically varying the dropout rate (p) during the training of object recognition models, they systematically manipulate the dimensionality and correlation structure (eigenspectrum) of internal representations. They find that an intermediate dropout level (approx. 70%) optimizes robustness to simulated neural lesions and generalization. Crucially, comparisons with high-resolution 7T fMRI data from the Natural Scenes Dataset reveal that models at this optimal robustness point also exhibit the highest representational alignment with human occipitotemporal cortex, suggesting that biological vision is constrained by similar pressures toward low-dimensional, robust feature spaces.
