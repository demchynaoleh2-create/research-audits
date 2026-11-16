# Raw data — case 01

| File | What | Source | Retrieved |
|---|---|---|---|
| comext_eu27_8711601090_monthly.csv | EU-27 monthly imports, CN 8711 60 10 and 8711 60 90, from China, Taiwan, Vietnam, Cambodia, Thailand, Malaysia, Indonesia and all non-EU; units, value, weight | Eurostat Comext DS-045409, pulled with `code/01_pull_comext_eu27.py` | Nov 2026 |
| mirror_units_871160_2018_2024.csv | Units of HS 8711 60 reported exported to the EU by China, Taiwan, Vietnam and Cambodia, against EU-recorded imports | UN Comtrade (https://comtradeplus.un.org/) and Eurostat Comext | Nov 2026 |
| comtrade_long.csv | Underlying UN Comtrade records for the mirror check, with request URLs | UN Comtrade public API | Nov 2026 |
| comtrade_cn_871160_2025_exports.txt | China's 2025 exports of HS 8711 60 by partner (M49 code \| units \| USD); partner sum equals the world total in the same response | UN Comtrade public preview API | 14 Nov 2026 |
| parts_eu_imports_frames_parts_eur_m.csv | EU-27 imports of bicycle frames, forks and parts (8714 91, 8714 99) by origin, € million a year | Eurostat Comext DS-045409 | Nov 2026 |
