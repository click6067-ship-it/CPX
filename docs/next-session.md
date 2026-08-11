# 다음 세션 인계 — 설사·변비 발현소견 검토표 (2026-08-11 4라운드 종료 시점)

> 이 파일부터 읽고 시작한다. 이전 세션 전문은 `~/main/logs/`, 요약은 `docs/worklog.md` 맨 끝,
> 검수 이력 정본은 `docs/verification-log.yaml`(4라운드까지 기록됨).

## 지금 어디까지 됐나

**커밋·푸시 완료 (공개 repo)**
- `ontology/diarrhea.yaml` **15질환** · `ontology/constipation.yaml` **13질환**
  (3라운드까지 각 12질환 → Codex 지적으로 4카드 분리. 아래 "질환 분리" 참조)
- `docs/verification-log.yaml` — 검수기록 정본. `ontology_report.py`가 리포트 HTML에 렌더
- `scripts/textbook_mine.py`(인용 채굴) · `scripts/findings_review.py`(인용 기계대조 + 렌더 + `--snap`)

**미커밋 (저작권 — 교재 원문 인용 포함, `data/working/`는 gitignored)**
- `data/working/findings/{diarrhea,constipation}_findings.json` + `.html`
- 설사 소견56·조건17·참고48 / 변비 소견37·조건6·참고38 = **202건, 인용 대조 202/202 통과**
- 바탕화면 사본 = `CPX_설사변비_온톨로지_260811/9_설사_*_v4.*`, `10_변비_*_v4.*`

## 🚨 최우선 — Codex 4라운드 MAJOR 122건 미반영

원문 = 바탕화면 `CPX_설사변비_온톨로지_260811/Codex검수4_수정본_luna.md`
(입력으로 쓴 브리프도 같은 폴더 `Codex검수4_입력브리프.md` — 재현용)

4라운드 판정 **REVISE — BLOCKER 1 · MAJOR 122 · MINOR 4**.
BLOCKER 1건은 즉시 반영했다(아래). **MAJOR 122·MINOR 4는 손대지 않았다.** 세 덩어리로 나뉜다:

### ① 추가 질환 분리 요구 — **교수 판단 필요, 임의로 하지 말 것**
Codex는 더 쪼개라고 한다: Campylobacter/Salmonella/Yersinia 분기 · Crohn/UC 분리 ·
고칼슘혈증·전해질이상·내분비 변비 분리 · 약물유발 설사를 약물군별로 분리 · V. cholerae·ETEC 등 별도 카드.
전부 따르면 카드가 25개를 넘어 **CPX 10분 station 교육용 범위를 벗어난다.**
공식 감별목록(기본진료수행지침)도 아직 없다. → **분리 여부는 지도교수에게 물어보고 결정한다.**

### ② Rome IV 기준 정밀화 — 원문 확보가 선행
현재 IBS·기능성 변비의 Rome 인용은 **Tintinalli의 축약형**이라
"증상 시작 6개월 전부터" · "6개 항목 중 2개 이상" · IBS-C/M subtype의 변 형태 비율 기준이 빠져 있다.
Rome IV 원문(또는 이를 정확히 옮긴 교재)을 코퍼스에서 찾거나 확보해야 한다.

### ③ 경보징후(red flag) 보강 — **교재 채굴로 바로 채울 수 있다. 여기부터 하면 된다.**
- 기능성 변비: 혈변·체중감소·철결핍빈혈·구토·가스 불통·발열·새로 발생한 변비·가족력
- 신경질환성 변비: **마미증후군/급성 척수압박** — 요폐·안장부 감각저하·급성 하지약화·항문긴장도 저하
- C. difficile: 24시간 내 3회 이상 비형성변, 전격성 징후(저혈압·장폐색·독성거대결장)
- 대장암: 배변습관 변화·변 굵기 변화·복부/직장 종괴·폐색
- 치열: 외측·다발성 치열 = Crohn·감염·종양 등 이차성 원인 시사

