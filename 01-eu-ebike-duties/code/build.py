#!/usr/bin/env python3
"""Case 01 · "EU duties crushed Chinese e-bike imports." Checked against customs data.
Single source of truth: every number in the report is computed here from data/raw/ and written to
data/derived/facts.json; every chart is drawn here. Run from the repo root:
    python3 01-eu-ebike-duties/code/build.py && python3 build/render.py 01-eu-ebike-duties
Raw data were pulled with code/01_pull_comext_eu27.py (Eurostat Comext DS-045409) and the UN Comtrade public API.
Rule: part-years are compared only with the same months of other years.
"""
import os, sys, json
import pandas as pd, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); C = os.path.dirname(H); RAW = os.path.join(C, "data", "raw")
OUT = os.path.join(C, "data", "derived"); CH = os.path.join(C, "charts")
sys.path.insert(0, os.path.join(os.path.dirname(C), "build")); import theme as T
os.makedirs(OUT, exist_ok=True); os.makedirs(CH, exist_ok=True)

d = pd.read_csv(os.path.join(RAW, "comext_eu27_8711601090_monthly.csv"), dtype={"product": str})
d["year"] = d.time.str[:4].astype(int); d["m"] = d.time.str[5:7].astype(int)
EB, OTHER = "87116010", "87116090"
last = d.dropna(subset=["SUPPLEMENTARY_QUANTITY"]).time.max(); LY, LM = int(last[:4]), int(last[5:])
claims = pd.read_csv(os.path.join(C, "claims.csv"))

def ser(partner, product=EB, col="SUPPLEMENTARY_QUANTITY"):
    x = d[(d.partner == partner) & (d["product"] == product)].set_index("time")[col]
    return x.sort_index()
cn = ser("CN"); cn_val = ser("CN", col="VALUE_IN_EUROS"); cn_kg = ser("CN", col="QUANTITY_IN_100KG") * 100
ann = d[(d["product"] == EB) & (d.year < LY)].groupby(["partner", "year"]).SUPPLEMENTARY_QUANTITY.sum().unstack()
ytd = d[(d["product"] == EB) & (d.m <= LM)].groupby(["partner", "year"]).SUPPLEMENTARY_QUANTITY.sum().unstack()
ytd90 = d[(d["product"] == OTHER) & (d.m <= LM)].groupby(["partner", "year"]).SUPPLEMENTARY_QUANTITY.sum().unstack()
share = ytd.loc["CN"] / ytd.loc["EXT_EU27_2020"] * 100
v25 = d[(d["product"] == EB) & (d.year == 2025)].groupby("partner")[["VALUE_IN_EUROS", "SUPPLEMENTARY_QUANTITY"]].sum()
uv25 = (v25.VALUE_IN_EUROS / v25.SUPPLEMENTARY_QUANTITY)

# the collapse, dated
jul18, sep18 = cn["2018-07"], cn["2018-09"]
s = lambda a, b: cn.loc[a:b].sum()
h1_17, h1_18 = s("2017-01", "2017-06"), s("2018-01", "2018-06")
ad_17, ad_18 = s("2017-08", "2017-12"), s("2018-08", "2018-12")
ekg = (cn_val / cn_kg); kgu = cn_kg / cn

# mirror check HS 8711 60 (EU records 8711 60 10 + 8711 60 90)
mir = pd.read_csv(os.path.join(RAW, "mirror_units_871160_2018_2024.csv"))
EU27 = [40, 56, 100, 191, 196, 203, 208, 233, 246, 251, 276, 300, 348, 372, 380, 428, 440, 442, 470, 528, 616, 620, 642, 703, 705, 724, 752]
rows = [l.strip().split("|") for l in open(os.path.join(RAW, "comtrade_cn_871160_2025_exports.txt")) if "|" in l]
ct25 = {int(a): float(b) for a, b, c in rows}
cn_rep25 = sum(ct25[k] for k in EU27 if k in ct25)
eu_rec25 = float(d[(d.partner == "CN") & (d.year == 2025)].SUPPLEMENTARY_QUANTITY.sum())
mcn = mir[mir.partner == "CN"].set_index("year")[["partner_reported_units", "eu_recorded_units"]]
mcn.loc[2025] = [cn_rep25, eu_rec25]; mcn["ratio"] = mcn.partner_reported_units / mcn.eu_recorded_units
mcn["gap"] = mcn.partner_reported_units - mcn.eu_recorded_units
mcn.round(3).to_csv(os.path.join(OUT, "mirror_china_871160.csv"))
eb24 = float(ann.loc["CN", 2024]); ebike_share24 = eb24 / mcn.loc[2024, "eu_recorded_units"] * 100
pooled = mcn.loc[[2024, 2025], "partner_reported_units"].sum() / mcn.loc[[2024, 2025], "eu_recorded_units"].sum()
vn = mir[mir.partner == "VN"]; kh24 = float(mir[(mir.partner == "KH") & (mir.year == 2024)].ratio.iloc[0])

