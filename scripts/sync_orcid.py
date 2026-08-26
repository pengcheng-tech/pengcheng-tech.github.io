#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_orcid.py — Synchronize publications.bib with the ORCID works of the author.

Pulls the work list from the ORCID Public API for a given ORCID iD, optionally
cross-checks it against DBLP / Google Scholar / Scopus, resolves conflicts with
the priority  Google Scholar > ORCID > DBLP, compares against the repository's
publications.bib, and APPENDS only the NEW entries (existing entries are never
modified, so hand-added fields are preserved).

Usage examples:
  python3 scripts/sync_orcid.py --dry-run
  python3 scripts/sync_orcid.py --dry-run --min-year 2018
  python3 scripts/sync_orcid.py                # real mode: appends new entries
  python3 scripts/sync_orcid.py --dblp-pid 76/185-7 --dry-run
  SCOPUS_API_KEY=xxx python3 scripts/sync_orcid.py --include-scopus --dry-run

Only the Python standard library is required. Google Scholar support is
best-effort: it is used only if the optional third-party package `scholarly`
is installed (Scholar blocks plain HTTP scraping), otherwise it is skipped
with a warning.
"""

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request

ORCID_DEFAULT = "0000-0002-4453-2274"
DBLP_PID_DEFAULT = "76/185-7"
BIB_DEFAULT = "publications.bib"
USER_AGENT = "sync-orcid/1.0 (mailto:pengcheng326@hotmail.com)"


# --------------------------------------------------------------------------
# Minimal BibTeX parsing (stdlib only)
# --------------------------------------------------------------------------

def parse_bib(path):
    """Return list of (bibtype, key, dict_of_fields) for a .bib file.

    Handles nested braces inside field values (e.g. LaTeX macros or
    brace-protected strings) with a depth-counting scanner.
    """
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    entries = []
    i, n = 0, len(text)
    while i < n:
        m = re.compile(r"@\s*([A-Za-z]+)\s*\{").search(text, i)
        if not m:
            break
        bibtype = m.group(1).lower()
        j = m.end()
        k = text.find(",", j)
        if k < 0:
            break
        key = text[j:k].strip()
        fields = {}
        p = k + 1
        while p < n:
            while p < n and (text[p].isspace() or text[p] == ","):
                p += 1
            if p >= n or text[p] == "}":
                break
            fm = re.compile(r"([A-Za-z0-9_\-]+)\s*=").match(text, p)
            if not fm:
                break
            name = fm.group(1).lower()
            p = fm.end()
            while p < n and text[p].isspace():
                p += 1
            if p < n and text[p] == "{":
                depth = 0
                start = p
                while p < n:
                    if text[p] == "{":
                        depth += 1
                    elif text[p] == "}":
                        depth -= 1
                        if depth == 0:
                            break
                    p += 1
                val = text[start + 1:p]
                p += 1
            else:
                m2 = re.compile(r"[^,\s}]+").match(text, p)
                val = m2.group(0) if m2 else ""
                p = m2.end() if m2 else p
            fields[name] = val.strip()
        entries.append((bibtype, key, fields))
        depth = 0
        while j < n:
            if text[j] == "{":
                depth += 1
            elif text[j] == "}":
                depth -= 1
                if depth == 0:
                    j += 1
                    break
            j += 1
        i = j
    return entries


def bib_doi(entry):
    """Normalize a DOI for comparison (lowercase, strip URL prefix)."""
    doi = (entry.get("doi") or "").strip().lower()
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi)
    return doi


def bib_title_key(entry):
    return normalize_title(entry.get("title", ""))


def normalize_title(t):
    t = t.lower()
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


# --------------------------------------------------------------------------
# Network helpers
# --------------------------------------------------------------------------

def http_get_json(url, accept="application/json"):
    req = urllib.request.Request(url, headers={"Accept": accept, "User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def http_get_text(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


# --------------------------------------------------------------------------
# ORCID
# --------------------------------------------------------------------------

def fetch_orcid_works(orcid_id):
    """Return list of summaries: {put_code, title, type, year, external_ids}."""
    url = f"https://pub.orcid.org/v3.0/{orcid_id}/works"
    data = http_get_json(url)
    works = []
    for group in data.get("group", []):
        w = group["work-summary"][0]
        title = ((w.get("title", {}).get("title") or {}).get("value") or "").strip()
        year = ((w.get("publication-date", {}).get("year") or {}).get("value") or "")
        ext = {}
        for e in group.get("external-ids", {}).get("external-id", []):
            ext[e.get("external-id-type")] = e.get("external-id-value")
        works.append({
            "put_code": w.get("put-code"),
            "title": title,
            "type": w.get("type"),
            "year": year,
            "external_ids": ext,
        })
    return works


def fetch_orcid_work(orcid_id, put_code):
    """Fetch one full work record (includes contributors)."""
    url = f"https://pub.orcid.org/v3.0/{orcid_id}/work/{put_code}"
    w = http_get_json(url)
    title = ((w.get("title", {}).get("title") or {}).get("value") or "").strip()
    authors = []
    for c in w.get("contributors", {}).get("contributor", []):
        name = (c.get("credit-name") or {}).get("value") or ""
        if not name:
            orcid_uri = (c.get("contributor-orcid") or {}).get("uri") or ""
            name = orcid_uri.rstrip("/").split("/")[-1]
        authors.append(name.strip())
    ext = {}
    for e in w.get("external-ids", {}).get("external-id", []):
        ext[e.get("external-id-type")] = e.get("external-id-value")
    date = w.get("publication-date", {})
    year = ((date.get("year") or {}).get("value") or "")
    month = ((date.get("month") or {}).get("value") or "")
    day = ((date.get("day") or {}).get("value") or "")
    return {
        "title": title,
        "authors": authors,
        "type": w.get("type"),
        "year": year,
        "month": month,
        "day": day,
        "external_ids": ext,
    }


# --------------------------------------------------------------------------
# arXiv enrichment (arXiv DOIs are not registered with Crossref)
# --------------------------------------------------------------------------

def fetch_arxiv(abs_id):
    """Fetch full authors + title for an arXiv id via the arXiv API."""
    import xml.etree.ElementTree as ET
    url = f"https://export.arxiv.org/api/query?id_list={abs_id}&max_results=1"
    try:
        text = http_get_text(url)
        ns = {"a": "http://www.w3.org/2005/Atom"}
        root = ET.fromstring(text)
        for e in root.findall("a:entry", ns):
            title = " ".join((e.findtext("a:title", "", ns) or "").split())
            authors = [a.findtext("a:name", "", ns) for a in e.findall("a:author", ns)]
            return {"title": title, "authors": authors}
    except Exception:  # noqa: BLE001
        return None
    return None


def clean_title(title):
    """Drop CJK (e.g. Chinese) segments from a title, keeping the Latin part."""
    parts = [p for p in title.split(",") if not re.search(r"[\u4e00-\u9fff]", p)]
    cleaned = ",".join(parts).strip()
    return cleaned or title


# --------------------------------------------------------------------------
# Crossref enrichment (authoritative metadata for new entries)
# --------------------------------------------------------------------------

def fetch_crossref(doi):
    """Return metadata for a DOI from Crossref, or None on failure.

    Used to enrich new entries with the authoritative journal/booktitle,
    volume, issue, pages, full author names and year.
    """
    if not doi:
        return None
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi)
    try:
        m = http_get_json(url)["message"]
    except Exception:  # noqa: BLE001
        return None
    authors = []
    for a in m.get("author", []):
        given = a.get("given", "")
        family = a.get("family", "")
        authors.append(f"{given} {family}".strip() or a.get("name", ""))
    year = ""
    for k in ("published-print", "published-online", "issued"):
        dp = m.get(k, {}).get("date-parts")
        if dp and dp[0]:
            year = str(dp[0][0])
            break
    return {
        "title": (m.get("title") or [""])[0],
        "authors": authors,
        "container": (m.get("container-title") or [""])[0],
        "volume": m.get("volume", ""),
        "number": m.get("issue", ""),
        "pages": m.get("page", ""),
        "year": year,
    }


# --------------------------------------------------------------------------
# DBLP
# --------------------------------------------------------------------------

def fetch_dblp_publications(pid):
    """Fetch the DBLP XML profile for a person pid and return record dicts."""
    import xml.etree.ElementTree as ET
    url = f"https://dblp.org/pid/{pid}.xml"
    text = http_get_text(url)
    root = ET.fromstring(text)
    recs = []
    for rec in root.findall("r"):
        for pub in rec:
            if pub.tag not in ("article", "inproceedings", "incollection"):
                continue
            def g(name):
                e = pub.find(name)
                return (e.text or "").strip() if e is not None else ""
            authors = [e.text or "" for e in pub.findall("author")]
            recs.append({
                "title": g("title"),
                "authors": authors,
                "venue": g("journal") or g("booktitle"),
                "year": g("year"),
                "volume": g("volume"),
                "number": g("number"),
                "pages": g("pages"),
                "doi": g("doi"),
                "ee": g("ee"),
            })
    return recs


# --------------------------------------------------------------------------
# Google Scholar (best effort via optional `scholarly` package)
# --------------------------------------------------------------------------

def fetch_google_scholar(user_id, timeout=30):
    """Return list of {title, authors, venue, year} from the GS citation profile.

    Scholar actively blocks plain HTTP scraping; this function only works when
    the optional third-party package `scholarly` is installed and the network
    permits it. Returns (works, error_message).
    """
    try:
        from scholarly import scholarly as _scholarly
    except ImportError:
        return None, "optional package 'scholarly' not installed; Google Scholar skipped"
    try:
        author = _scholarly.search_author_id(user_id)
        profile = _scholarly.fill(author)
        works = []
        for pub in profile.get("publications", []):
            bib = pub.get("bib", {})
            author_str = bib.get("author", "")
            authors = [a.strip() for a in re.split(r"\s+and\s+", author_str) if a.strip()]
            works.append({
                "title": bib.get("title", ""),
                "authors": authors,
                "venue": bib.get("venue", ""),
                "year": bib.get("pub_year", ""),
            })
        return works, None
    except Exception as exc:  # noqa: BLE001
        return None, f"Google Scholar fetch failed: {exc}"


# --------------------------------------------------------------------------
# Scopus (optional; needs SCOPUS_API_KEY)
# --------------------------------------------------------------------------

def fetch_scopus_author(scopus_author_id, api_key):
    """Fetch Scopus author retrieval (needs an API key); returns works or None."""
    try:
        url = (
            f"https://api.elsevier.com/content/author/author_id/{scopus_author_id}"
            f"?field=publication-range&httpAccept=application/json"
        )
        req = urllib.request.Request(url, headers={"X-ELS-APIKey": api_key, "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)
    except Exception as exc:  # noqa: BLE001
        print(f"[scopus] skipped: {exc}")
        return None


# --------------------------------------------------------------------------
# Main logic
# --------------------------------------------------------------------------

def build_bib_index(entries):
    by_doi = {}
    by_title = {}
    for etype, key, fields in entries:
        doi = bib_doi(fields)
        if doi:
            by_doi.setdefault(doi, []).append((etype, key, fields))
        tkey = bib_title_key(fields)
        if tkey:
            by_title.setdefault(tkey, []).append((etype, key, fields))
    return by_doi, by_title


def entry_to_bibtex(etype, key, fields):
    lines = [f"@{etype}{{{key},"]
    for name, val in fields.items():
        lines.append(f"  {name:<12} = {{{val}}},")
    lines[-1] = lines[-1].rstrip(",")
    lines.append("}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="print what would change without writing")
    ap.add_argument("--orcid", default=ORCID_DEFAULT, help=f"ORCID iD (default {ORCID_DEFAULT})")
    ap.add_argument("--bib", default=BIB_DEFAULT, help=f"path to publications.bib (default {BIB_DEFAULT})")
    ap.add_argument("--dblp-pid", default=None, help="DBLP person pid to cross-check (e.g. 76/185-7)")
    ap.add_argument("--include-gs", action="store_true", help="also pull Google Scholar (needs optional 'scholarly' package)")
    ap.add_argument("--include-scopus", action="store_true", help="also pull Scopus (needs SCOPUS_API_KEY env var)")
    ap.add_argument("--scopus-author-id", default="59105707000")
    ap.add_argument("--gs-user", default="hz3kfCEAAAAJ", help="Google Scholar user id")
    ap.add_argument("--min-year", type=int, default=0, help="only consider works published in or after this year")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    # 1. existing bib index
    try:
        existing = parse_bib(args.bib)
    except FileNotFoundError:
        print(f"[error] {args.bib} not found.", file=sys.stderr)
        sys.exit(1)
    by_doi, by_title = build_bib_index(existing)
    print(f"[bib] {args.bib}: {len(existing)} existing entries")

    # 2. ORCID works (source of truth for 'new' candidates)
    print(f"[orcid] fetching works for {args.orcid} ...")
    try:
        summaries = fetch_orcid_works(args.orcid)
    except Exception as exc:  # noqa: BLE001
        print(f"[error] ORCID fetch failed: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"[orcid] {len(summaries)} works on profile")

    # 3. optional DBLP cross-check
    dblp_by_title = {}
    if args.dblp_pid:
        print(f"[dblp] fetching profile {args.dblp_pid} ...")
        try:
            for rec in fetch_dblp_publications(args.dblp_pid):
                tkey = normalize_title(rec["title"])
                dblp_by_title.setdefault(tkey, rec)
        except Exception as exc:  # noqa: BLE001
            print(f"[dblp] skipped: {exc}")

    # 4. optional Google Scholar (conflict resolution priority #1)
    gs_by_title = {}
    gs_note = None
    if args.include_gs:
        works, err = fetch_google_scholar(args.gs_user)
        if err:
            gs_note = err
            print(f"[gs] {err}")
        else:
            for w in works:
                gs_by_title[normalize_title(w["title"])] = w
            print(f"[gs] {len(works)} works fetched (conflict priority: Google Scholar)")

    # 5. optional Scopus
    if args.include_scopus:
        import os
        key = os.environ.get("SCOPUS_API_KEY")
        if not key:
            print("[scopus] SCOPUS_API_KEY not set; skipped")
        else:
            fetch_scopus_author(args.scopus_author_id, key)

    # 6. classify ORCID works against the bib
    new_candidates = []
    matched = 0
    for s in summaries:
        ext = s["external_ids"]
        doi = (ext.get("doi") or "").lower()
        if doi:
            doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi)
        tkey = normalize_title(s["title"])
        if doi and doi in by_doi:
            matched += 1
            continue
        if tkey and tkey in by_title:
            matched += 1
            continue
        year = s["year"] or "0"
        try:
            if int(year) < args.min_year:
                continue
        except ValueError:
            pass
        new_candidates.append(s)

    print(f"[match] {matched} ORCID works already in bib; {len(new_candidates)} new candidate(s)")

    # 7. build proposed entries (conflict resolution: GS > ORCID > Crossref/arXiv > DBLP)
    proposed = []
    for s in new_candidates:
        work = fetch_orcid_work(args.orcid, s["put_code"])
        ext = work["external_ids"]
        doi = ext.get("doi") or ""
        tkey = normalize_title(work["title"])

        # enrichment sources (Crossref for regular DOIs; arXiv API for arXiv DOIs)
        cr = None
        ax = None
        m_ax = None
        if doi:
            m_ax = re.match(r"^10\.48550/arxiv\.(\S+)$", doi, re.I)
            if m_ax:
                ax = fetch_arxiv(m_ax.group(1))
            else:
                cr = fetch_crossref(doi)

        # conflict resolution — Google Scholar wins when available
        gs = gs_by_title.get(tkey)
        enrich = cr or ax or {}
        if gs:
            year = gs.get("year") or enrich.get("year") or work["year"]
            venue = gs.get("venue") or ""
            authors = gs.get("authors") or enrich.get("authors") or work["authors"]
        else:
            year = enrich.get("year") or work["year"]
            venue = ""
            authors = enrich.get("authors") or work["authors"]

        dblp = dblp_by_title.get(tkey) or {}
        if m_ax:
            venue = venue or f"arXiv preprint arXiv:{m_ax.group(1)}"
        else:
            venue = venue or enrich.get("container") or dblp.get("venue") or orcid_venue(work)

        bibtype = "article" if work["type"] in ("journal-article", "other") else "inproceedings"
        if work["type"] in ("conference-paper", "conference-review"):
            bibtype = "inproceedings"

        fields = {
            "title": clean_title(enrich.get("title") or work["title"]),
            "author": " and ".join(authors) if authors else "",
            "year": year,
            "doi": doi,
            "url": f"https://doi.org/{doi}" if doi else "",
        }
        for k in ("volume", "number", "pages"):
            v = enrich.get(k) or ""
            if not v:
                v = dblp.get(k) or ""
            if k == "volume" and v.startswith("abs/"):
                v = ""  # DBLP CoRR volume placeholder, not a real volume
            if k == "pages" and v:
                v = v.replace("-", "--")
            if v:
                fields[k] = v
        if venue:
            fields["venue"] = venue
            if bibtype == "inproceedings":
                fields["booktitle"] = venue
            else:
                fields["journal"] = venue

        key = slugify(fields["title"])
        proposed.append((key, bibtype, fields, work, enrich))

    # 8. report
    print()
    if not proposed:
        print("[result] nothing to add — ORCID is fully in sync with the bib")
        return

    print(f"[result] {len(proposed)} new entr{'y' if len(proposed) == 1 else 'ies'} to append:")
    for key, bibtype, fields, work, enrich in proposed:
        print("-" * 70)
        print(f"  @{bibtype}{{{key},")
        for name, val in fields.items():
            print(f"    {name:<12} = {{{val}}},")
        print("  }")
        if enrich.get("container"):
            src = "Crossref/arXiv-enriched"
        elif enrich:
            src = "partially enriched"
        else:
            src = "ORCID only"
        print(f"  (orcid type: {work['type']}; year: {work['year']}; source: {src})")

    if gs_note:
        print()
        print(f"[note] {gs_note}")

    if args.dry_run:
        print()
        print("[dry-run] no files were written. Re-run without --dry-run to append.")
        return

    # 9. real mode: append new entries, preserving everything else
    with open(args.bib, "r", encoding="utf-8") as fh:
        bib_text = fh.read()
    if not bib_text.endswith("\n"):
        bib_text += "\n"
    additions = []
    for key, bibtype, fields, work, enrich in proposed:
        additions.append(entry_to_bibtex(bibtype, key, fields))
    with open(args.bib, "w", encoding="utf-8") as fh:
        fh.write(bib_text)
        fh.write("\n".join(additions))
        fh.write("\n")
    print(f"[done] appended {len(proposed)} entr{'y' if len(proposed) == 1 else 'ies'} to {args.bib}")


def orcid_venue(work):
    """Map an ORCID work type to a rough venue label when nothing better exists."""
    mapping = {
        "journal-article": "Journal article",
        "conference-paper": "Conference paper",
        "book-chapter": "Book chapter",
        "book": "Book",
        "other": "Preprint",
    }
    return mapping.get(work.get("type"), work.get("type") or "")


def slugify(title):
    s = title.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    return s[:80].strip("-") or "untitled"


if __name__ == "__main__":
    main()
