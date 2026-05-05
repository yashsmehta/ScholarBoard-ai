---
name: Thomas Naselaris
institution: University of Minnesota
department: Department of Neuroscience
lab_name: Naselaris Lab
main_research_area: computational neuroscience
total_citations: 10140
h_index: 29
---

# Thomas Naselaris

*computational neuroscience* — University of Minnesota, Department of Neuroscience, Naselaris Lab.

## Background

Thomas Naselaris is an Associate Professor in the Department of Neuroscience at the University of Minnesota and a member of the Medical Discovery Team on Optical Imaging and Brain Science. Naselaris's research focuses on the generative capabilities of the human visual system, employing high-field fMRI and voxel-wise encoding models to investigate how the brain represents natural scenes and mental imagery. They have developed mathematical frameworks for reconstructing visual experiences from human brain activity through neural decoding. Currently, Naselaris's work integrates deep learning with functional neuroimaging to examine the transformations between perceptual and mnemonic representations in the visual cortex.

## Papers

### 2025 — Variation in the geometry of concept manifolds across human visual cortex
*PLOS Computational Biology*
Authors: Ghislain St-Yves, Kendrick Kay, Thomas Naselaris

The efficacy of linear read-outs from high-level visual cortex in classifying visual concepts depends on the representational geometry of concept manifolds—the sets of neural activity patterns encoding varied exemplars of a specific category. This study utilizes ultra-high-field 7T fMRI data from the Natural Scenes Dataset (NSD) and a brain-optimized deep neural network (GNet) to quantify how manifold geometry evolves across the cortical hierarchy. We show that improvements in few-shot linear classification accuracy in the brain are predominantly driven by increases in 'geometric signal' (the distance between manifold centers), rather than changes in manifold dimensionality or overlap. In contrast, classification improvements in deep neural network layers are driven by increases in effective manifold dimensionality. Our results reveal that the human visual cortex and task-optimized artificial networks employ divergent geometric strategies to achieve conceptual disentanglement, despite operating under similar computational constraints.

### 2025 — A transformation from vision to imagery in the human brain
*bioRxiv*
Authors: Tiasha Saha Roy, Jesse Breedlove, Ghislain St-Yves, Kendrick Kay, Thomas Naselaris

While it is established that mental imagery reactivates the visual cortex, the precise relationship between activity patterns during perception and imagery remains debated. We introduce the concept of an 'imagery transformation'—a linear mapping that relates visual activity patterns to mental imagery patterns for the same stimuli. Analyzing 7T fMRI data across two independent datasets, we demonstrate that imagery is not merely 'weak vision' or a simple rescaling of perceptual activity. In early visual areas (V1-V3), imagery transformations involve a significant reduction in neural dimensionality and a reorientation of the representational subspace, with imagery dimensions explaining only 25–50% of visual variance. Conversely, in high-level visual areas, the transformation approximates an identity function, suggesting a transition from pure reactivation in higher stages to a more complex, lossy compression in earlier stages of the visual hierarchy.

### 2025 — NSD-Imagery: A Benchmark Dataset for Extending fMRI Vision Decoding Methods to Mental Imagery
*Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)*
Authors: Reese Kneeland, Paul S. Scotti, Ghislain St-Yves, Jesse L. Breedlove, Kendrick N. Kay, Thomas Naselaris

We present NSD-Imagery, a high-resolution 7T fMRI benchmark dataset extending the Natural Scenes Dataset (NSD) to include neural responses during mental imagery of both simple geometric patterns and complex natural scenes. We evaluate a suite of state-of-the-art vision decoding models (including MindEye1, MindEye2, and Brain Diffuser) on their ability to generalize from seen images to internally generated mental images. Our results demonstrate that decoding performance on mental imagery is largely decoupled from seen-image reconstruction performance. Specifically, models utilizing simple linear decoding architectures and multimodal feature alignment generalize more robustly to mental imagery, whereas complex architectures tend to overfit the visual training distribution. These findings provide a critical resource for developing brain-computer interfaces intended for clinical applications where visual information is internally generated.

### 2024 — fMRI vision reconstruction methods robustly generalize to mental imagery
*Conference on Cognitive Computational Neuroscience (CCN)*
Authors: Reese Kneeland, Ghislain St-Yves, Jesse Breedlove, Kendrick Kay, Thomas Naselaris

Recent breakthroughs in generative AI and large-scale neuroimaging datasets have enabled high-fidelity reconstruction of seen images from human fMRI activity. However, the extension of these methods to mental imagery remains a primary challenge for clinical brain-computer interfaces. We evaluate several leading vision decoding frameworks on fMRI activity measured while subjects imagined previously memorized stimuli. We demonstrate that these models generalize robustly to mental imagery, producing reconstructions that are consistently identified by naive human raters in forced-choice tasks. Quantitative analysis reveals that reconstruction quality is more dependent on the alignment between the training and test image distributions than on stimulus complexity. Notably, reconstructions of imagined natural scenes were identified with higher accuracy than reconstructions of much simpler perceived geometric stimuli, highlighting the role of naturalistic priors in current decoding methodologies.
