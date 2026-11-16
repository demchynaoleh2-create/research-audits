#!/usr/bin/env python3
"""Acceptance checks for the whole repository. Run from the repo root after build/build_all.py:
    python3 acceptance/run_checks.py
Exit code 0 = every check passes. Prints one line per check.
"""
import os, re, sys, csv, json, glob, subprocess
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASES = {"01": "01-eu-ebike-duties", "02": "02-truck-battery-swapping", "03": "03-ai-report-audit"}
# Internal working names must not appear in public files. Only their hashes are stored here.
import hashlib
FORBIDDEN_HASHES = {"09cf980b5ff304ac", "57de4cf40144bdf7", "5fb4211228d73e0b", "693b286515bd1dd0", "7319021c1cc1e94a", "970ec274ca867815", "e12ce8285efc67c6", "f003e57a2e2a6269"}
def has_internal(t):
    toks = set(re.findall(r"[^\W\d_]+", t.lower()))
    return any(hashlib.sha256(w.encode()).hexdigest()[:16] in FORBIDDEN_HASHES for w in toks)
results = []

def ok(cid, cond, msg):
    results.append((cid, bool(cond), msg))

def text(path):
    return open(path, encoding="utf-8").read()

def visible(html):
    from bs4 import BeautifulSoup
    s = BeautifulSoup(html, "html.parser")
    for t in s(["script", "style"]): t.decompose()
    return s.get_text(" ")

for n, folder in CASES.items():
    d = os.path.join(ROOT, folder)
    html_path, pdf, facts = os.path.join(d, "report.html"), os.path.join(d, "report.pdf"), os.path.join(d, "data/derived/facts.json")
    ok(f"G{n}-files", all(os.path.exists(p) for p in (html_path, pdf, facts, os.path.join(d, "claims.csv"))), "report, PDF, facts and claims exist")
    html = text(html_path); vis = visible(html)
    ok(f"G{n}-jinja", "{{" not in html and "{%" not in html, "no unrendered template code")
    ok(f"G{n}-cyrillic", not re.search(r"[Ѐ-ӿ]", vis), "English only in the report")
    ok(f"G{n}-internal", not has_internal(vis), "no internal names in the report")
    pages = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout).group(1))
    ok(f"G{n}-pages", 7 <= pages <= 8, f"7–8 pages (has {pages})")
    rows = list(csv.reader(open(os.path.join(d, "claims.csv"), encoding="utf-8")))
    head, body = rows[0], rows[1:]
    ok(f"G{n}-csv", all(len(r) == len(head) for r in body), "claims.csv rows all have the header's column count")
    ids = [r[0] for r in body]
    ok(f"G{n}-unique", len(ids) == len(set(ids)), "claim ids unique")
    for pre in sorted({i[0] for i in ids}):
        nums = [int(i[1:]) for i in ids if i[0] == pre]
        ok(f"G{n}-seq-{pre}", nums == list(range(1, len(nums) + 1)), f"{pre}-ids run 1..{len(nums)} without gaps")
    refs = set()
    for m in re.finditer(r'class="ref">\[([^\]]+)\]', html):
        refs |= {x.strip() for x in m.group(1).split(",")}
    missing = sorted(r for r in refs if re.fullmatch(r"[A-Z]\d\d", r) and r not in ids)
    ok(f"G{n}-refs", not missing, "every [ref] in the report exists in claims.csv" + (f" (missing {missing})" if missing else ""))
    for c in glob.glob(os.path.join(d, "charts", "*.svg")):
        ok(f"G{n}-chart-{os.path.basename(c)}", os.path.exists(c[:-4] + ".png"), "chart has SVG and PNG")

# repo-wide public files
for p in ["README.md", "METHOD.md", "LICENSE", "REVIEW_LOG.md"]:
    path = os.path.join(ROOT, p)
    ok(f"R-{p}", os.path.exists(path), f"{p} exists")
    if os.path.exists(path):
        t = text(path)
        ok(f"R-{p}-cyr", not re.search(r"[Ѐ-ӿ]", t), f"{p} in English")
        ok(f"R-{p}-int", not has_internal(t), f"{p} has no internal names")
bad = []
for path in glob.glob(os.path.join(ROOT, "**", "*"), recursive=True):
    if os.path.isfile(path) and path.rsplit(".", 1)[-1] in ("md", "py", "j2", "yaml", "csv", "json", "txt", "html", "css"):
        if has_internal(open(path, encoding="utf-8", errors="ignore").read()): bad.append(os.path.relpath(path, ROOT))
ok("R-internal-all", not bad, "no internal names in any text file" + (f" (found in {bad})" if bad else ""))
sha = os.path.join(ROOT, CASES["03"], "data/raw/SHA256SUMS.txt")
if os.path.exists(sha):
    r = subprocess.run(["sha256sum", "-c", "--quiet", os.path.basename(sha)], cwd=os.path.dirname(sha), capture_output=True, text=True)
    ok("R-sha256", r.returncode == 0, "central-bank snapshots match their SHA-256 checksums")

# per-finding checks
for c in yaml.safe_load(open(os.path.join(ROOT, "acceptance", "checklist.yaml"), encoding="utf-8")):
    d = os.path.join(ROOT, CASES[str(c["case"]).zfill(2)])
    if c["type"] == "fact":
        f = json.load(open(os.path.join(d, "data/derived/facts.json")))
        try: res = eval(c["expr"], {"abs": abs, "round": round}, {"f": f})
        except Exception as e: res = False
        ok(c["id"], res, c["why"])
    else:
        vis = visible(text(os.path.join(d, "report.html")))
        hit = re.search(c["pattern"], vis)
        ok(c["id"], hit if c["type"] == "present" else not hit, c["why"])

w = max(len(r[0]) for r in results)
for cid, passed, msg in results:
    print(f"{'PASS' if passed else 'FAIL'}  {cid:<{w}}  {msg}")
fails = sum(not p for _, p, _ in results)
print(f"\n{len(results) - fails}/{len(results)} checks pass")
sys.exit(1 if fails else 0)
