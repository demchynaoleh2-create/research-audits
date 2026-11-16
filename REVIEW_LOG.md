# Review log

## Version 1.0 — 15 November 2026

The three audits were reviewed three times before publication by independent AI reviewers. Each worked only from the published files, recomputed the numbers from the data and opened the cited sources. Together they raised 75 findings. Version 1.0 is a rebuild from scratch rather than a patch, because the reviews showed that patches made after the first review introduced new inconsistencies.

### Most consequential corrections
| Case | Before | After |
|---|---|---|
| 01 | Duties dated to 2019 | Provisional duty from 19 July 2018; the collapse happened in August–September 2018 |
| 01 | The 1.3m mirror gap described as e-bikes | Labelled HS 8711 60 (e-bikes, e-scooters and other electric two-wheelers); e-bikes are under 5% of recorded units |
| 01 | The 60%/25% assembly thresholds described as a way to avoid a finding | Described as necessary, not sufficient, for a finding |
| 01 | "The rate follows the exporter" | The duty attaches to the producer |
| 01 | Year-end timing not tested as an explanation of the mirror gap | Tested on 2025: the gap did not close (ratio 1.22) |
| 02 | Break-even "8–28 swaps a day" from four selected operators | Full price list (75 EU tariffs); country-matched 10–13 |
| 02 | Model priced an open network while the verdict recommended closed loops | Closed loop priced on a published hourly truck cost |
| 02 | Chinese swap share shown falling from 55% to 23% across different sources | Steady ~30% in 2023–2025 (ICCT, checked against the original) |
| 03 | A misread survey share reported as ambiguous | Contradicted: the source's 23% and 4% add up to 27% |
| 03 | Generating prompt not published | Published in `03-ai-report-audit/input/prompt.md` |
| 03 | A third-quarter figure compared with a fourth-quarter peak | Like-for-like quarters |
| All | Numbers typed by hand in reports and README | Every number computed by code into `facts.json`; acceptance checks in `acceptance/` |

Each finding that could recur is encoded in `acceptance/checklist.yaml` with its review id.

### Third review (final, 16 November 2026)
36 findings (2 critical, 13 material). All critical and material ones are fixed and encoded as checks:
| Case | Before | After |
|---|---|---|
| 03 | "5 of 7 readings in the plateau"; January–February said to lack a base | Monthly series read from the central-bank workbook from 2024: 5 of 9 readings; the recovery signal fired in February and has not been cancelled — growth is decelerating |
| 03 | 49% primary / 24% republisher only | 59% / 14%: eight country and monthly claims are in the central bank's own tables |
| 03 | A survey share called "contradicted by its source" | Partly right: the report repeated the source's ambiguous wording |
| 01 | "A widening mirror gap shows bikes entering outside the record" | The gap is consistent with, but does not measure, e-bike evasion; other causes listed |
| 02 | "1,700 megawatt points" | 1,700 high-performance points, megawatt share unstated |
| 02 | One hourly cost for all operations | Two-shift variant added; thresholds 12–15 (CCS) |
| 02 | Single driver "never" pays | Priced on today's CCS: about 44 swaps a day |
| All | Internal names listed in the public check script | Stored as hashes only; every text file is scanned |
