---
name: Se-Bum Paik
institution: Korea Advanced Institute of Science and Technology
department: Department of Brain and Cognitive Sciences
lab_name: Cognitive Intelligence Laboratory
main_research_area: Computational and systems neuroscience
total_citations: 1919
h_index: 23
---

# Se-Bum Paik

*Computational and systems neuroscience* — Korea Advanced Institute of Science and Technology, Department of Brain and Cognitive Sciences, Cognitive Intelligence Laboratory.

## Background

Se-Bum Paik is a computational neuroscientist and Associate Professor at KAIST, where they direct the Cognitive Intelligence Laboratory. Paik’s research investigates the developmental principles underlying the functional architecture of sensory systems in both biological and artificial neural networks. By integrating theoretical neuroscience, computational modeling, and psychophysical experiments, Paik explores how cognitive functions and neural topographies, such as cortical orientation maps, emerge from spontaneous activity and structural constraints. Their work has demonstrated that visual capabilities, including face and object detection, can arise in untrained deep neural networks as a result of innate biological strategies for information processing.

## Papers

### 2026 — Brain-Inspired Warm-Up Training with Random Noise for Uncertainty Calibration
*Nature Machine Intelligence*
Authors: Jeonghwan Cheon, Se-Bum Paik

This study demonstrates a developmental 'warm-up' strategy using random noise to enhance the uncertainty calibration of deep neural networks, inspired by the spontaneous prenatal random activity in the mammalian brain. By pretraining networks with random inputs and stochastic labels before the onset of structured sensory experience, the authors demonstrate a significant reduction in Expected Calibration Error (ECE) and overconfidence across varied architectures, including ResNet and Vision Transformers. This bio-inspired initialization regularizes the latent space and reshapes the loss landscape, facilitating robust probabilistic inference without diminishing top-1 classification accuracy on standard benchmarks.

### 2025 — Gradual sensory maturation promotes abstract representation learning
*bioRxiv*
Authors: Jeonghwan Cheon, Se-Bum Paik

In biological systems, sensory organs mature gradually, exposing the brain to progressively higher-resolution inputs. This research investigates the computational benefits of this sensory maturation using neural network simulations and human psychophysics. The authors show that a low-to-high resolution training curriculum promotes the emergence of abstract, shape-based representations and prevents 'shortcut learning' of superficial high-frequency textures. This developmental scaffold results in enhanced out-of-distribution generalization, improved robustness to domain shifts, and more disentangled latent representations compared to models trained on static, high-fidelity data.

### 2025 — One-Time Soft Alignment Enables Resilient Learning without Weight Transport
*arXiv*
Authors: Jeonghwan Cheon, Jaehyuk Bae, Se-Bum Paik

Addressing the 'weight transport problem' in biologically plausible deep learning, the authors propose 'One-Time Soft Alignment' (OTSA), which approximates error gradients without continuous forward-backward weight synchronization. By implementing a soft alignment of synaptic weights during the initialization phase, the model achieves credit assignment efficiency comparable to standard backpropagation on large-scale tasks like ImageNet. Spectral analyses reveal that OTSA facilitates smoother gradient flow and convergence to flatter minima, ensuring robust performance against weight quantization and stochastic hardware noise in neuromorphic implementations.

### 2025 — Neuromimetic metaplasticity for adaptive continual learning without catastrophic forgetting
*Neural Networks*
Authors: Suhee Cho, Hyeonsu Lee, Seungdae Baek, Se-Bum Paik

This paper presents a neuromimetic metaplasticity framework inspired by human working memory to mitigate catastrophic forgetting in sequential learning. The model incorporates heterogeneous synapses with varying stability and plasticity, dynamically modulating individual learning rates based on synaptic importance to previous tasks. This mechanism allows the network to solidify critical weights while maintaining flexibility for new information, enabling effective class-incremental learning without extensive data replay or structural expansion. Benchmarking on Split-CIFAR and sequential tasks demonstrates that this adaptive plasticity model significantly outperforms traditional regularization techniques in stability and memory capacity.

### 2025 — Hard-wired visual filters for environment-agnostic object recognition
*Patterns*
Authors: Minjun Kang, Seungdae Baek, Se-Bum Paik

The study explores the hypothesis that innate, 'hard-wired' architectures in the early visual pathway provide a foundation for environment-agnostic perception. By replacing the initial layers of deep neural networks with fixed Gabor-like filters modeled after biological receptive fields (GbDNNs), the authors show that such architectures are highly resilient to significant domain shifts, such as transitions from photographs to sketches. The results indicate that fixed structural priors in early vision facilitate the encoding of global shape information while suppressing sensitivity to local textures and noise, offering a brain-inspired strategy for invariant object recognition across diverse environmental contexts.