parts = pd.read_csv(os.path.join(RAW, "parts_eu_imports_frames_parts_eur_m.csv")).set_index("year")
fin = d[(d.partner == "CN") & (d["product"] == EB) & (d.year < LY)].groupby("year").VALUE_IN_EUROS.sum() / 1e6

F = dict(
    last=last, LM=LM, jul18=int(jul18), sep18=int(sep18), drop_jul_sep=(sep18 / jul18 - 1) * 100,
    y17=int(ann.loc["CN", 2017]), y18=int(ann.loc["CN", 2018]), y19=int(ann.loc["CN", 2019]), y25=int(ann.loc["CN", 2025]),
    d19_18=(ann.loc["CN", 2019] / ann.loc["CN", 2018] - 1) * 100, d19_17=(ann.loc["CN", 2019] / ann.loc["CN", 2017] - 1) * 100,
    d25_18=(ann.loc["CN", 2025] / ann.loc["CN", 2018] - 1) * 100,
    h1_17=int(h1_17), h1_18=int(h1_18), h1_chg=(h1_18 / h1_17 - 1) * 100, ad_chg=(ad_18 / ad_17 - 1) * 100,
    ekg_jul18=float(ekg["2018-07"]), ekg_aug18=float(ekg["2018-08"]), ekg_sep18=float(ekg["2018-09"]),
    kgu_jul18=float(kgu["2018-07"]), kgu_sep18=float(kgu["2018-09"]),
    kgu_med_lo=float(kgu.loc["2017-01":"2024-12"].groupby(lambda t: t[:4]).median().min()),
    kgu_med_hi=float(kgu.loc["2017-01":"2024-12"].groupby(lambda t: t[:4]).median().max()),
    uvm_jul18=float(cn_val["2018-07"] / cn["2018-07"]), uvm_sep18=float(cn_val["2018-09"] / cn["2018-09"]),
    sh18=float(share[2018]), sh19=float(share[2019]), sh25=float(share[2025]), sh26=float(share[LY]),
    ytd_cn26=int(ytd.loc["CN", LY]), ytd_cn25=int(ytd.loc["CN", 2025]), ytd_cn_chg=(ytd.loc["CN", LY] / ytd.loc["CN", 2025] - 1) * 100,
    kh23=int(ann.loc["KH", 2023]), kh25=int(ann.loc["KH", 2025]), kh_ytd26=int(ytd.loc["KH", LY]), kh_ytd25=int(ytd.loc["KH", 2025]),
    kh_ytd23=int(ytd.loc["KH", 2023]), kh_share26=float(ytd.loc["KH", LY] / ytd.loc["EXT_EU27_2020", LY] * 100),
    tw18=int(ann.loc["TW", 2018]), tw22=int(ann.loc["TW", 2022]), vn18=int(ann.loc["VN", 2018]), vn22=int(ann.loc["VN", 2022]),
    uv_cn=float(uv25["CN"]), uv_kh=float(uv25["KH"]), uv_vn=float(uv25["VN"]), uv_tw=float(uv25["TW"]),
    o90_18=int(ytd90.loc["CN", 2018]), o90_19=int(ytd90.loc["CN", 2019]), o90_25=int(ytd90.loc["CN", 2025]), o90_26=int(ytd90.loc["CN", LY]),
    gap24=float(mcn.loc[2024, "gap"]), ratio24=float(mcn.loc[2024, "ratio"]), gap25=float(mcn.loc[2025, "gap"]), ratio25=float(mcn.loc[2025, "ratio"]),
    cn_rep25=cn_rep25, eu_rec25=eu_rec25, pooled=float(pooled), ratio_lo=float(mcn.loc[2018:2023, "ratio"].min()), ratio_hi=float(mcn.loc[2018:2023, "ratio"].max()),
    ebike_share24=float(ebike_share24), gap_x_ebikes=float(mcn.loc[2024, "gap"] / eb24),
    vn_lo=float(1 / vn.ratio.max()), vn_hi=float(1 / vn.ratio.min()), kh_ratio24=kh24,
    parts18=float(parts.loc[2018, "CN"]), parts25=float(parts.loc[2025, "CN"]), fin18=float(fin[2018]), fin19=float(fin[2019]), fin25=float(fin[2025]),
    n_claims=int(len(claims)), n_audited=int(claims.id.str.startswith("A").sum()), n_evidence=int(claims.id.str.startswith("C").sum()),
    audited=claims[claims.id.str.startswith("A")][["id", "side", "claim", "verdict"]].to_dict("records"),
)
json.dump(F, open(os.path.join(OUT, "facts.json"), "w"), indent=1, default=float, ensure_ascii=False)
pd.DataFrame({"units_cn": cn, "eur_per_kg": ekg.round(2), "kg_per_unit": kgu.round(1)}).to_csv(os.path.join(OUT, "china_monthly_87116010.csv"))

