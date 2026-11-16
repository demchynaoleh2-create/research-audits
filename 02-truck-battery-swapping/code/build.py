#!/usr/bin/env python3
"""Case 02 · Europe's truckmakers say heavy trucks do not need battery swapping. Are they right?
Single source of truth: every number in the report is computed here from data/raw/ and written to
data/derived/facts.json; every chart is drawn here. Run from the repo root:
    python3 02-truck-battery-swapping/code/build.py && python3 build/render.py 02-truck-battery-swapping
Parameters carry a class: D documented, I inference/estimate, O open assumption (see PARAMS).
"""
import os, sys, json
import pandas as pd, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); C = os.path.dirname(H); RAW = os.path.join(C, "data", "raw")
OUT = os.path.join(C, "data", "derived"); CH = os.path.join(C, "charts")
sys.path.insert(0, os.path.join(os.path.dirname(C), "build")); import theme as T
os.makedirs(OUT, exist_ok=True); os.makedirs(CH, exist_ok=True)

# ---------------- inputs ----------------
el = pd.read_csv(os.path.join(RAW, "eurostat_nrg_pc_205.csv"))
PERIOD, BAND = "2026-S1", "MWH500-1999"          # latest half-year; band of a station at ~10 swaps/day (~1.1 GWh/yr)
dep = el[(el.time == PERIOD) & (el.consumption_band == BAND)].set_index("country").value
sc = pd.read_csv(os.path.join(RAW, "scania_preferred_2026-11-01.csv")); sc = sc[sc.eu27 == 1]
oil = pd.read_csv(os.path.join(RAW, "oil_bulletin_diesel.csv")); oil_last = oil.date.max()
cnr = pd.read_csv(os.path.join(RAW, "cnr_nl_2024_cost_profile.csv")).set_index("item").value
cs = pd.read_csv(os.path.join(RAW, "china_swap.csv")); eu = pd.read_csv(os.path.join(RAW, "eu_e_trucks.csv"))
claims = pd.read_csv(os.path.join(C, "claims.csv"))

PARAMS = {  # name: (value, class, source)
    "pack_kwh": (500, "I", "C31 Swaptopus ~500 kWh"),
    "packs": (24, "O", "our assumption for a corridor station"),
    "pack_eur_kwh": (100, "I", "C10 BNEF USD 108/kWh, rounded; no truck-specific price"),
    "station_ex_battery": (600_000, "I", "C11 ~half of USD 1.0-1.5m is battery inventory"),
    "capex_low": (630_000, "I", "C12 Chinese operator"),
    "wacc": (0.08, "O", "assumption"), "life": (10, "O", "assumption"),
    "kwh_per_swap": (300, "O", "60% of a 500 kWh pack"),
    "kwh_per_km": (1.1, "I", "typical 40 t e-truck"), "l_per_km": (0.326, "I", "typical 40 t diesel"),
    "swap_min": (5, "D", "C07"), "mcs_min": (30, "I", "C03/C04 manufacturer claims, 20-80%"),
    "mcs_min_hi": (40, "I", "A01 analysts 30-40"), "ccs_min": (60, "I", "C03"), "break_min": (45, "D", "C01"),
}
p = {k: v[0] for k, v in PARAMS.items()}
crf = p["wacc"] / (1 - (1 + p["wacc"]) ** -p["life"])
capex = p["station_ex_battery"] + p["packs"] * p["pack_kwh"] * p["pack_eur_kwh"]
ann = {"high": capex * crf, "low": p["capex_low"] * crf}
cap_per_swap = lambda n, k="high": ann[k] / (n * 365)

# ---------------- open network: earn the public-tariff premium ----------------
median_tariff = float(sc.eur_kwh.median())
COUNTRY = {"DE": "Germany", "ES": "Spain", "FR": "France", "IT": "Italy", "NL": "Netherlands", "PL": "Poland"}
rows = []
for cc, name in COUNTRY.items():
    t = float(sc[sc.country == name].eur_kwh.median()); d = float(dep[cc]); prem = t - d
    rows.append(dict(cc=cc, country=name, tariff=t, depot=d, premium=prem,
                     be_high=ann["high"] / (prem * 365 * p["kwh_per_swap"]), be_low=ann["low"] / (prem * 365 * p["kwh_per_swap"])))
