---
name: Andreas Tolias
institution: Stanford University
department: Department of Ophthalmology
lab_name: Tolias Lab
main_research_area: NeuroAI and computational neuroscience
total_citations: 24190
h_index: 74
---

# Andreas Tolias

*NeuroAI and computational neuroscience* — Stanford University, Department of Ophthalmology, Tolias Lab.

## Background

Tolias is a Professor of Ophthalmology at Stanford University and directs a research program focused on the intersection of systems neuroscience and artificial intelligence. Their work utilizes large-scale neural recordings and machine learning to investigate the network-level principles of perceptual inference and decision-making. Tolias led the MICrONS project, which produced a functional connectomics dataset, and developed 'digital twins' to simulate biological brain computation. Their current research focuses on reverse-engineering biological algorithms to design AI systems that are interpretable, robust, and efficient.

## Papers

### 2026 — Deep learning-driven characterization of single cell tuning in primate visual area V4 supports topological organization
*eLife*
Authors: Konstantin F. Willeke, Kelli Restivo, Katrin Franke, Arne F. Nix, Santiago A. Cadena, Tori Shinn, Cate Nealley, Gabrielle Rodriguez, Saumil Patel, Alexander S. Ecker, Fabian H. Sinz, Andreas S. Tolias

This study employs a data-driven, deep-learning framework to investigate the functional organization of macaque visual area V4, a region selective for complex naturalistic features that are difficult to parameterize. By training convolutional neural network models to predict the spiking activity of over 1,200 single units, the authors synthesized 'most exciting images' (MEIs) using in silico activation maximization, which were subsequently validated through in vivo closed-loop experiments. The results reveal that V4 neurons exhibit highly structured selectivity for non-parametric features such as complex textures, curvatures, and eye-like motifs. Critically, contrastive clustering of these model-derived selectivities demonstrated that V4 neurons are organized into functional groups with shared feature preferences, providing evidence for a topographic or columnar organization of mid-level visual features across the cortical surface.

### 2026 — Dual-feature selectivity enables bidirectional coding in visual cortical neurons
*eLife*
Authors: Katrin Franke, Nikos Karantzas, Konstantin Willeke, Maria Diamantaki, Kandan Ramakrishnan, Hasan Atakan Bedel, Pavithra Elumalai, Kelli Restivo, Paul Fahey, Cate Nealley, Tori Shinn, Gabrielle Garcia, Saumil Patel, Alexander Ecker, Edgar Y. Walker, Emmanouil Froudarakis, Sophia Sanborn, Fabian H. Sinz, Andreas Tolias

Challenging the classical 'feature detector' paradigm, this work identifies a dual-feature encoding strategy in the mammalian visual cortex where neurons are tuned to two distinct features—one activating and one suppressive—relative to a non-zero baseline firing rate. Leveraging deep learning-based 'functional digital twins' of V1 and V4 neurons in both macaques and mice, the researchers demonstrate that neuronal activity varies linearly along a low-dimensional axis anchored by these opposing preferred and non-preferred features. This bidirectional code structures stimulus representation across the population and is conserved across species, suggesting a fundamental computational strategy likely mediated by feature-selective inhibitory normalization that enhances representational expressivity within the cortical hierarchy.

### 2025 — Foundation model of neural activity predicts response to new stimulus types
*Nature*
Authors: Eric Y. Wang, Paul G. Fahey, Zhuokun Ding, Stelios Papadopoulos, Kayla Ponder, Marissa A. Weis, Andersen Chang, Taliah Muhammad, Saumil Patel, Zhiwei Ding, Dat Tran, Jiakun Fu, Casey M. Schneider-Mizell, Nuno Maçarico da Costa, R. Clay Reid, Forrest Collman, Nuno Maçarico da Costa, Katrin Franke, Alexander S. Ecker, Jacob Reimer, Xaq Pitkow, Fabian H. Sinz, Andreas S. Tolias

