---
name: Frank Tong
institution: Vanderbilt University
department: Department of Psychology
lab_name: Tong Lab
main_research_area: Neural bases of visual perception
total_citations: 15788
h_index: 45
---

# Frank Tong

*Neural bases of visual perception* — Vanderbilt University, Department of Psychology, Tong Lab.

## Background

Frank Tong investigates the neural foundations of visual perception, attentional selection, and object recognition using high-resolution 7-Tesla fMRI, visual psychophysics, and computational modeling. Tong applied multivariate pattern classification to decode subjective mental states and the contents of visual working memory from early cortical activity. Their research examines how early visual areas contribute to conscious awareness and the maintenance of information in the absence of physical stimuli. Currently, Tong compares biological perception with convolutional neural networks to model visual processing and robustness.

## Papers

### 2025 — Emergence of form-independent direction selectivity in human V3A and MT+
*Journal of Vision*
Authors: Sang Wook Hong, Frank Tong

This fMRI study investigated the neural progression from form-dependent to form-invariant motion representations in the human visual hierarchy. Utilizing multivariate pattern analysis (MVPA) and linear decoding, the researchers examined direction-selective activity for two distinct motion types: drifting sinusoidal gratings and random dots. While early visual areas (V1, V2) exhibited robust direction selectivity for each stimulus individually, they failed to generalize across motion types, indicating that their responses are primarily driven by local orientation-motion contingencies. In contrast, higher-order dorsal areas V3A and MT+ demonstrated significant cross-stimulus generalization for both linear and spiral motion trajectories. These findings reveal that form-invariant motion selectivity, essential for overcoming the aperture problem and achieving robust motion perception, emerges predominantly in specialized regions of the dorsal stream.

### 2025 — Category-specific perceptual learning of robust object recognition modelled using deep neural networks
*PLOS Computational Biology*
Authors: Hojin Jang, Frank Tong

This study examines the computational and behavioral underpinnings of noise robustness in object recognition through the lens of perceptual learning. Human participants and convolutional neural networks (CNNs) were trained to identify objects from animate and inanimate categories embedded in varying levels of Gaussian noise. Behavioral results indicated that humans acquire category-specific improvements in robustness, whereas standard pre-trained CNNs initially displayed more category-general gains. However, when CNN models were pre-tuned to match human-level baseline accuracy, they replicated the human pattern of category-specific refinement. A layer-wise susceptibility analysis using Pearson correlation metrics showed that category-general robustness to signal-to-noise ratio (SSNR) fluctuations emerged in early layers, while category-specific enhancements were localized in deeper layers, suggesting a hierarchical organization of learned robustness.

### 2024 — Convolutional neural network models applied to neuronal responses in macaque V1 reveal limited nonlinear processing
*Journal of Vision*
Authors: Hui-Yuan Miao, Frank Tong

The research re-evaluates the prevailing view that deep, multi-layered nonlinear computations are necessary to predict the complex response properties of macaque V1 neurons. By systematically comparing standard CNN architectures (e.g., VGG-19) with simpler models, the authors discovered that the high predictive performance of deeper layers often results from non-computational factors, specifically the scaling of input image dimensions relative to unit receptive field sizes. When controlling for these variables, a modified version of AlexNet featuring significantly fewer nonlinear stages was found to be sufficient to account for V1 activity. Further analysis using Gabor pyramid models and tests for contrast saturation and normalization confirmed that relatively shallow hierarchical processing can effectively model V1 responses, indicating that the perceived necessity for deep nonlinear models in primary visual cortex may be overstated.

### 2024 — Improved modeling of human vision by incorporating robustness to blur in convolutional neural networks
*Nature Communications*
Authors: Hojin Jang, Frank Tong

Standard convolutional neural networks (CNNs) exhibit severe vulnerability to image blur, a phenomenon pervasive in natural human vision due to peripheral resolution limits and optical defocus. This paper demonstrates that incorporating a 'developmental diet' of blurry images during training—or providing specific blur-augmentation—results in CNN models that are significantly more aligned with human behavioral and neural data. Blur-trained networks demonstrated superior performance in predicting fMRI representational similarity matrices (RSM) across the visual hierarchy (V1 through VOT) and exhibited a robust shape bias, contrasting with the texture-bias of standard models. These results suggest that the pervasive blur encountered during biological development acts as a critical constraint that encourages the learning of more generalized, robust, and human-like visual representations.

### 2024 — Evidence of strong amodal completion in both early and high-level visual cortices
*bioRxiv*
Authors: David D. Coggan, Frank Tong

Amodal completion allows the visual system to represent the complete geometry of objects despite partial occlusion, but the cortical locus of these completed features remains contentious. Using high-resolution fMRI and multivoxel activity pattern analysis, this study mapped the representation of occluded object parts in human observers. The data revealed that information concerning the shape of occluded regions is decodable as early as V1, as well as in intermediate areas V2, V3, and V4, and high-level object-selective regions (LO, pFs). The finding of completion-related signals in primary visual cortex supports the hypothesis that amodal completion involves an active, feedback-driven reconstruction of missing features at early retinotopic sites, rather than being solely a result of high-level semantic or symbolic inference.
