---
name: Gemma Roig
institution: Goethe University Frankfurt
department: Department of Computer Science
lab_name: Computational Vision and Artificial Intelligence (CVAI) Lab
main_research_area: brain-inspired artificial intelligence
total_citations: 4239
h_index: 33
---

# Gemma Roig

*brain-inspired artificial intelligence* — Goethe University Frankfurt, Department of Computer Science, Computational Vision and Artificial Intelligence (CVAI) Lab.

## Background

Gemma Roig is a Full Professor at Goethe University Frankfurt and leads the Computational Vision and Artificial Intelligence lab. Roig’s research integrates computer vision with cognitive neuroscience to develop brain-inspired AI architectures and uses deep neural networks as models for predicting human brain activity and behavior. They investigate representational alignment, multimodal learning, and invariant object recognition, utilizing data from MRI and EEG to benchmark machine intelligence against human perception. Before joining Goethe University, Roig held research and faculty positions at the Singapore University of Technology and Design and the MIT Center for Brains, Minds and Machines.

## Papers

### 2025 — Net2Brain: a toolbox to compare artificial vision models with human brain responses
*Frontiers in Neuroinformatics*
Authors: Domenic Bersch, Martina G. Vilas, Sari Saba-Sadiya, Timothy Schaumlöffel, Kshitij Dwivedi, Christina Sartzetaki, Radoslaw M. Cichy, Gemma Roig

This work presents Net2Brain, an open-source Python framework designed to integrate diverse deep neural network (DNN) architectures into cognitive neuroscience research workflows. The toolbox provides an automated pipeline for downloading standard neuroimaging datasets—such as the Natural Scenes Dataset (NSD) and the BOLD Moments video dataset—and extracting hierarchical activations from a library of over 600 models, including vision-only, multimodal, and large language models (LLMs). Comparison between artificial and biological representational spaces is facilitated through built-in functionalities for representational similarity analysis (RSA), ridge-regression-based encoding models, and variance partitioning. The framework enables high-throughput benchmarking of brain-model alignment across the human visual hierarchy, supporting the systematic investigation of how different architectural components and training paradigms approximate cortical processing.

### 2025 — Cognitive Neural Architecture Search Reveals Hierarchical Entailment
*arXiv preprint arXiv:2502.11141*
Authors: Lukas Kuhn, Sari Saba-Sadiya, Gemma Roig

Addressing the debate between hierarchical and 'shallow' theories of the primate ventral stream, this research employs evolutionary neural architecture search (NAS) to evolve convolutional neural network (CNN) topologies optimized for alignment with human fMRI data. The study demonstrates that when architectures are evolved to maximize representational similarity with later regions of the ventral pathway (such as the inferior temporal cortex), they naturally develop structured representational hierarchies. Notably, these evolved architectures achieve higher brain-alignment scores than standard pretrained models even when using random weights. Furthermore, the identified brain-aligned architectures perform competitively on supervised image classification tasks, suggesting that the hierarchical structure required for biological alignment provides a powerful inductive bias for generalizable visual intelligence.

### 2025 — Beyond Data Augmentations: Generalization Abilities of Few-Shot Segmentation Models
*Proceedings of the 20th International Joint Conference on Computer Vision, Imaging and Computer Graphics Theory and Applications (VISAPP)*
Authors: Muhammad Ahsan, Guy Ben-Yosef, Gemma Roig

This paper introduces a novel evaluation paradigm termed 'half-shot learning' (HSL) to assess the robustness of few-shot semantic segmentation (FSS) models under severe data degradations. The authors propose a highly augmented testing suite where support images are subjected to aggressive cropping, occlusion, and transformation to simulate realistic perception challenges. Experimental results expose significant performance gaps in state-of-the-art FSS models when processing partially viewed objects. To mitigate these shortcomings, the work proposes the integration of spatial and channel-wise attention modules, demonstrating that enhancing the model's internal sense of 'objectness' through targeted attention mechanisms improves generalization to unseen categories in degraded support contexts.

### 2025 — Efficient Unsupervised Shortcut Learning Detection and Mitigation in Transformers
*IEEE/CVF International Conference on Computer Vision (ICCV)*
Authors: Lukas Kuhn, Sari Sadiya, Jorg Schlotterer, Florian Buettner, Christin Seifert, Gemma Roig

Shortcut learning, where models rely on spurious or task-irrelevant features, remains a critical barrier to deploying robust AI in high-stakes environments. This work proposes a mechanistic interpretability framework to detect and mitigate such shortcuts in Transformer architectures without the need for manual bias annotations. The method identifies attention heads and feature subspaces that encode non-robust correlations by analyzing their impact on model decisions across diverse data partitions. An unsupervised decorrelation strategy is then applied to the latent space to suppress these identified shortcuts. Validation across multiple datasets, including medical diagnostics, shows that the framework significantly enhances worst-group accuracy and out-of-distribution generalization while maintaining computational efficiency on standard hardware.

### 2024 — Limited but Consistent Gains in Adversarial Robustness by Co-training Object Recognition Models with Human EEG
*European Conference on Computer Vision (ECCV)*
Authors: Manshan Guo, Bhavin Choksi, Sari Sadiya, Alessandro T. Gifford, Martina G. Vilas, Radoslaw M. Cichy, Gemma Roig

This study evaluates whether incorporating biological inductive biases from human neural responses can improve the reliability of artificial neural networks against adversarial perturbations. Using a dual-task learning framework, ResNet-50 models were co-trained to perform image classification while simultaneously predicting human EEG signals recorded during natural image viewing. The investigation focuses on the temporal dynamics of brain-model alignment, finding that networks successfully mimicking human representational patterns—particularly those occurring roughly 100ms post-stimulus in the parieto-occipital sensors—exhibit statistically consistent improvements in robustness against FGSM and PGD attacks. These results suggest that the representational geometry of the human visual system captures robust features that are inherently missing in purely supervised machine learning models.
