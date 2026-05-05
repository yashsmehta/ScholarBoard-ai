---
name: Nikolaus Kriegeskorte
institution: Columbia University
department: Departments of Psychology and Neuroscience
lab_name: Visual Inference Lab
main_research_area: cognitive computational neuroscience
total_citations: 37091
h_index: 72
---

# Nikolaus Kriegeskorte

*cognitive computational neuroscience* — Columbia University, Departments of Psychology and Neuroscience, Visual Inference Lab.

## Background

Nikolaus Kriegeskorte is a Professor of Psychology and Neuroscience at Columbia University and the Director of Cognitive Imaging at the Zuckerman Mind Brain Behavior Institute. Kriegeskorte specializes in cognitive computational neuroscience, developing deep neural network models that simulate the human visual system's ability to recognize objects and scenes. They developed Representational Similarity Analysis (RSA), a methodology that characterizes neural representations through their geometry to facilitate comparisons between brain activity, behavior, and computational models. Their current research focuses on integrating feedforward and recurrent processing in brain-inspired AI to investigate the inferential nature of biological vision.

## Papers

### 2025 — Transformer brain encoders explain human high-level visual responses
*arXiv*
Authors: Hossein Adeli, Sun Minni, Nikolaus Kriegeskorte

Traditional linear encoding models frequently fail to account for the complex spatial and feature-routing properties inherent in high-level cortical visual processing. This research investigates how the attention mechanism from transformer architectures can model the dynamic routing of retinotopic visual features to category-selective brain regions. The authors propose the Transformer Brain Encoder (TBEn), an encoder-decoder framework utilizing a frozen vision transformer backbone and learnable ROI-specific queries. These queries aggregate information through cross-attention to predict fMRI responses during natural scene viewing. TBEn significantly outperforms alternative factored encoding methods in predictive accuracy across various datasets and modalities. Furthermore, the model offers intrinsic interpretability by visualizing the attention-routing signals that drive specific categorical regions, suggesting a mechanistic account of how the human brain routes visual content based on relevance.

### 2025 — In Silico Mapping of Visual Categorical Selectivity Across the Whole Brain
*Advances in Neural Information Processing Systems (NeurIPS)*
Authors: Ethan Hwang, Hossein Adeli, Wenxuan Guo, Andrew Luo, Nikolaus Kriegeskorte

Elucidating the functional specialization of the human cortex often requires experimenter-defined hypotheses, which may overlook novel selectivities. This paper presents an in silico framework for the data-driven discovery of visual categorical selectivity across the entire brain. The methodology utilizes an encoder-decoder transformer featuring a brain-region-to-image-feature cross-attention mechanism to nonlinearly map deep network features to fMRI activation patterns. By pairing this brain encoder with diffusion-based generative models and large-scale datasets (ImageNet, BrainDIVE), the researchers synthesize optimal stimuli that maximize activation within specific cortical parcels. The approach reveals regions with complex compositional selectivity for diverse semantic concepts, validated through rigorous in silico statistical testing on held-out data. This pipeline enables the generation of novel, data-driven hypotheses about functional selectivity to be subsequently tested in empirical fMRI studies.

### 2025 — When do measured representational distances reflect the neural representational geometry?
*eLife*
Authors: Veronica Bossio Botero, Nikolaus Kriegeskorte

The fidelity of representational distances estimated from sparse (neural recordings) or pooled (fMRI voxels) measurements to the ground-truth neural representational geometry is a fundamental concern in systems neuroscience. Using theoretical analysis and simulations, the authors demonstrate that while random sampling of individual neurons yields undistorted distances, measurement channels that average across neurons with non-negative weights introduce linear distortions. These distortions overweight the population-mean dimension and attenuate signal dimensions orthogonal to it. Crucially, the study proves that removing the pattern mean from measured responses recovers the ground-truth representational geometry exactly in expectation. These results provide a formal justification for the use of correlation distance in representational similarity analysis and emphasize mean-centering as a vital step for accurately relating neural data to computational models.

### 2025 — Collective inference of the truth of propositions from crowd probability judgments
*arXiv*
Authors: Patrick Stinson, Jasper van den Bosch, Trenton Jerde, Nikolaus Kriegeskorte

Aggregating human probability judgments offers a pathway to collective intelligence, yet is hindered by individual miscalibration and cognitive biases. This study investigates the inference of objective truth from a collection of graded confidence ratings using data from 376 participants judging 1,200 general-knowledge claims. The authors introduce unsupervised and supervised probabilistic models that jointly estimate the truth of propositions and individual subject parameters for accuracy and miscalibration. Findings demonstrate that accounting for individual calibration significantly enhances the accuracy of collective inference compared to simple majority voting or uncalibrated averaging. This computational framework provides a robust method for online communities and collaborators to pool distributed intelligence with a well-calibrated sense of uncertainty, potentially facilitating the identification of reliable information in social networks.

### 2024 — The Topology and Geometry of Neural Representations
*Proceedings of the National Academy of Sciences (PNAS)*
Authors: Baihan Lin, Nikolaus Kriegeskorte

Characterizing brain representations requires descriptions that distinguish functional regions while remaining robust to idiosyncratic noise and neuroanatomical differences. This paper proposes topological representational similarity analysis (tRSA), an extension of traditional RSA that moves beyond geometric descriptions (RDMs) to characterize the topology of neural population codes. Using summary statistics derived from persistent homology, tRSA captures how activity patterns 'hang together' at an intermediate scale, reflecting the underlying manifold structure. Evaluation using fMRI data and artificial neural network simulations shows that topological signatures are more invariant across individuals than geometric signatures while maintaining high sensitivity to the computational function of cortical regions and network layers. This framework enables researchers to calibrate comparisons between brains and models to be sensitive to geometry, topology, or a combination of both.
