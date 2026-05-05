---
name: Benoit Cottereau
institution: University of Toulouse
department: Centre de Recherche Cerveau et Cognition (CerCo)
lab_name: SV3M (Spatial Vision in Man, Monkey and Machine)
main_research_area: Spatial vision and computational neuroscience
total_citations: 3052
h_index: 27
---

# Benoit Cottereau

*Spatial vision and computational neuroscience* — University of Toulouse, Centre de Recherche Cerveau et Cognition (CerCo), SV3M (Spatial Vision in Man, Monkey and Machine).

## Background

Benoit Cottereau is a CNRS Research Director at the CerCo laboratory in Toulouse and the IPAL laboratory in Singapore, specializing in the mechanisms of spatial vision and 3D scene understanding. Their research combines human and non-human primate neuroimaging (fMRI, EEG, MEG) with psychophysical experiments and computational modeling. Cottereau focuses on the development of bio-inspired artificial vision systems, utilizing event-based cameras and spiking neural networks to model biological processes such as optic flow, binocular disparity, and symmetry perception. This work encompasses fundamental neuroscience, clinical applications for rehabilitating visual pathologies like macular degeneration, and the design of energy-efficient artificial intelligence for robotic navigation.

## Papers

### 2025 — Learning to Remove Lens Flare in Event Camera
*arXiv preprint arXiv:2512.09016*
Authors: Haiqian Han, Lingdong Kong, Jianing Li, Ao Liang, Chengtao Zhu, Jiacheng Lyu, Lai Xing Ng, Xiangyang Ji, Wei Tsang Ooi, Benoit R. Cottereau

This work introduces E-Deflare, the first systematic framework for remediating lens flare artifacts in event-based vision systems. The authors establish a theoretical foundation by deriving a physics-grounded forward model that characterizes the non-linear suppression of event generation caused by internal reflections and scattering within optical lenses. To facilitate model training and evaluation, the E-Deflare Benchmark is presented, consisting of the large-scale E-Flare-2.7K synthetic dataset and the E-Flare-R real-world test set captured via a custom optical system. Empirical results demonstrate that modeling the suppression mechanism allows for superior restoration of asynchronous event streams, significantly improving the performance of downstream perception tasks in the presence of challenging optical artifacts.

### 2025 — Temporal recurrence as a general mechanism to explain neural responses in the auditory system
*Communications Biology*
Authors: Ulysse Rançon, Timothée Masquelier, Benoit R. Cottereau

This research investigates the computational role of recurrent connectivity in spiking neural networks (SNNs) for reproducing the complex temporal dynamics observed in biological auditory neurons. The authors demonstrate that a parsimonious architecture incorporating temporal recurrence and lateral connections can effectively account for diverse neural response properties, including adaptation, frequency selectivity, and the distinction between transient and sustained firing patterns. Unlike traditional compartment-based models, this recurrent SNN approach leverages internal memory within the feedback loops to process asynchronous auditory signals across multiple timescales, suggesting that temporal recurrence is a fundamental mechanism for the biological representation of time-varying sensory information.

### 2025 — Talk2Event: Grounded Understanding of Dynamic Scenes from Event Cameras
*Advances in Neural Information Processing Systems (NeurIPS)*
Authors: Lingdong Kong, Dongyue Lu, Alan Liang, Rong Li, Yuhao Dong, Tianshuai Hu, Lai Xing Ng, Wei Tsang Ooi, Benoit R. Cottereau

The authors present Talk2Event, a novel benchmark for attribute-aware language-driven object grounding in event-based perception. Developed from real-world driving data, the benchmark includes over 30,000 referring expressions annotated with four key attributes: appearance, status, viewer-relative spatial positioning, and inter-object relational cues. To bridge the gap between asynchronous event streams and natural language, the study proposes EventRefer, a framework utilizing a Mixture of Event-Attribute Experts (MoEE) to dynamically integrate multimodal features. This attribute-centric approach facilitates spatially and temporally aware grounding, achieving substantial performance gains over state-of-the-art baselines in event-only, frame-only, and sensor-fusion settings.

### 2025 — Motion processing in visual cortex of maculopathy patients
*Journal of Neuroscience*
Authors: Célia Michaud, Jade Guénot, Cynthia Faurite, Mathilde Gallice, Christophe Chiquet, Nathalie Vayssière, Isabelle Berry, Yves Trotter, Vincent Soler, Carole Peyrin, Benoit R. Cottereau

This study characterizes the functional integrity of the motion-selective cortical network in patients with central vision loss due to maculopathy using functional magnetic resonance imaging (fMRI). By utilizing translational random-dot kinematograms, the researchers mapped neural activity in a specialized network including the human V5/MT+ complex, areas V3A and V6, and peripheral subregions of the early visual cortex (V1–V3). The results show that maculopathy patients exhibit robust and comparable activation patterns to those found in control participants viewing stimuli with artificial scotomas. These findings indicate that the large-scale cortical organization of the motion processing system remains largely stable following the onset of a central scotoma, with no evidence of significant functional reorganization in these high-level visual areas.

### 2025 — EventFly: Event Camera Perception from Ground to the Sky
*IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)*
Authors: Lingdong Kong, Dongyue Lu, Xiang Xu, Lai Xing Ng, Wei Tsang Ooi, Benoit R. Cottereau

The paper introduces EventFly, a framework designed to ensure robust cross-platform and cross-domain adaptation in event-based visual perception. The methodology addresses the challenge of domain shift encountered when deploying models across event sensors with varying resolutions, noise characteristics, and acquisition perspectives (e.g., ground-level vs. aerial). By unifying multi-modal visual grounding and modeling sensor-invariant asynchronous dynamics, EventFly facilitates effective adaptation to disparate hardware configurations. Comprehensive evaluations on large-scale benchmarks demonstrate that the framework achieves state-of-the-art performance in semantic scene understanding and object localization under significant shifts in perspective and sensor modality.