ctry = pd.DataFrame(rows).sort_values("be_high"); ctry.round(4).to_csv(os.path.join(OUT, "breakeven_by_country.csv"), index=False)
eu_dep = float(dep["EU27_2020"]); eu_prem = median_tariff - eu_dep
be_eu = ann["high"] / (eu_prem * 365 * p["kwh_per_swap"]); be_eu_low = ann["low"] / (eu_prem * 365 * p["kwh_per_swap"])
earn_open = eu_prem * p["kwh_per_swap"]

# ---------------- closed loop: earn saved truck time ----------------
time_cost = (cnr.vehicle_financing_ownership + cnr.insurance + cnr.vehicle_taxes + cnr.overheads) / cnr.driving_hours_per_year
hour = float(cnr.driver_cost_per_driving_hour + time_cost)
save_mcs, save_ccs = p["mcs_min"] - p["swap_min"], p["ccs_min"] - p["swap_min"]
earn_mcs, earn_ccs = save_mcs / 60 * hour, save_ccs / 60 * hour
be = lambda earn, k="high": ann[k] / (earn * 365)
trucks = lambda n: n / 2
# two-shift variant: fixed time costs spread over two shifts, driver still paid per hour
hour2 = float(cnr.driver_cost_per_driving_hour + time_cost / 2)
earn_mcs2, earn_ccs2 = save_mcs / 60 * hour2, save_ccs / 60 * hour2
# single driver on today's CCS: the charge outlasts the break by ccs - break minutes
save_single_ccs = p["ccs_min"] - p["break_min"]; earn_single_ccs = save_single_ccs / 60 * hour                       # each truck swaps twice a day (illustration)

# ---------------- energy cost per km, Germany (claim A07) ----------------
de_dep = float(dep["DE"]); de_pub = float(sc[sc.country == "Germany"].eur_kwh.median())
diesel_l = float(oil[(oil.date == oil_last) & (oil.country == "DE")].with_taxes.iloc[0]) / 1000 / 1.19
km = [("Depot charging", de_dep * p["kwh_per_km"]),
      ("Swap, 60 a day", (de_dep + cap_per_swap(60) / p["kwh_per_swap"]) * p["kwh_per_km"]),
      ("Swap, 20 a day", (de_dep + cap_per_swap(20) / p["kwh_per_swap"]) * p["kwh_per_km"]),
      ("Public charging (preferred)", de_pub * p["kwh_per_km"]),
      ("Swap, 10 a day", (de_dep + cap_per_swap(10) / p["kwh_per_swap"]) * p["kwh_per_km"]),
      ("Diesel", diesel_l * p["l_per_km"])]
km_d = dict(km)
diesel_25 = float(oil[(oil.country == "DE") & (oil.date.str[:4] == "2025")].with_taxes.mean()) / 1000 / 1.19
swap_eq_diesel25 = ann["high"] / ((diesel_25 * p["l_per_km"] / p["kwh_per_km"] - float(dep["DE"])) * 365 * p["kwh_per_swap"])
swap_eq_diesel = ann["high"] / ((diesel_l * p["l_per_km"] / p["kwh_per_km"] - de_dep) * 365 * p["kwh_per_swap"])

# ---------------- China and EU adoption ----------------
cv = cs[cs.source_name.str.contains("CVWorld", na=False) & (cs.metric == "swap_hdt_share_of_bev_sales")]
cv25 = float(cv[cv.period == "2025"].value.iloc[0]); cv26 = float(cv[cv.period == "2026-01/2026-09"].value.iloc[0])
q = eu[eu.period_basis == "standalone_quarter"].pivot_table(index="period", columns="powertrain", values="units")
q["share"] = q["ECV_BEV_PHEV"] / q["ALL"] * 100
y25 = eu[(eu.period == "2025-01/2025-12") & (eu.source_vintage.str.contains("current"))].set_index("powertrain").units
q326 = float(q.loc["2026-Q3", "share"])
ytd26 = q.loc[["2026-Q1", "2026-Q2", "2026-Q3"]]; eu_ytd26 = float(ytd26.ECV_BEV_PHEV.sum() / ytd26.ALL.sum() * 100)

