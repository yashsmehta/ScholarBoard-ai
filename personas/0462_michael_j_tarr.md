---
name: Michael J Tarr
institution: Carnegie Mellon University
department: Department of Psychology
lab_name: TarrLab
main_research_area: computational cognitive neuroscience and vision
total_citations: 25312
h_index: 69
---

# Michael J Tarr

*computational cognitive neuroscience and vision* — Carnegie Mellon University, Department of Psychology, TarrLab.

## Background

Michael J. Tarr is the Kavčić-Moura Professor of Cognitive and Brain Science at Carnegie Mellon University and investigates the computational and neural architectures underlying high-level visual perception. Tarr’s research focuses on how the primate brain transforms two-dimensional retinal inputs into representations of objects, faces, and scenes, emphasizing the role of perceptual expertise and learning. They employ a multi-disciplinary approach that integrates large-scale functional neuroimaging, such as the BOLD5000 dataset, with deep learning and generative AI models to bridge the gap between biological and artificial vision systems. Tarr’s current work explores the inductive biases of the human visual system and develops NeuroAI frameworks to map cortical semantic selectivity across the ventral visual pathway.

## Papers

### 2025 — Brain Mapping with Dense Features: Grounding Cortical Semantic Selectivity in Natural Images With Vision Transformers
*International Conference on Learning Representations (ICLR)*
Authors: Andrew F. Luo, Jacob Yeung, Rushikesh Zawar, Shaurya Dewan, Margaret M. Henderson, Leila Wehbe, Michael J. Tarr

This research introduces BrainSAIL (Semantic Attribution and Image Localization), a novel voxel-wise encoding framework designed to link human cortical selectivity with spatially distributed semantic features in naturalistic visual scenes. By leveraging dense spatial representations from large-scale vision transformers (ViTs), the method extracts semantically consistent embeddings that bridge the gap between raw pixel data and neural activations. BrainSAIL employs a denoising distillation process to isolate specific image subregions that drive neural tuning patterns in category-selective areas, such as the fusiform face area and parahippocampal place area. The results demonstrate that incorporating dense semantic grounding provides a more granular and interpretable mapping of high-level visual representations in the human brain compared to whole-image embedding models.

### 2025 — Reanimating Images using Neural Representations of Dynamic Stimuli
*Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)*
Authors: Jacob Yeung, Andrew F. Luo, Gabriel Sarch, Margaret M. Henderson, Deva Ramanan, Michael J. Tarr

The study presents BrainNRDS (Neural Representations of Dynamic Stimuli), a computational framework that explicitly disentangles static and motion-related representations as they are processed in the human visual cortex. Utilizing state-of-the-art video diffusion models (DragNUWA), the authors demonstrate that dense, object-level optical flow can be decoded directly from fMRI brain activity. The approach establishes that video-based encoders outperform traditional static image models in predicting neural responses to naturalistic dynamic stimuli. Furthermore, the decoded neural signals are shown to enable the realistic reanimation of static frames, providing insights into the distinct cortical pathways subserving spatial and temporal visual processing in motion-rich environments.

### 2025 — The Oomplet dataset toolkit as a flexible and extensible system for large-scale, multi-category image generation
*Scientific Reports*
Authors: John P. Kasarda, Angela Zhang, Hua Tong, Yan Tan, Rui Wang, Timothy Verstynen, Michael J. Tarr

This paper introduces the Oomplet Dataset Toolkit (ODT), an open-source generative stimulus engine designed for the high-throughput study of perceptual learning in biological and artificial systems. The toolkit generates 'Oomplets'—cartoon-like humanoid characters—parameterized across ten distinct feature dimensions, allowing for the creation of over 9.1 million unique stimuli with controlled categorical boundaries. Through behavioral validation, the authors show that human adults effectively discriminate categories based on varying subsets of these dimensions. The ODT provides a scalable and customizable alternative to internet-sourced image datasets, facilitating rigorous assessments of how visual complexity and feature variability influence category acquisition and representational development.

### 2025 — Cortical representations supporting coarse and fine object categorization
*Journal of Vision*
Authors: Margaret M. Henderson, Sungjoon Park, Leila Wehbe, Michael J. Tarr

Intermediate visual features may be sufficient to support certain types of object categorization, even in the absence of recognizable high-level properties. We hypothesize that the role of these features depends on the granularity of a task: fine-grained distinctions (types of birds) may require high-level, complex features, while coarser distinctions (animals vs. vehicles) may be accessible from low-level features alone. Differences in the diagnostic features relevant to these different tasks may also lead to task-dependent differences in how object images are cortically encoded during coarse and fine categorization. Across both behavioral and fMRI studies, we leveraged a computational texture synthesis procedure (Gatys et al.; 2015, NeurIPS) to generate “texturized” versions of target object images by matching their summary statistics at different layers of a deep neural network. This results in images that vary continuously in their feature complexity. Participants viewed these images and performed a 2-alternative forced choice task discriminating the image category at either a coarser (superordinate) or a finer (basic) level. We found that observers could behaviorally discriminate a subset of object categories at an above-chance level based on the simplest texturized images tested. Categorization of simple texture images was highest for coarse categories (vs. fine), natural objects (vs. artificial), and color images (vs. grayscale). In the brain, we used multivariate classification within higher visual cortex to demonstrate evidence for distributed neural representations of both coarse and fine object categories. As in the behavioral data, discriminability of these representations was lower for texturized as compared to original images, but coarse category information could be decoded with above-chance accuracy even from cortical responses to simple texturized images. Taken together, these results indicate that intermediate visual features contribute to object categorization in a manner that depends on task precision.

### 2024 — Gatekeeping Without Peer Review
*PsyArXiv*
Authors: Michael J. Tarr

This perspective analyzes the evolving landscape of scientific communication, focusing on the systemic shift toward rapid digital dissemination via preprints. The article examines how the traditional peer-review process serves as a centralized gatekeeping mechanism and contrasts this with emerging decentralized models where research impact is increasingly mediated by social media and algorithmic visibility. It evaluates the tradeoffs between the acceleration of scientific sharing and the risks associated with unvetted data, discussing the implications for institutional hiring, the preservation of scientific rigor, and the democratization of access to foundational research findings.