# ---------------- charts ----------------
idx = pd.to_datetime(cn.index)
# c1 hero: monthly imports from China with the legal timeline
f, ax = T.fig(174, 80)
ax.fill_between(idx, cn.values / 1000, color=T.ACCENT_L, lw=0, step="mid")
ax.plot(idx, cn.values / 1000, color=T.ACCENT, lw=1.6, drawstyle="steps-mid")
for dt, lab, y in [("2018-05-04", "registration\nMay 2018", 118), ("2018-07-19", "provisional duty\n19 Jul 2018", 96),
                   ("2019-01-18", "definitive\nJan 2019", 74), ("2025-01-25", "extended\nJan 2025", 74)]:
    ax.axvline(pd.Timestamp(dt), color=T.INK, lw=0.8, ls=(0, (2, 2)))
    ax.text(pd.Timestamp(dt) + pd.Timedelta(days=25), y, lab, fontsize=7.2, color=T.INK, va="top")
ax.annotate(f"{F['jul18']:,} in Jul 2018\n→ {F['sep18']:,} in Sep ({F['drop_jul_sep']:.0f}%)", xy=(pd.Timestamp("2018-09-15"), sep18 / 1000),
            xytext=(pd.Timestamp("2020-03-01"), 52), fontsize=7.6, color=T.INK, arrowprops=dict(arrowstyle="-", color=T.INK3, lw=0.7))
ax.set_ylim(0, 125); ax.set_ylabel("e-bikes per month, thousands"); T.grid_y(ax)
T.title(ax, "Recorded imports collapsed within two months of the provisional duty, then partly rebuilt",
        "EU-27 imports of pedal-assist e-bikes (CN 8711 60 10) from China, monthly, Jan 2017 – " + pd.Timestamp(last).strftime("%b %Y") + ". Eurostat Comext.")
T.save(f, os.path.join(CH, "c1_monthly"))

# c2 value per kg and weight per unit, 2017-2019
f, (a1, a2) = T.fig(174, 60, ncols=2, gridspec_kw={"width_ratios": [1.6, 1], "wspace": 0.28})
w = slice("2017-01", "2019-12"); iw = pd.to_datetime(ekg.loc[w].index)
for a in (a1, a2): a.axvline(pd.Timestamp("2018-07-19"), color=T.INK, lw=0.8, ls=(0, (2, 2)))
a1.plot(iw, ekg.loc[w].values, color=T.ACCENT, lw=2); a1.set_ylim(0, 30); a1.set_ylabel("€ per kg declared"); T.grid_y(a1)
a1.text(pd.Timestamp("2018-09-20"), F["ekg_sep18"] - 2.2, f"€{F['ekg_sep18']:.1f}/kg in Sep 2018", fontsize=7.3)
a1.text(pd.Timestamp("2018-07-25"), F["ekg_jul18"] + 2, f"€{F['ekg_jul18']:.1f}/kg in Jul 2018", fontsize=7.3)
a1.set_title("Declared value per kg", fontsize=9)
a2.plot(iw, kgu.loc[w].values, color=T.CONTEXT, lw=2); a2.set_ylim(0, 35); a2.set_ylabel("kg per e-bike"); T.grid_y(a2)
a2.set_title("Weight per e-bike", fontsize=9)
for a in (a1, a2): a.xaxis.set_major_locator(__import__("matplotlib.dates", fromlist=["YearLocator"]).YearLocator()); a.xaxis.set_major_formatter(__import__("matplotlib.dates", fromlist=["DateFormatter"]).DateFormatter("%Y"))
f.suptitle("The declared value per kilo halved in two months; the bikes did not get lighter", x=0.06, ha="left", fontsize=11, fontweight="medium", color=T.INK, y=1.12)
T.save(f, os.path.join(CH, "c2_value_per_kg"))

