# data/ 구조 (docs/data-governance.md 참조)
- `raw_private/` 🔒 실제 부산대 사례 원본 (gitignore·수정금지·SaaS금지)
- `working/` 🔒 비식별 작업본 (gitignore)
  - `train_prompt/` 프롬프트·few-shot·lexicon  · `dev_tune/` 개발·디버깅  · `locked_eval/` 🔒최종평가 전용(잠금)
- `cases/` 공개가능 가상 gold (커밋 OK) · `transcripts/` 데모 대화 · `toy/` 공개 재현용 데이터셋 · `fixtures.json` 하네스 라벨
