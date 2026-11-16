"""Case 03 · build facts and charts from claims.csv and the NBU snapshot. Run: python3 code/build.py"""
import json, os, sys
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); C = os.path.join(HERE, ".."); sys.path.insert(0, os.path.join(C, "..", "build"))
import theme as T
D = lambda *p: os.path.join(C, *p)

# ---------- claims and mapping ----------
cl = pd.read_csv(D("claims.csv"))
Q = {"Will a team still deliver in two years?": "C52 C60 C61 C62 C63",
     "Is there talent for my stack?": "C16 C40 C41 C43 C44 C45 C46 C47 C53 C57 C58 C59",
     "What will it cost?": "C49 C50 C64",
     "Can I contract, protect IP and pay?": "C48 C75 C77",
     "Are other buyers staying?": "C01 C02 C03 C04 C05 C06 C07 C08 C09 C12 C13 C14 C15 C20 C21 C22 C24 C25 C26 C27 C28 C29 C30 C31 C32 C33 C34 C35 C36 C37 C38 C39 C51 C55 C65 C66 C67 C69 C70 C72 C73 C74 C76",
     "Recommendation itself": "C78",
     "Background, no bearing on the decision": "C10 C11 C17 C18 C19 C23 C42 C54 C56 C68 C71"}
m = pd.DataFrame([(c, q) for q, ids in Q.items() for c in ids.split()], columns=["id", "question"])
assert set(m.id) == set(cl.id) and m.id.is_unique
x = cl.merge(m, on="id")
V = {"SUPPORTED": "supported", "SUPPORTED_SECONDARY_ONLY": "republisher", "PARTIAL": "partial",
     "CITATION_MISMATCH": "wrong", "UNVERIFIABLE": "wrong", "CONTRADICTED": "wrong"}
x["v"] = x.verdict.map(V)
os.makedirs(D("data", "derived"), exist_ok=True)
x[["id", "question", "verdict", "v"]].to_csv(D("data", "derived", "claim_question_map.csv"), index=False)
crit = x[x.question.isin(list(Q)[0:1] + list(Q)[2:4])]

# ---------- NBU ----------
nb = pd.read_csv(D("data", "raw", "nbu_extract.csv")); it = nb[nb.item_ua == "Комп'ютерні послуги"]
yr = it[it.freq == "A"].set_index("period").value.astype(float); yr.index = yr.index.astype(int)
qt = it[it.freq == "Q"].set_index("period").value.astype(float)
# monthly series read straight from the NBU workbook (sheet 2.1, row 50 = computer services), Jan 2024 onward
import openpyxl
from openpyxl.utils import column_index_from_string as _ci
_ws = openpyxl.load_workbook(D("data", "raw", "Trade_m.xlsx"), read_only=True, data_only=True)["2.1"]
_rows = list(_ws.iter_rows(min_row=1, max_row=50, values_only=True))
mo = {}
_MON = ("січ", "лют", "бер", "кві", "тра", "чер", "лип", "сер", "вер", "жов", "лис", "гру")
for k in range(_ci("FP") - 1, len(_rows[49])):
    v, h = _rows[49][k], _rows[5][k]
    if v is None or not (isinstance(h, str) and h.lower().startswith(_MON)) or "-" in h: break
    n = k - (_ci("FP") - 1); mo[f"{2024 + n // 12}-{n % 12 + 1:02d}"] = float(v)
mo = pd.Series(mo)
_chk = it[it.freq == "M"].set_index("period").value.astype(float)
assert all(abs(mo[p_] - _chk[p_]) < 0.5 for p_ in _chk.index), "workbook and extract disagree"
mo.to_csv(D("data", "derived", "nbu_computer_services_monthly.csv"), header=["usd_m"])
qt["2026-Q3"] = mo[["2026-07", "2026-08", "2026-09"]].sum()
tot25 = nb[(nb.item_ua == "Експорт послуг усього") & (nb.period == "2025")].value.astype(float).iloc[0]
t3 = mo.rolling(3).sum(); yoy = {}
for p in t3.index:
    y_, mm = p.split("-"); pr = f"{int(y_)-1}-{mm}"
    if pr in t3.index and pd.notna(t3[p]) and pd.notna(t3[pr]): yoy[p] = (t3[p] / t3[pr] - 1) * 100
