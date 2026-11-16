#!/usr/bin/env python3
"""Case B data pull: EU imports of e-bikes (CN 87116010) + neighbour code 87116090.
Source: Eurostat Comext, dataset DS-045409 (EU trade since 1988 by HS2-4-6 and CN8), monthly.
Eurostat Comext API: multi-value parameters work; responses are JSON-stat 2.0.
Run:  python3 comext_ebikes.py      -> data/comext_long_v2.csv, data/summary.csv, charts/*.png
Needs: requests, pandas, matplotlib.  Writes only new files in ./data and ./charts.
"""
import itertools, json, os, sys, time
from datetime import date
import requests, pandas as pd

BASE = "https://ec.europa.eu/eurostat/api/comext/dissemination/statistics/1.0/data/DS-045409"
REPORTERS = ["EU27_2020"]
PARTNERS  = ["CN", "TW", "VN", "KH", "TH", "MY", "ID", "EXT_EU27_2020"]   # EXT = all non-EU origins
PRODUCTS  = ["87116010", "87116090"]                  # 90 = rival explanation (possible circumvention)
INDICATORS = ["SUPPLEMENTARY_QUANTITY", "VALUE_IN_EUROS", "QUANTITY_IN_100KG"]
START = (2017, 1)

def months():
    y, m = START; t = date.today()
    while (y, m) <= (t.year, t.month):
        yield f"{y}-{m:02d}"; m += 1
        if m == 13: y, m = y + 1, 1

def fetch(reporter, product, times):
    params = [("format","JSON"),("lang","en"),("freq","M"),("flow","1"),
              ("reporter",reporter),("product",product)]
    params += [("partner",p) for p in PARTNERS] + [("indicators",i) for i in INDICATORS]
    params += [("time",t) for t in times]
    for attempt in range(4):
        r = requests.get(BASE, params=params, timeout=120)
        if r.status_code == 200: return r.json()
        time.sleep(5 * (attempt + 1))
    r.raise_for_status()

def jsonstat_rows(j):
    ids, sizes = j["id"], j["size"]
    cats = [sorted(j["dimension"][d]["category"]["index"].items(), key=lambda kv: kv[1]) for d in ids]
    out = []
    for flat, val in j.get("value", {}).items():
        k = int(flat); idx = []
        for s in reversed(sizes): idx.append(k % s); k //= s
        idx.reverse()
        row = {d: cats[n][idx[n]][0] for n, d in enumerate(ids)}
        row["value"] = val; out.append(row)
    return out

def main():
    os.makedirs("data", exist_ok=True)
    allm = list(months()); rows = []
    for rep, prod in itertools.product(REPORTERS, PRODUCTS):
        for i in range(0, len(allm), 24):               # 24 months per call keeps URLs short
            chunk = allm[i:i+24]
            rows += jsonstat_rows(fetch(rep, prod, chunk))
            print(f"{rep} {prod} {chunk[0]}..{chunk[-1]} ok", file=sys.stderr)
    df = pd.DataFrame(rows)
    wide = df.pivot_table(index=["reporter","partner","product","time"], columns="indicators",
                          values="value", aggfunc="sum").reset_index()
    wide["eur_per_unit"] = wide["VALUE_IN_EUROS"] / wide["SUPPLEMENTARY_QUANTITY"]
    wide.to_csv("data/comext_long_v2.csv", index=False)
    meta = {"dataset":"DS-045409","pulled":date.today().isoformat(),"rows":len(wide),
            "last_month_with_data": wide.dropna(subset=["SUPPLEMENTARY_QUANTITY"])["time"].max()}
    json.dump(meta, open("data/meta.json","w"), indent=2)

    print(json.dumps(meta))

if __name__ == "__main__":
    main()
