#!/usr/bin/env python3
"""excalidraw → PNG 미리보기 (레이아웃 겹침/관통 시각 점검용). 인자: 입력.excalidraw 출력.png"""
import json, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Rectangle, Polygon, FancyArrowPatch

fm.fontManager.addfont("/home/click/.local/share/fonts/malgun.ttf")
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

src, out = sys.argv[1], sys.argv[2]
d = json.load(open(src, encoding="utf-8"))
els = [e for e in d["elements"] if not e.get("isDeleted")]

fig, ax = plt.subplots(figsize=(12.5, 9))
for e in els:
    t = e["type"]; x, y, w, h = e["x"], e["y"], e["width"], e["height"]
    bg = e.get("backgroundColor", "transparent"); fc = "none" if bg == "transparent" else bg
    ls = "--" if e.get("strokeStyle") == "dashed" else "-"
    sc = e.get("strokeColor", "#1e1e1e")
    if t == "rectangle":
        ax.add_patch(Rectangle((x, y), w, h, facecolor=fc, edgecolor=sc, linewidth=1.5, linestyle=ls, zorder=1))
    elif t == "diamond":
        ax.add_patch(Polygon([(x + w / 2, y), (x + w, y + h / 2), (x + w / 2, y + h), (x, y + h / 2)],
                             closed=True, facecolor=fc, edgecolor=sc, linewidth=1.5, zorder=1))
    elif t == "arrow":
        pts = [(x + px, y + py) for px, py in e["points"]]
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        ax.plot(xs, ys, color=sc, linewidth=1.6, linestyle=ls, zorder=3)
        ax.add_patch(FancyArrowPatch(pts[-2], pts[-1], arrowstyle="-|>", mutation_scale=14,
                                     color=sc, linewidth=1.6, zorder=3))
    elif t == "text":
        ha = e.get("textAlign", "left")
        tx = x + w / 2 if ha == "center" else x
        ax.text(tx, y, e["text"], ha=ha, va="top", fontsize=e.get("fontSize", 16) * 0.72,
                color=sc, zorder=4)

_xs = [e["x"] for e in els] + [e["x"] + e["width"] for e in els]
_ys = [e["y"] for e in els] + [e["y"] + e["height"] for e in els]
ax.set_xlim(min(_xs) - 25, max(_xs) + 25); ax.set_ylim(min(_ys) - 25, max(_ys) + 25)
ax.invert_yaxis(); ax.set_aspect("equal"); ax.axis("off")
plt.tight_layout()
plt.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
print("PNG:", out)
