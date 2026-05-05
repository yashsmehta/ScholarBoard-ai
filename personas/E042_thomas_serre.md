---
name: Thomas Serre
institution: Brown University
department: Cognitive, Linguistic, and Psychological Sciences; Computer Science
lab_name: Serre Lab
main_research_area: computational and biological vision
total_citations: 22171
h_index: 56
---

# Thomas Serre

*computational and biological vision* — Brown University, Cognitive, Linguistic, and Psychological Sciences; Computer Science, Serre Lab.

## Background

Thomas Serre is a Professor of Cognitive, Linguistic, and Psychological Sciences and Computer Science at Brown University. Serre conducts research at the intersection of biological and artificial vision, focusing on the computational principles of the visual cortex. Their work investigates how recurrent and feedback circuitry support visual reasoning and perception. By developing brain-inspired deep learning architectures and cognitive benchmarks, Serre aims to quantify the alignment between human and machine vision to advance neuroscience and artificial intelligence.

## Papers

### 2025 — Better artificial intelligence does not mean better models of biology
*Trends in Cognitive Sciences*
Authors: Drew Linsley, Pinyuan Feng, Thomas Serre

While deep neural networks (DNNs) were initially characterized by increasing alignment with primate perceptual and neural data as they achieved higher performance on computer vision benchmarks, recent empirical evidence suggests this alignment has plateaued or diverged as models scale toward superhuman accuracy. The authors argue that this divergence indicates the emergence of visual strategies in artificial systems that differ fundamentally from the biological constraints of primates. By evaluating representational and functional alignment across three distinct benchmarks, they posit that engineering-driven optimization for large-scale internet data is insufficient for modeling biological vision. They propose that computational neuroscience must prioritize algorithms intrinsically grounded in biological visual principles rather than maximizing performance on standard AI benchmarks.

### 2025 — Feature binding in biological and artificial vision
*Trends in Cognitive Sciences*
Authors: Pieter R. Roelfsema, Thomas Serre

This work reviews the classical 'property binding problem' in vision science, examining how the brain integrates features like color and motion into coherent object representations. The authors evaluate traditional modular theories of functional segregation against evidence from deep learning models and large-scale clinical lesion studies. They find that deep neural networks (DNNs) achieve state-of-the-art performance in complex visual recognition without utilizing the explicit binding mechanisms, such as temporal synchrony, historically hypothesized to be essential for biological vision. The review suggests that natural vision may instead rely on a distributed, covariance-based representational architecture, and it discusses how this perspective reconciles findings of specialization without the need for strict segregation in the primate visual cortex.

### 2025 — Tracking objects that change in appearance with phase synchrony
*International Conference on Learning Representations (ICLR)*
Authors: Sabine Muzellec, Drew Linsley, Alekh Karkada Ashok, Ennio Mingolla, Girik Malik, Rufin VanRullen, Thomas Serre

The authors examine the computational hypothesis that neural synchrony serves as an attentional mechanism allowing biological visual systems to track objects as they undergo significant appearance transformations due to lighting, pose, or non-rigidity. They introduce the Complex-Valued Recurrent Neural Network (CV-RNN), a novel architecture where neural magnitude encodes feature identity and phase represents spatial coordinates, enabling the decoupling of location from appearance. Performance is evaluated using 'FeatureTracker,' a large-scale challenge testing the ability of observers to track appearance-morphing stimuli. While state-of-the-art feedforward and standard recurrent neural networks fail to maintain object identity under these shifts, the CV-RNN demonstrates human-like tracking capabilities, providing a computational proof-of-concept for phase synchronization as a neural substrate for dynamic object tracking.

### 2025 — The 3D-PC: A benchmark for visual perspective taking in humans and machines
*International Conference on Learning Representations (ICLR)*
Authors: Drew Linsley, Peisen Zhou, Alekh Karkada Ashok, Akash Nagaraj, Gaurav Suhas Gaonkar, Francis Lewis, Zygmunt Pizlo, Thomas Serre

Visual Perspective Taking (VPT)—the ability to reason about an agent's egocentric viewpoint within a 3D environment—is a critical component of human spatial intelligence that requires robust 3D scene processing. The authors introduce the 3D Perception Challenge (3D-PC) to evaluate whether emergent 3D analysis capabilities in deep neural networks (DNNs) are sufficient for VPT. The benchmark comprises three tasks: depth order estimation, basic VPT (VPT-basic), and a controlled task (VPT-Strategy) designed to eliminate heuristic visual shortcuts. Experiments involving 327 DNNs show that while models often exceed human performance in depth ordering, they fail significantly in VPT-basic. Furthermore, models fine-tuned on VPT-basic fail to generalize to VPT-Strategy, highlighting a persistent gap between artificial systems and human-like 3D geometric reasoning.

### 2024 — Deceptive learning in histopathology
*Histopathology*
Authors: Sahar Shahamatdar, Daryoush Saeed-Vafa, Drew Linsley, Farah Khalil, Katherine Lovinger, Lester Li, Howard T. McLeod, Sohini Ramachandran, Thomas Serre

The authors systematically evaluate the trustworthiness of visual strategies learned by deep neural networks (DNNs) in histopathological image analysis. Using a dataset of whole-slide images (WSIs) from lung adenocarcinoma, they compare DNN performance on tumor detection, tissue-of-origin identification, and molecular profiling of KRAS and EGFR mutations. While DNNs demonstrate robust and generalizable strategies for tumor localization, the study reveals that their success in molecular profiling is 'deceptive,' relying on spurious correlations between histological subtypes and specific mutations rather than direct morphological indicators of genotype. This finding is confirmed through failure to generalize to laser-capture microdissection datasets, emphasizing the necessity of interpretability frameworks to differentiate between reliable diagnostic tools and models exploiting dataset-specific biases.
