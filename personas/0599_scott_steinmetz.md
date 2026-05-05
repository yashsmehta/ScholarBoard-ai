---
name: Scott Steinmetz
institution: Sandia National Labs
department: Center for Computing Research
main_research_area: Computational neuroscience and visual perception
total_citations: 61
h_index: 5
---

# Scott Steinmetz

*Computational neuroscience and visual perception* — Sandia National Labs, Center for Computing Research.

## Background

Scott T. Steinmetz is a researcher at Sandia National Laboratories within the Center for Computing Research, where their work focuses on computational neuroscience and human-machine teaming. Steinmetz investigates the capacity of accuracy-optimized convolutional neural networks (CNNs) to model the primate dorsal stream, specifically analyzing optic flow tuning and self-motion perception in brain area MSTd. At Sandia, they also develop frameworks for "Trusted AI," examining how human operators calibrate trust in autonomous systems through performance characterization and transparency. Steinmetz earned a Ph.D. in Cognitive Science from Rensselaer Polytechnic Institute, where they conducted research on the attentional modulation of the pupillary light response.

## Papers

### 2024 — ReLU, Sparseness, and the Encoding of Optic Flow in Neural Networks
*Sensors*
Authors: Oliver W. Layton, Siyuan Peng, Scott T. Steinmetz

This study examines the impact of different activation functions—specifically ReLU, leaky ReLU, GELU, and Mish—on the precision, robustness, and internal representational characteristics of convolutional neural networks (CNNs) and multi-layer perceptrons (MLPs) trained to estimate self-motion from optic flow. The researchers found that architectures utilizing ReLU and leaky ReLU achieved significantly higher accuracy in heading estimation and demonstrated greater resilience when exposed to novel optic flow patterns compared to those using GELU or Mish. Technical analysis suggests that these advantages arise from the capacity of ReLU-based functions to induce sparser neural representations. The work characterizes the encoding of optic flow signals and highlights how sparseness can be leveraged to improve the reliability of visual navigation systems in mobile robotics, particularly in environments where GPS or radio signals are unavailable.

### 2024 — Accuracy optimized neural networks do not effectively model optic flow tuning in brain area MSTd
*Frontiers in Neuroscience*
Authors: Oliver W. Layton, Scott T. Steinmetz

While accuracy-optimized convolutional neural networks (CNNs) have successfully modeled neural responses in the primate ventral stream, their efficacy in representing the dorsal stream, specifically optic flow processing in the dorsal medial superior temporal area (MSTd), remains largely unexplored. This research compares the tuning properties of neurons within accuracy-optimized CNNs to neurophysiological data from primate MSTd and to the Non-Negative Matrix Factorization (NNMF) model. The study reveals that although accuracy-maximized CNNs can provide highly precise estimates of translational and rotational self-motion, they fail to replicate the specific optic flow tuning signatures observed in biological MSTd neurons. Conversely, the NNMF model, despite achieving lower overall motion estimation accuracy, exhibits tuning characteristics—such as a characteristic 90-degree offset in preferred directions—that align more closely with biological observations. The findings suggest that the functional architecture of MSTd is shaped by computational constraints beyond simple error minimization, such as nonnegativity and sparsity.