# ---------------- facts ----------------
F = dict(
    capex_m=capex / 1e6, capex_low_k=p["capex_low"] / 1e3, crf=crf, ann_k=ann["high"] / 1e3,
    median_tariff=median_tariff, tariff_min=float(sc.eur_kwh.min()), tariff_max=float(sc.eur_kwh.max()), n_tariffs=int(len(sc)),
    n_operators=int(sc.cpo.nunique()), eu_dep=eu_dep, eu_prem=eu_prem, be_eu=be_eu, be_eu_low=be_eu_low, earn_open=earn_open,
    be_ctry_lo=float(ctry.be_high.min()), be_ctry_hi=float(ctry.be_high.max()),
    ctry_lo=ctry.iloc[0].country, ctry_hi=ctry.iloc[-1].country,
    trucks_lo=trucks(ctry.be_high.min()), trucks_hi=trucks(ctry.be_high.max()),
    hour=hour, driver_hour=float(cnr.driver_cost_per_driving_hour), time_cost=float(time_cost),
    save_mcs=save_mcs, save_ccs=save_ccs, earn_mcs=earn_mcs, earn_ccs=earn_ccs,
    be_mcs=be(earn_mcs), be_ccs=be(earn_ccs), be_mcs_low=be(earn_mcs, "low"), be_ccs_low=be(earn_ccs, "low"),
    cap20=cap_per_swap(20), cap20_low=cap_per_swap(20, "low"),
    min_needed_20=cap_per_swap(20) / hour * 60,
    km={k: round(v, 3) for k, v in km}, swap_eq_diesel=swap_eq_diesel, diesel_l=diesel_l, oil_date=oil_last,
    de_dep=de_dep, de_pub=de_pub,
    cn_icct=30, cn_cv25=cv25, cn_cv26=cv26, eu_ecv25=int(y25["ECV_BEV_PHEV"]), eu_all25=int(y25["ALL"]),
    eu_share25=float(y25["ECV_BEV_PHEV"] / y25["ALL"] * 100), eu_q326=q326,
    period=PERIOD, hour2=hour2, earn_mcs2=earn_mcs2, earn_ccs2=earn_ccs2, be_mcs2=be(earn_mcs2), be_ccs2=be(earn_ccs2),
    save_single_ccs=save_single_ccs, earn_single_ccs=earn_single_ccs, be_single=be(earn_single_ccs), be_single_low=be(earn_single_ccs, "low"),
    diesel_25=diesel_25, swap_eq_diesel25=swap_eq_diesel25, eu_ytd26=eu_ytd26, n_countries=int(sc.country.nunique()),
    ctry_n={COUNTRY[c]: int((sc.country == COUNTRY[c]).sum()) for c in COUNTRY}, n_claims=int(len(claims)), n_audited=int(claims.id.str.startswith("A").sum()),
    n_evidence=int(claims.id.str.startswith("C").sum()), **{k: v[0] for k, v in PARAMS.items()},
    audited=claims[claims.id.str.startswith("A")][["id", "side", "claim", "verdict", "note"]].to_dict("records"),
    ctry=ctry.round(3).to_dict("records"),
)
json.dump(F, open(os.path.join(OUT, "facts.json"), "w"), indent=1, default=float, ensure_ascii=False)
json.dump({k: list(v) for k, v in PARAMS.items()}, open(os.path.join(OUT, "params.json"), "w"), indent=1)

# ---------------- charts ----------------
# c1 hero: what one swap must earn vs what it can earn, by business case
f, ax = T.fig(174, 84)
xs = np.linspace(3, 40, 300)
ax.plot(xs, [cap_per_swap(x) for x in xs], color=T.ACCENT, lw=2.4)
ax.plot(xs, [cap_per_swap(x, "low") for x in xs], color=T.ACCENT_L, lw=2.0)
ax.text(7.2, 104, f"capital per swap,\n€{capex/1e6:.1f}m station", ha="left", color=T.ACCENT, fontsize=7.5)
ax.text(4.6, 80, f"€{p['capex_low']/1e3:.0f}k station", ha="left", color="#c0703f", fontsize=7.5)
for yv, lab, col, ls in [(earn_open, f"open network: tariff premium €{earn_open:.0f}", T.COMPARE, "-"),
                         (earn_ccs, f"relay drivers, CCS only: {save_ccs:.0f} min = €{earn_ccs:.0f}", T.COMPARE, "--"),
                         (earn_mcs, f"relay, MCS free: {save_mcs:.0f} min = €{earn_mcs:.0f}", T.COMPARE, ":"),
                         (0, "one driver on the legal break: charging hidden, €0 saved", T.INK3, "-")]:
    ax.axhline(yv, color=col, lw=1.1, ls=ls)
    off = -6.5 if yv == earn_ccs else 2.2
    ax.text(39.7, yv + off, lab, color=col if yv else T.INK2, fontsize=7.3, ha="right")
