#!/usr/bin/env python3
"""Rebuild everything from raw data and run the acceptance checks.
    python3 build/build_all.py
Needs Python 3.11+, the packages in requirements.txt, the Inter and Charter fonts, and Google Chrome (for PDF).
"""
import os, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASES = ["03-ai-report-audit", "01-eu-ebike-duties", "02-truck-battery-swapping"]
def run(*cmd):
    print("$", " ".join(cmd)); r = subprocess.run(cmd, cwd=ROOT)
    if r.returncode: sys.exit(r.returncode)
for c in CASES:
    run(sys.executable, f"{c}/code/build.py")
    run(sys.executable, "build/render.py", c)
import json, re, jinja2
fx = {k: json.load(open(os.path.join(ROOT, c, "data/derived/facts.json"))) for k, c in zip(["c3", "c1", "c2"], CASES)}
n_checks = None
r = subprocess.run([sys.executable, "acceptance/run_checks.py"], cwd=ROOT, capture_output=True, text=True)
m = re.search(r"/(\d+) checks pass", r.stdout); n_checks = int(m.group(1)) if m else "all"
env = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.join(ROOT, "build")), undefined=jinja2.StrictUndefined)
open(os.path.join(ROOT, "README.md"), "w").write(env.get_template("README.md.j2").render(n_checks=n_checks, **fx))
print("README.md written")
run(sys.executable, "acceptance/run_checks.py")
