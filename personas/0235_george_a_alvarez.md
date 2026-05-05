---
name: George A. Alvarez
institution: Harvard University
department: Department of Psychology
lab_name: Vision Sciences Laboratory
main_research_area: Biological and artificial vision
total_citations: 19388
h_index: 60
---

# George A. Alvarez

*Biological and artificial vision* — Harvard University, Department of Psychology, Vision Sciences Laboratory.

## Background

George A. Alvarez is the Fred Kavli Professor of Neuroscience in the Department of Psychology at Harvard University and a visiting scholar at the Kempner Institute. Alvarez’s research investigates the computational constraints of the human visual system, with a focus on the mechanisms of attentional selection, visual working memory, and resource allocation. They employ a methodology that combines human psychophysics and neuroimaging with deep neural network (DNN) modeling to study how the brain processes visual information. Recent work by Alvarez focuses on the alignment between biological and artificial intelligence, using deep learning frameworks to model perceptual phenomena such as lightness illusions and contour integration.

## Papers

### 2025 — Bi-Orthogonal Factor Decomposition for Vision Transformers
*39th AAAI Conference on Artificial Intelligence (AAAI-25)*
Authors: Fenil R. Doshi, Thomas Fel, Talia Konkle, George A. Alvarez

The authors propose Bi-orthogonal Factor Decomposition (BFD), a diagnostic framework for analyzing information exchange in Vision Transformers (ViTs) by disentangling token activations into orthogonal positional and content factors. By applying ANOVA-based statistical decomposition followed by Singular Value Decomposition (SVD) of the query-key interaction matrix, they uncover bi-orthogonal modes that mediate communication between tokens. Their results demonstrate that self-attention energy is primarily driven by content-content interactions, with heads specializing into distinct content-content, content-position, and position-position operators. The analysis further identifies that the superior holistic shape processing of self-supervised models like DINOv2 is attributed to intermediate-layer mechanisms that simultaneously preserve positional structure and enrich semantic content through long-range contextual interactions.

### 2025 — A feedforward mechanism for human-like contour integration
*PLOS Computational Biology*
Authors: Fenil R. Doshi, Talia Konkle, George A. Alvarez

This study challenges the necessity of recurrent and top-down feedback for perceptual organization by demonstrating that purely feedforward deep convolutional neural networks (DCNNs) can emulate human-like contour integration. The authors show that ImageNet-pretrained architectures like Alexnet, when fine-tuned on contour detection tasks, replicate human psychophysical signatures including gestalt 'good continuation' and uncrowding effects. The research identifies two critical inductive biases supporting this capacity: a gradual progression of receptive field sizes across the model hierarchy and a learned sensitivity bias for gradually curved contours (~20°). These findings provide a computational existence proof that feedforward hierarchical processing is sufficient to implement complex mechanisms of perceptual grouping and organization.

### 2025 — Visual Anagrams Reveal Hidden Differences in Holistic Shape Processing Across Vision Models
*Advances in Neural Information Processing Systems (NeurIPS 2025)*
Authors: Fenil R. Doshi, Thomas Fel, Talia Konkle, George A. Alvarez

The authors introduce 'Visual Anagrams,' a diagnostic benchmark consisting of object pairs that share identical local part statistics but differ in their global configural arrangements. They develop the Configural Shape Score (CSS) to quantify this holistic shape sensitivity across 86 pretrained vision models, finding that ImageNet accuracy and standard shape-vs-texture bias do not fully account for configural competence. Through attention ablation and representational similarity analysis, the study reveals that high-CSS models, such as self-supervised and language-aligned Vision Transformers, leverage long-range contextual interactions in middle-to-late layers to integrate local features into compositional shape representations. The results suggest that robust, human-like vision requires architectural frameworks that integrate local texture with global configural cues.

### 2025 — Understanding Inhibition Through Maximally Tense Images
*39th AAAI Conference on Artificial Intelligence (AAAI-25)*
Authors: Chris Hamblin, Srijani Saha, Talia Konkle, George A. Alvarez

This research explores the functional role of feature inhibition in neural network vision models, investigating how these systems ensure images do not express specific features despite the inherent asymmetry of ReLU activation functions. The authors propose probing these mechanisms using 'maximally tense images' (MTIs)—stimuli designed to simultaneously drive high levels of excitation and inhibition for a target feature. They introduce two interpretability techniques: +/- attribution inversions, which decompose images into excitatory and inhibitory components, and the attribution atlas, which characterizes the global manifold of inhibitory responses. The study further examines the challenges posed by feature superposition, demonstrating how interfering features can produce attribution patterns that mimic inhibitory motifs.

### 2024 — Feature Accentuation: Revealing 'What' Features Respond to in Natural Images
*arXiv preprint*
Authors: Christopher Hamblin, Thomas Fel, Srijani Saha, Talia Konkle, George A. Alvarez

The authors introduce 'feature accentuation,' a post-hoc interpretability method for visualizing the spatial and semantic drivers of neural unit responses in complex natural images. Unlike traditional feature visualization that generates synthetic patterns from noise, feature accentuation applies gradient-based optimization to natural image seeds to emphasize the specific attributes (e.g., textures, object parts) that drive a unit's activation. This approach generates naturalistic visualizations that localize relevant features and provide a high-resolution tool for assessing model-brain alignment. The method is used to synthesize targeted stimulus sets that systematically vary along model-specific encoding axes, enabling a more stringent test of the computational features driving neural responses in biological vision systems.
