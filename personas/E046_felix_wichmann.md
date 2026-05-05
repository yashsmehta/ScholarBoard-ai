---
name: Felix Wichmann
institution: University of Tübingen
department: Department of Computer Science
lab_name: Neural Information Processing Group
main_research_area: computational vision and psychophysics
total_citations: 18967
h_index: 46
---

# Felix Wichmann

*computational vision and psychophysics* — University of Tübingen, Department of Computer Science, Neural Information Processing Group.

## Background

Felix Wichmann is a Professor of Neural Information Processing at the University of Tübingen, where they investigate human perception through psychophysical experimentation and computational modeling. Wichmann’s work includes the statistical analysis of psychometric functions and the evaluation of deep neural networks as behavioral models of human vision. Their research integrates machine learning, Bayesian inference, and signal detection theory to study the connection between early spatial vision and high-level object recognition. Current projects in Wichmann's laboratory focus on "shortcut learning" in artificial systems, the role of shape versus texture in recognition, and the perceptual mechanisms underlying the detection of causality.

## Papers

### 2026 — Behavioral differences between humans and machines arise early in visual processing
*Journal of Vision*
Authors: Thomas Klein, Wieland Brendel, Felix A. Wichmann

This study interrogates the validity of Deep Neural Networks (DNNs) as computational models of human visual perception by analyzing behavioral discrepancies in object recognition. While DNNs demonstrate high predictive accuracy for primate cortical neural activity, psychophysical experiments reveal significant error inconsistencies. The authors find that these behavioral misalignments between humans and machines originate at the earliest stages of visual processing. The research highlights that DNNs fail to exhibit human-like robustness and representational alignment, particularly when challenged with out-of-distribution stimuli. The findings suggest that current architectures lack the fundamental mechanistic principles of the primate ventral stream, necessitating a shift toward image-computable models that more accurately reflect the biological constraints of human early vision.

### 2025 — Estimating the contribution of early and late noise in vision from psychophysical data
*Journal of Vision*
Authors: Jesús Malo, José Juan Esteve-Taboada, Guillermo Aguilar, Marianne Maertens, Felix A. Wichmann

This research addresses the longstanding challenge in psychophysics of disentangling the relative contributions of early-stage (e.g., photoreceptor) and late-stage (decision-level) inner noise in visual detection and discrimination. Utilizing noise propagation theory through a nonlinear model cascade, the authors develop a method to quantify these noise sources using only behavioral data. The analysis demonstrates that while threshold-only datasets require significant external noise to distinguish sources, the use of full psychometric functions allows for reliable quantification even in the absence of external noise. Quantitative estimates reveal that early visual processing substantially reduces retinal noise, with behavioral early noise levels found to be significantly lower than those predicted by theoretical models of cone photocurrents, such as ISETBio.

### 2024 — Plaid masking explained with input-dependent dendritic nonlinearities
*Scientific Reports*
Authors: Marcelo Bertalmío, Alexia Durán Vizcaíno, Jesús Malo, Felix A. Wichmann

The standard linear-nonlinear cascade model of spatial vision fails to account for plaid masking, a robust perceptual phenomenon where contrast thresholds for a test grating are elevated by a masking grating. This study proposes the Intrinsically Nonlinear Receptive Field (INRF) model, which replaces traditional linear filters with input-dependent dendritic nonlinearities. By implementing biologically realistic neurons where dendritic integration is sensitive to the specific spatiotemporal properties of the stimulus, the model successfully predicts experimental plaid masking data that has eluded the standard model for over three decades. The results suggest that these critical nonlinearities may be operative as early as the retinal ganglion cells, providing a more accurate representation of early spatial vision mechanics.

### 2024 — Error consistency between humans and machines as a function of presentation duration
*Journal of Vision*
Authors: Thomas Klein, Wieland Brendel, Felix A. Wichmann

Assessments of behavioral alignment between human observers and Artificial Neural Networks (ANNs) often utilize error consistency as a metric, yet the temporal constraints of human vision are frequently ignored. This paper systematically investigates how stimulus presentation duration (ranging from 8.3 ms to over 1000 ms) impacts error consistency across natural, lowpass-filtered, and noisy images. The authors demonstrate that although humans can perform 8-way object classification with single-frame (8.3 ms) exposures, increased presentation time significantly enhances both performance and behavioral alignment with ANNs. These findings suggest that fair human-machine comparisons must account for the time-dependent nature of human visual processing, particularly the role of recurrent cortical feedback in resolving difficult or corrupted visual inputs.

### 2024 — Comparing supervised learning dynamics: Deep neural networks match human data efficiency but show a generalisation lag
*arXiv*
Authors: Lukas S. Huber, Fred W. Mast, Felix A. Wichmann

This paper investigates the learning dynamics of deep neural networks (DNNs) relative to human observers in a supervised object recognition task. While humans exhibit near-immediate generalization to novel categories, DNNs frequently demonstrate a 'generalization lag,' requiring significantly more exposure to achieve comparable robustness to image distortions. The authors utilize a systematic psychophysical paradigm to compare the data efficiency and representational divergence between the two systems. The results indicate that while DNNs can match human data efficiency in certain controlled environments, their failure to generalize rapidly to out-of-distribution examples highlights a fundamental difference in the underlying learning algorithms or inductive biases, pointing toward a divergence in representational strategy.