yoy = pd.Series(yoy); yoy = yoy[yoy.index >= "2026-01"]
_v = list(yoy.values); _m = list(yoy.index)
rec_fire = next((_m[i] for i in range(1, len(_v)) if _v[i] >= 5 and _v[i-1] >= 5), None)
rec_cancel = next((_m[i] for i in range(1, len(_v)) if rec_fire and _m[i] > rec_fire and _v[i] < 2 and _v[i-1] < 2), None)
inside = int(((yoy >= -2) & (yoy <= 4)).sum())
# headline re-check: report value vs NBU
head = [("2022 exports", "~$7.3bn", f"${yr[2022]:,.0f}m", None),
        ("2023 change", "−8.4%", f"{(yr[2023]/yr[2022]-1)*100:+.1f}%", abs(-8.4 - (yr[2023]/yr[2022]-1)*100)),
        ("2024 change", "−4.3%", f"{(yr[2024]/yr[2023]-1)*100:+.1f}%", abs(-4.3 - (yr[2024]/yr[2023]-1)*100)),
        ("2025 exports, change", "$6.66bn, +3.3%", f"${yr[2025]:,.0f}m, {(yr[2025]/yr[2024]-1)*100:+.1f}%", abs(3.3 - (yr[2025]/yr[2024]-1)*100)),
        ("Share of services exports, 2025", "41.6%", f"{yr[2025]/tot25*100:.1f}%", abs(41.6 - yr[2025]/tot25*100)),
        ("Jan–Sep 2026 vs Jan–Sep 2025", "“flat to slightly up”", f"{(qt[['2026-Q1','2026-Q2','2026-Q3']].sum()/qt[['2025-Q1','2025-Q2','2025-Q3']].sum()-1)*100:+.1f}%", None)]
maxdev = max(h[3] for h in head if h[3] is not None)

F = dict(
    n_claims=len(cl), counts={k: int(v) for k, v in cl.verdict.value_counts().items()},
    supported_share=round((cl.verdict == "SUPPORTED").mean() * 100), republisher_share=round((cl.verdict == "SUPPORTED_SECONDARY_ONLY").mean() * 100),
    q5=int((x.question == "Are other buyers staying?").sum()), q5_share=round((x.question == "Are other buyers staying?").mean() * 100),
    background=int((x.question == list(Q)[-1]).sum()),
    crit_n=len(crit), crit_wrong=int((crit.v == "wrong").sum()), crit_partial=int((crit.v == "partial").sum()),
    crit_not_full=int(crit.v.isin(["wrong", "partial"]).sum()), crit_firm=int(crit.verdict.isin(["CITATION_MISMATCH", "CONTRADICTED"]).sum()), crit_soft=int(crit.verdict.isin(["PARTIAL", "UNVERIFIABLE"]).sum()),
    maxdev_pp=round(maxdev, 2), headline=head,
    yoy={k: round(v, 1) for k, v in yoy.items()}, yoy_inside=inside, rec_fire=pd.Timestamp(rec_fire + "-01").strftime("%B") if rec_fire else None, rec_cancel=rec_cancel, yoy_n=len(yoy), yoy_last=round(yoy.iloc[-1], 1),
    q4_2025_vs_q4_2021=round((qt["2025-Q4"] / qt["2021-Q4"] - 1) * 100, 1), q3_2026_vs_q3_2021=round((qt["2026-Q3"] / qt["2021-Q3"] - 1) * 100, 1),
    annual_2025_vs_2022=round((yr[2025] / yr[2022] - 1) * 100, 1), q3_2026=round(qt["2026-Q3"]), nbu_rechecked=int(cl.locator.fillna("").str.contains("snapshot data/raw").sum()))
