---
layout: archive
title: "Professional Activities"
permalink: /activities/
author_profile: true
---

{% include base_path %}

## Professional Membership

### China Computer Federation (CCF) - Senior Member

- **Status**: Elected Senior Member of the China Computer Federation (CCF)
- **Elected**: May 2026

<img src="/images/ccf_senior_member.jpg" alt="CCF Senior Member Certificate" width="500">

---

{% for section in site.data.service.sections %}
## {{ section.heading }}
{% for group in section.groups %}
### {{ group.title }}
{% if group.sort == "none" %}
{% for b in group.bullets -%}
- {{ b.text }}
{% endfor %}
{% else %}
{% assign bs = group.bullets | sort: "date_sort" | reverse %}
{% for b in bs -%}
- {{ b.text }}
{% endfor %}
{% endif %}
{% if group.images %}
{% for img in group.images -%}
**{{ img.label }}**
<img src="{{ img.src }}" alt="{{ img.alt }}" width="{{ img.width }}">
{% endfor %}
{% endif %}
{% if group.comment %}{{ group.comment }}
{% endif %}{% endfor %}
{% endfor %}

## Research Collaboration & Grant Activities

### International Grant Proposals - SFI Collaboration (2019)
- **Project**: "Security and Privacy of Personal Voice Assistants"
- **Role**: Contributed to the preparation of grant proposal
- **PI**: Prof. Utz Roedig (University College Cork)

### Current Research Projects - National Funding
**National Natural Science Foundation of China (NSFC):**
- **Principal Investigator (2025-2028)**: "Research on Speech Synthesis Data Compliance Management Technology Based on Intrinsic Characteristics of Audio Signals" (NSFC General Program Project)
- **Participant Role**: Multiple NSFC projects including Key Projects on cross-chain security and deep learning applications

**Key R&D Programs of China:**
- **Active Participation**: Multiple national-level research programs in AI security, machine learning model security, and industrial cryptographic systems
- **Focus Areas**: Multimodal AI security and blockchain technologies

### Industry Collaboration - Zhejiang University-Alibaba Project (2025-2026)
- **Role**: Principal Investigator
- **Project**: "Active and Passive Security Protection Technologies for the Maojing Voice Interaction System"

## Academic Mentorship & Supervision

### Current Supervision Activities - Graduate Student Mentorship
- **Ph.D. Students**: Co-supervising 5 Ph.D. students at Zhejiang University
- **Master's Students**: Co-supervising 7 Master's students at Zhejiang University
- **Research Focus**: AIGC security, multimodal privacy protection, and voice system security

### Mentorship Achievements
- **National Graduate Scholarship Winner (2024)**: Co-supervised Master's student received China's highest-level scholarship for graduate students
- **Degree Completion Success**: Successfully co-mentored 1 Ph.D. student, 5 Master's students, and 1 undergraduate student to degree completion
- **Guidance Areas**: Thesis design, research execution, publication strategies, and career development

### Teaching Experience - International Teaching Assistance
- **University College Cork, Ireland**: Teaching Assistant for CS4615 - Computer Systems Security (Lab/Practical sessions)
- **Lancaster University, UK**: Teaching Assistant for SCC110 - Software Development (Lab/Practical sessions)

## Academic Outreach & International Exchange

### Visiting Scholar Experience - University College Cork (2019-2020)
- **Institution**: Department of Computer Science, University College Cork (UCC), Ireland
- **Research Focus**: Advanced voice assistant security and acoustic-channel vulnerabilities

### Specialized Training - São Paulo Advanced Science School (2017)
- **Host Institution**: University of São Paulo, Brazil
- **Program**: ESPCA (São Paulo Advanced Science School) - Smart Cities
- **Recognition**: Selected as one of 75 global top graduate students and postdoctoral researchers
- **Sponsorship**: São Paulo Research Foundation (FAPESP)
- **Focus**: Smart city technologies, IoT security, and urban computing systems

---

*These professional activities demonstrate a commitment to advancing the cybersecurity research community through editorial leadership, peer review excellence, student mentorship, and collaborative research initiatives spanning academia and industry.*
