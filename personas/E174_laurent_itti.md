---
name: Laurent Itti
institution: University of Southern California
department: Thomas Lord Department of Computer Science
lab_name: iLab
main_research_area: Computational vision and attention
total_citations: 63116
h_index: 80
---

# Laurent Itti

*Computational vision and attention* — University of Southern California, Thomas Lord Department of Computer Science, iLab.

## Background

Laurent Itti is a Professor of Computer Science, Psychology, and Neuroscience at the University of Southern California and the director of the iLab. Itti developed computational frameworks for visual saliency and bottom-up attention that simulate the neural mechanisms biological systems use to prioritize visual stimuli. Their research connects computational neuroscience and machine vision, focusing on scene understanding, eye-movement control, and the role of Bayesian surprise in perception. Itti’s recent work applies neuromorphic algorithms to real-time gaze prediction and uses eye-tracking behavior as a diagnostic tool for identifying neurological disorders.

## Papers

### 2025 — Riemannian-Geometric Fingerprints of Generative Models
*Proceedings of the IEEE/CVF International Conference on Computer Vision (ICCV)*
Authors: Hae Jin Song, Laurent Itti

This work introduces a formal geometric framework for generative model (GM) attribution by defining fingerprints and artifacts within the context of Riemannian geometry. To overcome the limitations of Euclidean distance metrics in high-dimensional feature spaces, the authors propose learning Riemannian metrics from data, effectively characterizing GMs on non-Euclidean manifolds. The methodology utilizes geodesic distances and a kNN-based Riemannian center of mass to represent and analyze model-specific artifacts across diverse architectures and modalities, including vision and vision-language models. Empirical results across 27 distinct model architectures demonstrate significant improvements in attribution accuracy and cross-dataset generalization compared to previous Euclidean methods, facilitating robust identification of synthetic data in both white-box and black-box deployment scenarios.

### 2025 — Perforated Backpropagation: A Neuroscience Inspired Extension to Artificial Neural Networks
*arXiv preprint (cs.NE)*
Authors: Rorry Brenner, Laurent Itti

The authors propose 'Perforated Backpropagation,' a novel optimization paradigm that mimics the non-linear computational properties of biological dendrites within deep neural network architectures. The method extends the standard artificial neuron unit by introducing 'Dendrite Nodes' that are trained to minimize the residual error of the original neurons after an initial convergence phase. By freezing these nodes and re-optimizing the primary network parameters using integrated feedback signals, the system achieves hierarchical feature coding more representative of biological neural systems. Experiments using PyTorch across multiple vision and language domains, including EMNIST and SNLI datasets, demonstrate that the inclusion of dendrite-inspired nodes enables up to 90% model compression and accuracy improvements of up to 16% over original baseline architectures.

### 2024 — USCILab3D: A Large-scale, Long-term, Semantically Annotated Outdoor Dataset
*Advances in Neural Information Processing Systems (NeurIPS) Datasets and Benchmarks Track*
Authors: Kiran Lekkala, Henghui Bao, Peixu Cai, Wei Zer Lim, Chen Liu, Laurent Itti

This paper presents USCILab3D, a comprehensive multi-modal outdoor dataset curated over 12 months using a teleoperated mobile robot equipped with a five-camera rig and a 360-degree LiDAR. The dataset comprises 1.4 million point clouds and 10 million images covering diverse environmental, weather, and lighting conditions across 229 acres. Automated labeling using state-of-the-art foundation models provides semantic annotations for 267 distinct object categories. The repository includes precise 3D reconstructions, pose-stamped trajectories, and multi-view imagery, specifically designed to address gaps in fine-grained semantic 3D vision. Benchmarking results for novel view synthesis and semantic segmentation demonstrate the dataset's efficacy in facilitating robust 3D perception and robotic navigation research in complex real-world settings.

### 2024 — Bird's Eye View Based Pretrained World model for Visual Navigation
*International Symposium on Robotics Research (ISRR)*
Authors: Kiran Lekkala, Chen Liu, Laurent Itti

This paper introduces a world model architecture that enhances the sim-to-real transferability of visual navigation agents through a latent Bird's Eye View (BEV) representation. The system employs a perception module pretrained on unlabeled video and trajectory data from the CARLA simulator to translate first-person view (FPV) RGB streams into egocentric BEV embeddings. Temporal dynamics and observation uncertainty are managed via a Mixture Density LSTM and anchor image-based state checking. The frozen pretrained model enables zero-shot deployment on physical differential drive robots, significantly accelerating reinforcement learning and goal-based planning in unseen environments. Results indicate that BEV representations provide a more robust and transferable latent space for navigation compared to direct FPV-based latent models.

### 2024 — Evaluating Pretrained models for Deployable Lifelong Learning
*Proceedings of the IEEE/CVF Winter Conference on Applications of Computer Vision (WACV)*
Authors: Kiran Lekkala, Eshan Bhargava, Yunhao Ge, Laurent Itti

The authors establish the DeLL (Deployment for Lifelong Learning) benchmark to evaluate the scalability and resource efficiency of visual reinforcement learning systems in continual learning scenarios. The proposed architecture integrates a task-mapper based on Few-Shot Class Incremental Learning (FSCIL) with an encoder pretrained on curated datasets. This modular design allows the system to recognize new tasks and load corresponding policy parameters without catastrophic forgetting or extensive computational overhead. Evaluated on the Atari 2600 suite, the system demonstrates superior performance in retaining knowledge across expanding task sequences and high efficiency in deploying to novel RL environments with minimal fine-tuning and reduced memory footprints.
