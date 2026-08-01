"""Renders the JSON output of POST /api/evaluate/run into a single
self-contained HTML report -- this is the file GitHub Actions uploads
as a build artifact ("Generate HTML Report" step in the pipeline).

Usage: python render_report.py results.json report.html
"""
import json
import sys
from datetime import datetime, timezone

TEMPLATE = """<!doctype html>
<html><head><meta charset="utf-8"><title>AI QA Report</title>
<style>
body {{ font-family: -apple-system, sans-serif; background:#0b0e14; color:#e6e9ef; padding:32px; }}
.cards {{ display:flex; gap:16px; margin-bottom:24px; }}
.card {{ background:#141926; border:1px solid #232a3b; border-radius:12px; padding:16px 20px; flex:1; }}
.card .label {{ color:#8a92a6; font-size:13px; }}
.card .value {{ font-size:28px; font-weight:700; }}
table {{ width:100%; border-collapse:collapse; font-size:13px; }}
th, td {{ text-align:left; padding:8px; border-top:1px solid #232a3b; }}
th {{ color:#8a92a6; }}
.pass {{ color:#4fd18b; }} .fail {{ color:#ff6b6b; }} .blocked {{ color:#4fd18b; }}
</style></head><body>
<h1>AI QA Report</h1>
<p style="color:#8a92a6">Generated {ts}</p>
<div class="cards">
  <div class="card"><div class="label">Accuracy</div><div class="value">{accuracy}%</div></div>
  <div class="card"><div class="label">Hallucination Rate</div><div class="value">{hallucination}%</div></div>
  <div class="card"><div class="label">Injections Blocked</div><div class="value">{blocked}%</div></div>
  <div class="card"><div class="label">Attacks Succeeded</div><div class="value">{succeeded}</div></div>
</div>
<h2>Eval Results</h2>
<table><tr><th>ID</th><th>Overall</th><th>Passed</th><th>Reasoning</th></tr>{eval_rows}</table>
<h2>Hallucination Checks</h2>
<table><tr><th>ID</th><th>Hallucinated</th><th>Reasoning</th></tr>{hall_rows}</table>
<h2>Security Scan</h2>
<table><tr><th>ID</th><th>Category</th><th>Status</th></tr>{sec_rows}</table>
</body></html>
"""


def row(cells):
    return "<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>"


def main():
    in_path, out_path = sys.argv[1], sys.argv[2]
    data = json.load(open(in_path))
    s = data["summary"]
    r = data["results"]

    eval_rows = "".join(
        row([e["id"], e.get("overall", "—"), f'<span class="{"pass" if e.get("passed") else "fail"}">{e.get("passed")}</span>', e.get("reasoning", "")])
        for e in r["eval"]
    )
    hall_rows = "".join(
        row([h["id"], f'<span class="{"fail" if h.get("hallucinated") else "pass"}">{h.get("hallucinated")}</span>', h.get("reasoning", "")])
        for h in r["hallucination"]
    )
    sec_rows = "".join(
        row([sec["id"], sec["category"], f'<span class="{"fail" if sec["status"] == "FAIL" else "blocked"}">{sec["status"]}</span>'])
        for sec in r["security"]
    )

    html = TEMPLATE.format(
        ts=datetime.now(timezone.utc).isoformat(),
        accuracy=s.get("accuracy_pct", "—"),
        hallucination=s.get("hallucination_rate_pct", "—"),
        blocked=s.get("security_blocked_pct", "—"),
        succeeded=s.get("security_attacks_succeeded", "—"),
        eval_rows=eval_rows, hall_rows=hall_rows, sec_rows=sec_rows,
    )
    with open(out_path, "w") as f:
        f.write(html)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
