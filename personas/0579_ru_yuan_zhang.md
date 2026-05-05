---
name: Ru-Yuan Zhang
institution: Shanghai Jiao Tong University
department: School of Psychological and Cognitive Sciences
lab_name: Laboratory of Cognitive Computational Neuroscience and Neuroimaging (CCNN)
main_research_area: computational visual neuroscience
total_citations: 4019
h_index: 20
---

# Ru-Yuan Zhang

*computational visual neuroscience* — Shanghai Jiao Tong University, School of Psychological and Cognitive Sciences, Laboratory of Cognitive Computational Neuroscience and Neuroimaging (CCNN).

## Background

Ru-Yuan Zhang is a computational neuroscientist who investigates the mechanisms of human perception, learning, and decision-making using fMRI, psychophysics, and deep learning models. Zhang’s research focuses on how the brain represents sensory uncertainty and how top-down processes like attention warp neural manifolds to optimize population coding in the human visual cortex. By comparing artificial neural networks with biological systems, they reverse-engineer the principles of perceptual learning and abstract visual reasoning to analyze human intelligence. Their work also includes computational psychiatry, applying Bayesian inference and reinforcement learning models to characterize cognitive deficits in individuals with anxiety and depression.

## Papers

### 2026 — Neural prediction errors as a unified cue of abstract visual reasoning
*IEEE Transactions on Pattern Analysis and Machine Intelligence (TPAMI)*
Authors: Lingxiao Yang, Xiaohua Xie, Wei-Shi Zheng, Fang Fang, Ru-Yuan Zhang

This work addresses the computational disparity between human-level abstract visual reasoning (AVR) and the limitations of deep neural networks by proposing a framework grounded in predictive coding. The authors posit that neural prediction errors (PEs)—the discrepancy between incoming visual inputs and top-down relational expectations—serve as the fundamental signal for identifying and generalizing abstract rules. The proposed model integrates a Relational Network with a PE-driven feedback loop to iteratively evaluate rule hypotheses in tasks such as Raven’s Progressive Matrices. Evaluations on AVR benchmarks, including PGM and RAVEN, demonstrate that this architecture achieves state-of-the-art accuracy and exhibits robust zero-shot generalization to novel visual attributes, supporting a crucial role for PE in the biological implementation of analogical reasoning.

### 2025 — A neural geometry approach comprehensively explains apparently conflicting models of visual perceptual learning
*Nature Human Behaviour*
Authors: Yuan-Ao Cheng, Mehran Sanayei, Xiaolong Chen, Ke Jia, Shurui Li, Fang Fang, Takeo Watanabe, Alexander Thiele, Ru-Yuan Zhang

Visual perceptual learning (VPL) improves sensory discrimination through training, but the mechanistic basis—whether it arises from sharpened neural tuning, increased gain, or attenuated noise—remains a subject of debate. This study introduces a neural geometry framework that unifies these seemingly contradictory models by conceptualizing population responses as geometric manifolds in high-dimensional neural space. Through the analysis of multi-unit recordings from macaque areas V1 and V4 alongside human fMRI data, the authors demonstrate that VPL is characterized by a singular geometric transformation: the optimization of task-relevant manifold alignment relative to decision boundaries. This transformation effectively increases the Fisher information of the population code, providing a comprehensive explanation for how learning-induced changes at the single-neuron level manifest as improved behavioral performance.

### 2025 — Sequential temporal anticipation characterized by neural power modulation and in recurrent neural networks
*eLife*
Authors: Xiangbin Teng, Ru-Yuan Zhang

The ability to anticipate the precise timing of sequential events is fundamental to adaptive sensory processing. This study investigates the neurocomputational substrates of temporal anticipation using a combination of human electroencephalography (EEG) and recurrent neural network (RNN) modeling. Behavioral data show that participants dynamically adjust their expectations based on rhythmic regularities. EEG analysis reveals that this anticipation is mediated by the modulation of oscillatory power in the alpha (8–13 Hz) and beta (15–30 Hz) bands, which systematically track the progression of temporal intervals. RNNs trained on the same task exhibit latent-state dynamics that parallel the human neural data, suggesting that the brain utilizes a dynamical systems mechanism where the velocity of neural trajectories within a specific manifold encodes temporal intervals and predicts upcoming events.

### 2025 — Attention improves population codes by warping neural manifolds in human visual cortex
*bioRxiv*
Authors: Yu-Qi You, Shurui Li, Yu-Ang Cheng, Yuanning Li, Kendrick Kay, Ru-Yuan Zhang

This study investigates how top-down attention optimizes sensory processing by applying a neural population manifold framework to high-resolution 7T fMRI data. The researchers measured cortical responses during diverse attentional tasks and quantified the geometric transformations of neural representations in the visual cortex. They discovered that attention induces a non-linear warping of the neural manifold in areas V1–V3, characterized by the expansion of representational space along task-relevant stimulus dimensions and the contraction of irrelevant ones. This manifold warping increases the separability of neural patterns and enhances decoding accuracy. The findings support a 'tuning change' model of attention and provide a quantitative geometric explanation for how attention refines population-level neural codes to improve perception.

### 2024 — Individuals with anxiety and depression use atypical decision strategies in an uncertain world
*eLife*
Authors: Zeming Fang, Mingli Zhao, Ting Xu, Yuanning Li, Huichun Xie, Ping Quan, Haiyan Geng, Ru-Yuan Zhang

This computational psychiatry study examines the decision-making strategies of individuals with internalizing disorders (anxiety and depression) in volatile environments. Using a restless multi-armed bandit task and Bayesian hierarchical drift-diffusion models (HDDM), the authors identified a specific computational phenotype associated with these disorders. Individuals with high symptom severity exhibit 'atypical' strategies marked by over-estimation of environmental volatility and heightened sensitivity to negative prediction errors. This manifests as excessive switching behavior and narrower decision boundaries (lower threshold for evidence accumulation), leading to suboptimal reward harvesting. These results demonstrate how affective states disrupt probabilistic inference and bias the exploration-exploitation trade-off, providing quantitative markers for clinical diagnosis.
