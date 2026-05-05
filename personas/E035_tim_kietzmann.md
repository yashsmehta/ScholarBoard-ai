---
name: Tim Kietzmann
institution: University of Osnabrück
department: Institute of Cognitive Science
lab_name: Kietzmann Lab
main_research_area: cognitive computational neuroscience
total_citations: 5021
h_index: 29
---

# Tim Kietzmann

*cognitive computational neuroscience* — University of Osnabrück, Institute of Cognitive Science, Kietzmann Lab.

## Background

Tim C. Kietzmann is a Professor of Machine Learning at the University of Osnabrück's Institute of Cognitive Science. Their research integrates deep learning and cognitive neuroscience to characterize the neuro-computational principles of human vision, focusing on how recurrent neural networks model the dynamic transformation of sensory signals in the brain. By combining neuroimaging techniques like MEG, EEG, and fMRI with neuro-inspired artificial intelligence, Kietzmann investigates how biological systems derive representations from environmental regularities. Kietzmann previously held positions at the Donders Institute and the University of Cambridge, where they used connectionist models to explain cortical dynamics.

## Papers

### 2025 — Predictive remapping and allocentric coding as consequences of energy efficiency in recurrent neural network models of active vision
*Patterns*
Authors: Thomas Nortmann, Philip Sulewski, Tim C. Kietzmann

The maintenance of visual stability across saccadic eye movements is hypothesized to depend on predictive mechanisms using efference copies to anticipate forthcoming foveal inputs. This study examines whether such sophisticated computations require hard-wired evolutionary scaffolds or can emerge from the fundamental constraint of metabolic energy efficiency. Recurrent neural networks (RNNs) were trained to minimize preactivation costs while processing sequences of natural image patches and saccadic oculomotor signals. Results demonstrate that targeted inhibitory predictive remapping and the transformation of egocentric retinal coordinates into an allocentric reference frame emerge autonomously from energy-efficiency optimization. These models self-organized into prediction and error units, mirroring hierarchical predictive coding architectures. Multi-scale temporal analyses via virtual lesioning revealed both rapid lateral predictive signals and slower evidence integration cycles. These findings suggest that complex neurophysiological remapping and spatial coding arise from simple physical principles of efficient information processing.

### 2025 — Predicting upcoming visual features during eye movements yields scene representations aligned with human visual cortex
*arXiv*
Authors: Sushrut Thorat, Adrien Doerig, Alexander Kroner, Carmen Amme, Tim C. Kietzmann

Effective visual intelligence requires unified scene representations that integrate localized snapshots into a coherent structure. We propose Glimpse Prediction Networks (GPNs), recurrent neural models trained to predict the high-level feature embeddings of forthcoming glimpses along human-like scanpaths using self-supervised learning. GPNs successfully internalize the co-occurrence statistics and spatial arrangement of scene components, and their recurrent variants integrate information over multiple saccades into a unified representation. Using the Natural Scenes Dataset (NSD), we demonstrate that GPN internal representations align significantly with human fMRI responses across mid-to-high-level visual cortex, particularly in ventral and dorsal stream areas. GPNs outperform semantic-supervised controls and match state-of-the-art vision models, indicating that next-glimpse prediction during active vision is a biologically plausible, self-supervised computational route to brain-aligned scene representations.

### 2025 — Brain-language fusion enables interactive neural readout and in-silico experimentation
*arXiv*
Authors: Victoria Bosch, Daniel Anthes, Adrien Doerig, Sushrut Thorat, Peter König, Tim C. Kietzmann

Neural decoding has historically been limited to static, non-interactive mappings between brain activity and specific labels or reconstructions. We introduce CorText, a framework that integrates functional magnetic resonance imaging (fMRI) neural activity directly into the latent semantic space of a Large Language Model (LLM). Trained on neural responses to naturalistic scenes, CorText facilitates open-ended natural language interaction with brain data, generating descriptive captions and answering nuanced queries based solely on neural input. The system demonstrates zero-shot generalization to novel semantic categories and enables in-silico cortical microstimulation experiments. By applying counterfactual prompts to neural activity, we observed consistent, graded mappings between brain states and generated language, shifting the neural decoding paradigm toward generative, flexible interfaces between neuroimaging data and linguistic output.

### 2025 — Why we linger: Memory encoding, rather than visual processing demand, drives fixation timing on natural scenes – evidence from a large-scale MEG dataset
*ResearchSquare*
Authors: Philip Sulewski, Carmen Amme, Martin N. Hebart, Peter König, Tim C. Kietzmann

We investigated the neural determinants of fixation duration using a large-scale active vision dataset (AVS) that includes magnetoencephalography (MEG), eye-tracking, and semantic scene captioning. Multivariate analysis of MEG source-space dynamics and artificial neural network (ANN) modeling revealed that fixation durations do not correlate with visual processing latency or ventral stream representational dynamics. Instead, fixation timing is positively correlated with predicted patch memorability and inclusion in natural language captions. Electrophysiological results show that longer fixations co-occur with increased theta-gamma phase-amplitude coupling in the hippocampus and frontal cortex. These findings suggest that the brain's decision to remain fixated is not constrained by early sensory processing bottlenecks but is actively driven by downstream requirements for stabilizing cortical representations during memory encoding.

### 2025 — Adopting a human developmental visual diet yields robust, shape-based AI vision
*arXiv*
Authors: Zejin Lu, Sushrut Thorat, Radoslaw M. Cichy, Tim C. Kietzmann

Artificial intelligence systems typically exhibit a significant misalignment with human vision, characterized by a heavy reliance on texture over shape and vulnerability to image distortions. We introduce the Developmental Visual Diet (DVD), a training curriculum for computer vision models that simulates the trajectory of human visual maturation from infancy to adulthood. By progressively increasing the complexity and fidelity of visual input, models naturally develop a robust shape bias and human-level abstract shape recognition. DVD-trained architectures demonstrate superior resilience to image corruptions and adversarial noise compared to large-scale foundation models trained on orders of magnitude more data. These results provide evidence that robust, human-aligned AI vision can be achieved by optimizing the developmental learning trajectory rather than merely scaling dataset size, offering a resource-efficient route toward biologically plausible artificial visual systems.
