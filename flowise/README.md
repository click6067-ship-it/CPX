# Flowise — CPX 사례개발 루프 캔버스

`src/cpx/graph.py` 의 LangGraph(생성→심사→수정 루프)를 **Flowise(별도 로우코드 빌더)의 노드로
재구성**한 것. ⚠️ LangGraph 코드를 자동 렌더한 게 아니다(그건 `docs/cpx-langgraph.png`).
Flowise는 자체 캔버스에서 손으로 짜는 빌더라, 여기 JSON은 그 캔버스에 올릴 **수동 재구성본**이다.
**골격(노드·연결·조건분기·루프)은 graph.py와 구조적으로 동일**하나 *1:1 동치는 아니다* — 종료조건
세부(②B `must_fix=0`)는 Flowise route 에 단순화돼 있다(아래 ⚠️). graph.py 가 정본.
실행 세부(모델 자격증명·state·structured output)는 캔버스에서 마저 설정하면 실제 실행도 가능하다.

## 산출물
- `cpx-case-loop.agentflow.json` — Flowise Agentflow V2 import 파일 (7노드·7엣지)
- `build_agentflow.py` — 위 JSON 생성기(Flowise 내장 템플릿의 검증된 노드 블록을 추출·재조립). 재현용.

## 띄우기 (이미 세팅됨)
```bash
PORT=3100 flowise start          # 전역 설치됨(npm i -g flowise). http://localhost:3100
```
- **로컬 관리자 계정 생성 완료**: 이메일 `admin@cpx.local` (비번은 별도 보관 — *소스에 커밋 안 함*).
  분실 시 `~/.flowise` 초기화 후 첫 방문에서 재생성. (로컬 전용, 외부 비노출)
- **플로우 import 완료**: Agentflows 에 "CPX 사례개발 루프 (LangGraph 재구성)" 이미 있음 → 열면 바로 캔버스.
- 렌더 미리보기: `flowise/cpx-flowise-canvas.png`
- 데이터는 `~/.flowise` 에 저장.

> 재현용 스크립트: `flowise/shot.js` (헤드리스 로그인→캔버스 스크린샷).
> 자격증명은 env 로: `FLOWISE_EMAIL=… FLOWISE_PASSWORD=… node flowise/shot.js <flowId>`.
> 새로 import 하려면 README 아래 "캔버스에 올리기" 절차 또는 build_agentflow.py 재생성.

## 캔버스에 올리기 (import)
1. 브라우저로 `http://localhost:3100` → 로그인.
2. 좌측 **Agentflows** → 새 Agentflow 생성(빈 캔버스).
3. 캔버스 우상단 **설정(⚙ / 햄버거) → Load Agentflow** → `cpx-case-loop.agentflow.json` 선택.
   (또는 Agentflows 목록의 Import 아이콘으로 파일 업로드.)
4. 노드가 좌→우로 뜬다. 각 LLM 노드의 **모델 드롭다운**을 너의 provider(gpt-5.5=OpenAI / Gemini)로
   바꾸고 credential 연결하면 실행 가능. (기본값은 템플릿의 Anthropic — 바꿔야 함.)

## graph.py ↔ Flowise 노드 매핑
| graph.py | Flowise 노드 | 비고 |
|---|---|---|
| `START` | Start (formInput: symptom, diagnosis) | `develop_case(symptom, diagnosis)` 미러 |
| `n_generate` | ① generate (LLM) | `generator._draft` |
| `n_review` | ② review (LLM, structured: verdict+must_fix) | `reviewer.review`+`review_clinical`, state 기록 |
| `route()` | route (Condition: verdict==Accept / ==Minor / Else) | Accept·Minor→확정, Else→수정 |
| `END` | ✅ confirmed (Direct Reply) | 종료 |
| `n_revise` | ✏️ revise (LLM) | `generator._revise` |
| `revise→review` 루프 | ↩ loop (loopBackToNode=review, maxLoopCount=2) | `max_rounds` |

> ⚠️ **종료조건 차이(의도적 단순화)**: graph.py 정본 = `(②A∈{Accept,Minor} AND ②B must_fix=0) OR rounds≥max_rounds`.
> 현재 Flowise route 는 **verdict 만** 보고 Accept/Minor 면 확정한다 — 즉 `must_fix>0` 인 Accept/Minor 도
> 확정될 수 있어 graph.py 와 다르다. 충실하게 하려면 캔버스에서 Condition 에 `must_fix==0` 분기를 추가할 것.
> (이 캔버스는 *작동 원리 설명용*이며 임상 게이트의 정본은 graph.py 다.)
