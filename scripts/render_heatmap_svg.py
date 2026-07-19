#!/usr/bin/env python3
import datetime, json, os

HERE = os.path.dirname(__file__)
IN_PATH = os.path.join(HERE, "..", "data", "contributions.json")
OUT_PATH = os.path.join(HERE, "..", "contrib-heatmap.svg")

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
CELL, GAP = 12, 3
STEP, PAD, LEFT_LABEL_W, TOP_LABEL_H, TITLEBAR_H = CELL + GAP, 22, 30, 20, 30
BG, BG2, FRAME, MUTED, ACCENT, GREEN, GOLD = "#0a0e14", "#0d1420", "#1f6feb", "#7d8590", "#22d3ee", "#39d353", "#f2cc60"

# --- TIMING ---
START_DELAY = 0
COL_T, ROW_T, CELL_DUR = 0.035, 0.080, 0.65

def level_for(count):
    if count == 0: return 0
    elif count <= 5: return 1
    elif count <= 15: return 2
    elif count <= 30: return 3
    elif count <= 50: return 4
    return 5

def build_grid(days):
    first = datetime.date.fromisoformat(days[0]["date"])
    grid, col = [], [None] * ((first.weekday() + 1) % 7)
    for d in days:
        date = datetime.date.fromisoformat(d["date"])
        weekday = (date.weekday() + 1) % 7
        while len(col) < weekday: col.append(None)
        col.append((d["date"], d["count"], level_for(d["count"])))
        if len(col) == 7: grid.append(col); col = []
    if col:
        while len(col) < 7: col.append(None)
        grid.append(col)
    return grid

def render(data):
    days = data["days"]
    grid = build_grid(days)
    n_cols = len(grid)
    art_w, art_h = n_cols * STEP, 7 * STEP
    
    month_labels, seen_months = [], set()
    for ci, column in enumerate(grid):
        for cell in column:
            if cell is None: continue
            date = datetime.date.fromisoformat(cell[0])
            key = (date.year, date.month)
            if key not in seen_months and date.day <= 7:
                seen_months.add(key); month_labels.append((ci, date.strftime("%b")))
            break

    canvas_w, canvas_h = PAD + LEFT_LABEL_W + art_w + PAD, TITLEBAR_H + TOP_LABEL_H + art_h + 88 + PAD

    css = f"""
@keyframes cell {{ 0% {{ opacity: 0; transform: translateY(-8px); }} 100% {{ opacity: 1; transform: translateY(0); }} }}
.c {{ opacity: 0; animation: cell {CELL_DUR:.2f}s cubic-bezier(.2,.8,.2,1) both; }}
""".strip()

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w}" height="{canvas_h}" viewBox="0 0 {canvas_w} {canvas_h}" font-family="monospace">',
        f'<style>{css}</style>',
        f'<rect width="{canvas_w}" height="{canvas_h}" rx="12" fill="{BG}"/>',
        f'<rect x="0.5" y="0.5" width="{canvas_w-1}" height="{canvas_h-1}" rx="12" fill="none" stroke="{FRAME}" stroke-opacity="0.55"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{canvas_w}" y2="{TITLEBAR_H}" stroke="{FRAME}" stroke-opacity="0.35"/>'
    ]
    
    for i, dotcol in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        parts.append(f'<circle cx="{PAD + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{dotcol}"/>')
    parts.append(f'<text x="{canvas_w/2}" y="{TITLEBAR_H/2 + 4}" fill="{MUTED}" font-size="12" text-anchor="middle">harsh@github: ~/contributions --graph</text>')

    grid_top, grid_left = TITLEBAR_H + TOP_LABEL_H, PAD + LEFT_LABEL_W
    for ci, label in month_labels:
        parts.append(f'<text x="{grid_left + ci * STEP}" y="{TITLEBAR_H + 14}" fill="{MUTED}" font-size="10">{label}</text>')
    for wi, wname in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
        parts.append(f'<text x="{PAD}" y="{grid_top + wi * STEP + CELL * 0.78:.1f}" fill="{MUTED}" font-size="9">{wname}</text>')

    for ci, column in enumerate(grid):
        for ri, cell in enumerate(column):
            if cell is None: continue
            delay = START_DELAY + ci * COL_T + ri * ROW_T
            parts.append(f'<rect class="c" x="{grid_left + ci * STEP}" y="{grid_top + ri * STEP}" width="{CELL}" height="{CELL}" rx="2.5" fill="{PALETTE[cell[2]]}" style="animation-delay:{delay:.3f}s"/>')

    leg_y = grid_top + art_h + 6
    leg_x = canvas_w - PAD - (len(PALETTE) * (CELL - 1) + 70)
    parts.append(f'<text x="{leg_x}" y="{leg_y + CELL*0.8:.1f}" fill="{MUTED}" font-size="10" text-anchor="end">Less</text>')
    lx = leg_x + 8
    for color in PALETTE:
        parts.append(f'<rect x="{lx}" y="{leg_y}" width="{CELL-1}" height="{CELL-1}" rx="2.2" fill="{color}"/>')
        lx += CELL
    parts.append(f'<text x="{lx + 4}" y="{leg_y + CELL*0.8:.1f}" fill="{MUTED}" font-size="10">More</text>')
    
    sep_y = leg_y + CELL + 14
    parts.append(f'<line x1="0" y1="{sep_y}" x2="{canvas_w}" y2="{sep_y}" stroke="{FRAME}" stroke-opacity="0.25"/>')

    total, best, rng = data["total_contributions"], data["best_day"], data["range"]
    parts.append(f'<text x="{PAD}" y="{sep_y + 24}" font-size="13" fill="{GREEN}"><tspan font-weight="700">{total:,}</tspan><tspan fill="{MUTED}"> contributions in the last year</tspan></text>')
    parts.append(f'<text x="{canvas_w - PAD}" y="{sep_y + 24}" font-size="12" fill="{MUTED}" text-anchor="end">{rng["start"]} → {rng["end"]}</text>')
    
    cs, ls = data["current_streak"]["length"], data["longest_streak"]["length"]
    parts.append(f'<text x="{PAD}" y="{sep_y + 48}" font-size="13" fill="{MUTED}">current streak <tspan fill="{ACCENT}" font-weight="700">{cs} days</tspan> · longest <tspan fill="{ACCENT}" font-weight="700">{ls} days</tspan></text>')
    parts.append(f'<text x="{canvas_w - PAD}" y="{sep_y + 48}" font-size="12" fill="{MUTED}" text-anchor="end">best day <tspan fill="{GOLD}" font-weight="700">{best["count"]}</tspan> on {best["date"]}</text>')

    parts.append("</svg>")
    return "".join(parts)

if __name__ == "__main__":
    with open(IN_PATH) as f: data = json.load(f)
    svg = render(data)
    with open(OUT_PATH, "w") as f: f.write(svg)