ax.set_xlim(3, 40); ax.set_ylim(-4, 125); ax.set_xlabel("swaps per day at one station"); ax.set_ylabel("€ per swap")
T.grid_y(ax)
T.title(ax, "A swap station pays only where each swap earns more than it costs in capital",
        "Orange: capital per swap. Blue: what a swap earns — a price premium or saved truck time.")
T.save(f, os.path.join(CH, "c1_earn_vs_cost"))

# c2 minutes per stop vs the mandatory break
f, ax = T.fig(174, 58)
bars = [("Battery swap", p["swap_min"], p["swap_min"], T.ACCENT), ("Megawatt charging, 20→80%", p["mcs_min"], p["mcs_min_hi"], T.COMPARE),
        ("CCS charging, 20→80%", p["ccs_min"], p["ccs_min"], T.CONTEXT)]
for i, (lab, a, b, col) in enumerate(bars):
    ax.barh(i, a, color=col, height=0.5);
    if b > a: ax.barh(i, b - a, left=a, color=T.COMPARE_L, height=0.5)
    ax.text(max(b, p["break_min"] if i == 1 else b) + 1.2, i, f"{a}–{b} min" if b > a else f"~{a} min", va="center", fontsize=8, color=T.INK)
ax.axvline(p["break_min"], color=T.INK, lw=1.2)
ax.text(p["break_min"] + 0.8, 0, "legal break after\n4.5 h driving: 45 min", fontsize=7.5, color=T.INK, va="center")
ax.set_yticks(range(3)); ax.set_yticklabels([b[0] for b in bars]); ax.invert_yaxis(); ax.set_xlim(0, 72); ax.set_xlabel("minutes the truck stands still per energy stop")
T.grid_x(ax); ax.spines["left"].set_visible(False)
T.title(ax, "Megawatt charging fits inside the break a driver must take anyway", "Manufacturer and analyst figures; the swap time is CATL's corridor figure.")
T.save(f, os.path.join(CH, "c2_minutes"))

# c3 open network break-even by country
f, ax = T.fig(174, 70)
cc = ctry.reset_index(drop=True)
for i, r in cc.iterrows():
    ax.plot([r.be_low, r.be_high], [i, i], color=T.CONTEXT, lw=2.2, solid_capstyle="round")
    ax.scatter([r.be_high], [i], s=46, color=T.ACCENT, zorder=3, edgecolor="white", lw=1.2)
    ax.scatter([r.be_low], [i], s=30, color=T.ACCENT_L, zorder=3, edgecolor="white", lw=1)
    ax.text(r.be_high + 0.5, i, f"{r.be_high:.1f}   (tariff €{r.tariff:.3f} − depot €{r.depot:.3f})", va="center", fontsize=7.5, color=T.INK)
ax.set_yticks(range(len(cc))); ax.set_yticklabels(cc.country); ax.invert_yaxis()
ax.set_xlim(0, max(cc.be_high) * 1.9); ax.set_xlabel("swaps per day at which capital is covered (dark: €1.8m station; light: €630k)")
T.grid_x(ax); ax.spines["left"].set_visible(False)
T.title(ax, f"An open station needs roughly {ctry.be_high.min():.0f}–{ctry.be_high.max():.0f} swaps a day where prices can be matched",
        f"Median preferred public tariff per country (Scania list, 1 Nov 2026) minus industrial electricity ({PERIOD}, 0.5–2 GWh band).")
T.save(f, os.path.join(CH, "c3_open_breakeven"))

# c4 energy cost per km Germany
f, ax = T.fig(174, 62)
for i, (lab, v) in enumerate(km):
    col = T.ACCENT if lab.startswith("Swap") else (T.INK2 if lab == "Diesel" else T.COMPARE)
    ax.barh(i, v, color=col, height=0.55); ax.text(v + 0.008, i, f"€{v:.2f}", va="center", fontsize=8)
