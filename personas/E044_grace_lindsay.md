---
name: Grace Lindsay
institution: New York University
department: Department of Psychology and Center for Data Science
lab_name: Lindsay Lab
main_research_area: computational neuroscience and visual attention
total_citations: 4124
h_index: 16
---

# Grace Lindsay

*computational neuroscience and visual attention* — New York University, Department of Psychology and Center for Data Science, Lindsay Lab.

## Background

Grace Lindsay is an Assistant Professor at New York University who utilizes computational neuroscience, psychology, and machine learning to study neural information processing. Their research employs artificial neural networks as functional models of the visual system to investigate how attentional mechanisms modulate sensory processing and task performance. Lindsay evaluates the validity of analytical tools in systems neuroscience and develops computer vision applications for climate change mitigation, such as analyzing satellite imagery to track environmental transitions. They are also the author of 'Models of the Mind,' a book detailing the mathematical history and theoretical foundations of brain research.

## Papers

### 2024 — Neural Circuit Architectural Priors for Quadruped Locomotion
*arXiv preprint (arXiv:2410.07174)*
Authors: Nikhil X. Bhattasali, Venkatesh Pattabiraman, Lerrel Pinto, Grace W. Lindsay

Learning-based approaches to quadrupedal locomotion typically employ generic multilayer perceptrons (MLPs) that lack biological inductive biases, requiring extensive data or reward engineering to achieve robust movement. This study introduces Quadruped NCAP, an artificial neural network architecture incorporating architectural priors derived from mammalian spinal cord and limb neural circuits, such as central pattern generators and afferent feedback loops. The results demonstrate that these biologically inspired priors enable significantly higher data and parameter efficiency than standard MLPs, achieving comparable performance with orders of magnitude fewer parameters. The model exhibits superior generalization across varied terrains and robotic body configurations, and notably, it facilitates direct deployment on a physical quadruped robot without the reliance on conventional sim-to-real transfer methodologies, highlighting the efficacy of nervous-system-inspired connectivity in embodied control.

### 2024 — Improving satellite imagery segmentation using multiple Sentinel-2 revisits
*arXiv preprint (arXiv:2409.17363)*
Authors: Kartik Jindgar, Grace W. Lindsay

The analysis of remote sensing data frequently employs computer vision models pre-trained on static datasets, which fail to exploit the temporal dimension provided by frequent satellite revisits. This work evaluates various multi-temporal input strategies for fine-tuning pre-trained models on satellite imagery, specifically targeting the semantic segmentation of power substations—a task critical for monitoring climate change mitigation efforts. Through extensive testing across multiple model architectures, the study finds that fusing temporal representations within the latent space of the model is markedly superior to traditional data augmentation or input-level stacking. Architecturally, a SWIN Transformer-based model outperforms both U-Net and standard Vision Transformer (ViT) variants. These results, verified on a building density estimation benchmark, provide a specialized framework for leveraging the temporal revisits inherent in satellite data to enhance the performance of deep learning models in environmental remote sensing.

### 2024 — Multilevel interpretability of artificial neural networks: leveraging framework and methods from neuroscience
*arXiv preprint (arXiv:2408.12664)*
Authors: Zhonghao He, Jascha Achterberg, Katie Collins, Kevin K. Nejad, Danyal Akarca, Yinzhu Yang, Wes Gurnee, Ilia Sucholutsky, Yuhan Tang, Rebeca Ianov, George Ogden, Chole Li, Kai J. Sandbrink, Stephen Casper, Anna Ivanova, Grace W. Lindsay

As artificial neural networks (ANNs) approach the complexity of biological brains, relating their high-dimensional internal structures to external task behaviors has become a significant challenge. This paper proposes a multilevel interpretability framework adapted from David Marr’s three levels of analysis—computation, algorithm, and implementation—to provide a structured approach for understanding intelligent systems. We review and organize a suite of analytical tools from systems neuroscience, including neural population geometry analysis, decoding probes, and causal circuit manipulations, which can be applied to ANNs. By mapping specific interpretability goals to these levels, the framework seeks to bridge the gap between architectural properties and behavioral outputs, clarifying the assumptions and priorities required to reverse-engineer both biological and artificial neural computations.

### 2024 — Grounding neuroscience in behavioral changes using artificial neural networks
*Current Opinion in Neurobiology*
Authors: Grace W. Lindsay

Connecting neural population activity to functional outcomes is a central goal of systems neuroscience, yet the conceptualization of 'function' remains varied. This review advocates for grounding this goal in the causal relationship between specific neural circuit changes and observable changes in behavior. Artificial neural networks (ANNs) are presented as a uniquely observable and controllable format for testing such hypotheses, as they utilize complex transformations to produce task-relevant behavior. By serving as mechanistic models, ANNs allow researchers to causally test whether a given neural modification is sufficient to produce an experimentally observed behavioral shift. Furthermore, the work highlights the utility of importing interpretability methods from the field of artificial intelligence to identify the specific neural features and representational geometries that drive task performance and behavioral dynamics.

### 2024 — Editorial overview: Computational neuroscience as a bridge between artificial intelligence, modeling and data
*Current Opinion in Neurobiology*
Authors: Grace W. Lindsay

This editorial overview examines the current state of computational neuroscience as a pivotal intermediary between the development of artificial intelligence, theoretical modeling, and the influx of high-resolution neural data. The transformative impact of new experimental methodologies, which enable the collection of massive, multi-modal datasets, has necessitated a shift from single-neuron models to population-level frameworks. The article synthesizes recent advancements in five key areas: machine learning for neuroscience, neurosciences for machine learning, neural computation principles, computational models of sensory-motor circuits, and novel data analysis methods. It emphasizes the 'neuroconnectionist' paradigm, where brain-inspired architectures are used to simulate complex cognition and behavior, and discusses how the synergy between interpretability in AI and systems neuroscience is providing new insights into the functional organization of the cortex.
