---
name: Shinji Nishimoto
institution: Osaka University
department: Graduate School of Frontier Biosciences
lab_name: Perceptual and Cognitive Neuroscience Laboratory
main_research_area: computational and cognitive neuroscience
total_citations: 6476
h_index: 24
---

# Shinji Nishimoto

*computational and cognitive neuroscience* — Osaka University, Graduate School of Frontier Biosciences, Perceptual and Cognitive Neuroscience Laboratory.

## Background

Nishimoto is a Professor at Osaka University and a Principal Investigator at the Center for Information and Neural Networks (CiNet). Their research focuses on the quantitative modeling of human brain activity evoked by naturalistic stimuli to investigate the neural basis of perceptual and cognitive functions. Nishimoto has worked on reconstructing dynamic visual experiences from fMRI signals and developing brain-decoding techniques using deep learning and generative models. Their current projects involve building high-dimensional encoding models to examine how the brain represents information across diverse modalities, timescales, and internal states.

## Papers

### 2026 — A Quantitative Benchmark of Visual Information in Human Brain Recordings Across fMRI, MEG, and EEG
*bioRxiv*
Authors: Taisei Hara, Yoshito Masai, Shinji Nishimoto

This research establishes a formal quantitative benchmark for evaluating the representational information content across functional magnetic resonance imaging (fMRI), magnetoencephalography (MEG), and electroencephalography (EEG) under identical experimental conditions. Utilizing the large-scale THINGS image database consisting of 1,854 object categories, the authors employ a unified decoding and encoding pipeline to assess the representational fidelity of each modality. The findings delineate a clear efficiency-precision trade-off: fMRI exhibits the highest spatial specificity and asymptotic decoding accuracy (reaching ~87%) for categorical representations, whereas MEG and stimulus-level aggregated EEG (group-level structure) demonstrate superior efficiency in capturing hierarchical visual features within short measurement intervals. This framework provides a principled basis for cross-modal comparison and modality selection based on the spatiotemporal scaling properties of visual neural representations.

### 2025 — Text-to-music generation models capture musical semantic representations in the human brain
*Nature Communications*
Authors: Timo I. Denk, Yu Takagi, Takuya Matsuyama, Andrea Agostinelli, Tomoya Nakai, Christian Frank, Shinji Nishimoto

This study investigates the functional correspondence between generative music models and the human auditory system by reconstructing heard musical stimuli from fMRI signals. Using the MusicLM framework and joint music-text embeddings (MuLan), the authors develop voxel-wise encoding models to map high-level musical semantics—such as genre, instrumentation, and mood—onto cortical activity. Results demonstrate that music-specific deep neural network (DNN) features provide significantly higher predictive accuracy for activity in the primary auditory cortex and superior temporal gyrus compared to general auditory models. Furthermore, the researchers achieve high-fidelity music reconstruction through retrieval-based decoding and latent conditioning of the MusicLM generator, indicating that the brain's internal representations of musical meaning are hierarchically aligned with the feature extraction mechanisms of state-of-the-art generative AI.

### 2025 — Conversational content is organized across multiple timescales in the brain
*Nature Human Behaviour*
Authors: Masahiro Yamashita, Rieko Kubo, Shinji Nishimoto

Using fMRI hyperscanning of interacting dyads, this paper explores the neural architecture of language production and comprehension during spontaneous, interactive dialogue. By applying encoding models based on contextual word embeddings from large language models (LLMs), the authors quantify the linguistic coupling between speakers and listeners across broadly distributed cortical networks. The research identifies a timescale-dependent functional organization: shorter linguistic units (words and sentences) engage overlapping neural populations for production and comprehension, while longer-range discourse structures and narrative contexts recruit distinct, specialized systems. These findings suggest that the human brain dynamically adapts its representational strategy to facilitate mutual understanding across varying hierarchical levels of conversational meaning.

### 2025 — Cortical representational geometry of diverse tasks reveals subject-specific and subject-invariant cognitive structures
*Communications Biology*
Authors: Tomoya Nakai, Rieko Kubo, Shinji Nishimoto

This investigation examines the variability and invariance of cognitive representational geometry in the human cortex across 25 diverse tasks using fMRI. By integrating inter-subject correlation (ISC) and representational similarity analysis (RSA), the authors quantify the consistency of the abstract 'cognitive structure'—defined by the relational distances between task-evoked activity patterns. While primary sensory and higher-order visual regions exhibit high inter-subject invariance, the representational geometry in the fronto-parietal association cortex is found to be significantly individualized. Despite this person-specific variability, the idiosyncratic cognitive structures are robust enough to allow for 100% accurate subject identification from multi-task neural data, revealing a fundamental duality between shared functional backbones and highly individualized cognitive control systems.

### 2024 — Unveiling Multi-level and Multi-modal Semantic Representations in the Human Brain using Large Language Models
*Proceedings of the 2024 Conference on Empirical Methods in Natural Language Processing (EMNLP)*
Authors: Yuko Nakagi, Takuya Matsuyama, Naoko Koide-Majima, Hiroto Q. Yamaguchi, Rieko Kubo, Shinji Nishimoto, Yu Takagi

To map the hierarchical organization of semantic information in the human brain, this study utilizes fMRI recordings from participants viewing 8.3 hours of naturalistic movie stimuli. The authors employ Large Language Models (LLMs) to extract multi-level latent representations corresponding to speech content, visual object categories, and narrative story context. Voxel-wise encoding models demonstrate that LLM-derived features significantly outperform traditional semantic models, particularly in modeling the high-level background narrative. The research reveals a systematic cortical distribution of semantic selectivity: speech information is localized in temporal language networks, visual objects in the ventral stream, and story-level context in the default mode network, underscoring the necessity of multi-modal and multi-level modeling to understand how the brain constructs coherent narrative experiences.