```bash
.venv/bin/python scripts/textbook_mine.py "검색어" --book rosen     # 채굴 (rosen·tintinalli·sabiston·PART2·PART10·PART12)
.venv/bin/python scripts/findings_review.py data/working/findings/diarrhea_findings.json   # 검증+렌더
.venv/bin/python scripts/findings_review.py <파일> --snap            # 단어중간 절단 인용 복원(1회성 정비)
```
quote만 정확히 넣으면 book·page·검증은 기계가 한다. 검증 실패는 표에 ✗로 남는다.

## 이번 라운드에 한 것 (4라운드)

| 한 일 | 결과 |
|---|---|
| 3라운드 BLOCKER 2건 | ✅ 해결 — 4라운드에서 **재지적되지 않음** |
| role 재정비 (MAJOR 94) | ✅ 구조로 해결 — `참고항목` 축 신설로 검사·치료·감별·역학을 findings에서 분리 |
| 질환 분리 | ✅ 설사 12→15 · 변비 12→13 (검토표·yaml·cypher·그래프 전부) |
| 🐛 인용 페이지 버그 | ✅ **기존 150건 중 54건(36%)이 틀려 있었다** — 수정·교차검증 143/143 |
| 인용 단어중간 절단 8건 | ✅ `--snap`으로 복원 |
| Rosen·Tintinalli 채굴 | ⚠️ 시작함(0건 → 다수). 밀도는 여전히 부족 |
| Codex 4라운드 검수 | ⚠️ REVISE — BLOCKER 1 즉시반영, MAJOR 122 미반영 |

### 질환 분리 내역 (되돌리지 말 것 — 임상 안전 근거 있음)
- 설사: `invasive_bacterial_enterocolitis`(침습성) / `shigellosis_dysentery`(Shigella 이질) /
  **`stec_infection`(STEC·O157:H7)** — 🚨 STEC를 Shigella와 묶으면 **항생제 원칙이 정면 충돌**한다
  (Shigella 이질은 경우에 따라 항균치료 대상, STEC는 **항생제 금기** — HUS 위험). Codex 4라운드 BLOCKER.
- 설사: `preformed_toxin_food_poisoning`(1~6h·구토 우세) / `in_vivo_toxin_food_poisoning`(6~24h·C. perfringens)
- 변비: `anal_fissure`(배변 후 **통증성** 출혈) / `internal_hemorrhoid`(**무통성** 선홍색 출혈)
  — 핵심 소견이 서로 모순이라 한 카드로 묶을 수 없다

## 밀도 — 참고표 수준까지 (여전히 최대 격차)

| | 참고표(복통) | 현재 설사 | 현재 변비 |
|---|---|---|---|
| 질환당 발현소견 | **18** | 3.7 | 2.8 |
| 질환당 배경조건 | **10** | 1.1 | 0.5 |

Rosen·Tintinalli는 이번에 처음 채굴을 시작했다(그전엔 0건). 응급 관련 서술(탈수 중증도·수액 지표·
입원/귀가 기준·병원체별 잠복기표)은 여전히 수확 여지가 크다.

## 반드시 지킬 것 (실제로 걸린 것들)

- **인용 대조 100%가 "맞다"는 뜻이 아니다.** 대조는 *문장이 교재에 실재하는가*만 본다.
  *그 인용이 이 소견의·이 role의 근거가 맞는가*는 못 본다. 3라운드 BLOCKER 2건이 그 틈으로 들어왔다.
  이번 라운드에도 같은 유형을 **자체 발견**했다 — 약물유발 변비의 required 배경조건에 병력청취 문장이
  인용으로 붙어 있었다(대조는 통과). **대조 통과 = 채택 가능이 아니다.** 검토표 HTML 상단에 못 박아 뒀다.
- **분리가 새 위험을 만들 수 있다.** 3라운드 BLOCKER를 고치려고 이질 카드를 만들었더니
  그 카드가 4라운드의 새 BLOCKER가 됐다. 카드를 쪼갤 때는 **쪼갠 결과가 서로 충돌하지 않는지** 본다.
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
