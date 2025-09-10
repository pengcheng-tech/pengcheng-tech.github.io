---
title: "ALIF: Low-Cost Adversarial Audio Attacks on Black-Box Speech Platforms Using Linguistic Features"
collection: publications
category: conferences
permalink: /publication/2024-alif
excerpt: 'This paper proposes linguistic feature-based attacks using TTS/ASR reciprocity, enabling single-query adversarial samples with 97.7% query cost reduction. Validated on four commercial systems and adopted by NVIDIA for their AI security toolkit.'
date: 2024-05-01
venue: 'IEEE Symposium on Security and Privacy (SP 2024)'
paperurl: ''
bibtexurl: ''
citation: '**Peng Cheng**, Yuwei Wang, Peng Huang, Zhongjie Ba, Xiaohong Lin, Feng Lin, Li Lu, Kui Ren. "ALIF: Low-Cost Adversarial Audio Attacks on Black-Box Speech Platforms Using Linguistic Features." Proceedings of IEEE Symposium on Security and Privacy. San Francisco, CA, USA. 2024. doi: 10.1109/SP54263.2024.00047.'
---

Extensive research has revealed that adversarial examples (AE) pose a significant threat to voice-controllable smart devices. Recent studies have proposed black-box adversarial attacks that require only the final transcription from an automatic speech recognition (ASR) system. However, these attacks typically involve many queries to the ASR, resulting in substantial costs. Moreover, AE-based adversarial audio
samples are susceptible to ASR updates. In this paper, we identify the root cause of these limitations, namely the inability to construct AE attack samples directly around the decision boundary of deep learning (DL) models. Building on this
observation, we propose ALIF, the first black-box adversarial linguistic feature-based attack pipeline. We leverage the reciprocal process of text-to-speech (TTS) and ASR models to generate perturbations in the linguistic embedding space where the decision boundary resides. Based on the ALIF pipeline, we present the ALIF-OTL and ALIF-OTA schemes for launching attacks in both the digital domain and the physical playback environment on four commercial ASRs and voice assistants. Extensive evaluations demonstrate that ALIF-OTL and -OTA significantly improve query efficiency by 97.7% and 73.3%, respectively, while achieving competitive performance compared to existing methods. Notably, ALIF-OTL can generate an attack sample with only one query. Furthermore, our testof-time experiment validates the robustness of our approach against ASR updates.