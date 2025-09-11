---
title: "Robust Watermarks Leak: Channel-Aware Feature Extraction Enables Adversarial Watermark Manipulation"
collection: publications
category: undergoing
permalink: /publication/2025-watermark-leak
excerpt: 'This paper reveals inherent tradeoffs in watermark robustness, enabling single-image attacks to extract and forge watermarks while maintaining visual fidelity, exposing fundamental vulnerabilities in current watermarking approaches.'
date: 2025-02-01
venue: 'arXiv preprint'
paperurl: 'https://arxiv.org/abs/2502.06418'
bibtexurl: ''
citation: 'Zhongjie Ba, Yaoxin Zhang, **Peng Cheng** (corresponding author), Bin Gong, Xiaoyuan Zhang, Qingni Wang, Kui Ren. (2025). "Robust Watermarks Leak: Channel-Aware Feature Extraction Enables Adversarial Watermark Manipulation." *arXiv preprint*, arXiv:2502.06418, 2025, https://doi.org/10.48550/arXiv.2502.06418.'
---

Watermarking plays a key role in the provenance and detection of AI-generated content. While existing methods prioritize robustness against real-world distortions (e.g., JPEG compression and noise addition), we reveal a fundamental tradeoff: such robust watermarks inherently improve the redundancy of detectable patterns encoded into images, creating exploitable information leakage. To leverage this, we propose an attack framework that extracts leakage of watermark patterns through multi-channel feature learning using a pre-trained vision model. Unlike prior works requiring massive data or detector access, our method achieves both forgery and detection evasion with a single watermarked image. Extensive experiments demonstrate that our method achieves a 60\% success rate gain in detection evasion and 51\% improvement in forgery accuracy compared to state-of-the-art methods while maintaining visual fidelity. Our work exposes the robustness-stealthiness paradox: current "robust" watermarks sacrifice security for distortion resistance, providing insights for future watermark design.