VL = {"SUPPORTED": "Supported", "SUPPORTED_SECONDARY_ONLY": "Republisher only", "PARTIAL": "Partly right", "CITATION_MISMATCH": "Cited page does not say it", "UNVERIFIABLE": "Unverifiable", "CONTRADICTED": "Contradicted by its source"}
F["crit_rows"] = [[r.id, r.question.replace("Will a team still deliver in two years?", "Continuity").replace("What will it cost?", "Cost").replace("Can I contract, protect IP and pay?", "Contracting"), r.claim_short, VL[r.verdict]] for r in crit.sort_values(["question", "id"]).itertuples()]
json.dump(F, open(D("data", "derived", "facts.json"), "w"), indent=1, ensure_ascii=False)

# ---------- Chart 1 (hero): 78 claims as a dot grid by question ----------
order = list(Q); vorder = ["supported", "republisher", "partial", "wrong"]
f, ax = T.fig(174, 88)
for i, q in enumerate(order):
    s = x[x.question == q].copy(); s["o"] = s.v.map({k: j for j, k in enumerate(vorder)}); s = s.sort_values("o")
    y = len(order) - 1 - i
    for j, (_, r) in enumerate(s.iterrows()):
        ax.scatter(j, y, s=78, color=T.VERDICT[r.v], edgecolor="white", linewidth=0.6, zorder=3)
    ax.text(-1.2, y, q, ha="right", va="center", fontsize=9, color=T.INK)
    ax.text(len(s) + 0.3, y, str(len(s)), va="center", fontsize=7.5, color=T.INK3)
ax.set_xlim(-0.8, 46); ax.set_ylim(-0.7, len(order) - 0.3); ax.axis("off")
crit_y = [len(order) - 1 - order.index(q) for q in (order[0], order[2], order[3])]
ax.axhspan(min(crit_y) - 0.45, max(crit_y) + 0.45, xmin=0, xmax=0.2, color=T.ACCENT_L, alpha=0.35, zorder=0, lw=0)
labs = {"supported": "supported by primary source", "republisher": "only by a republisher", "partial": "partly right", "wrong": "unsupported or wrong"}
for k in vorder: ax.scatter([], [], s=40, color=T.VERDICT[k], label=labs[k])
ax.legend(loc="lower center", bbox_to_anchor=(0.36, -0.2), ncol=4, handletextpad=0.2, columnspacing=1.2)
T.title(ax, "Most claims answer the easy question; the three that decide a deal get eleven",
        "Each dot is one of 78 claims in the AI report, placed under the buyer's question it bears on (our mapping) and coloured by our verdict")
T.save(f, D("charts", "c1_claims_grid"))

# ---------- Chart 2: where the audit changes the reading (ranges) ----------
f, ax = T.fig(174, 80)
rows = [("2026 growth: report", 2, 4, T.ACCENT), ("2026 growth: regional IT cluster", 1.1, 2.6, T.CONTEXT), ("2026 growth: plan on (audit)", 1, 3, T.COMPARE)]
for i, (lab, a, b, col) in enumerate(rows[::-1]):
    ax.plot([a, b], [i, i], color=col, lw=7, solid_capstyle="round"); ax.text(-0.3, i, lab, ha="right", va="center", fontsize=8, color=T.INK)
    ax.text(b + 0.18, i, f"{a:+.1f} to {b:+.1f}%", va="center", fontsize=7.5, color=T.INK2)
ax.axvline(F["yoy_last"], color=T.INK2, lw=0.8, ls=(0, (2, 2))); ax.text(F["yoy_last"] + 0.08, 2.55, f"latest 3-month reading {F['yoy_last']:+.1f}%", ha="left", fontsize=7.5, color=T.INK2)
ax.set_xlim(0, 6); ax.set_ylim(-0.6, 2.9); ax.set_yticks([]); ax.spines["left"].set_visible(False); T.grid_x(ax); ax.set_xlabel("% change on 2025")
T.title(ax, "The report's 2026 outlook sits above the industry's own estimate", "Ranges for full-year 2026 computer-services exports; NBU data to September 2026")
T.save(f, D("charts", "c2_outlook"))

