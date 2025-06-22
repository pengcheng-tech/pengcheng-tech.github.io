---
title: "SurrogatePrompt: Bypassing the Safety Filter of Text-to-Image Models via Substitution"
collection: publications
category: Conference Papers
permalink: /publication/2024-surrogateprompt
excerpt: 'This paper exposes critical vulnerabilities in commercial text-to-image models through SurrogatePrompt, achieving 88% success rate in bypassing safety filters to generate unsafe content. The findings were acknowledged by Midjourney and Stability.ai.'
date: 2024-10-01
venue: 'Proceedings of the ACM SIGSAC Conference on Computer and Communications Security (CCS 2024)'
paperurl: ''
bibtexurl: ''
citation: 'Ba, Z., Zhong, J., Lei, J., Cheng, P. (corresponding author), Wang, Q., Qin, Z., Wang, Z., Ren, K. (2024). "SurrogatePrompt: Bypassing the Safety Filter of Text-to-Image Models via Substitution." *Proceedings of the ACM SIGSAC Conference on Computer and Communications Security (CCS 2024)*, 1166–1180.'
---

Advanced text-to-image models such as DALL⋅E 2, Midjourney, and Stable Diffusion can generate highly realistic images, raising significant concerns regarding the potential proliferation of unsafe content. This includes adult, violent, or deceptive imagery of political figures. Despite claims of rigorous safety mechanisms implemented in these models to restrict the generation of Not-Safe-For-Work (NSFW) content, we successfully devise and exhibit the first prompt attacks on Midjourney, producing abundant photorealistic NSFW images. We reveal the fundamental principles of such prompt attacks and strategically substitute high-risk sections within a suspect prompt to evade closed-source safety measures. Our novel framework, SurrogatePrompt, systematically generates attack prompts, utilizing large language models and image-to-text modules to automate attack prompt creation at scale. Evaluation results disclose an 88% success rate in bypassing Midjourney's proprietary safety filter with our attack prompts, leading to counterfeit images depicting political figures in violent scenarios with high probability. We also demonstrate attacks generating explicit adult-themed imagery. Both subjective and objective assessments validate that the images generated from our attack prompts present considerable safety hazards.