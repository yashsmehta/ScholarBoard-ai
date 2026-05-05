---
name: Iris Groen
institution: University of Amsterdam
department: Informatics Institute
lab_name: Video & Image Sense Lab (VIS Lab)
main_research_area: human vision and computational neuroscience
total_citations: 2290
h_index: 18
---

# Iris Groen

*human vision and computational neuroscience* — University of Amsterdam, Informatics Institute, Video & Image Sense Lab (VIS Lab).

## Background

Groen is an Associate Professor and MacGillavry Fellow at the University of Amsterdam’s Informatics Institute, specializing in the intersection of cognitive neuroscience and computer vision. Their research examines the neural representation of real-world scenes and videos by employing human brain imaging techniques, including fMRI, EEG, and ECoG, alongside deep neural networks. Groen investigates how the human brain processes natural image statistics and extracts action affordances from the environment to understand the principles of biological vision. Through this interdisciplinary approach, they aim to develop bio-inspired models of perception and align artificial intelligence with human neural processing.

## Papers

### 2026 — The Human Brain as a Dynamic Mixture of Expert Models in Video Understanding
*International Conference on Learning Representations (ICLR)*
Authors: Christina Sartzetaki, Anne W. Zonneveld, Pablo Oyarzo, Alessandro T. Gifford, Radoslaw M. Cichy, Pascal Mettes, Iris I. A. Groen

This research performs a large-scale benchmarking of model-brain alignment using over 100 static and temporally-integrative deep video architectures compared against dynamic electroencephalography (EEG) recordings of naturalistic video stimuli. We implement a novel Cross-Temporal Representational Similarity Analysis (CT-RSA) to evaluate the correspondence between time-unfolded model features and the millisecond-scale evolution of neural response patterns. Our analysis reveals a distinct shift in neural preference: posterior electrodes initially align with hierarchical static object representations before transitioning to mid-level, temporally-integrating action features that closely track the dynamic content of the video. In contrast, frontal electrodes exhibit alignment with high-level static action representations without fine-grained temporal correspondence. We conclude that the brain functions as a dynamic mixture of expert models, where state-space models and self-supervised pretraining offer superior alignment to intermediate temporal integration in the human visual system.

### 2025 — Representation of locomotive action affordances in human behavior, brains, and deep neural networks
*Proceedings of the National Academy of Sciences (PNAS)*
Authors: Clemens G. Bartnik, Christina Sartzetaki, Abel Puigseslloses Sanchez, Elijah Molenkamp, Steven Bommer, Nikolina Vukšić, Iris I. A. Groen

This study characterizes the neural basis of locomotive action affordance perception (e.g., walking, climbing, or swimming) by comparing human behavioral annotations, multi-voxel fMRI responses, and deep neural network (DNN) activations to diverse real-world scenes. We demonstrate that the human visual cortex, specifically within scene-selective regions, represents locomotive affordances as a unique representational space that is distinct from low-level image properties, object content, or global scene categories. Representational Similarity Analysis (RSA) of fMRI patterns shows that these affordance representations emerge independently of the observer's task. We find that while standard DNNs trained on object or scene classification capture some behavioral variance, they generally fail to align with the specialized neural representations of locomotive affordances. These results identify a novel class of ecological representations in the human brain dedicated to identifying action possibilities within the environment.

### 2025 — One Hundred Neural Networks and Brains Watching Videos: Lessons from Alignment
*International Conference on Learning Representations (ICLR)*
Authors: Christina Sartzetaki, Gemma Roig, Cees G. M. Snoek, Iris I. A. Groen

We present the first large-scale benchmarking of 99 deep video models to assess their representational alignment with human brain activity recorded via fMRI during naturalistic video viewing. We systematically disentangle four factors—temporal modeling, classification task, architecture (CNN vs. Transformer), and training dataset—to determine their impact on brain scoring across multiple regions of interest (ROIs). Our results show that temporal modeling is critical for alignment to early visual areas, while optimization for action-recognition task spaces is essential for alignment to high-level cortical regions. We identify significant differences in layer-wise alignment patterns between CNNs and Transformers and observe a negative correlation between computational complexity (FLOPs) and alignment in semantic-processing regions, suggesting that more efficient models may better approximate the human visual system's representations.

### 2025 — BrainACTIV: Identifying visuo-semantic properties driving cortical selectivity using diffusion-based image manipulation
*International Conference on Learning Representations (ICLR)*
Authors: Diego García Cerdas, Christina Sartzetaki, Magnus Petersen, Gemma Roig, Pascal Mettes, Iris I. A. Groen

We introduce Brain Activation Control Through Image Variation (BrainACTIV), a framework that leverages pretrained diffusion models to manipulate reference images to maximize or minimize activity in target human cortical regions. Unlike standard brain-optimized image synthesis methods that generate isolated samples, BrainACTIV produces controlled image variations that allow for fine-grained identification of the visuo-semantic properties driving selective neural responses. We demonstrate that this method effectively modulates predicted fMRI responses and aligns with established category preferences in specialized ROIs (e.g., faces, bodies, and places) while maintaining structural similarity to the original image. Furthermore, we show how BrainACTIV can accentuate subtle representational differences between regions selective for the same category, offering a robust tool for hypothesis-driven neuroscientific stimulus generation.

### 2024 — Temporal dynamics of short-term neural adaptation across human visual cortex
*PLoS Computational Biology*
Authors: Amber Marijn Brands, Sasha Devore, Orrin Devinsky, Werner Doyle, Adeen Flinker, Daniel Friedman, Patricia Dugan, Jonathan Winawer, Iris I. A. Groen

Using time-varying intracranial electroencephalography (iEEG), we investigate how neural adaptation patterns vary across the human visual hierarchy in response to naturalistic image categories with varying durations and repetition intervals. We identify two distinct signatures of short-term adaptation: response decay to sustained stimuli and repetition suppression. We find that higher visual areas in the ventral- and lateral-occipitotemporal cortex exhibit significantly slower adaptation and recovery dynamics compared to early visual areas (V1-V3). To account for these hierarchical differences, we implement an augmented delayed divisive normalization (DN) model with category-dependent input scaling. The model successfully predicts neural response time courses across the hierarchy, suggesting that area-specific normalization dynamics and category selectivity are the primary computational drivers of temporal adaptation in the human visual system.
