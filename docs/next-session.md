# 다음 세션 인계 — 설사·변비 발현소견 검토표 (2026-08-11 **10라운드** 종료 시점)

> 이 파일부터 읽고 시작한다. 이전 세션 전문은 `~/main/logs/`, 요약은 `docs/worklog.md` 맨 끝,
> 검수 이력 정본은 `docs/verification-log.yaml`(**10라운드까지** 기록됨).

## 지금 어디까지 됐나

**커밋·푸시 완료 (공개 repo)**
- `ontology/diarrhea.yaml` **19질환** · `ontology/constipation.yaml` **14질환**
  (3라운드까지 각 12질환 → Codex 지적으로 분리. 아래 "질환 분리" 참조)
- `docs/verification-log.yaml` — 검수기록 정본. `ontology_report.py`가 리포트 HTML에 렌더
- `scripts/textbook_mine.py`(인용 채굴) · `scripts/findings_review.py`(인용 기계대조 + 렌더 + `--snap`)

**미커밋 (저작권 — 교재 원문 인용 포함, `data/working/`는 gitignored)**
- `data/working/findings/{diarrhea,constipation}_findings.json` + `.html`
- 설사 소견81·조건19·참고87 / 변비 소견55·조건7·참고48 = **297건, 인용 대조 297/297 통과 · 구조 경고 0건**
- 바탕화면 사본 = `CPX_설사변비_온톨로지_260811/15_설사_*_v7.*`, `16_변비_*_v7.*` (v4~v6도 나란히 보존)

## 🚨 최우선 — Codex 7차 MAJOR 잔여 + 8차 검수

원문 = 바탕화면 `Codex검수7_luna.md`(4~7차 전부 보존. 입력 브리프도 각각)

**7차 판정 REVISE — BLOCKER 1 · MAJOR/MINOR 28. BLOCKER와 구조 모순·주요 MAJOR는 10라운드에서 반영.**
전량은 아니며 **8차 재검수도 하지 않았다** — 거기서부터 시작하면 된다.

### 🔴 가장 중요한 사실 — 7회 연속 REVISE
**매 라운드 새 BLOCKER가 나왔고, 5·6·7차의 BLOCKER는 전부 직전 라운드의 내 수정이 만든 것이었다.**
특히 **혈성 설사 항생제 규칙은 세 번 고쳐도 계속 지적됐다**:
① 혈변만으로 항생제(3차) → ② STEC 배제를 전면 금지로(6차, 치료 지연) → ③ 병렬 조건(7차, 같은 환자가
양쪽 충족) → ④ 우선순위 규칙(현재).
**이 한 규칙에 임상 권위자의 확정이 필요하다.** LLM 왕복으로 수렴시킬 수 있는 문제가 아니다.

### ⭐ 새 도구 — `findings_review.py`가 구조 모순도 잡는다
인용 대조가 통과해도 표가 모순되는 것을 코드로 검사한다(첫 실행에서 12건 검출, Codex보다 많았다):
같은 축 안의 인용 중복 · `required_없음_사유`와 required 공존 · `해당없음` 축에 소견 존재 · required도 사유도 없음.
**수정 스크립트를 돌린 뒤에는 반드시 이 경고를 확인할 것.**

### ⚠️ 먼저 알아야 할 것 — 분리는 교수 결정이 아니다
4라운드 인계에 나는 "추가 분리는 CPX 범위를 넘으니 **지도교수 판단 필요**"라고 적었고 그렇게 보고했다.
사용자가 "추가질환분리까지 자동으로"라고 지시해 5라운드에서 실행했다.
**따라서 현재 19+14 카드 구성은 임상 권위자의 결정이 아니라 사용자 지시에 따른 실행 결과다.**
각 카드 `basis`와 `verification-log.yaml` 5라운드에 그렇게 명시해 뒀다.
**교수 보고 시 이 점을 먼저 말할 것.** 공식 감별목록 확보 후 재검토 대상.

### ③ 아직 안 한 추가 분리 (Codex가 더 요구한 것)
V. cholerae·ETEC 등 병원체별 카드, 약물유발 설사의 약물군별 세분, 골반장기탈출 별도 카드.
카드가 더 늘어나면 CPX 10분 station 범위를 확실히 벗어난다. **분리보다 지금 있는 카드를 채우는 게 먼저다.**

### ④ Rome IV 기준 정밀화 — 원문 확보가 선행
현재 IBS·기능성 변비의 Rome 인용은 **Tintinalli의 축약형**이라
"증상 시작 6개월 전부터" · "6개 항목 중 2개 이상" · IBS-C/M subtype의 변 형태 비율 기준이 빠져 있다.
Rome IV 원문(또는 이를 정확히 옮긴 교재)을 코퍼스에서 찾거나 확보해야 한다.

