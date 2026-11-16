"""Render a case: facts.json + report.html.j2 -> report.html -> report.pdf. Usage: python3 build/render.py 03-ai-report-audit"""
import json, os, subprocess, sys
import jinja2
case = sys.argv[1]; root = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); C = os.path.join(root, case)
F = json.load(open(os.path.join(C, "data", "derived", "facts.json")))
env = jinja2.Environment(loader=jinja2.FileSystemLoader(C), undefined=jinja2.StrictUndefined, autoescape=False)
env.filters["n"] = lambda v, d=0: f"{v:,.{d}f}"
env.filters["pct"] = lambda v, d=1: f"{v:+.{d}f}%".replace("-", "−")
env.filters["pp"] = lambda v, d=1: f"{abs(v):.{d}f}%"
html = env.get_template("report.html.j2").render(f=F)
from bs4 import BeautifulSoup
soup = BeautifulSoup(html, "html.parser")
for sec in soup.find_all("section", class_="page"):
    kids = [k for k in sec.children if getattr(k, "name", None)]
    if not any(k.name == "h2" for k in kids): continue
    blocks, cur = [], None
    for k in kids:
        if k.name == "h2" or cur is None:
            cur = soup.new_tag("div", attrs={"class": "blk"}); blocks.append(cur)
        cur.append(k.extract())
    for b in blocks: sec.append(b)
script = soup.new_tag("script")
script.string = """
(function(){var mm=96/25.4;
document.querySelectorAll('section.page').forEach(function(sec){
  var blks=sec.querySelectorAll(':scope > .blk'); if(blks.length<2) return;
  sec.style.setProperty('--gap','4mm');
  var used=0; sec.childNodes.forEach(function(n){ if(n.nodeType===1) used+=n.getBoundingClientRect().height; });
  var free=sec.getBoundingClientRect().height-used-(blks.length-1)*4*mm;
  var g=Math.max(4, Math.min(9, 4+free/(blks.length-1)/mm));
  sec.style.setProperty('--gap', g.toFixed(1)+'mm');
});})();"""
soup.body.append(script)
html = str(soup)
if "--debug" in sys.argv: html = html.replace("<body>", "<body class=\"debug\">")
open(os.path.join(C, "report.html"), "w").write(html)
subprocess.run(["google-chrome", "--headless=new", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
                f"--print-to-pdf={os.path.join(C, 'report_debug.pdf' if '--debug' in sys.argv else 'report.pdf')}", os.path.join(C, "report.html")],
               check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180)
print("rendered", case)
