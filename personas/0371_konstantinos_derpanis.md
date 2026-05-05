---
name: Konstantinos Derpanis
institution: York University
department: Department of Electrical Engineering and Computer Science
lab_name: Computational Vision and Imaging Lab
main_research_area: Computer vision and motion analysis
total_citations: 8847
h_index: 42
---

# Konstantinos Derpanis

*Computer vision and motion analysis* — York University, Department of Electrical Engineering and Computer Science, Computational Vision and Imaging Lab.

## Background

Konstantinos G. Derpanis is an Associate Professor at York University and a Faculty Affiliate at the Vector Institute, focusing on computer vision, human motion understanding, and temporal sequence analysis. Their research applies deep learning and probabilistic modeling to 3D human pose estimation, motion segmentation, and point tracking through occlusions. This work connects computational vision and vision science by using neural network architectures to model human lightness and illusion perception. Derpanis also conducts research on spatio-temporal representations and weakly supervised learning for sequence alignment in video datasets.

## Papers

### 2025 — Universal Sparse Autoencoders: Interpretable Cross-Model Concept Alignment
*International Conference on Machine Learning (ICML)*
Authors: Harrish Thasarathan, Julian Forsyth, Thomas Fel, Matthew Kowal, Konstantinos G. Derpanis

The authors introduce Universal Sparse Autoencoders (USAEs), a novel framework designed to identify and align interpretable semantic concepts across multiple disparate pretrained deep neural networks. In contrast to conventional concept-based interpretability techniques that operate on a per-model basis, USAEs facilitate the discovery of a joint concept space capable of reconstructing and interpreting internal activations from multiple architectures simultaneously. This is achieved by training a single overcomplete sparse autoencoder (SAE) to minimize a shared objective across varying tasks and datasets, thereby capturing common factors of variation. Empirical results demonstrate that USAEs uncover semantically coherent universal concepts in vision models, spanning from low-level textures to high-level object parts. Furthermore, the framework enables novel applications such as coordinated activation maximization for multi-model visualization and analysis.

### 2025 — Geometry-Aware Diffusion Models for Multiview Scene Inpainting
*British Machine Vision Conference (BMVC)*
Authors: Ahmad Salimi, Tristan Ty Aumentado-Armstrong, Marcus A. Brubaker, Konstantinos G. Derpanis

This work addresses the problem of 3D scene inpainting where input images from multiple viewpoints contain masked regions requiring consistent completion. The authors propose a geometry-aware conditional generative model that avoids the blurriness typical of radiance-field-based fusion methods by operating in a learned feature space. The methodology employs an autoregressive inpainting strategy, conditioning each new view on previously generated content while utilizing a multi-view depth estimator to gradually reconstruct scene geometry. Key geometric cues, including depth maps and shadow volumes, are rendered to provide explicit constraints on the diffusion process. The model demonstrates state-of-the-art performance on the SPIn-NeRF and NeRFiller benchmarks, notably maintaining multi-view consistency even in the few-view setting where traditional 3D fitting methods fail.

### 2025 — Quantifying and Learning Static vs. Dynamic Information in Deep Spatiotemporal Networks
*IEEE Transactions on Pattern Analysis and Machine Intelligence (TPAMI)*
Authors: Matthew Kowal, Mennatullah Siam, Md. Amirul Islam, Neil D. B. Bruce, Richard P. Wildes, Konstantinos G. Derpanis

This paper presents a systematic approach to quantifying the degree of absolute static (appearance-based) versus dynamic (motion-based) information encoded within the hidden representations of deep spatiotemporal models. The methodology utilizes a novel sampling procedure to generate video pairs that isolate specific factors of variation, followed by a mutual-information-based metric to assess unit-wise bias across various layers and channels. Extensive evaluations across action recognition and video segmentation tasks reveal that many state-of-the-art models exhibit a significant bias toward static features. To mitigate this, the authors propose StaticDropout, a semantically guided dropout mechanism that selectively suppresses static-biased channels during training. Results show that balancing static and dynamic representations improves performance on datasets requiring temporal reasoning, such as Something-Something-V2.

### 2025 — PixFoundation 2.0: Do Video Multi-Modal LLMs Use Motion in Visual Grounding?
*arXiv preprint*
Authors: Mennatullah Siam, Matthew Kowal, Md Amirul Islam, Richard P. Wildes, Konstantinos G. Derpanis

The authors investigate the pixel-level visual grounding capabilities of video multi-modal large language models (MLLMs), specifically examining whether these models utilize temporal motion cues or rely primarily on static appearance. Identifying deficiencies in current benchmarks where single-frame analysis often suffices for motion-related queries, the paper introduces four motion-centric probing techniques and a new benchmark, MoCentric-Bench. These probes assess the model's ability to distinguish authentic motion from synthetic counterparts and its comprehension of temporal ordering. The findings indicate that current video MLLMs often fail at dense spatiotemporal grounding tasks when static shortcuts are removed. Simple motion-centric adaptation techniques are explored to improve performance, setting a new baseline for future research in dense video understanding and reasoning.

### 2024 — Visual Concept Connectome (VCC): Open World Concept Discovery and Their Interlayer Connections in Deep Models
*IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)*
Authors: Matthew Kowal, Richard P. Wildes, Konstantinos G. Derpanis

The Visual Concept Connectome (VCC) is proposed as an unsupervised methodology for elucidating the internal representational structure of vision models across multiple layers. Unlike prior concept discovery methods that are restricted to single-layer analysis, VCC reveals fine-grained semantic concepts and their weighted interlayer connections throughout the entire network depth. This approach enables a global analysis of network structure, characterizing the branching patterns and hierarchical assemblies of concepts. The authors use VCCs to perform a comparative study between CNNs and Transformers, demonstrating that Transformers exhibit higher levels of compositionality in deeper layers. Practical utility is shown through failure mode debugging, where VCCs are used to identify the specific layers and concept assemblies responsible for classification errors in image classification tasks.
