---
layout: archive
title: "CV"
permalink: /cv/
author_profile: true
redirect_from:
  - /resume
---

{% include base_path %}

{% assign cv = site.data.cv %}

<div class="cv-download-links">
  <a href="{{ base_path }}/files/CV_Peng_Cheng.pdf?v={{ site.time | date: '%Y%m%d%H%M%S' }}" class="btn btn--primary">Download CV as PDF</a>
</div>

Professional Experience
======

{% for work in cv.work %}
**{{ work.position }}, {{ work.organization }}**
*{{ work.startDate }} – {{ work.endDate }}*

{% if work.summary %}{{ work.summary }}{% endif %}
{% for h in work.highlights %}
- {{ h }}
{% endfor %}

---
{% endfor %}

Education
======

{% for edu in cv.education %}
**{{ edu.degree }}{% if edu.major %}, {{ edu.major }}{% endif %} — {{ edu.institution }}{% if edu.location %}, {{ edu.location }}{% endif %}**

*{{ edu.startDate }} – {{ edu.endDate }}*

{% if edu.details %}{{ edu.details }}{% endif %}

---
{% endfor %}

Publications
======

{% assign pub_groups = "representative|other|preprint|thesis" | split: "|" %}
{% assign pub_headings = "Representative Publications|Other Publications (Reverse Chronological Order)|Preprints / Under Review|Thesis" | split: "|" %}
{% for i in (0..pub_groups.size) %}{% if i < pub_groups.size %}
{% assign g = pub_groups[i] %}
{% assign items = cv.publications | where: "group", g %}
{% if items.size > 0 %}
**{{ pub_headings[i] }}**
{% for p in items %}
- {{ p.name }}{% if p.publisher %} — *{{ p.publisher }}*{% endif %}{% if p.year %} ({{ p.year }}){% endif %}
{% endfor %}

{% endif %}
{% endif %}{% endfor %}

Research Projects
======

{% for proj in cv.projects %}
{% unless proj.name contains "Total Research Funding" %}
- **{{ proj.name }}**{% if proj.role %} ({{ proj.role }}){% endif %}{% if proj.organization %} — {{ proj.organization }}{% endif %}{% if proj.startDate or proj.endDate %} ({{ proj.startDate }}–{{ proj.endDate }}){% endif %}
{% endunless %}
{% endfor %}

Honors & Awards
======

{% for a in cv.awards %}
- **{{ a.title }}**{% if a.event %} — {{ a.event }}{% endif %}{% if a.date %} ({{ a.date }}){% endif %}{% if a.role %} — {{ a.role }}{% endif %}{% if a.summary %} — {{ a.summary }}{% endif %}
{% endfor %}

Student Supervision & Mentorship
======

{% for s in cv.supervision %}
- {{ s }}
{% endfor %}

Academic Services
======

**Journal Editorial Roles**
{% for e in cv.service.editorial %}
- {{ e }}
{% endfor %}

**Conference Program Committees**
{% for p in cv.service.program_committees %}
- {{ p }}
{% endfor %}

**Conference Reviewer**
{% for r in cv.service.conference_reviewer %}
- {{ r }}
{% endfor %}

**Journal Reviewer**
{% for j in cv.service.journal_reviewer %}
- {{ j }}
{% endfor %}

**Reviewer Recognition**
{% for r in cv.service.recognition %}
- {{ r }}
{% endfor %}

Other Academic Activities
======

{% for a in cv.activities %}
- {{ a }}
{% endfor %}

Impacts
======

**Industry Contributions**
{% for i in cv.impacts.industry %}
- {{ i }}
{% endfor %}

**Media Recognition**
{% for m in cv.impacts.media %}
- {{ m }}
{% endfor %}