ax.set_yticks(range(len(km))); ax.set_yticklabels([k for k, _ in km]); ax.invert_yaxis(); ax.set_xlim(0, max(km_d.values()) * 1.18)
ax.set_xlabel("energy cost per km, Germany, excl. VAT"); T.grid_x(ax); ax.spines["left"].set_visible(False)
T.title(ax, f"A swap beats diesel on energy cost only above about {swap_eq_diesel:.0f} swaps a day",
        f"Swap = depot electricity plus the station's capital per kWh. Diesel: EU Weekly Oil Bulletin, {oil_last}.")
T.save(f, os.path.join(CH, "c4_cost_per_km"))

# c5 China share vs Europe adoption
f, (a1, a2) = T.fig(174, 66, ncols=2, gridspec_kw={"width_ratios": [1, 1.25], "wspace": 0.35})
a1.fill_between([2023, 2025], 29, 31, color=T.COMPARE_L, lw=0)
a1.text(2022.75, 34, "ICCT: steady ~30%,\n2023–2025", fontsize=7.3, color=T.COMPARE)
a1.scatter([2025, 2026], [cv25, cv26], color=T.ACCENT, s=36, zorder=3)
a1.plot([2025, 2026], [cv25, cv26], color=T.ACCENT, lw=1.4)
a1.text(2026.05, cv26, f"{cv26:.0f}%\nJan–Sep", fontsize=7.3, va="center")
a1.text(2025.08, cv25 - 4.5, f"{cv25:.0f}%", fontsize=7.3, ha="center")
a1.set_xticks([2023, 2024, 2025, 2026]); a1.set_xlim(2022.6, 2026.7); a1.set_ylim(0, 45)
a1.set_ylabel("% of electric heavy-truck sales"); T.grid_y(a1)
a1.set_title("China: swap-capable share", fontsize=9); a1.text(2022.65, 2, "orange: CVWorld (one compiler)", fontsize=6.8, color=T.INK2)
xs2 = list(q.index); a2.bar(range(len(xs2)), q.share, color=[T.ACCENT if x == "2026-Q3" else T.CONTEXT for x in xs2], width=0.7)
a2.set_xticks([i for i, x in enumerate(xs2) if x.endswith("Q1")]); a2.set_xticklabels([x[:4] for x in xs2 if x.endswith("Q1")], fontsize=7.3, ha="left")
a2.text(len(xs2) - 1, q326 + 0.1, f"{q326:.1f}%", ha="center", fontsize=7.3); a2.set_ylim(0, 3.4); T.grid_y(a2)
a2.set_title("EU: chargeable share of new heavy trucks", fontsize=9)
f.suptitle("China built swapping alongside charging; Europe is still at 2–3% electric", x=0.06, ha="left", fontsize=11, fontweight="medium", color=T.INK, y=1.05)
T.save(f, os.path.join(CH, "c5_adoption"))

# c6 closed loop: threshold vs hourly cost (sensitivity)
f, ax = T.fig(174, 62)
hs = np.linspace(30, 120, 200)
for mins, ls, lab in [(save_ccs, "-", f"{save_ccs:.0f} min saved (CCS alternative)"), (save_mcs, "--", f"{save_mcs:.0f} min saved (MCS alternative)")]:
    for k, col in [("high", T.ACCENT), ("low", T.ACCENT_L)]:
        ax.plot(hs, [ann[k] / (mins / 60 * h * 365) for h in hs], color=col, ls=ls, lw=2)
    ax.text(121, ann["high"] / (mins / 60 * 120 * 365), lab, fontsize=7.3, va="center", color=T.INK)
ax.axvline(hour, color=T.COMPARE, lw=1.1); ax.text(hour + 1, 58, f"Dutch 2024 profile: €{hour:.0f}/h", color=T.COMPARE, fontsize=7.3)
ax.set_ylim(0, 62); ax.set_xlim(30, 150); ax.set_xticks(range(30, 130, 10))
ax.set_xlabel("cost of one hour of a standing truck with its driver, €"); ax.set_ylabel("swaps a day to pay"); T.grid_y(ax)
T.title(ax, "The dearer an hour of truck time, the sooner a closed loop pays", "Dark: €1.8m station; light: €630k. Solid: CCS is the alternative; dashed: megawatt charging is.")
T.save(f, os.path.join(CH, "c6_closed_sensitivity"))

print(json.dumps({k: (round(v, 2) if isinstance(v, float) else v) for k, v in F.items() if k not in ("audited", "ctry", "km")}, indent=0, default=str)[:2500])
print(ctry.round(3).to_string()); print(km_d)
