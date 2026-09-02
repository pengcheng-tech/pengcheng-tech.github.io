---
permalink: /
author_profile: true
redirect_from: 
  - /about/
  - /about.html
---

## Latest Update
- 📢 **Postdoc Opening — Computer Vision & Deep Learning at HBKU, Qatar**. The A-Sense: Autism Sensing Center of Excellence at the College of Science and Engineering (https://www.hbku.edu.qa/en/cse/a-sense), Hamad Bin Khalifa University (Doha, Qatar) is recruiting a Postdoctoral Researcher with strong expertise in Computer Vision, Deep Learning, and Machine Learning, focused on behavioral analysis from video data for autism assessment, classification, detection, and intervention. Requirements include a PhD in Computer Science or related field with a strong expertise on Computer Vision and Deep Learning/Machine Learning, proficiency in Python (PyTorch/TensorFlow/Keras/OpenCV), and a strong publication record. Initial 1-year appointment, renewable, based in Doha. Apply portal: https://lnkd.in/dAyYsdy5 — please share with anyone who might be interested.

## Short Bio

Peng Cheng is currently a researcher with the State Key Laboratory of Blockchain and Data Security at Zhejiang University, Hangzhou, China. He received his Ph.D. degree in Computer Science from Lancaster University, Lancaster, UK. He was a visiting researcher at University College Cork, Cork, Ireland, from 2019 to 2020. He was a postdoctoral research associate at the School of Cyber Science and Technology, Zhejiang University, Hangzhou, China.  His research interests include audio deepfake detection, speech privacy preservation, and IoT security. Results have been published in renowned international journals and conferences such as Proc. IEEE, CCS, S&P, and WWW. His research was a finalist for the 2019 Black Hat Conference Pwnie Award for Innovative Research.

## Research Interests

My research centers on AI-generated content (AIGC) security—securing generative systems and their outputs across the full pipeline, from model development to deployment. I work along three complementary directions: **compliance** (auditing safety filters and paralinguistic toxicity in generative models), **controllability** (robust, forgery-resistant watermarking for provenance and accountability), and **authenticity** (generalizable, robust deepfake detection across languages, generators, and modalities). Alongside this focus, I remain actively engaged in speech, acoustic, and IoT security—investigating vulnerabilities such as sensor-based eavesdropping and adversarial voice commands, and developing privacy-preserving, lightweight defenses for voice-enabled and embedded devices. My broader goal is to build AI systems that are secure against malicious manipulation, safe from unintended behaviors, and respectful of user privacy.

## Recent News
{% assign news_sorted = site.data.news | sort: "date_sort" | reverse %}
{% for item in news_sorted %}
{%- if item.commented -%}
<!--- **{{ item.date_display }}**: {{ item.text }}-->
{%- else -%}
- **{{ item.date_display }}**: {{ item.text }}{% if item.links %}{% for link in item.links %} [[{{ link.label }}]]({{ link.url }}){% endfor %}{% endif %}
{%- endif %}
{% endfor %}
## Selected Publications

- Peng Huang, Kun Pan, Qingni Wang, **Peng Cheng***, Li Lu, Zhongjie Ba, Kui Ren. "SecHeadset: A Practical Privacy Protection System for Real-time Voice Communication." *Proceedings of the ACM MobiSys*. Anaheim, California, US. 2025. doi: to appear.

- Zhongjie Ba, Jieming Zhong, Jiachen Lei, **Peng Cheng***, Qingni Wang, Zhan Qin, Zhibo Wang, Kui Ren. "SurrogatePrompt: Bypassing the Safety Filter of Text-to-Image Models via Substitution." *Proceedings of the ACM SIGSAC Conference on Computer and Communications Security*. Salt Lake City, UT, USA. 2024. doi: 10.1145/3658644.3670317.

- Zhongjie Ba, Bin Gong, Yuwei Wang, Liu Liu, **Peng Cheng***, Fengxiao Lin, Li Lu, Kui Ren. "Indelible 'Footprints' of Inaudible Command Injection." *IEEE Transactions on Information Forensics and Security*. 2024.

- **Peng Cheng**, Yuwei Wang, Peng Huang, Zhongjie Ba, Xiaodong Lin, Fengxiao Lin, Li Lu, Kui Ren. "ALIF: Low-Cost Adversarial Audio Attacks on Black-Box Speech Platforms Using Linguistic Features." *IEEE Symposium on Security and Privacy*. San Francisco, CA, USA. 2024. doi: 10.1109/SP54263.2024.00104.

- Peng Huang, Yihao Wei, **Peng Cheng**, Zhongjie Ba, Li Lu, Fengxiao Lin, Yuwei Wang, Kui Ren. "Phoneme-Based Proactive Anti-Eavesdropping with Controlled Recording Privilege." *IEEE Transactions on Dependable and Secure Computing*. 2024.

- Zhongjie Ba, Qing Wen, **Peng Cheng***, Yuwei Wang, Fengxiao Lin, Li Lu, Zhibo Liu. "Transferring Audio Deepfake Detection Capability Across Languages." *Proceedings of the ACM Web Conference*. Austin, TX, USA. 2023. doi: 10.1145/3543507.3583422.

- **Peng Cheng**, Yuexin Wu, Yi Hong, Zhongjie Ba, Fengxiao Lin, Li Lu, Kui Ren. "UniAP: Protecting Speech Privacy With Non-Targeted Universal Adversarial Perturbations." *IEEE Transactions on Dependable and Secure Computing*. 21(1), 31–46, 2023. doi: 10.1109/TDSC.2023.3288610.

- **Peng Cheng**, Utz Roedig. "Personal Voice Assistant Security and Privacy—A Survey." *Proceedings of the IEEE*. 110(4), 476–507, 2022. doi: 10.1109/JPROC.2022.3153167.

For a complete list of publications, please visit my [Google Scholar profile](https://scholar.google.com/citations?user=hz3kfCEAAAAJ&hl=en).


## Professional Services

{% for item in site.data.service.featured -%}
- {{ item }}
{% endfor %}

[See all →](/activities/)

## Awards

{% assign awards_featured = site.data.awards | where: "featured", true | sort: "date_sort" | reverse %}
{% for a in awards_featured -%}
- **{{ a.title }}**{% if a.event %} — {{ a.event }}{% endif %}
{% endfor %}

[See all →](/awards/)

## Industry Impact

My research has made significant contributions to industry security:

- **AI Model Security**: Identified vulnerabilities in commercial text-to-image models (Midjourney, Stability.ai) through SurrogatePrompt attack method
- **Watermarking Systems**: Developed wmcopier method, recognized by Amazon's Responsible AI Team for identifying critical vulnerabilities
- **Open-Source Contributions**: ALIF framework adopted by NVIDIA for their official AI security toolkit
- **Media Recognition**: SonarSnoop research featured in IT media (Motherboard, ZDNet, Sophos) and praised by renowned security experts

<!--## Contact

- **Email**: pengcheng326@hotmail.com
- **Phone**: (86) 15057169279
- **Website**: https://pengcheng-tech.github.io/
- **Location**: Hangzhou, Zhejiang, China
- **Google Scholar**: https://scholar.google.com/citations?user=hz3kfCEAAAAJ&hl=en-->