### ⑤ 경보징후(red flag) — 5라운드에서 일부 완료
기능성 변비(Rosen p321 alarm symptoms) · 신경질환성 변비(마미증후군, Bates p463·p380) ·
C. difficile(전격성 = 설사 없이 급성 복증·패혈증, 백혈구 ≥15,000) · 대장암(배변습관 변화+종괴, Bates p311·p338) ·
치열(비전형 = 직장염·크론병 등 이차성, Bates p313). 남은 것: CDI의 "24시간 내 3회 이상 비형성변" 정량 기준.

```bash
.venv/bin/python scripts/textbook_mine.py "검색어" --book rosen     # 채굴 (rosen·tintinalli·sabiston·bates·PART2·PART10·PART12)
.venv/bin/python scripts/findings_review.py data/working/findings/diarrhea_findings.json   # 검증+렌더
.venv/bin/python scripts/findings_review.py <파일> --snap            # 단어중간 절단 인용 복원(1회성 정비)
.venv/bin/python scripts/ontology_lint.py                           # ⭐ yaml 손대면 반드시 (id 충돌·라벨 누락)
```
quote만 정확히 넣으면 book·page·검증은 기계가 한다. 검증 실패는 표에 ✗로 남는다.

## 이번까지 한 것 (4·5라운드)

| 한 일 | 결과 |
|---|---|
| 3라운드 BLOCKER 2건 | ✅ 해결 — 4라운드에서 **재지적되지 않음** |
| role 재정비 (MAJOR 94) | ✅ 구조로 해결 — `참고항목` 축 신설로 검사·치료·감별·역학을 findings에서 분리 |
| 질환 분리 | ✅ 설사 12→15 · 변비 12→13 (검토표·yaml·cypher·그래프 전부) |
| 🐛 인용 페이지 버그 | ✅ **기존 150건 중 54건(36%)이 틀려 있었다** — 수정·교차검증 143/143 |
| 인용 단어중간 절단 8건 | ✅ `--snap`으로 복원 |
| Rosen·Tintinalli 채굴 | ⚠️ 시작함(0건 → 다수). 밀도는 여전히 부족 |
| Codex 4라운드 검수 | ⚠️ REVISE — BLOCKER 1 즉시반영 |
| **5라운드** 추가 분리 | ✅ 설사 15→19 · 변비 13→14 (**사용자 결정**, 교수 판단 아님) |
| **5라운드** 경보징후 보강 | ✅ Rosen·Bates·Harrison 채굴로 5개 카드에 red flag 추가 |
| **5라운드** Codex 재검수 | ✅ 실시 — REVISE (BLOCKER 2 · MAJOR 102 · MINOR 8) |
| **6라운드** BLOCKER 2건 | ✅ 반영 — 아래 "되풀이된 함정" 참조 |
| **6라운드** MAJOR 102 | 🔴 **미반영 — 다음 세션 최우선(얇은 카드 채우기)** |

### 질환 분리 내역 (되돌리지 말 것 — 임상 안전 근거 있음)
- 설사: `invasive_bacterial_enterocolitis`(침습성) / `shigellosis_dysentery`(Shigella 이질) /
  **`stec_infection`(STEC·O157:H7)** — 🚨 STEC를 Shigella와 묶으면 **항생제 원칙이 정면 충돌**한다
  (Shigella 이질은 경우에 따라 항균치료 대상, STEC는 **항생제 금기** — HUS 위험). Codex 4라운드 BLOCKER.
- 설사: `preformed_toxin_food_poisoning`(1~6h·구토 우세) / `in_vivo_toxin_food_poisoning`(6~24h·C. perfringens)
- 설사(5라운드): `campylobacter_enteritis` / `nontyphoidal_salmonella`(**건강 성인엔 항생제 금지**) /
  `yersinia_enterocolitis`(가성충수염) · `ulcerative_colitis`(직장출혈·뒤무직) / `crohn_disease`(**항문주위 병변 1/3**) ·
  `microscopic_colitis`
- 변비(5라운드): `hypercalcemia_constipation` / `electrolyte_disturbance`
  — 🐛 이때 새 질환 id `hypercalcemia`가 **증상 라벨** `hypercalcemia`와 충돌해 그래프에서 한 노드로
  합쳐질 뻔했다. 검증 스크립트에 **질환 id ↔ 증상 라벨 충돌 검사**를 추가했으니 분리할 때 꼭 돌릴 것.
- 변비: `anal_fissure`(배변 후 **통증성** 출혈) / `internal_hemorrhoid`(**무통성** 선홍색 출혈)
  — 핵심 소견이 서로 모순이라 한 카드로 묶을 수 없다

