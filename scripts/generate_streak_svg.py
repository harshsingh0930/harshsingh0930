#!/usr/bin/env python3
import sys, json, os, datetime, urllib.request

USER = sys.argv[1] if len(sys.argv) > 1 else "harshsingh0930"
OUT  = sys.argv[2] if len(sys.argv) > 2 else "streak.svg"

def get_data(user):
    url = f"https://github-contributions-api.jogruber.de/v4/{user}?y=last"
    try:
        with urllib.request.urlopen(url, timeout=25) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        here = os.path.join(os.path.dirname(os.path.abspath(__file__)), "contrib.json")
        if os.path.exists(here): return json.load(open(here))
        raise

data = get_data(USER)
contribs, total = data["contributions"], data["total"]["lastYear"]

# ---- Layout & Timing ----
CELL, GAP, RAD, LEFT, TOP = 13, 3, 2.5, 34, 24
COLORS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
GRAY = "#7d8590"
MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

START_DELAY = 1.0
REVEAL_DUR, DUR = 4.0, 0.7

n = len(contribs)
NW = (n + 6) // 7
W, H = LEFT + NW*(CELL+GAP) + 6, TOP + 7*(CELL+GAP) + 22
maxorder = (NW-1) + 6*0.55

rects, labels = [], []
sd, last_m = datetime.date.fromisoformat(contribs[0]["date"]), None

for wk in range(NW):
    d = sd + datetime.timedelta(days=wk*7)
    if d.month != last_m:
        last_m = d.month
        labels.append(f'<text class="lbl" x="{LEFT+wk*(CELL+GAP)}" y="{TOP-8}">{MONTHS[d.month-1]}</text>')

for name, r in [("Mon",1),("Wed",3),("Fri",5)]:
    labels.append(f'<text class="lbl" x="2" y="{TOP+r*(CELL+GAP)+CELL-2}">{name}</text>')

for i, c in enumerate(contribs):
    wk, row, lvl = i//7, i%7, c["level"]
    x, y = LEFT + wk*(CELL+GAP), TOP + row*(CELL+GAP)
    delay = round(START_DELAY + (wk + row*0.55)/maxorder * REVEAL_DUR, 3)
    rects.append(f'<rect class="c {"g" if lvl>=1 else "e"}" x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="{RAD}" fill="{COLORS[lvl]}" style="animation-delay:{delay}s"/>')

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif">
<style>
  text.lbl {{ fill:{GRAY}; font-size:12px; font-weight:600; }}
  text.total {{ fill:#e6edf3; font-size:14px; font-weight:700; }}
  .c {{ transform-box:fill-box; transform-origin:center; opacity:0; animation:pop {DUR}s ease-out both; }}
  .g {{ animation:pop {DUR}s ease-out both, flash {DUR+0.2}s ease-out both; }}
  
  @keyframes pop {{ 0%{{opacity:0;transform:scale(.3)}} 60%{{opacity:1;transform:scale(1.05)}} 100%{{opacity:1;transform:scale(1)}} }}
  @keyframes flash {{ 0%{{filter:brightness(2.2)}} 50%{{filter:brightness(2.2)}} 100%{{filter:brightness(1)}} }}
</style>
<rect width="{W}" height="{H}" fill="none"/>
{''.join(labels)}
{''.join(rects)}
<text class="total" x="{LEFT}" y="{H-6}">{total:,} contributions in the last year</text>
</svg>'''

with open(OUT, "w") as f: f.write(svg)
