# DATASET_VERSION (템플릿 — 실제 사례 도착 시 채움)

> 실제 부산대 사례를 받으면 격리(`scripts/quarantine.py`) 후 이 파일을 채운다. (docs/data-governance.md §3·§5)

## 실제 사례 (raw_private)
- 버전:
- 출처: (예: 부산대 의학교육실 / 연구책임자, 2026-__-__ 수령)
- 허용 범위: (내부 연구용 / 공개 불가 / 비식별 후 일부 공개?)
- 비식별 상태: (환자·학생·기관·개발자명 제거 여부)
- 제외 규칙: (불완전·중복·민감 등)
- 분할 규칙: train_prompt / dev_tune / locked_eval (비율·시드·분할일)
- 🔒 locked_eval 개봉 예정일:
- 접촉자/일시: (누가 언제 만졌나 — 감사 추적)
- 해시: `data/raw_private/<날짜>_pusan/inventory.json` 참조

## 공개 toy 데이터 (data/toy/)
- 성격: **가상·비식별** (재현용). 외부인이 실제 사례 없이 repo 실행 가능.
- 사례: diarrhea_kim · headache_park · chestpain_lee (전부 fictional)
