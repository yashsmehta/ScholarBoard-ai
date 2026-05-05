---
name: Carlos Ponce
institution: Harvard University
department: Department of Neurobiology, Harvard Medical School
lab_name: Ponce Lab
main_research_area: Visual neuroscience and machine learning
total_citations: 1242
h_index: 14
---

# Carlos Ponce

*Visual neuroscience and machine learning* — Harvard University, Department of Neurobiology, Harvard Medical School, Ponce Lab.

## Background

Carlos Ponce is an Assistant Professor of Neurobiology who investigates the neural mechanisms of visual recognition and perception. Ponce's laboratory uses electrophysiological recordings in rhesus macaques and deep learning frameworks, including generative adversarial networks and convolutional neural networks, to identify visual features encoded by neurons in the cortical hierarchy. Through closed-loop experimental designs, Ponce extracts data from the brain to characterize the internal models the primate visual system uses to interpret complex, naturalistic scenes. This approach links biological vision and artificial intelligence to refine automated recognition technologies and determine how sensory signals become cognitive representations.

## Papers

### 2025 — Brain feature maps reveal progressive animal-feature representations in the ventral stream
*Science Advances · 1 citations*
Authors: Zhanqi Zhang, Till S. Hartmann, Richard T. Born, Margaret S. Livingstone, Carlos R. Ponce

Primate visual recognition is hypothesized to rely on object-centric representations, but cortical neurons may instead follow organizational principles based on generic features across textures and environments. This study utilized multielectrode arrays to record from V1/V2, V4, and posterior inferotemporal (PIT) cortex, employing an unsupervised heatmap approach to characterize local operations within natural scenes. We discovered that while foveal populations across the hierarchy respond to entire scenes, their activity focuses on salient subregions within object contours. Notably, there is a progressive increase in selectivity for animal-related features, such as faces and limbs, along the visual hierarchy. This trend was consistent with biological tuning but diverged from various artificial neural network architectures, suggesting that the monkey ventral stream is fundamentally organized to prioritize ethologically relevant local animal features over general object configurations.

### 2025 — Structure as an inductive bias for brain–model alignment
*Nature Machine Intelligence*
Authors: Binxu Wang, Carlos R. Ponce

The alignment between artificial neural networks (ANNs) and the biological visual system remains a central challenge in computational neuroscience. Recent evidence suggests that standard convolutional architectures exhibit inherent alignment with cortical representations even before task-specific training. This work evaluates how structural constraints in deep learning models serve as inductive biases that facilitate this alignment. We argue that the architectural regularities of ANNs, such as spatial locality and weight sharing, mirror the fundamental organizational principles of the primate ventral stream. These structural properties may be more critical for achieving brain-like representations than the specific objectives of the training tasks themselves, suggesting that future models should prioritize biological architectural constraints to improve their fidelity as digital twins of the visual cortex.

### 2024 — Functional segregation of inputs in artificial neural networks for vision
*ICLR 2025 (OpenReview Preprint)*
Authors: Giordano Ramos-Traslosheros, Carlos R. Ponce

Biological and artificial intelligence systems both utilize signed inputs, yet the role of inhibitory signals in high-level visual representations like the inferotemporal (IT) cortex is poorly understood. This study investigated how ImageNet-trained artificial neural networks (ANNs) and macaque IT neurons segregate learned representations into positive and negative weights. By employing gradient-based feature visualization and ablation of weight polarities, we found that ReLU-based ANNs segregate object and foreground information into positive weights, while background and contextual information are primarily encoded in negative weights. This segregation was found to be dependent on signal rectification, as Tanh-based networks failed to maintain this distinction. Similar results obtained when modeling primate neuronal responses suggest that signal rectification and inhibitory mechanisms are critical for shaping feature selectivity in the primate ventral stream.

### 2024 — A concentration of visual cortex-like neurons in prefrontal cortex
*Nature Communications · 8 citations*
Authors: Olivia Rose, Carlos R. Ponce

While visual recognition is primarily attributed to the ventral stream, recent evidence suggests that the ventrolateral prefrontal cortex (vlPFC) plays a significant role in visual processing. This study investigated whether vlPFC neurons possess sensory properties comparable to the visual cortex, such as receptive fields, image selectivity, and the ability to guide the synthesis of highly activating stimuli through generative networks. By recording from vlPFC sites in monkeys, we identified a subpopulation of neurons that exhibit stable visual encoding of world statistics. These neurons appear to be anatomically clustered, consistent with functional organization identified via fMRI. The findings suggest that stable visual representations in the vlPFC may provide the necessary foundation for the integration of sensory and cognitive processes across the brain.

### 2024 — Neural Dynamics of Object Manifold Alignment in the Ventral Stream
*bioRxiv (Preprint)*
Authors: Binxu Wang, Carlos R. Ponce

Primate ventral stream neurons respond to an immense landscape of natural images, yet the principles governing their alignment with generative image manifolds are unclear. This study used a closed-loop evolutionary algorithm to optimize stimuli from two generative networks: DeePSim, which parameterizes local image patterns, and BigGAN, which emphasizes object identity and configurational nuisance variables. We recorded from multi-electrode arrays in V1, V4, and posterior IT (PIT) of macaque monkeys. While V1 and V4 neurons showed stronger alignment with the local pattern-based DeePSim manifold, PIT neurons demonstrated comparable alignment to both textural and object-centric manifolds. Crucially, object-like responses in PIT emerged later than texture-driven responses, suggesting that global configurational selectivity requires additional processing. These results indicate that the primate visual system aligns to a representational space that current artificial models do not fully capture.