# c3 share and substitutes
f, (a1, a2) = T.fig(174, 64, ncols=2, gridspec_kw={"width_ratios": [1, 1.2], "wspace": 0.3})
yrs = list(share.index)
a1.bar(yrs, share.values, color=[T.ACCENT if y in (2018, LY) else T.ACCENT_L for y in yrs], width=0.7)
for y, v in zip(yrs, share.values): a1.text(y, v + 1.2, f"{v:.0f}", ha="center", fontsize=7)
a1.set_ylim(0, 80); a1.set_xticks(yrs); a1.set_xticklabels([str(y)[2:] for y in yrs], fontsize=7.3); a1.set_yticks([])
a1.spines["left"].set_visible(False); a1.set_title(f"China's share of non-EU imports, % (Jan–{pd.Timestamp(last):%b})", fontsize=8.5)
ay = [y for y in ann.columns]
for p, col, lab in [("CN", T.ACCENT, "China"), ("TW", T.COMPARE, "Taiwan"), ("VN", T.CONTEXT, "Vietnam"), ("KH", T.INK2, "Cambodia")]:
    a2.plot(ay, ann.loc[p].values / 1000, color=col, lw=2 if p in ("CN", "TW") else 1.6)
    a2.text(ay[-1] + 0.2, ann.loc[p].values[-1] / 1000 + {"CN": -28, "TW": 28}.get(p, 0), lab, fontsize=7.2, va="center", color=T.INK)
a2.set_xlim(ay[0] - 0.3, ay[-1] + 1.6); a2.set_ylabel("thousand e-bikes a year"); T.grid_y(a2); a2.set_xticks(ay); a2.set_xticklabels([str(y)[2:] for y in ay], fontsize=7.3)
a2.set_title("Imports by origin, full years", fontsize=8.5, loc="left")
f.suptitle("China's share fell from two-thirds to a seventh, and has climbed back to about two-fifths", x=0.06, ha="left", fontsize=11, fontweight="medium", color=T.INK, y=1.12)
T.save(f, os.path.join(CH, "c3_share_origins"))

# c4 mirror check
f, ax = T.fig(174, 62)
ys = list(mcn.index)
ax.bar(ys, mcn.ratio.values, color=[T.ACCENT if y >= 2024 else T.CONTEXT for y in ys], width=0.62)
for y, r, g in zip(ys, mcn.ratio.values, mcn.gap.values):
    ax.text(y, r + 0.02, f"{r:.2f}" + (f"\n+{g/1e6:.2f}m units" if y >= 2024 else ""), ha="center", fontsize=7.2, va="bottom")
ax.axhline(1, color=T.INK, lw=0.8); ax.set_ylim(0.8, 1.6); ax.set_xticks(ys); T.grid_y(ax)
ax.set_ylabel("China reported ÷ EU recorded")
T.title(ax, "China reports shipping more electric two-wheelers to the EU than the EU records arriving",
        "HS 8711 60 (e-bikes, e-scooters, other electric two-wheelers); pedal-assist e-bikes are under 5% of the recorded units. UN Comtrade and Eurostat.")
T.save(f, os.path.join(CH, "c4_mirror"))

# c5 the uncovered code and parts
f, (a1, a2) = T.fig(174, 60, ncols=2, gridspec_kw={"wspace": 0.32})
yy = [y for y in ytd90.columns if y >= 2017]
a1.bar(yy, ytd90.loc["CN", yy].values / 1e6, color=T.CONTEXT, width=0.7)
a1.bar(yy, ytd.loc["CN", yy].values / 1e6, color=T.ACCENT, width=0.7)
a1.set_xticks(yy); a1.set_xticklabels([str(y)[2:] for y in yy], fontsize=7.3); T.grid_y(a1); a1.set_ylabel(f"million units, Jan–{pd.Timestamp(last):%b}")
a1.set_title("Units from China: grey 8711 60 90, orange e-bikes", fontsize=8.5)
py = [y for y in parts.index if y >= 2017]
a2.plot(py, parts.loc[py, "CN"].values, color=T.CONTEXT, lw=2); a2.plot(py, fin.loc[py].values, color=T.ACCENT, lw=2)
a2.text(py[-1] + 0.2, parts.loc[py[-1], "CN"], "frames, forks\nand parts", fontsize=7, va="center")
a2.text(py[-1] + 0.2, fin.loc[py[-1]], "finished\ne-bikes", fontsize=7, va="center", color=T.ACCENT)
a2.set_xlim(py[0] - 0.3, py[-1] + 2); a2.set_xticks(py); a2.set_xticklabels([str(y)[2:] for y in py], fontsize=7.3); T.grid_y(a2); a2.set_ylabel("€ million a year")
a2.set_title("Value from China", fontsize=8.5)
f.suptitle("Around the dutiable code, the undutied flows grew", x=0.06, ha="left", fontsize=11, fontweight="medium", color=T.INK, y=1.12)
T.save(f, os.path.join(CH, "c5_around_the_code"))

print(json.dumps({k: (round(v, 2) if isinstance(v, float) else v) for k, v in F.items() if k != "audited"}, indent=0, default=str))
print(mcn.round(3))