We developed a foundation model of the mouse visual cortex by training a deep neural network on a massive corpus of neural activity recorded from multiple individuals. This model demonstrates unprecedented zero-shot generalization, accurately predicting neuronal responses to novel stimulus domains—such as coherent motion and noise patterns—that were absent from the training set. Beyond sensory response prediction, the model's latent functional embeddings serve as a 'functional barcode' that can be transferred to predict anatomical properties, including synaptic connectivity, dendritic morphology, and cell type classification within the MICrONS dataset. These findings establish that large-scale neural data can be used to build foundation models that capture universal principles of cortical computation and relate function directly to cellular anatomy.

### 2025 — Functional connectomics reveals general wiring rule in mouse visual cortex
*Nature*
Authors: Zhuokun Ding, Paul G. Fahey, Stelios Papadopoulos, Eric Y. Wang, Brendan Celii, Christos Papadopoulos, Andersen Chang, Alexander B. Kunin, Dat Tran, Jiakun Fu, Zhiwei Ding, Saumil Patel, Lydia Ntanavara, Rachel Froebe, Kayla Ponder, Taliah Muhammad, J. Alexander Bae, Agnes L. Bodor, Derrick Brittain, JoAnn Buchanan, Daniel J. Bumbarger, Manuel A. Castro, Erick Cobos, Sven Dorkenwald, Leila Elabbady, Akhilesh Halageri, Zhen Jia, Chris Jordan, Dan Kapner, Nico Kemnitz, Sam Kinn, Kisuk Lee, Kai Li, Ran Lu, Thomas Macrina, Gayathri Mahalingam, Eric Mitchell, Shanka Subhra Mondal, Shang Mu, Barak Nehoran, Sergiy Popovych, Casey M. Schneider-Mizell, William Silversmith, Marc Takeno, Russel Torres, Nicholas L. Turner, William Wong, Jingpeng Wu, Wenjing Yin, Szi-Chieh Yu, Dimitri Yatsenko, Emmanouil Froudarakis, Fabian Sinz, Krešimir Josić, Robert Rosenbaum, H. Sebastian Seung, Forrest Collman, Nuno Maçarico da Costa, R. Clay Reid, Edgar Y. Walker, Xaq Pitkow, Jacob Reimer, Andreas S. Tolias

Utilizing the millimetre-scale MICrONS dataset, which combines in vivo calcium imaging with electron microscopy, we investigated the relationship between synaptic connectivity and functional tuning across the visual hierarchy. By applying a digital twin model to disentangle feature tuning from spatial receptive field overlap, we identified a universal 'like-to-like' wiring rule: neurons with similar feature selectivities are preferentially connected across different cortical layers and areas, including feedback pathways. We also discovered a higher-order connectivity principle where postsynaptic cohorts exhibit greater functional similarity than predicted by pairwise rules. Recurrent neural network simulations show that these connectivity motifs mirror those optimized for task performance, suggesting that structured, non-random connectivity is essential for robust sensory processing and efficient credit assignment in biological networks.

### 2024 — Asymmetric distribution of color-opponent response types across mouse visual cortex supports superior color vision in the sky
*eLife*
Authors: Katrin Franke, Chenchen Cai, Kayla Ponder, Jiakun Fu, Sacha Sokoloski, Philipp Berens, Andreas S. Tolias

This study systematically maps the cortical representation of color in the mouse, revealing a pronounced functional asymmetry across the visual field. Using large-scale population imaging and unsupervised clustering of responses to chromatic noise, we show that over one-third of neurons in V1 exhibit color-opponency in their receptive field (RF) centers. This color-opponency is markedly concentrated in the posterior visual cortex, which encodes the upper visual field (the sky). The asymmetry is driven by a localized population of Green-On/UV-Off neurons, a cortical specialization that is absent in the retinal output. Computational modeling suggests that this uneven distribution of chromatic response types is optimized for the statistics of natural scenes to improve the detection of dark UV-absorbing objects against the sky, potentially serving as an ethological adaptation for aerial predator detection.
