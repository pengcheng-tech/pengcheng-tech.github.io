---
title: "WMCopier: Forging Invisible Watermarks on Arbitrary Images"
collection: publications
category: conferences
permalink: /publication/2025-wmcopier
excerpt: 'This paper proposes WMCopier, a no-box watermark forgery attack using diffusion models to forge invisible watermarks onto arbitrary images, effectively deceiving both open-source and commercial watermark detectors (including Amazon's system) and revealing critical vulnerabilities in current watermarking systems. Recognized by Amazon's Responsible AI Team.'
date: 2025-12-01
venue: 'The 39th Conference on Neural Information Processing Systems (NeurIPS 2025)'
paperurl: 'https://arxiv.org/abs/2503.22330'
bibtexurl: ''
citation: 'Ziping Dong, Chao Shuai, Zhongjie Ba, **Peng Cheng**, Zhan Qin, Qinglong Wang, Kui Ren. (2025). "WMCopier: Forging Invisible Watermarks on Arbitrary Images." The 39th Conference on Neural Information Processing Systems (NeurIPS 2025).'
---

Invisible Image Watermarking is crucial for ensuring content provenance and accountability in generative AI. While Gen-AI providers are increasingly integrating invisible watermarking systems, the robustness of these schemes against forgery attacks remains poorly characterized. This is critical, as forging traceable watermarks onto illicit content leads to false attribution, potentially harming the reputation and legal standing of Gen-AI service providers who are not responsible for the content. In this work, we propose WMCopier, an effective watermark forgery attack that operates without requiring any prior knowledge of or access to the target watermarking algorithm. Our approach first models the target watermark distribution using an unconditional diffusion model, and then seamlessly embeds the target watermark into a non-watermarked image via a shallow inversion process. We also incorporate an iterative optimization procedure that refines the reconstructed image to further trade off the fidelity and forgery efficiency. Experimental results demonstrate that WMCopier effectively deceives both open-source and closed-source watermark systems (e.g., Amazon's system), achieving a significantly higher success rate than existing methods. Additionally, we evaluate the robustness of forged samples and discuss the potential defenses against our attack.