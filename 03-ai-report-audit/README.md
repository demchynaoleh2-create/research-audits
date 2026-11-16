# Can a buyer act on this AI research report?

- **Read:** [report.pdf](report.pdf) (8 pages; the first page is the client summary).
- **Check a claim:** [claims.csv](claims.csv) — every claim with class, verdict, source URL and locator. Report references such as [C05] point to its rows.
- **Rebuild:** `python3 03-ai-report-audit/code/build.py && python3 build/render.py 03-ai-report-audit` from the repository root. Every number comes from `data/derived/facts.json`, computed from `data/raw/`.
- **Theory references:** [theory_sources.md](theory_sources.md).
