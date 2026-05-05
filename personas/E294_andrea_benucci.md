---
name: Andrea Benucci
institution: RIKEN Center for Brain Science
department: School of Biological and Behavioural Sciences
lab_name: Laboratory for Neural Circuits and Behavior
main_research_area: Visual and computational neuroscience
total_citations: 4475
h_index: 18
---

# Andrea Benucci

*Visual and computational neuroscience* — RIKEN Center for Brain Science, School of Biological and Behavioural Sciences, Laboratory for Neural Circuits and Behavior.

## Background

Andrea Benucci is a neuroscientist who investigates the computational principles of sensory processing and visual perception. Benucci's research integrates large-scale neural recordings, such as two-photon imaging and high-density electrophysiology, with patterned optogenetic manipulations and artificial neural network modeling. They developed automated, high-throughput behavioral platforms that standardize mouse training for complex visual tasks to facilitate the study of population-level neural dynamics. Their recent work focuses on the plasticity of cortical representations and how non-visual signals, including motor-related inputs, are integrated within the visual hierarchy to support perceptual stability and decision-making.

## Papers

### 2024 — Regularizing hyperparameters of interacting neural signals in the mouse cortex reflect states of arousal
*PLOS Computational Biology*
Authors: Dmitry R. Lyamzin, Andrea Alamia, Mohammad Abdolrahmani, Ryo Aoki, Andrea Benucci

In this study, the researchers utilized a generalized linear model (GLM) to analyze the interaction dynamics between saccade- and body-movement-related neural activations in the mouse posterior cortex. To address the problem of overfitting in high-dimensional series expansions, they employed automatic locality determination (ALD) regularization to estimate second-order interaction kernels. They discovered that the resulting regularization hyperparameters, specifically the precision and prior width, exhibited significant across-animal variability. This variability was not stochastic but systematically correlated with fluctuations in the animals' internal arousal levels and task engagement, as quantified by pupil size and the signal-to-noise ratio of visually evoked responses. The findings demonstrate that statistical hyperparameters in encoding models can serve as physiological biomarkers for global brain states, providing a layer of interpretability beyond traditional model parameters.

### 2024 — Efficient coding of natural images in the mouse visual cortex
*Nature Communications*
Authors: Federico Bolaños, Javier G. Orlandi, Ryo Aoki, Akshay V. Jagadeesh, Justin L. Gardner, Andrea Benucci

This research investigates the neural substrates of texture perception in mice, focusing on the hierarchy of the ventral visual stream. Using two-photon calcium imaging and mesoscale widefield recordings, the authors characterized neuronal population responses to synthetic texture stimuli generated via deep convolutional neural networks. They found that the secondary visual area (LM) exhibits a significantly higher degree of selectivity for higher-order image statistics compared to the primary visual cortex (V1). Texture representations were embedded in distinct, low-dimensional neural subspaces whose geometric distances correlated with the statistical similarity of the textures and the mice's behavioral discrimination thresholds. The study establishes a quantitative link between stimulus statistics, neural manifold geometry, and perceptual sensitivity, identifying texture vision as a functional hallmark of efficient coding in the murine cortical hierarchy.

### 2023 — Distributed context-dependent choice information in mouse posterior cortex
*Nature Communications · 17 citations*
Authors: Javier G. Orlandi, Mohammad Abdolrahmani, Ryo Aoki, Dmitry R. Lyamzin, Andrea Benucci

Choice information appears in multi-area brain networks mixed with sensory, motor, and cognitive variables. In the posterior cortex-traditionally implicated in decision computations-the presence, strength, and area specificity of choice signals are highly variable, limiting a cohesive understanding of their computational significance. Examining the mesoscale activity in the mouse posterior cortex during a visual task, we found that choice signals defined a decision variable in a low-dimensional embedding space with a prominent contribution along the ventral visual stream. Their subspace was near-orthogonal to concurrently represented sensory and motor-related activations, with modulations by task difficulty and by the animals' attention state. A recurrent neural network trained with animals' choices revealed an equivalent decision variable whose context-dependent dynamics agreed with that of the neural data. Our results demonstrated an independent, multi-area decision variable in the posterior cortex, controlled by task features and cognitive demands, possibly linked to contextual inference computations in dynamic animal-environment interactions.

### 2022 — Movement-related signals support classification invariance for stable visual perception
*Journal of Vision*
Authors: Andrea Benucci

Stable visual perception during eye and body movements suggests neural algorithms that convert location information—"where” type of signals—across multiple frames of reference, for instance, from retinocentric to craniocentric coordinates. Accordingly, numerous theoretical studies have proposed biologically plausible computational processes to achieve such transformations. However, how coordinate transformations can then be used by the hierarchy of cortical visual areas to produce stable perception remains largely unknown. Here, we explore the hypothesis that perceptual stability equates to robust classification of visual features relative to movements, that is, a “what” type of information processing. We demonstrate in CNNs that neural signals related to eye and body movements support accurate image classification by making “where” type of computations for coordinate transformations faster to learn and more robust relative to input perturbations. Accordingly, movement signals contributed to the emergence of activity manifolds associated with image categories in late CNN layers and to movement-related response modulations in network units as observed experimentally during saccadic eye movements. Therefore, by equating perception to classification, we provide a simple unifying computational framework to explain the role of movement signals in support of stable perception in dynamic interactions with the environment.

### 2022 — Motor-related signals support localization invariance for stable visual perception
*PLoS Computational Biology · 9 citations*
Authors: Andrea Benucci

Our ability to perceive a stable visual world in the presence of continuous movements of the body, head, and eyes has puzzled researchers in the neuroscience field for a long time. We reformulated this problem in the context of hierarchical convolutional neural networks (CNNs)-whose architectures have been inspired by the hierarchical signal processing of the mammalian visual system-and examined perceptual stability as an optimization process that identifies image-defining features for accurate image classification in the presence of movements. Movement signals, multiplexed with visual inputs along overlapping convolutional layers, aided classification invariance of shifted images by making the classification faster to learn and more robust relative to input noise. Classification invariance was reflected in activity manifolds associated with image categories emerging in late CNN layers and with network units acquiring movement-associated activity modulations as observed experimentally during saccadic eye movements. Our findings provide a computational framework that unifies a multitude of biological observations on perceptual stability under optimality principles for image classification in artificial neural networks.
