---
title: "Masked Diffusion Models Are Fast and Privacy-Aware Learners"
collection: publications
category: undergoing
permalink: /publication/2023-masked-diffusion
excerpt: 'This paper explores privacy-preserving capabilities of masked diffusion models, demonstrating their potential for fast learning while maintaining privacy guarantees in generative AI applications.'
date: 2023-06-01
venue: 'arXiv preprint'
paperurl: 'https://arxiv.org/abs/2306.11363'
bibtexurl: ''
citation: 'Jiachen Lei, Qingni Wang, **Peng Cheng***, Zhongjie Ba, Zhan Qin, Zhibo Wang, Zhiyi Liu, Kui Ren. "Masked Diffusion Models Are Fast and Privacy-Aware Learners." arXiv preprint arXiv:2306.11363. 2023. doi: to appear.'
---

Diffusion model has emerged as the de-facto model for image generation, yet the heavy training overhead hinders its broader adoption in the research community. We observe that diffusion models are commonly trained to learn all finegrained visual information from scratch. This paradigm may cause unnecessary training costs hence requiring in-depth investigation. In this work, we show that it suffices to train a strong diffusion model by first pre-training the model to learn some primer distribution that loosely characterizes the unknown real image distribution. Then the pre-trained model can be fine-tuned for various generation tasks efficiently. In the pre-training stage, we propose to mask a high proportion (e.g., up to 90%) of input images to approximately represent the primer distribution and introduce a masked denoising score matching objective to train a model to denoise visible areas. In subsequent fine-tuning stage, we efficiently train diffusion model without masking. Utilizing the two-stage training framework, we achieves significant training acceleration and a new FID score record of 6.27 on CelebA-HQ 256 × 256 for ViT-based diffusion models. The generalizability of a pre-trained model further helps building models that perform better than ones trained from scratch on different downstream datasets. For instance, a diffusion model pre-trained on VGGFace2 attains a 46% quality improvement when fine-tuned on a different dataset that contains only 3000 images. Our code is available at https://github.com/jiachenlei/maskdm.