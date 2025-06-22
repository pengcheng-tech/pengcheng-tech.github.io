---
title: "Indelible \"Footprints\" of Inaudible Command Injection"
collection: publications
category: manuscripts
permalink: /publication/2024-indelible-footprints
excerpt: 'This paper discovers hardware-specific artifacts in ultrasound injections and designs DolphinTag to detect attacks via abnormal demodulation with 100% accuracy, achieving 99.8% accuracy on interference signatures through software methods.'
date: 2024-06-01
venue: 'IEEE Transactions on Information Forensics and Security (TIFS)'
paperurl: ''
bibtexurl: ''
citation: 'Ba, Z., Gong, B., Wang, Y., Liu, Y., Cheng, P. (corresponding author), Lin, F., Lu, L., Ren, K. (2024). "Indelible \"Footprints\" of Inaudible Command Injection." *IEEE Transactions on Information Forensics and Security (TIFS)*.'
---

Inaudible command injection transmits inaudible ultrasounds to inject adversarial speech commands into a voice assistant, therefore manipulating voice control systems (e.g., a garage door or a security camera) for illegitimate purposes. Although the attack is inaudible, we find it does leave visible “footprints”. Such attack “footprints” are the side product due to the interaction between the attack signal (i.e., input) and the acoustic components (i.e., transfer function), so they reflect the hardware characteristics of the sound capture system, including the microphone diaphragm, the low-pass filter, and the analog-to-digital converter. Moreover, unlike the non-linearity distortion that is erasable with signal-shaping techniques, the “footprints” are indelible because they are unrelated to the content of injected commands. We discover two types of indelible “footprints” embedded in the recording spectrogram, namely abnormal interfering noise and abnormal demodulation. A software-based detection method and a portable detector, DolphinTag, are further designed to identify these “footprints”. The software-based method achieves a detection accuracy of 99.8% on the phone models exhibiting abnormal interfering noise, and our DolphinTag achieves 100% detection accuracy which detects the ultrasound attack by actively facilitating the abnormal demodulation.