---
name: Martin A. Giese
institution: University of Tübingen
department: Section Computational Sensomotorics, Hertie Institute for Clinical Brain
  Research
lab_name: Section Computational Sensomotorics
main_research_area: Computational sensomotorics and action perception
total_citations: 11615
h_index: 52
---

# Martin A. Giese

*Computational sensomotorics and action perception* — University of Tübingen, Section Computational Sensomotorics, Hertie Institute for Clinical Brain Research.

## Background

Martin A. Giese is a Professor of Computational Sensomotorics at the University of Tübingen and leads a research section at the Hertie Institute for Clinical Brain Research and the Centre for Integrative Neuroscience. Giese’s research combines computational neuroscience and psychophysics to investigate the neural mechanisms underlying biological motion recognition and social perception. Their work involves the development of physiologically-inspired neural models and the use of computer animation to study how the brain represents body movements and facial expressions. This research applies these frameworks to clinical studies of movement disorders and social cognition deficits in psychiatric conditions.

## Papers

### 2025 — Facial expression recognition based on multi-domain norm-referenced encoding
*Neural Networks*
Authors: Michael Stettler, Alexander Lappe, Martin A. Giese

This study proposes a biologically-inspired neural mechanism to address the challenge of out-of-domain transfer in facial expression recognition, particularly when adapting models to unnatural morphologies like cartoon characters. The authors implement a norm-referenced encoding strategy where facial features are parameterized as deviation vectors relative to a domain-specific reference. By leveraging the principle that these relative deviations are preserved across distinct shape domains, the framework achieves extreme data efficiency, enabling successful adaptation to novel domains with as few as one training image. Evaluation on datasets featuring highly variable head shapes confirms the model's superior generalization and scalability compared to standard convolutional neural network benchmarks.

### 2025 — Another BRIXEL in the Wall: Towards Cheaper Dense Features
*arXiv*
Authors: Alexander Lappe, Martin A. Giese

The research introduces BRIXEL, a knowledge distillation framework aimed at reducing the computational and memory overhead associated with generating high-resolution dense feature maps in vision foundation models like DINOv3. To circumvent the quadratic complexity of transformer architectures at high input resolutions, the method employs a student network that learns to upsample its own feature maps to match the fidelity of a high-resource teacher. Empirical results demonstrate that BRIXEL significantly outperforms baseline models on dense downstream tasks while maintaining lower input resolutions, providing a computationally efficient path to achieving fine-grained spatial feature representation.

### 2025 — Register and [CLS] tokens yield a decoupling of local and global features in large ViTs
*arXiv*
Authors: Alexander Lappe, Martin A. Giese

This work investigates the emergence of high-frequency artifacts in the attention maps of self-supervised Vision Transformers such as DINOv2, identifying the model's tendency to repurpose patch tokens as implicit registers for global information as the underlying cause. While the integration of explicit register tokens cleans these attention maps, the authors demonstrate that this intervention induces a functional decoupling where global image semantics become isolated within the register tokens, losing their veridical correspondence with local features. The study further identifies similar decoupling effects for the [CLS] token in models lacking explicit registers, highlighting a critical trade-off between attention map interpretability and the integrative representation of visual information.

### 2024 — MacAction: Realistic 3D macaque body animation based on multi-camera markerless motion capture
*bioRxiv*
Authors: Lucas M. Martini, Anna Bognár, Rufin Vogels, Martin A. Giese

The authors present MacAction, an end-to-end pipeline for synthesizing high-fidelity 3D macaque body animations using synchronized multi-camera markerless motion capture and deep pose estimation. The system utilizes sparse manual keyframe annotations to achieve the kinematic precision required for life-like full-body simulations with 86 joints. Behavioral validation using eye-tracking with rhesus monkeys revealed a body-based uncanny valley effect, where animals exhibited conspecific-like gazing behavior for high-fidelity avatars but reduced engagement for intermediate levels of realism, confirming the sensitivity of the primate visual system to biomechanical realism in social stimuli.

### 2024 — Perceptual encoding of emotions in interactive bodily expressions
*iScience*
Authors: Andrea Christensen, Nick Taubert, Elisabeth M. J. Huis in 't Veld, Beatrice de Gelder, Martin A. Giese

This study explores how the human visual system perceptually integrates emotional signals from multiple interacting agents. Utilizing computer-animated dyads with independently manipulated emotional styles, the researchers demonstrate that the perception of an agent's emotion is systematically biased by the emotional context of its interaction partner. The results indicate that interacting emotional styles are jointly encoded by the brain rather than processed as independent signals, suggesting that the perception of social affect is fundamentally dependent on the interactive context and the relative alignment of emotional expressions between agents.
