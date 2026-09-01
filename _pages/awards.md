---
layout: archive
title: "Awards & Recognition"
permalink: /awards/
author_profile: true
---

{% include base_path %}

{% assign cats = "research|reviewer|academic|mentorship|industry|media" | split: "|" %}
{% assign heads = "Research Awards & Competition Recognition|Reviewer Excellence|Academic Excellence Awards|Mentorship & Supervision Awards|Industry Impact Recognition|Media Recognition & Expert Endorsement" | split: "|" %}
{% for i in (0..cats.size) %}{% if i < cats.size %}
{% assign cat = cats[i] %}
{% assign items = site.data.awards | where: "category", cat | sort: "date_sort" | reverse %}
{% if items.size > 0 %}
## {{ heads[i] }}

{% for a in items %}
### {{ a.title }}{% if a.event %} - {{ a.event }}{% endif %}
{% if a.subtitle %}**{{ a.subtitle }}**
{% endif %}{% if a.bullets %}{% for b in a.bullets %}{% if b.label and b.label != "" %}- **{{ b.label }}**: {{ b.text }}{% else %}- {{ b.text }}{% endif %}
{% endfor %}

{% endif %}{% if a.note %}- {{ a.note }}

{% endif %}{% if a.quote %}**{{ a.quote_label }}**
> *{{ a.quote }}*

{% endif %}{% if a.historical %}**{{ a.historical.label }}**: [{{ a.historical.text }}]({{ a.historical.url }})

{% endif %}{% if a.images %}{% for img in a.images %}{% if img.label and img.inline %}**{{ img.label }}**
<img src="{{ img.src }}" alt="{{ img.alt }}" width="{{ img.width }}">

{% else %}<img src="{{ img.src }}" alt="{{ img.alt }}" width="{{ img.width }}">

{% endif %}{% endfor %}{% endif %}{% if a.certificate %}**{{ a.certificate.label }}** [Download Certificate]({{ a.certificate.url }})

{% endif %}
{% endfor %}
{% endif %}
{% endif %}{% endfor %}

---

*These awards and recognitions reflect a consistent commitment to advancing cybersecurity research, fostering academic excellence, and making meaningful contributions to both academic and industrial communities in AI security and privacy protection.*
