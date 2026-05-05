---
name: Taiki Fukiage
institution: NTT Communication Science Laboratories
department: Human Information Science Laboratory, Sensory Representation Research
  Group
lab_name: Sensory Representation Research Group
main_research_area: human visual perception and media technology
---

# Taiki Fukiage

*human visual perception and media technology* — NTT Communication Science Laboratories, Human Information Science Laboratory, Sensory Representation Research Group, Sensory Representation Research Group.

## Background

Taiki Fukiage is a Senior Research Scientist at NTT Communication Science Laboratories specializing in vision science and media engineering. Fukiage earned a Ph.D. from the University of Tokyo in 2015 and develops mathematical models of human visual information processing to optimize artificial displays, including AR and VR technologies. Their research includes visibility-based rendering techniques, the 'Deformation Lamps' projection system, and comparative analyses between human depth perception and deep neural network representations. Currently, Fukiage investigates how to align machine vision models with human perceptual biases to improve image naturalness and visual comfort.

## Papers

### 2026 — Accuracy Does Not Guarantee Human-Likeness in Monocular Depth Estimators
*AAAI Conference on Artificial Intelligence (AAAI)*
Authors: Yuki Kubota, Taiki Fukiage

While deep neural networks (DNNs) have reached or surpassed human-level performance on physical-based depth benchmarks like KITTI, the alignment of these models' latent representations with human perceptual space remains a significant challenge for robustness and interpretability. We systematically evaluated 69 state-of-the-art monocular depth estimation architectures, including supervised, self-supervised, and generative models, by comparing their error distributions with human perceptual judgments. Utilizing affine fitting to decompose depth prediction errors into interpretable components—specifically depth compression, scaling, shearing, and translation—we identified a distinct trade-off between model accuracy and human similarity. Our results demonstrate that higher performance on objective metrics does not necessarily result in error patterns that reflect human perceptual biases, highlighting a critical divergence between superhuman accuracy and human-like visual space representation.

### 2025 — Human-like monocular depth biases in deep neural networks
*PLOS Computational Biology*
Authors: Yuki Kubota, Taiki Fukiage

Human 3D vision from monocular 2D inputs is characterized by systematic distortions, such as distance compression and viewpoint-dependent affine shifts. We conducted a large-scale psychophysical comparison between human depth perception and 64 diverse DNN architectures using a novel human-annotated dataset of natural indoor scenes. By applying an exponential-affine error decomposition framework, we found that both humans and highly accurate DNNs exhibit consistent biases, including depth compression and vertical visual field priors. Strikingly, the correlation between a model's depth estimation accuracy and its similarity to human error patterns suggests a convergence toward human-like heuristics as models improve. However, significant differences remain in ordinal depth perception within affine-invariant spaces, suggesting that DNNs may prioritize metric accuracy over the structural relationships preserved in biological vision.

### 2024 — Low-Latency Ocular Parallax Rendering and Investigation of Its Effect on Depth Perception in Virtual Reality
*IEEE Transactions on Visualization and Computer Graphics*
Authors: Yuri Mikawa, Taiki Fukiage

Ocular parallax—the subtle change in retinal images caused by the rotation of the eye around its center—is a vital but often neglected depth cue in gaze-contingent displays. To investigate its contribution to visual perception under free eye-movement conditions, we developed a high-frequency (360 Hz) and ultra-low-latency (4.8 ms) ocular parallax rendering system featuring custom gaze-tracking at the eye's front nodal point. Psychophysical evaluations revealed that ocular parallax significantly improves binocular fusion in stereoscopic viewing, even when rendering latency is relatively high. Conversely, monocular depth perception through dynamic occlusion cues requires extremely low latencies (sub-20 ms) to remain stable. These findings establish critical temporal requirements for immersive gaze-contingent graphics and demonstrate the visual system's integration of extra-retinal signals with ocular parallax shifts.

### 2024 — Human-centric Image Rendering for Natural and Comfortable Viewing—Image Optimization Based on Human Visual Information Processing Models
*NTT Technical Review*
Authors: Taiki Fukiage

Standard display technologies often fail to maintain image fidelity when projected onto non-ideal surfaces or viewed through semi-transparent see-through displays due to interference from background patterns and ambient light. We propose a human-centric rendering framework that optimizes displayed content by leveraging mathematical models of early-stage visual information processing, including multiscale frequency decomposition and contrast sensitivity functions. By prioritizing the reproduction of visual features to which the human visual system is most sensitive—such as specific spatial frequency bands and luminance contrasts—the proposed model maintains perceptual naturalness and visual comfort even when physical compensation for surface irregularities is constrained by hardware limitations. This approach facilitates consistent visual quality in ubiquitous display environments and augmented reality applications.
