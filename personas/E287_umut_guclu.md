---
name: Umut Güçlü
institution: Radboud University
department: Department of Artificial Intelligence
lab_name: Neural Coding Lab
main_research_area: NeuroAI and neural coding
total_citations: 5714
h_index: 33
---

# Umut Güçlü

*NeuroAI and neural coding* — Radboud University, Department of Artificial Intelligence, Neural Coding Lab.

## Background

Umut Güçlü is a Principal Investigator at the Donders Institute for Brain, Cognition and Behaviour, focusing on the integration of neuroscience and artificial intelligence. Güçlü’s research utilizes deep learning and in silico connectionism to develop computational frameworks for neural encoding and decoding, often referred to as 'brain reading' and 'brain writing.' They have worked on the reconstruction of perceived natural images from brain activity using generative adversarial networks and the characterization of feature complexity gradients in the human visual system. As an ELLIS Scholar, Güçlü’s work involves simulating and emulating in vivo neural computation to investigate the synergy between biological and machine intelligence.

## Papers

### 2025 — Neural encoding with affine feature response transforms
*arXiv*
Authors: Lynn Lê, Nils Kimman, Thirza Dado, Katja Seeliger, Paolo Papale, Antonio Lozano, Pieter Roelfsema, Marcel van Gerven, Yağmur Güçlütürk, Umut Güçlü

This study introduces Affine Feature Response Transforms (AFRT), a methodology designed to integrate neuroscientifically grounded spatial priors into linearizing encoding models that characterize the mapping from sensory stimuli to neural activity. Standard encoding frameworks often overlook the intrinsic retinotopic organization of the brain, which can compromise model efficiency and the biological interpretability of the learned feature mappings. AFRT addresses this by formalizing the feature response through affine transformations that respect the spatial topology of the cortex. When applied to high-dimensional neuroimaging datasets, AFRT demonstrates improved predictive performance for voxel-level responses and provides more coherent representations of receptive field characteristics, thereby enhancing the functional alignment between artificial feature spaces and biological neural hierarchies.

### 2025 — Inverse receptive field attention for naturalistic image reconstruction from the brain
*arXiv*
Authors: Lynn Lê, Thirza Dado, Katja Seeliger, Paolo Papale, Antonio Lozano, Pieter Roelfsema, Yağmur Güçlütürk, Marcel van Gerven, Umut Güçlü

This research presents a novel neural decoding paradigm for the high-fidelity reconstruction of naturalistic images and videos from functional magnetic resonance imaging (fMRI) data by leveraging the functional organization of neuronal receptive fields. The proposed Inverse Receptive Field Attention mechanism explicitly exploits spatial priors derived from retinotopic mapping to constrain the latent representations of image-to-image transformation networks. By integrating these spatial mappings into a generative modeling pipeline, the framework significantly improves the structural and semantic accuracy of visual reconstructions compared to baseline models. The approach demonstrates that incorporating biologically inspired spatial attention allows for the recovery of complex, dynamic visual experiences from large-scale, single-participant neuroimaging datasets with unprecedented detail.

### 2024 — MonkeySee: Space-time-resolved reconstructions of natural images from macaque multi-unit activity
*NeurIPS*
Authors: Lynn Le, Paolo Papale, Katja Seeliger, Antonio Lozano, Thirza Dado, Feng Wang, Pieter Roelfsema, Marcel van Gerven, Yağmur Güçlütürk, Umut Güçlü

This paper presents a convolutional neural network (CNN)-based decoder architecture designed to reconstruct naturalistic images from multi-unit activity (MUA) recorded via Utah arrays in macaque cortical areas V1, V4, and IT. The authors investigate the differentiation of neural readout characteristics across the visual hierarchy, demonstrating that the CNN-based technique effectively captures region-specific representations. A key contribution is the development of a space-time-resolved decoding framework that leverages the high temporal resolution of MUA to capture the dynamics of visual processing. Additionally, the introduction of a Learned Receptive Field (LRF) layer allows the model to dynamically organize neural inputs into 2D spatial representations during training, significantly enhancing both the fidelity of the reconstructions and the structural interpretability of the decoding process.

### 2024 — PAM: Predictive attention mechanism for neural decoding of visual perception
*bioRxiv*
Authors: Thirza Dado, Lynn Le, Marcel van Gerven, Yağmur Güçlütürk, Umut Güçlü

This work introduces Predictive Attention Mechanisms (PAMs), a novel task-driven architectural component for neural decoding that optimizes the integration of neural signals across the cortical hierarchy. Unlike standard self-attention mechanisms that compute input-input relationships, PAMs learn optimized 'output queries' during training that specifically target neural responses most relevant for reconstructing the latent features of generative models. This approach facilitates the dynamic allocation of attention across diverse brain regions based on their functional relevance to the reconstruction task. Validated on both macaque multi-unit activity and human fMRI datasets, PAM-enhanced decoders demonstrate superior performance in mapping brain activity to the latent spaces of generative adversarial networks and diffusion models, yielding high-precision reconstructions of perceived naturalistic stimuli.

### 2024 — Brain2GAN: Feature-disentangled neural encoding and decoding of visual perception in the primate brain
*PLOS Computational Biology*
Authors: Thirza Dado, Paolo Papale, Antonio Lozano, Lynn Le, Feng Wang, Marcel van Gerven, Pieter Roelfsema, Yağmur Güçlütürk, Umut Güçlü

This study characterizes the alignment between high-level neural representations in the macaque visual cortex and the feature-disentangled latent spaces of contemporary generative adversarial networks (GANs) and diffusion models. By analyzing multi-unit activity (MUA) recorded during a passive fixation task involving naturalistic images and faces, the authors compare the neural encoding efficacy of StyleGAN's z- and w-latents alongside language-contrastive CLIP representations. Mass univariate encoding analyses reveal that disentangled w-latent features significantly outperform conventional latents in predicting cortical responses, particularly in higher-level visual areas. Leveraging these feature-disentangled representations, the authors implement a multivariate decoding pipeline that achieves state-of-the-art spatiotemporal reconstructions of visual perception, underscoring the critical role of disentanglement in modeling biological visual processing.
