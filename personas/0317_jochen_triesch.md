---
name: Jochen Triesch
institution: Goethe University Frankfurt
department: Department of Physics and Department of Computer Science and Mathematics,
  Goethe University Frankfurt
lab_name: Research Group of Jochen Triesch
main_research_area: computational neuroscience and developmental AI
total_citations: 8690
h_index: 44
---

# Jochen Triesch

*computational neuroscience and developmental AI* — Goethe University Frankfurt, Department of Physics and Department of Computer Science and Mathematics, Goethe University Frankfurt, Research Group of Jochen Triesch.

## Background

Jochen Triesch holds positions as a Senior Fellow at the Frankfurt Institute for Advanced Studies and a Professor at Goethe University Frankfurt, specializing in the self-organization of intelligent behavior. Triesch developed the 'Active Efficient Coding' framework, which provides a theory for the joint development of sensory coding and motor control in biological systems such as binocular vision. Their research integrates computational modeling, machine learning, and developmental robotics to study how neural circuits adapt through synaptic plasticity and how artificial systems can emulate human-like cognitive development. Triesch currently focuses on developmental artificial intelligence, spiking neural networks, and the mathematical principles governing neural competition for synaptic resources.

## Papers

### 2025 — MIMo grows! Simulating body and sensory development in a multimodal infant model
*2025 IEEE International Conference on Development and Learning (ICDL)*
Authors: Francisco M. López, Miles Lenz, Marco G. Fedozzi, Arthur Aubret, Jochen Triesch

This study introduces MIMo v2, an expanded multimodal infant model implemented in the MuJoCo physics engine to facilitate the investigation of sensorimotor development. Unlike previous static embodiments, this version incorporates a dynamic growth module that modulates physical size, body mass, and joint actuation capabilities based on longitudinal pediatric data from birth to 24 months. The platform integrates bio-inspired features including a foveated visual system with age-dependent acuity scaling and stochastic sensorimotor latencies that simulate finite signal transmission speeds within the nervous system. The architecture is designed to support the autonomous acquisition of complex motor milestones, such as crawling and self-touch, providing a realistic in silico environment for modeling the co-development of body and mind.

### 2025 — Homeostatic regulation across fast and slow timescales through aggregate synaptic dynamics
*bioRxiv*
Authors: Petros Evgenios Vlachos, Jochen Triesch

The authors propose 'aggregate scaling,' a novel computational framework for neuronal homeostasis that models synapses as competitors for a shared pool of limited molecular building blocks. This approach addresses the discrepancy between the rapid timescales required for theoretical network stability and the slow kinetics of biological homeostatic plasticity (e.g., AMPA receptor trafficking). By integrating the competitive redistribution of these resources with Hebbian learning, the model achieves global stability and prevents runaway excitation in recurrent circuits. The resulting dynamics preserve essential physiological properties, including stable firing rates at homeostatic set-points and log-normal synaptic weight distributions, while reproducing experimental observations of slow-acting compensatory scaling during prolonged activity perturbations.

### 2025 — Hierarchical Residuals Exploit Brain-Inspired Compositionality
*European Symposium on Artificial Neural Networks, Computational Intelligence and Machine Learning (ESANN 2025)*
Authors: Francisco M. López, Jochen Triesch

This paper presents Hierarchical Residual Networks (HiResNets), a deep learning architecture inspired by the multi-level connectivity of the mammalian brain, specifically the direct skip connections from subcortical structures to various stages of the cortical hierarchy. By incorporating long-range residual connections between disparate hierarchical layers, the network is biased toward learning feature maps relative to compressed representations provided by skip links, thereby more effectively exploiting hierarchical compositionality. Experiments across several convolutional benchmarks, including modified ResNet-18 and ResNet-101 architectures, demonstrate that hierarchical residuals significantly improve classification accuracy and accelerate convergence. Analytical results suggest that these long-range projections facilitate more efficient semantic abstraction by providing richer gradient flow and structural priors.

### 2025 — A spiking neural network for active efficient coding
*Frontiers in Robotics and AI*
Authors: Thomas Barbier, Céline Teulière, Jochen Triesch

The authors develop the first fully spiking implementation of the Active Efficient Coding (AEC) framework, utilizing asynchronous inputs from neuromorphic event-based cameras. The system consists of a two-layer spiking neural network (SNN) that learns to efficiently encode visual features (resembling simple and complex cells in V1) through unsupervised spike-timing-dependent plasticity (STDP) and homeostatic mechanisms. The population activity of the encoding layers generates an intrinsic reward signal based on coding efficiency, which drives a spiking reinforcement learning agent. This agent learns closed-loop oculomotor control, including visual tracking of translating objects and gaze stabilization on rotating stimuli, without external supervision or extrinsic rewards. This work demonstrates the feasibility of achieving self-calibrating, energy-efficient sensorimotor learning in fully neuromorphic architectures.

### 2025 — Human Gaze Boosts Object-Centered Representation Learning
*arXiv*
Authors: Timothy Schaumlöffel, Arthur Aubret, Gemma Roig, Jochen Triesch

This work investigates how the foveated nature of human vision and active gaze behavior influence the self-supervised learning (SSL) of visual representations. By simulating five months of egocentric visual experience using the Ego4D dataset and human gaze prediction models, the researchers extracted gaze-centered foveal crops to mimic the selective amplification of central visual information. Training a time-contrastive SSL model on these modified streams revealed that focusing on central vision significantly improves the formation of object-centered representations compared to uniform full-field training. The analysis demonstrates that the SSL model successfully leverages the temporal slowness inherent in gaze movements to disentangle foreground objects from backgrounds, providing a critical step toward bio-inspired unsupervised visual learning from natural egocentric data.