## 밀도 — 참고표 수준까지 (여전히 최대 격차)

| | 참고표(복통) | 현재 설사 | 현재 변비 |
|---|---|---|---|
| 질환당 발현소견 | **18** | 3.4 | 3.1 |
| 질환당 배경조건 | **10** | 1.1 | 0.4 |

Rosen·Tintinalli는 이번에 처음 채굴을 시작했다(그전엔 0건). 응급 관련 서술(탈수 중증도·수액 지표·
입원/귀가 기준·병원체별 잠복기표)은 여전히 수확 여지가 크다.

## 반드시 지킬 것 (실제로 걸린 것들)

- **인용 대조 100%가 "맞다"는 뜻이 아니다.** 대조는 *문장이 교재에 실재하는가*만 본다.
  *그 인용이 이 소견의·이 role의 근거가 맞는가*는 못 본다. 3라운드 BLOCKER 2건이 그 틈으로 들어왔다.
  이번 라운드에도 같은 유형을 **자체 발견**했다 — 약물유발 변비의 required 배경조건에 병력청취 문장이
  인용으로 붙어 있었다(대조는 통과). **대조 통과 = 채택 가능이 아니다.** 검토표 HTML 상단에 못 박아 뒀다.
- **안전 수정도 과교정되면 반대 방향의 위해가 된다.** 6라운드에서 "혈변만으로 항생제"(3라운드 BLOCKER)를
  고치려고 "**항생제 전 STEC 배제**"를 전면 규칙으로 세웠더니, 6차 검수에서 **발열성 이질·영아·면역저하
  중증의 치료를 지연시킨다**는 새 BLOCKER가 됐다. **금지 규칙에는 반드시 예외를 함께 적는다.**
- **원문의 단서 조항을 자르지 않는다.** "PTH 상승 = 거의 항상 원발성"은 Harrison 원문 그대로였지만
  원문은 **바로 다음 문장에서 FHH 배제를 요구**한다. 그 한 문장을 빼고 옮긴 것이 BLOCKER가 됐다.
  **인용 대조로는 절대 잡히지 않는 유형**이며, 이 프로젝트에서 같은 계열의 네 번째 사례다.
- **분리가 새 위험을 만든다 — 두 번 겪었다.** ① 3라운드 BLOCKER를 고치려 만든 이질 카드가
  4라운드의 새 BLOCKER가 됐다. ② 5라운드에서 침습성 세균성 장염을 3개로 쪼개며 Harrison의
  "혈변이면 경험적 항생제" 항목을 **세 카드에 그대로 복제**해 3라운드 BLOCKER가 **되살아났다.**
  카드를 쪼갤 때는 **쪼갠 결과가 서로 충돌하지 않는지**, 그리고 **복제된 항목이 원래 맥락을
  잃지 않는지** 본다.
- **안전 규칙은 `주의` 필드가 아니라 항목 이름에 넣는다.** 위 ②를 놓친 이유가 이것이다 —
  STEC 경고를 부가 주석에만 달아 뒀더니 구조만 보면 "혈변이면 항생제"로 읽혔다.
  6라운드에서 공통 안전규칙을 해당 카드 **맨 앞 1급 항목**으로 올렸다.
- **교재 원문·실사례를 외부 SaaS(Codex 등)에 보내지 않는다.** Codex 검수는 **인용문을 제거한 뷰**로 넘긴다.
  4라운드에서는 한 걸음 더 나가 **내가 붙인 '주의' 문구까지 제거**했다 — 무엇을 이미 고쳤는지 알려주면
  검수가 편향된다(그래서 3라운드 BLOCKER 재지적 여부가 진짜 검증이 됐다).
- **검토표 산출물은 커밋 금지** (`data/working/`, gitignored). 도구 코드·yaml·검수기록만 커밋
- **Codex 401 `revoked`면 재로그인하지 말 것** — CODEX_HOME 불일치다. 메모리 `codex-home-mismatch-401` 참조.
  실행은 **repo 루트에서** (`/tmp`에서 돌리면 "Not inside a trusted directory"로 죽는다).
- 전체 `review_status: draft` — 교수 검증 전. 의학적 정확성 주장 금지

## 온톨로지 쪽 미완 (검토표와 별개)

- Harrison **판(edition) 미확정** — 원본 PDF 대조 전까지 대외 인용 금지.
  (Rosen 8th·Tintinalli 8th·Sabiston 19th는 판이 원문에 명시돼 있어 이 문제가 없다)
- 공식 감별목록(기본진료수행지침 OCR) 미확보 → 질환 카드는 "임시 teaching set"
- 1차 검수 MAJOR 잔여분 + 2라운드 수정본 재검수 미실시(`verification-log.yaml` 기록)
