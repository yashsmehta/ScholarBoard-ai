---
name: Rufin VanRullen
institution: CNRS
department: Centre de Recherche Cerveau et Cognition (CerCo)
lab_name: Neuro.AI
main_research_area: computational neuroscience and visual perception
total_citations: 21149
h_index: 68
---

# Rufin VanRullen

*computational neuroscience and visual perception* — CNRS, Centre de Recherche Cerveau et Cognition (CerCo), Neuro.AI.

## Background

Rufin VanRullen is a CNRS Research Director at the Centre de Recherche Cerveau et Cognition (CerCo) whose work spans computational neuroscience and artificial intelligence. VanRullen investigates the rhythmic nature of human vision, specifically examining how alpha and theta brain oscillations produce discrete "perceptual cycles" in attention and perception. Their current research, supported by an ERC Advanced Grant, focuses on developing brain-inspired AI architectures that incorporate the Global Workspace Theory and predictive coding principles. By combining psychophysical experiments with deep learning and EEG analysis, VanRullen seeks to characterize the neural dynamics that enable flexible and robust cognition.

## Papers

### 2026 — An Attention Mechanism for Robust Multimodal Integration in a Global Workspace Architecture
*arXiv*
Authors: Roland Bertin-Johannet, Lara Scipio, Léopold Maytié, Rufin VanRullen

Drawing on Global Workspace Theory (GWT) from cognitive neuroscience, this work introduces a top-down attention mechanism designed to select and integrate relevant modalities within a shared amodal workspace. The architecture addresses the bottleneck of flexible multimodal fusion by employing an attentional spotlight to prioritize specific input streams. Benchmarking on the Simple Shapes and MM-IMDb 1.0 datasets demonstrates that the inclusion of this attention mechanism significantly enhances robustness against modality-specific noise and corruptions. Additionally, the model exhibits robust cross-task and cross-modality generalization, positioning the workspace-based selector as a competitive alternative to contemporary multimodal attention frameworks while maintaining biological plausibility.

### 2025 — Modality-Agnostic Decoding of Vision and Language from fMRI
*arXiv*
Authors: Mitja Nikolaus, Milad Mozafari, Isabelle Berry, Rufin VanRullen

This study investigates the existence of modality-invariant neural representations by training modality-agnostic decoders to predict stimulus identity from functional Magnetic Resonance Imaging (fMRI) signals. Using a novel large-scale dataset, SemReps-8K, which captures brain activity during image viewing, reading of text descriptions, and mental imagery, the authors demonstrate that visual concepts can be decoded regardless of the presentation modality. Searchlight analyses identify expansive cortical regions that support these amodal representations, suggesting that the human brain utilizes generalized semantic codes to integrate information across disparate sensory inputs and internal cognitive states.

### 2025 — Evidence for compositionality in fMRI visual representations via Brain Algebra
*Communications Biology*
Authors: Matteo Ferrante, Tommaso Boccato, Nicola Toschi, Rufin VanRullen

This research explores the compositional nature of neural encoding through 'Brain Algebra,' a method of perturbing fMRI patterns to reflect conceptual modifications. By applying semantic vector perturbations (e.g., adding 'winter' or 'night' attributes) to baseline neural patterns and reconstructing the resulting images via generative latent diffusion models, the authors show that the brain's representational space supports systematic, algebraic combinations of concepts. The decoded outputs demonstrate predictable and meaningful perceptual shifts, such as modifying a scene's season or lighting while preserving core structural features. These results provide empirical support for an algebraic-like process governing the composition of abstract visual features in human cortical representations.

### 2025 — Enhancing deep neural networks through complex-valued representations and Kuramoto synchronization dynamics
*arXiv*
Authors: Sabine Muzellec, Andrea Alamia, Thomas Serre, Rufin VanRullen

Motivated by the biological solution to the binding problem, this paper proposes 'KomplexNet,' a hierarchical convolutional architecture that utilizes complex-valued units and Kuramoto synchronization dynamics to facilitate object-centric representation. By leveraging angular phases to group features belonging to the same object, the model implements both feedforward and recurrent feedback mechanisms to induce phase alignment. Experimental evaluations on multi-object categorization tasks, including overlapping digits and noisy image datasets, reveal that phase-based synchrony significantly improves classification accuracy and robustness to Gaussian noise. The findings suggest that incorporating synchronization dynamics into artificial neural networks enhances their capacity for structured scene decomposition and out-of-distribution generalization.

### 2024 — Semi-Supervised Multimodal Representation Learning Through a Global Workspace
*IEEE Transactions on Neural Networks and Learning Systems*
Authors: Benjamin Devillers, Léopold Maytié, Rufin VanRullen

This work evaluates a neural architecture inspired by the 'Global Workspace' (GW) for semi-supervised multimodal learning, aiming for more frugal and human-like knowledge acquisition. The system utilizes specialized, frozen unimodal encoders and decoders linked through a central latent workspace, with training driven by a self-supervised cycle-consistency objective. Across various vision-language pairings and datasets, the GW architecture successfully aligns disparate modalities with four to seven times less matched training data than standard supervised approaches. The resulting amodal representation proves highly effective for downstream classification, cross-modal retrieval, and robust transfer learning, demonstrating the functional utility of cognitively-inspired architectural bottlenecks.
