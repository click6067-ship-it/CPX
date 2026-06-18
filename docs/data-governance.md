# 데이터 거버넌스 & 누수 방화벽 (Data Governance)

> Codex 학술검수(2026-06-18) 반영. **실제 부산대 사례 도착 전 필독.** 데이터 누수 = 연구 무효화 1순위 위험.

## 1. 폴더 규칙
- `data/raw_private/<날짜>_pusan/` — **원본 그대로. 절대 수정·커밋·SaaS업로드·LLM채팅 붙여넣기 금지.** (gitignore)
- `data/working/` — 비식별 작업본. (gitignore)
  - `train_prompt/` — 프롬프트 예시·few-shot·lexicon 튜닝용
  - `dev_tune/` — 개발·디버깅·중간 평가용
  - `locked_eval/` — **🔒 잠금. 최종 H4 평가 전용. 프롬프트·데모·lexicon·RAG·수동디버깅에 절대 안 들어감.**
- `data/cases/`, `data/toy/` — 공개 가능(가상·비식별)만. 커밋 OK.

## 2. 누수 방화벽 (Leakage Firewall) — 가장 중요
- 같은 사례를 *생성 예시 + 튜닝 + VP조정 + 최종평가*에 동시 사용 → **결과 조용히 무효.**
- 규칙: 사례 도착 즉시 **train_prompt / dev_tune / locked_eval 분할**(깊이 보기 *전에* 분할 규칙부터). `locked_eval`은 평가 당일까지 안 엶.
- **생성 사례 vs 실제 사례 = provenance 태그로 분리. 절대 섞지 않음.**

## 3. 도착 시 절차 (오늘 밤)
1. 원본 → `data/raw_private/2026-06-18_pusan/` (gitignored). **수정 금지.**
2. `PYTHONPATH=src .venv/bin/python scripts/quarantine.py data/raw_private/2026-06-18_pusan` → 해시 + 인벤토리.
3. 비식별 작업본 생성(원본 불변). 식별정보(환자·학생·기관·개발자명) 제거.
4. 분할 규칙 확정 → train_prompt / dev_tune / locked_eval.
5. `data/DATASET_VERSION.md` 작성(출처·허용범위·제외규칙·분할규칙·비식별 상태·접촉자).
6. **그 다음에** ingestion 변환기(비식별 작업본 → `CpxCase` JSON).
- ⛔ 피하기: SaaS 업로드 · LLM 채팅에 원본 붙여넣기 · 커밋 · locked_eval을 예시로 · 전체 사례로 프롬프트 튜닝 · 생성/실제 혼합 · **smoke 점수를 검증으로 보고.**

## 4. 안전 경계 (교육용 — 임상 아님)
- 이 시스템 = **CPX 교육 전용.** 실제 의료조언·응급상담·사례 밖 진단/치료 권고·실제 환자 사용 = **차단·로그.** 산출물·UI에 "교육 전용, 임상 사용 금지" 명시.

## 5. 검증 프로토콜 스켈레톤 (H4-real 전, 교수팀과 확정)
- 표본 N(항목·사례별) · inclusion/exclusion · **primary endpoint**(예: AI-합의 weighted kappa by domain) · secondary(F1/P/R + bootstrap CI) · **인간-인간 floor 먼저** · adjudication(불일치 합의) · **오류 taxonomy**(원인별 FP/FN: 동의어누락·과매칭·복합항목·전사모호·PPI모호·VP누출) · **claim 언어**(과대주장 금지: "AI=인간 동등" ❌ → "전문가 검토 후 사용가능").
- **검증 registry**(`docs/validation-registry.md`, 추후): 모든 미래 논문 주장 → 데이터버전·commit·프롬프트버전·모델버전·eval스크립트·결과 매핑.

## 6. 재현성 패키지 (오픈소스 — 사례 비공개 유지하며)
- 공개: **toy CPX 데이터셋**(가상 3~5건+transcript+라벨) · 프롬프트 manifest · 모델/provider/버전 로그 · 의존성 lock · eval 스크립트 · 실행법 · 기대출력 · data card · 한계.
- 비공개: 부산대 원본·비식별 작업본·locked_eval. (CONSORT-AI: 개입·입출력·인간-AI 상호작용·오류사례 보고)
