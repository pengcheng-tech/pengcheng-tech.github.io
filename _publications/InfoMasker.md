---
title: "InfoMasker: Preventing Eavesdropping Using Phoneme-Based Noise"
collection: publications
category: conferences
permalink: /publication/2023-infomasker
excerpt: 'This paper designs ultrasonic noise injection systems to disrupt unauthorized recordings while preserving authorized access, reducing speech recognition accuracy to <50% even at low energy levels.'
date: 2023-02-01
venue: 'Network and Distributed System Security Symposium (NDSS 2023)'
paperurl: ''
bibtexurl: ''
citation: 'Huang, P., Wei, Y., Cheng, P., Ba, Z., Lu, L., Lin, F., Zhang, F., Ren, K. (2023). "InfoMasker: Preventing Eavesdropping Using Phoneme-Based Noise." *Network and Distributed System Security Symposium (NDSS 2023)*.'
---

With the wide deployment of microphone-equipped smart devices, more and more users have concerns that their voices would be secretly recorded. Recent studies show that microphones have nonlinearity and can be jammed by inaudible ultrasound, which leads to the emergence of ultrasonicbased anti-eavesdropping research. However, existing solutions are implemented through energetic masking and require high energy to disturb human voice. Since ultrasonic noise can only remain inaudible at limited energy, such noise can merely cover a short distance and can be easily removed by adversaries, which makes these solutions impractical. In this paper, we explore the idea of informational masking, study the transmission and coverage constraints of ultrasonic jamming, and implement a
highly effective anti-eavesdropping system, named InfoMasker. Specifically, we design a phoneme-based noise that is robust against denoising methods and can effectively prevent both humans and machines from understanding the jammed signals. We optimize the ultrasonic transmission method to achieve higher transmission energy and lower signal distortion, then implement a prototype of our system. Experimental results show that InfoMasker can effectively reduce the accuracy of all tested speech recognition systems to below 50% even at low energies (SNR=0), which is much better than existing noise designs.