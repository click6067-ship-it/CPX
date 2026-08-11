# 다음 세션 인계 — 설사·변비 발현소견 검토표 (2026-08-11 작성)

> 이 파일부터 읽고 시작한다. 이전 세션 전문은 `~/main/logs/`, 요약은 `docs/worklog.md` 맨 끝.

## 지금 어디까지 됐나

**커밋·푸시 완료 (공개 repo)**
- `ontology/diarrhea.yaml`·`constipation.yaml` — 각 12질환. Harrison Ch.49 + 부산대 실사례 3건 근거
- 근거등급 4번째 `station_differential_listed` (실사례 채점표에 **질환명이 명시**된 것만)
- `docs/verification-log.yaml` — 검수기록 정본. `ontology_report.py`가 리포트 HTML에 렌더
- `scripts/textbook_mine.py`(인용 채굴) · `scripts/findings_review.py`(인용 기계대조+렌더)

**미커밋 (저작권 — 교재 원문 인용 포함, `data/working/`는 gitignored)**
- `data/working/findings/{diarrhea,constipation}_findings.json` + `.html`
- 설사 소견70·조건17 / 변비 소견57·조건6 = **150건, 인용 대조 150/150 통과**

## 🚨 최우선 — 임상 안전 BLOCKER 2건 (Codex luna 검수 지적, 미반영)

전문 = `/tmp/cpx_evidence/codex_review2_임상타당성_luna.md`
(휘발 가능 — 없으면 바탕화면 `CPX_설사변비_온톨로지_260811/Codex검수2_임상타당성_luna.md`)

1. **세균성 장염 — 경험적 항생제** (`diarrhea_findings.json`)
   현재: "중등도 발열성 설사에서 대변 백혈구나 육안적 혈액이 있으면 경험적 항생제 시도 가능"
   문제: **STEC 감염에서 항생제가 HUS 위험을 높인다.** 혈변만으로 항생제를 권할 수 없음
   수정: 중증도·병원체·STEC 가능성을 고려한 제한적 적응증으로. 또는 이 항목 삭제

2. **배변협조장애 — 회장루** (`constipation_findings.json`)
   현재: "바이오피드백·물리치료에도 배변장애가 지속되면 정기 관장이나 회장루를 고려"
   문제: 회장루는 일반적 다음 단계가 아니며 과도·위험한 치료 제시
   수정: 전문 평가·재활·동반 구조병변 평가로

## 그다음 — role 체계 재정비 (MAJOR 94건의 뿌리)

Codex 총평: *"required/discriminator가 증상·역학·검사·치료·감별진단 문장과 혼재되어 role 체계가 무너져 있다."*

작업 방향:
- **소견이 아닌 것을 소견에서 빼기** — 검사 방법·치료 원칙·감별진단 목록·역학 통계가 `findings`에 섞여 있다. 이런 건 별도 축(management/differential)으로 옮기거나 삭제
- **required 남발 줄이기** — "그 질환이면 거의 항상 있는" 것만. 동반증상은 supporting
- **질환군 세분화** — 예: "세균성 장염(침습성·이질)"을 침습성 세균성 장염과 이질로 분리(Codex 지적)
- 수정 후 `findings_review.py` 재실행 → 인용 대조 유지 확인

## 그다음 — 밀도 (참고표 수준까지)

| | 참고표(복통) | 현재 설사 | 현재 변비 |
|---|---|---|---|
| 질환당 발현소견 | **18** | 5.8 | 4.8 |
| 질환당 배경조건 | **10** | 1.4 | 0.5 |
| 질환당 교재 종수 | **4** | 1~3 | 1~2 |

**미채굴 교재**: Rosen 8th · Tintinalli 8th (응급) — 탈수 중증도·수액 지표·귀가 기준 등 CPX에 딱 맞는 서술이 많은데 **한 건도 안 캤다.** 여기가 수확이 가장 클 구간.

```bash
.venv/bin/python scripts/textbook_mine.py "검색어" --book rosen   # 채굴
.venv/bin/python scripts/findings_review.py data/working/findings/diarrhea_findings.json  # 검증+렌더
```
quote만 정확히 넣으면 book·page·검증은 기계가 한다. 검증 실패는 표에 ✗로 남는다.

## 반드시 지킬 것 (오늘 실제로 걸린 것들)

- **인용 대조 100%가 "맞다"는 뜻이 아니다.** 대조는 *문장이 교재에 실재하는가*만 본다. *그 인용이 이 소견·이 role의 근거가 맞는가*는 못 본다. BLOCKER 2건이 정확히 그 틈으로 들어왔다. **인용 대조 통과 = 채택 가능**이 아니다.
- **교재 원문·실사례를 외부 SaaS(Codex 등)에 보내지 않는다.** 저작권·개인정보. Codex 검수는 **인용문을 제거한 뷰**(질환·축·소견명·role만)로 넘긴다 — 3라운드에서 쓴 방법
- **검토표 산출물은 커밋 금지** (`data/working/`, gitignored). 도구 코드만 커밋
- **Codex 401 `revoked`면 재로그인하지 말 것** — CODEX_HOME 불일치다. `echo $CODEX_HOME` + 양쪽 `auth.json` mtime 비교. 메모리 `codex-home-mismatch-401` 참조
- 전체 `review_status: draft` — 교수 검증 전. 의학적 정확성 주장 금지

## 온톨로지 쪽 미완 (검토표와 별개)

- Codex 1차 검수 MAJOR 14건 중 반영분 외 잔여 + **수정본 2차 검수 미실시**(`verification-log.yaml` 2라운드에 NOT_RUN 기록)
- Harrison **판(edition) 미확정** — 원본 PDF 대조 전까지 대외 인용 금지
- 공식 감별목록(기본진료수행지침 OCR) 미확보 → 12질환은 "임시 teaching set"