# ---------- Chart 3: NBU quarterly + gates ----------
f, (a1, a2) = T.fig(174, 100, ncols=2, gridspec_kw={"width_ratios": [1.7, 1]})
lab = list(qt.index); xs = range(len(lab))
a1.bar(xs, qt.values, color=[T.ACCENT if l == "2026-Q3" else (T.COMPARE if l == "2021-Q4" else T.CONTEXT_L) for l in lab], width=0.72)
a1.text(lab.index("2021-Q4"), qt["2021-Q4"] + 40, f"pre-war peak\n${qt['2021-Q4']:,.0f}m", ha="center", fontsize=7, color=T.COMPARE)
a1.text(len(lab) - 1, qt["2026-Q3"] + 40, f"Q3 2026\n${qt['2026-Q3']:,.0f}m", ha="center", fontsize=7, color=T.ACCENT)
a1.set_xticks([i for i, l in enumerate(lab) if l.endswith("Q1")]); a1.set_xticklabels([l[:4] for l in lab if l.endswith("Q1")])
a1.set_ylim(0, 2450); T.grid_y(a1); a1.set_ylabel("$ million")
T.title(a1, "Exports have plateaued below the 2021 peak", "NBU, computer services exports per quarter")
a2.axhspan(-2, 4, color=T.COMPARE_L, alpha=0.45, lw=0); a2.axhspan(-8, -5, color=T.ACCENT_L, alpha=0.5, lw=0); a2.axhspan(5, 8, color="#cfe6cf", alpha=0.6, lw=0)
for yv, t in [(0.6, "plateau · run the pilot"), (6.3, "recovery · scale up"), (-6.7, "erosion · EU entities only")]:
    a2.text(0.03, yv, t, transform=a2.get_yaxis_transform(), fontsize=7, color=T.INK2)
xm = range(len(yoy)); a2.plot(xm, yoy.values, color=T.INK, lw=1.8, zorder=3)
a2.scatter(xm, yoy.values, s=22, color=[T.ACCENT if not (-2 <= v <= 4) else T.INK for v in yoy.values], zorder=4, edgecolor="white", linewidth=0.6)
a2.set_xticks(list(xm)); a2.set_xticklabels([p[5:] for p in yoy.index]); a2.set_ylim(-8, 8); a2.axhline(0, color=T.INK3, lw=0.5)
T.title(a2, f"Growth slowing: {F['yoy_inside']} of {F['yoy_n']} readings inside the plateau band", "3-month sum vs a year earlier, %, 2026 (month)")
f.tight_layout(w_pad=2.2); T.save(f, D("charts", "c3_nbu_gates"))

# ---------- Chart 4: failure types ----------
ft = [("Cited only via a republisher", F["counts"].get("SUPPORTED_SECONDARY_ONLY", 0), T.VERDICT["republisher"]),
      ("Partly right: base, period or definition", F["counts"].get("PARTIAL", 0), T.VERDICT["partial"]),
      ("Cited page does not say it", F["counts"].get("CITATION_MISMATCH", 0), T.ACCENT),
      ("Unverifiable", F["counts"].get("UNVERIFIABLE", 0), T.ACCENT),
      ("Contradicted by its own source", F["counts"].get("CONTRADICTED", 0), T.ACCENT)]
f, ax = T.fig(174, 78)
for i, (l, n, c) in enumerate(ft[::-1]):
    ax.barh(i, n, color=c, height=0.62); ax.text(n + 0.3, i, str(n), va="center", fontsize=8, color=T.INK)
ax.set_yticks(range(len(ft))); ax.set_yticklabels([l for l, _, _ in ft[::-1]], fontsize=8, color=T.INK); ax.set_xlim(0, 24); T.grid_x(ax)
ax.set_xlabel("claims (of 78)")
T.title(ax, "Most problems are sourcing, not invention", "Claims that were not fully supported by a primary source, by type")
T.save(f, D("charts", "c4_failures"))
print(json.dumps({k: v for k, v in F.items() if k not in ("headline", "yoy")}, indent=1, ensure_ascii=False))
