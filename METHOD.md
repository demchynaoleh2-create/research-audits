# Method

This is how every audit in this repository is built. The same protocol is used on client work.

## 1. The decision before the facts
Every question stands in for a decision. Before any number is checked, each audit states who is deciding what, over which horizon, which claims bear on that decision and which are decoration, and what would change the answer. A correct answer to the wrong question is the most expensive kind of error, so this step comes first.

## 2. Someone else's claim, broken into atomic claims
Each audit starts from a claim made by someone else — an AI-generated report, an industry position, an official statement. Every number, ranking, causal statement and forecast becomes one row in `claims.csv`.

## 3. Every claim gets a class and a verdict
| Class | Meaning |
|---|---|
| **D** — documented | Stated in a primary source, or computed from one by code in this repository |
| **I** — inference | A conclusion drawn from documented facts; the reasoning is shown |
| **O** — open | Contested, unverifiable with available sources, or a forecast |

Verdicts say what the evidence supports, for example: supported by a primary source; supported only by a republisher; partly right (wrong number, period or definition); cited page does not say it; unverifiable; contradicted. Each row carries a source URL and an exact locator (table, row, article, page), so any sentence in a report can be traced to the line it rests on.

## 4. Primary sources over republishers
Statistics come from the office, central bank or legal text that produces them — Eurostat, the National Bank of Ukraine, EUR-Lex, UN Comtrade. Industry bodies and media are cross-checks and are labelled as secondary. Definitions are checked explicitly: which code, which aggregate, nominal or real, calendar or fiscal, full or partial year. Part-years are compared only with the same months of other years.

## 5. The strongest opposite reading
Each audit writes down the best alternative reading of the same evidence and the facts that would decide between them. A conclusion that has not faced a rival is labelled as such.

## 6. Scenarios with gates
Forward-looking conclusions are written as scenarios. Each has an entry signal and a cancellation condition, both observable in public data, so the reader knows what to watch and when the conclusion stops holding.

## 7. Three levels
The same facts are read for strategy (years), operations (quarters) and tactics (weeks).

## 8. One source of truth
For each case, `code/build.py` reads `data/raw/`, computes every data-derived number into `data/derived/facts.json` and draws every chart. The report is a template filled from that file; figures quoted from sources and decision thresholds are typed in the template and listed in `claims.csv`. `acceptance/run_checks.py` re-checks the published reports, including one check for every error found in review.

## 9. How AI is used — disclosed
The work uses an AI-assisted pipeline: models search, extract and draft; separate models review; every figure is checked against its source and computed by code, not prose. The author is responsible for every claim. Where an audit examines an AI-generated report, the generating model, its prompt and its search log are published with it (see `03-ai-report-audit/input/`).

## 10. Review
Before publication the three audits were reviewed twice by independent AI reviewers working from the published files only, with instructions to recompute numbers and open the cited sources. Their findings and what was done about each are summarised in `REVIEW_LOG.md`.
