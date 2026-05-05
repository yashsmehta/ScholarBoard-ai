---
name: Kenneth D. Miller
institution: Columbia University
department: Department of Neuroscience
lab_name: Miller Lab
main_research_area: computational neuroscience
total_citations: 16753
h_index: 51
---

# Kenneth D. Miller

*computational neuroscience* — Columbia University, Department of Neuroscience, Miller Lab.

## Background

Kenneth D. Miller is the Peter Taylor Professor of Neuroscience and a principal investigator at the Zuckerman Mind Brain Behavior Institute at Columbia University, where they co-direct the Center for Theoretical Neuroscience. Miller's research utilizes mathematical and computational methods to investigate the circuitry and development of the cerebral cortex, with a specific focus on the primary visual cortex (V1). Miller developed the Stabilized Supralinear Network (SSN) model, which provides a framework for understanding nonlinear cortical integration and context-dependent modulation of neural responses. Their current work uses data-driven modeling to investigate principles of neural computation and the self-organization of cortical circuits.

## Papers

### 2026 — Characteristics and dynamical signatures of recurrent cortical circuits during context-dependent processing
*bioRxiv*
Authors: Yue Kris Wu, Ho Yin Chau, Serena Di Santo, Kenneth D. Miller

This study employs data-driven computational modeling to infer the circuit architecture of the mouse primary visual cortex (V1) during context-dependent sensory processing. By fitting spatially extended stabilized supralinear networks (SSNs) to the observed responses of excitatory (E), parvalbumin (PV), somatostatin (SST), and vasoactive intestinal peptide (VIP) neurons, the researchers find that inhibitory stabilization is a dynamic process where the dominant inhibitory cell type affecting E-cells varies with stimulus parameters and spatial location. While PV-mediated stabilization is consistently required, the necessity for SST-mediated stabilization is stimulus-dependent. The analysis reveals that traditional uniform perturbations may fail to reveal paradoxical effects in certain inhibitory subtypes; instead, patterned perturbations are required to uncover the paradoxical response modes characteristic of inhibition-stabilized networks. Furthermore, the results demonstrate that recurrent excitatory connections and nonlinear input-output transformations are indispensable for reproducing cortical spatial response profiles, especially under conditions where feedforward thalamic inputs are weak.

### 2025 — Inpainting the Neural Picture: Inferring Unrecorded Brain Area Dynamics from Multi-Animal Datasets
*NeurIPS*
Authors: Ji Xia, Yizi Zhang, Shuqi Wang, Genevera I. Allen, Liam Paninski, Cole Lincoln Hurwitz, Kenneth D. Miller

The authors propose NeuroPaint, a transformer-based masked autoencoding architecture designed to reconstruct latent neural dynamics in unrecorded brain regions by exploiting the shared structure across large-scale multi-animal datasets. In typical high-density extracellular recordings (e.g., Neuropixels), only a subset of brain areas is sampled simultaneously. NeuroPaint leverages overlapping recorded regions across different sessions and animals to 'in-paint' missing activity through a cross-attention stitcher and temporal tokenization framework. Tested on both synthetic and large-scale empirical mouse datasets (e.g., the IBL brain-wide map), the model successfully infers single-neuron firing rates and inter-area interactions in unobserved regions. The results show that this approach significantly outperforms standard baselines like LFADS and enables population-level systems neuroscience analyses that transcend the physical limitations of single-subject recording sessions.

### 2025 — Stabilized Supralinear Network Model of Responses to Surround Stimuli in Primary Visual Cortex
*eNeuro*
Authors: Dina Obeid, Kenneth D. Miller

This research investigates the circuit mechanisms underlying visual center-surround interactions in primary visual cortex (V1) using the stabilized supralinear network (SSN) framework. The model accounts for three critical features of surround suppression: the suppression of both excitatory and inhibitory synaptic currents, the dominance of orientation-matched suppression (where surround suppression is strongest when the surround orientation matches the center orientation regardless of the cell’s preferred tuning), and feature-specific suppression observed in plaid stimuli. The authors demonstrate that a spatially two-dimensional SSN with strong local recurrent connectivity operates in an inhibition-stabilized regime that naturally reproduces these phenomena. The findings are further validated in a biologically realistic conductance-based spiking network, which also replicates the rapid decay kinetics of V1 activity following the silencing of thalamic inputs.

### 2025 — The geometry of the neural state space of decisions
*bioRxiv*
Authors: Mauro M. Monsalve-Mercado, Kenneth D. Miller

Through the analysis of large-scale population recordings from macaque area LIP during a motion-direction discrimination task, this study characterizes the geometric structure of decision-making in neural state space. Contrary to the standard drift-diffusion model (DDM) where evidence integration is viewed as a one-dimensional scaling of activity at choice targets, the data reveal that evidence accumulation occurs along adaptive, context-dependent directions on a curved decision manifold. The population activity undergoes a dynamical transition from sensory-driven deliberation to commitment, characterized by adaptive retinotopic shifts. The authors propose a mechanistic circuit model in which competitive interactions and self-excitation drive the 'winning' activity bump, transitioning the system from external-input-dominated to intrinsic-circuit-driven dynamics. The model’s predictions for how choice selectivity varies with trial speed are confirmed by single-trial and trial-averaged population analyses.

### 2024 — Contextual modulation emerges by integrating feedforward and feedback processing in mouse visual cortex
*Cell Reports*
Authors: Serena Di Santo, Mario Dipoppa, Andreas J. Keller, Morgane M. Roth, Massimo Scanziani, Kenneth D. Miller

This study develops a unified circuit model of the mouse primary visual cortex (V1) to explain how feedforward and feedback signals are integrated to generate complex contextual modulations. Reanalysis of V1 data reveals that increasing the spatial extent of a visual stimulus leads to only a minimal increase in the total area of the responsive neural population, a finding that challenges existing feedforward models of surround suppression (SS). The proposed model suggests that SS in Layer 2/3 is inherited from Layer 4, while 'inverse responses' (size-tuned responses to luminance-matched 'holes' in full-field gratings) are driven by wide feedback connections from higher cortical areas. Cross-orientation surround facilitation is explained by the integration of these feedback-driven inverse responses with feedforward-driven classical receptive field activity, illustrating a multi-stage mechanism for contextual processing across the cortical hierarchy.
