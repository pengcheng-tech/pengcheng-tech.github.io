---
title: "SecHeadset: A Practical Privacy Protection System for Real-time Voice Communication"
collection: publications
category: conferences
permalink: /publication/2025-secheadset
excerpt: 'This paper presents SecHeadset, a practical privacy protection system that prevents third parties from eavesdropping on speech content in VoIP and voice message applications by adding vowel-based noise to speech audio signals, validated through 204-user studies.'
date: 2025-01-01
venue: 'Proceedings of the ACM MobiSys 2025'
paperurl: ''
bibtexurl: ''
citation: 'Peng Huang, Kun Pan, Qingni Wang, **Peng Cheng***, Li Lu, Zhongjie Ba, Kui Ren. "SecHeadset: A Practical Privacy Protection System for Real-time Voice Communication." Proceedings of the ACM MobiSys. Anaheim, California, US. 2025. doi: to appear.' 
---
Voice communication is convenient while also poses risks of privacy leakage, due to potential interception or eavesdropping during voice transmission. Current protections of voice privacy are almost entirely controlled by communication service providers (CSPs), which operate as a black-box to users thus hard to fully trust. To take back the control of user privacy, in this paper, we introduce SecHeadset, an end-to-end solution for secure voice communication based on
voice obfuscation, which is plug-and-play and compatible with various CSPs. Our solution involves two parts. First, we design a voice-like noise masking scheme for voice obfuscation. The noise,
mimicking voice characteristics, could e!ectively obscure users’ voices while demonstrating resilience against noise reduction methods. Second, we develop a protocol that enables e"cient channel
state estimation and secure information exchange between two communication entities. Based on this information, we propose a lightweight algorithm for voice retrieval during communication.
We develop a prototype of SecHeadset and evaluate its performance with 8 widely-used applications, including Telegram and Skype. It reduces the voice recognition accuracy of various adversaries to below 15% while maintaining communication quality. We also integrate SecHeadset with o!-the-shelf portable devices and verify its real-world effectiveness.
