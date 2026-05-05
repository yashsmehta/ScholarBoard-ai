---
name: Tom P. Franken
institution: Washington University in St. Louis
department: Department of Neuroscience
lab_name: Franken Lab
main_research_area: sensory processing and perception
total_citations: 707
h_index: 11
---

# Tom P. Franken

*sensory processing and perception* — Washington University in St. Louis, Department of Neuroscience, Franken Lab.

## Background

Tom P. Franken is an Assistant Professor in the Department of Neuroscience at Washington University School of Medicine, where they investigate the neural mechanisms of sensory inference. Franken’s research focuses on how the brain resolves sensory ambiguities to represent objects, with an emphasis on border ownership assignment in the visual cortex and sound localization circuits in the brainstem. Using a combination of multielectrode electrophysiology, computational modeling, and behavioral assays, their work aims to characterize the cortical and subcortical computations that support stable perception. Franken has described how feedback signals organize into columns in the primate visual cortex and how artificial neural networks replicate brain-like grouping signals to predict dynamic visual scenes.

## Papers

### 2025 — Brain-like border ownership signals support prediction of natural videos
*iScience*
Authors: Zeyuan Ye, Ralf Wessel, Tom P. Franken

This research identifies the spontaneous emergence of border ownership (BOS) selectivity within PredNet, a hierarchical artificial neural network architecture optimized via self-supervision to perform next-frame prediction on naturalistic video sequences. The authors demonstrate that a subset of units in the network's representation and error layers develop BOS signals that remain invariant to luminance contrast polarity and exhibit robustness to common object transformations, mimicking the functional properties of BOS neurons in the primate visual cortex (e.g., area V4). Systematic ablation of these selective units reveals a disproportionate impairment in predictive accuracy for dynamic visual scenes containing moving objects. These findings suggest that the BOS computations observed in biological systems may not be specialized solely for static shape identification, but instead represent an emergent solution to the computational demand for stable spatiotemporal inference and anticipatory modeling in complex, dynamic visual environments.

### 2025 — Laminar organization of shadow-discounted lightness signals in area V4
*Journal of Vision*
Authors: Fatemeh Didehvar, Patrick Cavanagh, Tom P. Franken

Although the light reflected by an object varies directly with the amount of light falling on it, we perceive the object’s reflectance, its lightness (how black, gray, or white it is), as nearly constant. It is still poorly understood how the visual system does this: discounting the illumination to recover reflectance. Low-level theories emphasize spatial filtering operations at early stages of the visual system, whereas mid- and high-level theories propose that discounting occurs at higher stages. Here we leveraged high-density laminar recordings to study these computations in the primate brain. We used Neuropixels to record single- and multiunit neural activity from visual area V4 while a macaque viewed various scenes. On different trials we presented either shadow boards (checkerboards scenes partially in shadow), or paint boards, where the shadow edge was destroyed by averaging the luminance in each square. We presented the scenes such that the receptive field was centered on one square of the boards. We used current-source-density analysis to locate units to superficial, input or deep cortical layers. We then analyzed the shadow-discounted lightness signal (SDLS): we trained random forest decoders to predict the luminance of the square in the receptive field from neural responses to paint boards, and tested the decoders on responses not used during training, either to shadow boards (test-shadow) or to paint boards (test-paint). The SDLS, defined as the difference in predicted luminance between test-shadow and test-paint, was significantly positive (n=10 penetrations). We also found that the SDLS was not significant for neural populations in the input (granular) layer, but only in extragranular layers. Our experiments reveal shadow-discounted lightness signals in area V4. The laminar pattern suggests that these signals are computed at the level of V4 or higher areas, consistent with mid- and high-level theories of lightness.

### 2025 — Border ownership selectivity differs with cell class in visual area V4
*Journal of Vision*
Authors: Maryam Azadi, Fatemeh Didehvar, Tom P. Franken

An important step in the segmentation of visual scenes into discrete objects is assigning each border to the correct side of foreground (border ownership). Object borders are owned by one side at a time, suggesting a role for inhibitory neurons in the computation of border ownership. While border ownership signals are known to be prominent in primate visual cortex, the relation between border ownership selectivity and cell type is unknown. Here we investigated this using Neuropixels probes in macaque area V4. We inserted the probes orthogonally in the cortex to record from populations of well-isolated neurons while a macaque was viewing visual scenes. We first mapped the aggregate receptive field of the columnar population of simultaneously recorded cells. We then presented a luminance-defined square object such that only one of its borders fell in this receptive field. We varied the side-of-ownership, luminance contrast polarity and square orientation. We identified border ownership-selective (BOS) cells by assessing the statistical significance of the border ownership index (BOI, difference divided by sum of spike rates to opposite sides of ownership) at the border orientation corresponding to the preferred square position. We used spike duration to separate the population into narrow-spiking (putative inhibitory neurons) and broad-spiking (putative excitatory pyramidal) cells. As in prior studies, spike duration was strongly bimodal, and narrow-spiking cells had higher mean firing rates and higher peak-trough ratios than broad-spiking cells. About a third of both narrow-spiking and broad-spiking cells were tuned for border ownership. Broad-spiking BOS cells had significantly higher BOI magnitudes than narrow-spiking BOS cells. Our data suggest that putative pyramidal cells have stronger border ownership selectivity than putative inhibitory cells in V4. Because cells that project to other areas are pyramidal cells, this suggests that border ownership signals are prominent in the projections that leave V4.

### 2025 — Grouping signals in primate visual cortex
*Neuron · 3 citations*
Authors: Tom P. Franken, John H. Reynolds

Our understanding of scenes as organized collections of objects is remarkably stable despite eye movements. This may be due, in part, to neurons in area V2 that signal which side of a border is foreground (border ownership [BOS]) for hundreds of milliseconds after the defining information is deleted, and this signal transfers with eye movements. The grouping model explains this through a hypothetical short-latency grouping signal downstream. This would be a persistent pattern of preferred ownership toward the center of the receptive field, which also occurs de novo after eye movements. Our recordings identify such a grouping signal in macaque V4, which occurs fast enough to underlie BOS in V2. These V4 neurons are not as strongly tuned for contrast polarity as are BOS neurons. This suggests a division of labor in which grouping signals provide spatiotemporal continuity of segmented surfaces, whereas BOS neurons link this with feature information.

### 2024 — Brain-like border ownership signals support prediction of natural videos
*bioRxiv (Preprint)*
Authors: Zeyuan Ye, Ralf Wessel, Tom P. Franken

The study explores the development of border ownership (BOS) selectivity in PredNet, a deep-learning-based predictive coding model trained to anticipate future frames in natural video datasets. Quantitative analysis reveals that significant populations of neural units in the model exhibit selective firing dependent on the side-of-ownership of object borders, independent of the local contrast polarity. The researchers utilized ablation techniques to determine that these BOS-selective units are critical for the model's ability to maintain high-fidelity predictions during object motion. The emergence of these signals in a network lacking explicit object-level supervision indicates that scene segmentation circuits in the primate visual system may have evolved primarily to facilitate the prediction of future sensory inputs in dynamic environments, rather than to serve as a purely descriptive representational layer.
