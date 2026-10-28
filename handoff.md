# Handoff

Status: closed on 2026-10-28. Everything is pushed and live.

## Built and checked

- **Data, analysis and results:** done.
- **Paper:** `paper/main.tex`, published as `paper/fuel-lockstep.pdf` (11 pages).
- **Essay version:** `paper/essay/essay.tex`, published as `paper/fuel-lockstep-essay.pdf` (8 pages, pgfplots figures).
- **Explorer:** `index.html`.
- **Write-up:** `overview/`, seven interactive exhibits.

Both pages draw their charts from `assets/app.js` and `assets/data.json`. The write-up's fragment maps the chart colors and fonts to its own palette.

Checks passed:
- designcheck
- check.py
- no overflow at 390px
- no console errors on the live pages
- both PDFs compile with no errors, undefined references or overfull lines

## Refreshing with new data

Follow "How to run" in README.md, in order. `build_site.py` comes after the two LaTeX builds because it copies both PDFs.

## Open items

- **2017 Competition Commission report:** the full report is on legco.gov.hk, whose security certificate did not verify from this machine. The papers cite the Commission's press release and "At a Glance" summary instead.
- **Missing evidence:** station costs, rents, price-notice timing and dated discount terms would separate cost from conduct. None of them is public.
