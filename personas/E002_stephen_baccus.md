---
name: Stephen Baccus
institution: Stanford University
department: Department of Neurobiology
lab_name: Baccus Lab
main_research_area: retinal circuit computation
total_citations: 8195
h_index: 34
---

# Stephen Baccus

*retinal circuit computation* — Stanford University, Department of Neurobiology, Baccus Lab.

## Background

Stephen Baccus investigates the circuit mechanisms through which the retina encodes and adapts to natural visual environments. By integrating large-scale multielectrode recordings with biophysically-inspired deep learning models, their lab characterizes the nonlinear transformations performed by retinal interneurons during processes like contrast adaptation and motion sensitivity. Baccus also explores ultrasonic neuromodulation as a high-resolution, non-invasive method for stimulating neural tissue. Their work focuses on identifying principles of neural computation that explain how the visual system compresses information while maintaining ethological relevance.

## Papers

### 2026 — Causal Interpretation of Neural Network Computations with Contribution Decomposition (CODEC)
*International Conference on Learning Representations (ICLR)*
Authors: Joshua Melander, Zaki Alaoui, Shenghua Liu, Surya Ganguli, Stephen Baccus

The authors present CODEC, a framework for mechanistic interpretability that shifts the focus from correlational feature mapping to direct causal analysis of how hidden units drive network outputs. By decomposing the vector of neural contributions into sparse, low-dimensional modes, the method uncovers the hierarchical evolution of computations in image-classification and retinal encoding models. A key finding is the emergence of decorrelated positive and negative effects on the output in deeper layers, facilitating precise causal manipulation of network behavior. In the context of the retina, CODEC identifies the combinatorial logic of model interneurons that underpins dynamic receptive field properties.

### 2026 — Hybrid Where-What Neural Decoder: Approximating Bayesian Inference for Real-Time Spike-Train Reconstruction
*International Journal of Advanced Research*
Authors: Lane McIntosh, Niru Maheswaranathan, Aran Nayebi, Stephen Baccus

This work introduces a hybrid neural decoding architecture designed for real-time reconstruction of visual stimuli from retinal spike trains. The model approximates Bayesian inference by partitioning the decoding task into 'where' (spatial localization) and 'what' (feature identification) pathways, effectively handling the stochastic nature of fixational eye movements. By leveraging deep learning to mimic probabilistic computations, the decoder demonstrates superior performance in high-acuity tasks and provides a framework for understanding how the brain might integrate diverse population features to maintain a stable visual percept despite continuous image drift.

### 2025 — A mechanistically interpretable model of the retinal neural code for natural scenes with multiscale adaptive dynamics
*bioRxiv (Preprint) / Under review at TMLR*
Authors: Satchel Grant, Xuehao Ding, Dongsoo Lee, Heike Stein, Lane McIntosh, Niru Maheswaranathan, Stephen Baccus

The researchers developed a three-layer convolutional neural network (CNN) modified with local recurrent synaptic dynamics to model the responses of salamander retinal ganglion cells to complex natural scenes. By integrating a linear-nonlinear-kinetic (LNK) component, the model captures multiscale contrast adaptation spanning several orders of magnitude in time. The internal units of the network are directly relatable to retinal interneurons, allowing for a mechanistic explanation of how specific synaptic pathways contribute to ethological retinal computations and predictive coding under naturalistic conditions.

### 2024 — Adaptation of retinal discriminability to natural scenes
*bioRxiv (Preprint)*
Authors: Xuehao Ding, Dongsoo Lee, Joshua Brendan Melander, Stephen Baccus

Using methods from information geometry and generative machine learning, this study investigates how the discriminability of a salamander retinal ganglion cell population is optimized for natural visual environments. By analyzing the manifolds of natural stimuli and their corresponding neural representations, the authors show that the retina dynamically adapts its sensitivity to enhance information transmission, particularly for localized motion signals. Critically, the analysis refutes the idea that noise correlations are optimized to boost information; instead, they are shown to be a deleterious but inevitable consequence of the shared circuitry required for spatiotemporal adaptation.

### 2024 — Classification and analysis of retinal interneurons by computational structure under natural scenes
*bioRxiv (Preprint)*
Authors: Dongsoo Lee, Juyoung Kim, Stephen Baccus

The paper presents a novel approach to the functional classification of mouse retinal amacrine cells using high-resolution optical recordings and interpretable machine learning. By fitting a two-layer convolutional neural network to responses elicited by natural movies, the authors successfully categorized diverse interneuron types based on their internal computational roles. The study demonstrates that model-defined interneurons correspond to distinct biological amacrine cell types, revealing the specific inhibitory pathways that modulate ganglion cell output to encode natural scenes.
