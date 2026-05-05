---
name: John K. Tsotsos
institution: York University
department: Department of Electrical Engineering and Computer Science, Lassonde School
  of Engineering
lab_name: Laboratory for Active and Attentive Vision (LAAV)
main_research_area: computational vision and visual attention
total_citations: 26011
h_index: 76
---

# John K. Tsotsos

*computational vision and visual attention* — York University, Department of Electrical Engineering and Computer Science, Lassonde School of Engineering, Laboratory for Active and Attentive Vision (LAAV).

## Background

Tsotsos is a Distinguished Research Professor of Vision Science at York University and holds the NSERC Tier I Canada Research Chair in Computational Vision. They developed the Selective Tuning (ST) theory, a computational framework for visual attention that addresses the complexity of visual information processing through a hierarchy of winner-take-all mechanisms. Their research connects computational neuroscience and artificial intelligence, focusing on the integration of top-down attentional control with bottom-up sensory processing. Tsotsos also develops active vision systems for robotic navigation and object search.

## Papers

### 2025 — Real-world visual search goes beyond eye movements: Active searchers select 3D scene viewpoints too
*PLoS One*
Authors: Tiffany C. Wu, John K. Tsotsos

Traditional visual search paradigms often constrain observers to static 2D displays, thereby neglecting the high-dimensional viewpoint selection inherent in ecological settings. This study investigates the mechanisms of 3D active search using the Psychophysical Experimental Setup for Active Observers (PESAO) to track synchronized binocular gaze and head-neck kinematics in a physical workspace. Analysis of search-driven viewpoint selection reveals that observers actively optimize their viewing height and pose to resolve target-pose ambiguity and negotiate inter-object occlusions. While categorical accuracy remained robust throughout the task, search efficiency—quantified by response latencies, fixation counts, and locomotor distance—showed significant improvement, particularly in trials involving initially occluded targets. These results demonstrate that active vision involves a strategic integration of oculomotor and postural control to acquire optimal, informative views for 3D spatial reasoning.

### 2025 — Equiluminant Border Ownership Cells as a Missing Link in Color Form Perception
*bioRxiv*
Authors: Paria Mehrani, John K. Tsotsos

This research identifies a putative sub-population of border ownership (BOWN) neurons that encode the 'figure' side of borders defined exclusively by equiluminant chromatic contrast. Drawing on neurophysiological evidence from primate areas V1 and V4, the authors propose a hierarchical mechanistic model to demonstrate how these equiluminant BOWN signals are synthesized within the ventral stream. Computational simulations indicate that these neurons exhibit high color selectivity and orientation tuning comparable to luminance-driven BOWN cells. The model suggests these cells function as a critical intermediary, transforming V1 chromatic edge responses into object-centered shape representations in V4, thereby bridging the gap in color-form integration theories.

### 2025 — Boosting Reinforcement Learning in 3D Visuospatial Tasks Through Human-Informed Curriculum Design
*arXiv*
Authors: Markus D. Solbach, John K. Tsotsos

While Reinforcement Learning (RL) has shown efficacy in structured environments, its performance on complex visuospatial reasoning tasks involving active observation remains limited. This work evaluates the capacity of deep RL frameworks, including Proximal Policy Optimization (PPO) and imitation learning (BC/GAIL), to solve a 3D 'Same-Different' task. Initial results confirmed that end-to-end agents struggle to converge on optimal policies when confronted with the high-dimensional challenges of active viewpoint selection. However, by incorporating a human-informed curriculum—where the training regimen is strategically structured based on behavioral findings from real-world human psychophysics—agents successfully acquired the complex active observation strategies necessary for visuospatial problem-solving, underscoring the value of biologically-inspired curricula in the development of artificial general intelligence.

### 2024 — SCOUT+: Towards practical task-driven drivers' gaze prediction
*35th IEEE Intelligent Vehicles Symposium (IV)*
Authors: Iuliia Kotseruba, John K. Tsotsos

Drivers' gaze allocation exhibits high variability during complex safety-critical maneuvers, such as intersection crossing, where top-down task demands override bottom-up saliency. Traditional saliency models often fail in these scenarios because they represent task context implicitly. SCOUT+ is proposed as a practical, task-aware architecture for gaze prediction that utilizes readily available geospatial data (GPS-derived maps and routes) to explicitly model driving objectives. Evaluated on the DR(eye)VE and BDD-A benchmarks, SCOUT+ significantly outperforms baseline bottom-up models and achieves performance parity with models requiring privileged ground-truth task labels. This research highlights the effectiveness of incorporating latent task-based priors from environmental mapping to enhance the predictive accuracy of driver monitoring systems in practical, real-time applications.

### 2024 — Statistical Challenges with Dataset Construction: Why You Will Never Have Enough Images
*arXiv*
Authors: Josh Goldman, John K. Tsotsos

The generalization of deep neural networks (DNNs) from standardized computer vision benchmarks to safety-critical real-world applications is hindered by the statistical unreliability of current evaluation methodologies. This work presents a formal argument, supported by sampling theory, that the construction of a truly representative test set is mathematically and practically implausible for complex visual domains. The authors identify pervasive biases in existing datasets—including selection bias, geographical clustering, and availability bias—which violate the assumptions required for reliable statistical inference. Consequently, performance metrics derived from non-random holdout sets provide an incomplete and potentially misleading assessment of model robustness. The paper recommends that future validation protocols prioritize the verification of a model's internal decision-making logic and fault-tolerance over aggregate accuracy scores.
