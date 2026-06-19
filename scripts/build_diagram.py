"""
CPX-AI 작동방식 → excalidraw 다이어그램(.excalidraw) 생성.
실행: .venv/bin/python scripts/build_diagram.py
출력: docs/cpx-flow.excalidraw + 바탕화면 복사. excalidraw.com → File → Open(또는 드래그)로 열기.
"""
import json, shutil
from pathlib import Path

E = []
_id = [0]
def nid():
    _id[0] += 1
    return f"el{_id[0]}"

BASE = dict(angle=0, strokeColor="#1e1e1e", fillStyle="solid", strokeWidth=2,
            strokeStyle="solid", roughness=1, opacity=100, groupIds=[], frameId=None,
            seed=1, version=1, versionNonce=1, isDeleted=False, boundElements=[],
            updated=1, link=None, locked=False)


def rect(x, y, w, h, color):
    E.append({**BASE, "type": "rectangle", "id": nid(), "x": x, "y": y, "width": w,
              "height": h, "backgroundColor": color, "roundness": {"type": 3}})


def text(x, y, w, s, size=16, align="center", color="#1e1e1e"):
    lines = s.count("\n") + 1
    E.append({**BASE, "type": "text", "id": nid(), "x": x, "y": y, "width": w,
              "height": size * 1.25 * lines, "backgroundColor": "transparent",
              "strokeColor": color, "roundness": None, "text": s, "fontSize": size,
              "fontFamily": 1, "textAlign": align, "verticalAlign": "top",
              "baseline": size, "containerId": None, "originalText": s, "lineHeight": 1.25})


def box(x, y, w, h, label, color):
    rect(x, y, w, h, color)
    lines = label.count("\n") + 1
    text(x, y + (h - lines * 20) / 2, w, label, 16)


def arrow(x1, y1, x2, y2, label=None, color="#1e1e1e"):
    E.append({**BASE, "type": "arrow", "id": nid(), "x": x1, "y": y1,
              "width": x2 - x1, "height": y2 - y1, "strokeColor": color,
              "backgroundColor": "transparent", "roundness": {"type": 2},
              "points": [[0, 0], [x2 - x1, y2 - y1]], "lastCommittedPoint": None,
              "startBinding": None, "endBinding": None, "startArrowhead": None,
              "endArrowhead": "arrow"})
    if label:
        text((x1 + x2) / 2 - 30, (y1 + y2) / 2 - 22, 60, label, 13, color="#e8590c")


BLUE, GREEN, YEL, VIO, GRAY = "#a5d8ff", "#b2f2bb", "#ffec99", "#d0bfff", "#e9ecef"

text(40, 20, 900, "CPX-AI 작동방식 — 멀티 에이전트 + RAG + 검증(H2)", 24, "left")

# ── A. 사례 개발 루프 (교수자 지원) ──
text(40, 80, 400, "A. 사례 개발 루프  (교수 부담↓)", 18, "left", "#1971c2")
box(40, 120, 150, 70, "기존 CPX 사례\n(씨앗)", GRAY)
box(250, 120, 160, 80, "① 사례 생성\n(gpt-5.5)", BLUE)
box(470, 120, 170, 90, "② 사례 검토\n(gpt-5.5)\n구조 + 임상", BLUE)
box(710, 120, 130, 70, "확정 사례", GRAY)
arrow(190, 155, 250, 155)
arrow(410, 160, 470, 160)
arrow(640, 150, 710, 150, "Accept")
arrow(550, 210, 330, 210, "수정 루프")   # ②→① revise
box(450, 250, 210, 95, "RAG 근거 (오픈북)\ndense: Gemini 임베딩\nsparse: BM25\n→ 교과서(MedQA)", YEL)
arrow(555, 250, 555, 210)               # RAG→②

# ── B. 검증 (H2 — 지금 파일럿) ──
text(40, 380, 400, "B. 검증 (H2 — 지금 교수 파일럿)", 18, "left", "#6741d9")
box(40, 420, 160, 80, "교수 피드백\n(과거 = 정답지)", GRAY)
box(250, 420, 160, 80, "AI 리뷰\n(② 출력)", BLUE)
box(470, 420, 180, 90, "블라인드 설문\n교수가 A/B 평가\ncpx-adj-web", VIO)
box(720, 420, 170, 90, "집계\nrecall·precision\nblind·ICC·CI", VIO)
arrow(200, 460, 470, 460)
arrow(410, 465, 470, 465)
arrow(650, 465, 720, 465)
arrow(555, 210, 340, 420, "② 리뷰")     # ② → AI리뷰(검증 입력)

# ── C. 학생 런타임 ──
text(40, 555, 400, "C. 학생 런타임 (학습자 지원)", 18, "left", "#2f9e44")
box(40, 595, 150, 70, "확정 사례", GRAY)
box(250, 595, 170, 80, "③ 가상환자\n(GPT-4o · 음성)", GREEN)
box(480, 595, 130, 70, "학생 대화", GRAY)
box(660, 595, 150, 80, "④ 자동채점\n(GPT-4o)", GREEN)
box(860, 595, 110, 70, "피드백", GRAY)
arrow(190, 630, 250, 630)
arrow(420, 635, 480, 635)
arrow(610, 630, 660, 630)
arrow(810, 635, 860, 635)
arrow(775, 190, 115, 595, "확정→학생")   # 확정 사례 → 학생 런타임

# 범례
box(660, 250, 320, 95, "모델: 파랑=생성·검토(gpt-5.5)  초록=대화·채점(GPT-4o)\n노랑=RAG(Gemini임베딩+BM25)  보라=검증\n임베딩은 Gemini 유지 · Claude 결제 풀리면 ①②교체", "#fff9db")

doc = {"type": "excalidraw", "version": 2, "source": "cpx", "elements": E,
       "appState": {"viewBackgroundColor": "#ffffff", "gridSize": None}, "files": {}}
out = Path("docs/cpx-flow.excalidraw")
out.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
try:
    shutil.copy(out, "/mnt/c/Users/click/Desktop/cpx-작동방식.excalidraw")
    print("✅ 바탕화면 복사: cpx-작동방식.excalidraw")
except Exception as e:
    print("바탕화면 복사 실패:", e)
print(f"✅ {out} · 요소 {len(E)}개")
