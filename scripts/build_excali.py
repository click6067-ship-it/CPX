#!/usr/bin/env python3
"""CPX-AI 작동방식 excalidraw 생성 (좌표 직접 설계 — 박스 겹침 0, 화살표 박스 비관통).
출력: docs/cpx-flow-claude.excalidraw"""
import json, os

els, boxes = [], []
_s = [1000]
def sd():
    _s[0] += 7
    return _s[0]

def _base(t, x, y, w, h, **kw):
    e = {"id": f"{t[0]}{sd()}", "type": t, "x": x, "y": y, "width": w, "height": h,
         "angle": 0, "strokeColor": "#1e1e1e", "backgroundColor": "transparent",
         "fillStyle": "solid", "strokeWidth": 2, "strokeStyle": "solid", "roughness": 1,
         "opacity": 100, "groupIds": [], "frameId": None, "roundness": None, "seed": sd(),
         "version": 1, "versionNonce": sd(), "isDeleted": False, "boundElements": [],
         "updated": 1, "link": None, "locked": False}
    e.update(kw)
    els.append(e)
    return e

def rect(x, y, w, h, bg, stroke="#1e1e1e", dash=False, rounded=True):
    _base("rectangle", x, y, w, h, backgroundColor=bg, strokeColor=stroke,
          strokeStyle="dashed" if dash else "solid",
          roundness={"type": 3} if rounded else None)

def diamond(x, y, w, h, bg, stroke="#1e1e1e"):
    _base("diamond", x, y, w, h, backgroundColor=bg, strokeColor=stroke)
    boxes.append((x, y, w, h, "확정?"))

def text(x, y, w, h, s, fs=16, align="center", color="#1e1e1e"):
    lines = s.count("\n") + 1
    th = lines * fs * 1.25
    ty = y + (h - th) / 2 if h else y
    _base("text", x, ty, w, th, strokeColor=color, strokeWidth=1, fontSize=fs,
          fontFamily=2, textAlign=align, verticalAlign="top", text=s, originalText=s,
          containerId=None, lineHeight=1.25, baseline=int(fs * 0.9))

def node(x, y, w, h, label, bg, fs=16):
    rect(x, y, w, h, bg)
    text(x, y, w, h, label, fs)
    boxes.append((x, y, w, h, label.replace("\n", " ")))

def arrow(pts, label=None, dash=False, color="#1e1e1e", lpos=None):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    x0, y0 = pts[0]
    rel = [[p[0] - x0, p[1] - y0] for p in pts]
    _base("arrow", x0, y0, max(xs) - min(xs), max(ys) - min(ys),
          strokeStyle="dashed" if dash else "solid", strokeColor=color,
          roundness={"type": 2}, points=rel, lastCommittedPoint=None,
          startBinding=None, endBinding=None, startArrowhead=None, endArrowhead="arrow")
    if label:
        mx, my = lpos if lpos else (sum(xs) / len(xs), sum(ys) / len(ys))
        text(mx - 40, my - 9, 80, 16, label, 12, "center", "#495057")

# ===== 섹션 배경 (맨 뒤) =====
rect(20, 50, 1160, 250, "#e7f5ff", stroke="#74c0fc")    # A
rect(20, 335, 1160, 290, "#fff9db", stroke="#ffe066")   # B
rect(20, 650, 1160, 185, "#ebfbee", stroke="#8ce99a")   # C
text(40, 62, 460, 28, "A. 사례 개발 루프 (교수 지원)", 20, "left", "#1971c2")
text(40, 347, 460, 28, "B. 검증 — H2 (현재 파일럿)", 20, "left", "#e8590c")
text(40, 662, 460, 28, "C. 학생 런타임 (목표 산출물)", 20, "left", "#2f9e44")

# ===== A 노드 =====
node(60, 110, 170, 64, "기존 CPX 사례\n(씨앗)", "#a5d8ff")
node(280, 110, 170, 64, "① 생성\ngpt-5.5", "#a5d8ff")
node(500, 110, 188, 64, "② 검토\ngpt-5.5·구조+임상", "#a5d8ff", fs=15)
diamond(730, 104, 150, 76, "#ffd8a8"); text(730, 104, 150, 76, "확정?", 16)
node(930, 110, 170, 64, "확정 사례", "#63e6be")
node(500, 212, 220, 56, "RAG 근거\nGemini 임베딩+BM25 → 교과서", "#d0bfff", fs=13)
# A 화살표
arrow([[230, 142], [280, 142]])
arrow([[450, 142], [500, 142]])
arrow([[688, 142], [730, 142]])
arrow([[880, 142], [930, 142]], "예")
arrow([[610, 212], [610, 174]])
arrow([[805, 104], [805, 88], [365, 88], [365, 110]], "아니오·수정", color="#e8590c")

# ===== B 노드 =====
node(280, 400, 170, 64, "교수 과거 피드백\n(정답지)", "#ffec99")
node(280, 505, 170, 64, "② AI 리뷰", "#ffec99")
node(545, 452, 185, 64, "블라인드 설문\n교수 A/B 익명", "#ffd43b")
node(800, 452, 170, 64, "집계\nrecall·precision·ICC", "#ffec99")
# B 화살표
arrow([[450, 432], [545, 470]])
arrow([[450, 537], [545, 500]])
arrow([[730, 484], [800, 484]])
# cross A→B
arrow([[585, 174], [585, 188], [245, 188], [245, 537], [280, 537]], "② 리뷰 = 검증 대상", dash=True, color="#868e96", lpos=(415, 200))

# ===== C 노드 =====
node(280, 710, 170, 64, "③ 가상환자\nGPT-4o · 음성", "#b2f2bb")
node(500, 710, 170, 64, "학생 대화", "#b2f2bb")
node(720, 710, 170, 64, "④ 자동채점\nGPT-4o", "#b2f2bb")
node(940, 710, 170, 64, "피드백", "#b2f2bb")
# C 화살표
arrow([[450, 742], [500, 742]])
arrow([[670, 742], [720, 742]])
arrow([[890, 742], [940, 742]])
# cross A→C
arrow([[1015, 174], [1015, 690], [365, 690], [365, 710]], "확정 사례로 구동", dash=True, color="#868e96", lpos=(690, 680))

# ===== 겹침 검사 =====
def overlap(a, b):
    ax, ay, aw, ah, _ = a; bx, by, bw, bh, _ = b
    return ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah
warn = 0
for i in range(len(boxes)):
    for j in range(i + 1, len(boxes)):
        if overlap(boxes[i], boxes[j]):
            warn += 1
            print(f"  ⚠️ OVERLAP: {boxes[i][4]!r} ↔ {boxes[j][4]!r}")

doc = {"type": "excalidraw", "version": 2, "source": "https://excalidraw.com",
       "elements": els, "appState": {"viewBackgroundColor": "#ffffff", "gridSize": None},
       "files": {}}
out = os.path.join(os.path.dirname(__file__), "..", "docs", "cpx-flow.excalidraw")
with open(out, "w", encoding="utf-8") as f:
    json.dump(doc, f, ensure_ascii=False, indent=2)
print(f"SAVED {os.path.relpath(out)} (elements={len(els)}, nodes={len(boxes)}, overlaps={warn})")
