# Handoff

State on 2026-10-28: data, analysis, paper, explorer (index.html) and write-up (overview/) built and checked. Both pages draw their charts from assets/app.js and assets/data.json; the write-up maps the chart tokens in its fragment extra_css. designcheck PASS, check.py clean, no overflow at 390px, no console errors.

Refresh with new data: rerun the fetchers, then `run_all.py`, `make_exhibits.py`, `export_numbers.py`, `export_web.py`, `build_site.py`, rebuild the overview fragment and recompile the paper.

Open items:
- The full 2017 Competition Commission report is on legco.gov.hk, whose TLS chain did not verify from this machine; the paper cites the Commission's own press release and summary instead.
- Station costs, rents, price-notice timing and dated discount terms would separate cost from conduct; none are public.
