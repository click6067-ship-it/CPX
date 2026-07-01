# CLAUDE.md — CPX-AI 프로젝트

> 이 레포 작업 컨텍스트. **에이전트 공통 맥락·본질은 `AGENTS.md` 필독**(영구 정본). 상세 = `docs/`.

## 본질 (한 줄)
양산부산대병원·임선주 PI와 하는 **학술 연구 프로젝트**(영리 아님). 목적=**논문·검증·투명성**(오픈소스, 부산대 무료). 비즈니스 관점 비평은 부적합 → `AGENTS.md`.

## 🔑 현재 최우선 (2026-07-01)
**온톨로지 지식그래프로 근거 기반 생성** (박정빈 교수 비전). Neo4j로 구조화된 지식 내 LLM 사례 생성. 4-에이전트의 추가 레이어(①제약+validator). 정본 = `docs/ontology-plan.md`(교수 원문) · 진입점 = `docs/blueprint.md`. 미팅 7/2. **자세 = 교수 안 충실 실행(반박 아님) + 결과 측정.** 교수 숙제 7항목(엔티티·keyword 온톨로지·원인-증상-질환·markdown 사례변환·로컬35B/256k/TurboQuant·LLM wiki·Skill.MD) = 정본표 `ontology-plan §0`.

## 일하는 법
- Phase 0(정의)→research→plan→구현→테스트→**Codex 적대검수**. 검수는 *학술 엄밀성·검증·재현성·안전성·과대주장 방지* 축.
- **김용하 발언 = Claude+Codex 공동.** 결정은 `AGENTS.md`/`worklog.md`에 즉시 반영(Codex 동기화).
- 모든 작업 `worklog.md` 기록. 만든 건 김용하가 원리 이해 + 교수 설명 가능하게.
- 코드 `src/cpx/`, venv, 키 `.env`. 실행 `PYTHONPATH=src .venv/bin/python ...`.
- 실제 사례·전문가 라벨 전 = 손-라벨 **smoke**. 타당성 주장은 그 후.

## 문서
**`blueprint`(단일 진입점)** · **`ontology-plan`(온톨로지 정본·박정빈 원문)** · `transparency`(모델·데이터 정본) · `context-map`(결정·팀·방향) · `architecture`(v3) · `data-inventory`(데이터 지도) · `research-llm-cpx-sota` · `worklog` · `roadmap`(완성체크) · `competitor-meditutor`(참고만)
