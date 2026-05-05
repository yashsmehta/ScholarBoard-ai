---
name: Kendrick Kay
institution: University of Minnesota
department: Department of Radiology
lab_name: Computational Visual Neuroscience Laboratory (CVN Lab)
main_research_area: computational visual neuroscience
total_citations: 11859
h_index: 48
---

# Kendrick Kay

*computational visual neuroscience* — University of Minnesota, Department of Radiology, Computational Visual Neuroscience Laboratory (CVN Lab).

## Background

Kendrick Kay is an Associate Professor at the University of Minnesota’s Center for Magnetic Resonance Research (CMRR) specializing in the intersection of computational modeling and high-resolution functional MRI. Kay's research focuses on developing predictive encoding models to characterize how the human visual cortex represents naturalistic stimuli and facilitates perceptual decision-making. They have developed neuroimaging resources, such as the Natural Scenes Dataset (NSD), and statistical tools like GLMsingle for fMRI response estimates. Kay's current investigations use ultra-high-field (7T and 10.5T) imaging to resolve functional architectures across cortical layers and columns.

## Papers

### 2026 — A 7T fMRI dataset of synthetic images for out-of-distribution modeling of vision
*Nature Communications*
Authors: Alessandro T. Gifford, Radoslaw M. Cichy, Thomas Naselaris, Kendrick Kay

The authors present NSD-synthetic, a high-resolution 7 Tesla fMRI dataset comprising neural responses from eight participants to a suite of 284 controlled synthetic images. While contemporary massive visual neural datasets like the Natural Scenes Dataset (NSD) have advanced visual encoding models, their stimuli typically reside within a narrow naturalistic distribution, limiting the assessment of out-of-distribution (OOD) generalization. Using multidimensional scaling (MDS), this study demonstrates that neural responses to synthetic stimuli are distinct from responses to natural scenes and reliably encode stimulus-related signals. OOD generalization tests reveal that self-supervised deep neural networks (DNNs) significantly outperform task-supervised counterparts in predicting cortical activity for synthetic images, a distinction not readily apparent when using in-distribution naturalistic test sets. The findings establish that the magnitude of model failure is predicted by the geometric distance between test data and training distributions, providing a benchmark for developing more robust computational models of the human visual system.

### 2025 — Disentangling signal and noise in neural responses through generative modeling
*PLoS Computational Biology · 1 citations*
Authors: Kendrick Kay, Jacob S. Prince, Thomas Gebhart, Greta Tuckute, Jingyang Zhou, Thomas Naselaris, Heiko H. Schütt

Measurements of neural responses to identically repeated experimental events often exhibit large amounts of variability. This noise is distinct from signal, operationally defined as the average expected response across repeated trials for each given event. Accurately distinguishing signal from noise is important, as each is a target that is worthy of study (many believe noise reflects important aspects of brain function) and it is important not to confuse one for the other. Here, we describe a principled modeling approach in which response measurements are explicitly modeled as the sum of samples from multivariate signal and noise distributions. In our proposed method-termed Generative Modeling of Signal and Noise (GSN)-the signal distribution is estimated by subtracting the estimated noise distribution from the estimated data distribution. Importantly, GSN improves estimates of the signal distribution, but does not provide improved estimates of responses to individual events. We validate GSN using ground-truth simulations and show that it compares favorably with related methods. We also demonstrate the application of GSN to empirical fMRI data to illustrate a simple consequence of GSN: by disentangling signal and noise components in neural responses, GSN denoises principal components analysis and improves estimates of dimensionality. We end by discussing other situations that may benefit from GSN's characterization of signal and noise, such as estimation of noise ceilings for computational models of neural activity. A code toolbox for GSN is provided with both MATLAB and Python implementations.

### 2025 — A two-dimensional space of linguistic representations shared across individuals
*bioRxiv (Cold Spring Harbor Laboratory) · 1 citations*
Authors: Greta Tuckute, Elizabeth J. Lee, Yongtian Ou, Evelina Fedorenko, Kendrick Kay

Our ability to extract meaning from linguistic inputs and package ideas into word sequences is supported by a network of left-hemisphere frontal and temporal brain areas. Despite extensive research, previous attempts to discover differences among these language areas have not revealed clear dissociations or spatial organization. All areas respond similarly during controlled linguistic experiments as well as during naturalistic language comprehension. To search for finer-grained organizational principles of language processing, we applied data-driven decomposition methods to ultra-high-field (7T) fMRI responses from eight participants listening to 200 linguistically diverse sentences. Using a cross-validation procedure that identifies shared structure across individuals, we find that two components successfully generalize across participants, together accounting for about 32% of the explainable variance in brain responses to sentences. The first component corresponds to processing difficulty, and the second-to meaning abstractness; we formally support this interpretation through targeted behavioral experiments and information-theoretic measures. Furthermore, we find that the two components are systematically organized within frontal and temporal language areas, with the meaning-abstractness component more prominent in the temporal regions. These findings reveal an interpretable, low-dimensional, spatially structured representational basis for language processing, and advance our understanding of linguistic representations at a detailed, fine-scale organizational level.

### 2024 — Principles of intensive human neuroimaging
*Trends in Neurosciences*
Authors: Eline R. Kupers, Tomas Knapen, Elisha P. Merriam, Kendrick N. Kay

This article proposes a shift in human neuroimaging strategy toward 'intensive' fMRI, a methodology characterized by extensive, deep sampling of cognitive phenomena within individual subjects to support high-fidelity computational modeling and single-voxel investigation. Contrastive with 'wide' fMRI (large cohorts, brief scanning) and 'deep' fMRI (fewer subjects, more hours), intensive fMRI emphasizes the optimization of data quality, the inclusion of rich hypothesis-driven experimental designs, and the strategic curation of public datasets to maximize community impact. The authors discuss the fundamental principles and trade-offs of this approach, arguing that intensive sampling is essential for resolving the fine-scale functional organization of the brain and for developing precise models that generalize across individual variations in cortical topography.

### 2024 — The Natural Scenes Dataset: Lessons Learned and What's Next?
*Journal of Vision*
Authors: Eline R. Kupers, Celia Durkin, Clayton E. Curtis, Harvey Huang, Dora Hermes, Thomas Naselaris, Kendrick Kay

Release and reuse of rich neuroimaging datasets have rapidly grown in popularity, enabling researchers to ask new questions about visual processing and to benchmark computational models. One highly used dataset is the Natural Scenes Dataset (NSD), a 7T fMRI dataset where 8 subjects viewed more than 70,000 images over the course of a year. Since its recent release in September 2021, NSD has gained 1700+ users and resulted in 55+ papers and pre-prints. Here, we share behind-the-scenes considerations and inside knowledge from the NSD acquisition effort that helped ensure its quality and impact. This includes lessons learned regarding funding, designing, collecting, and releasing a large-scale fMRI dataset. Complementing the creator’s perspective, we also highlight the user’s viewpoint by revealing results from a large anonymous survey distributed amongst NSD users. These results will provide valuable (and often unspoken) insights into both positive and negative experiences interacting with NSD and other publicly available datasets. Finally, we discuss ongoing efforts towards two new large-scale datasets: (i) NSD-iEEG, an intracranial electroencephalography dataset with extensive electrode coverage in cortex and sub-cortex using a similar paradigm to NSD and (ii) Visual Cognition Dataset, a 7T fMRI dataset that samples a large diversity of tasks on a common set of visual stimuli (in contrast to NSD which samples a large diversity of stimuli during a single task). By sharing these lessons and ideas, we hope to facilitate new data collection efforts and enhance the ability of these datasets to support new discoveries in vision and cognition.
