---
title: "Smart Speaker Privacy Control—Acoustic Tagging for Personal Voice Assistants"
collection: publications
category: conferences
permalink: /publication/2019-acoustic-tagging
excerpt: 'This paper introduces acoustic tagging for privacy control, embedding imperceptible tags into voice streams to enable privacy preference signaling and unauthorized recording traceability in voice assistant systems.'
date: 2019-05-01
venue: 'IEEE Security and Privacy Workshops (SPW 2019)'
paperurl: ''
bibtexurl: ''
citation: '**Cheng, P.**, Bagci, I. E., Yan, J., Roedig, U. (2019). "Smart Speaker Privacy Control—Acoustic Tagging for Personal Voice Assistants." *IEEE Security and Privacy Workshops (SPW 2019)*, San Francisco, CA, USA, 144–149.'
---

Personal Voice Assistants (PVAs) such as the Siri, Amazon Echo and Google Home are now commonplace. PVAs continuously monitor conversations which may be transported to a cloud back end where they are stored, processed and maybe even passed on to other service providers. A user has little control over this process. She is unable to control the recording behaviour of surrounding PVAs, unable to signal her privacy requirements to back-end systems and unable to track conversation recordings. In this paper we explore techniques for embedding additional information into acoustic signals processed by PVAs. A user employs a tagging device which emits an acoustic signal when PVA activity is assumed. Any active PVA will embed this tag into their recorded audio stream. The tag may signal a cooperating PVA or back-end system that a user has not given a recording consent. The tag may also be used to trace when and where a recording was taken. We discuss different tagging techniques and application scenarios, and we describe the implementation of a prototype tagging device based on PocketSphinx. Using the popular PVA Google Home Mini we demonstrate that the device can tag conversations and that the tagging signal can be retrieved from conversations stored in the Google back-end system.