# 교수 파일럿 핸드오프 (H2 검증 설문)

> 상태: **배포 완료·검증 끝·수집함 클린 → 교수님께 전달 가능.** (2026-06-19)
> ⚠️ 이 문서는 **H2 검증 파일럿 전용** 운영 핸드오프. 프로젝트 전체 진입점 = `docs/blueprint.md`, 최우선 설계(온톨로지) = `docs/ontology-plan.md`.
> 모델/데이터/작동방식 = `docs/transparency.md` · 설계근거 = `docs/validation-design.md`

## 무엇
AI ②검토(gpt-5.5)가 교수 피드백에 얼마나 부합하는지 검증하는 **feasibility 파일럿**. 6사례, 사례별 [초안 전문 + 블라인드 비교(교수 vs AI 루브릭) + per-point recall + AI지적 precision]. 좌우 비교 레이아웃·목차·근거 하이라이트.

## 접속 (암호는 git에 안 적음 — 별도 전달)
- URL: **https://cpx-adj-web.vercel.app**
- **판정자 암호** → 교수님께 공유 (설문 응시용)
- **관리자 암호** → 비공개(결과 취합용, 교수님께 주지 말 것)
- 모드: **`?mode=hybrid` 권장** — 교수가 *사례별로* **블라인드 평가** 또는 **열람만** 선택(부담↓·블라인드 무결성 유지·원하는 사례만). `?mode=browse`(평가 없이 자유열람+메모)·기본 full(전체 강제)·`?mode=blind`(1단계만)·`?mode=recall`(2·3단계).

## 교수 초대 메시지 (복붙용)
> [CPX 사례 검토 AI 연구 — 전문가 평가 요청]
> 안녕하세요, 교수님. 부산대 의대 CPX 사례를 AI로 생성·검토하는 연구(연구책임자 임선주 교수)에서, **AI 검토가 교수님 피드백에 얼마나 부합하는지** 전문가 평가를 부탁드립니다.
> · 링크: https://cpx-adj-web.vercel.app/?mode=hybrid  · 접속 암호: (별도 안내)
> · 약 6사례 · 30~45분 · 모바일 가능 · 중간 저장됨 · **익명·자발적**
> 들어가시면 안내가 나옵니다. 솔직한 전문 판단이 가장 큰 도움이 됩니다. 감사합니다.

## 결과 받기 → 집계
응답이 쌓이면(관리자 암호로 확인):
```
PYTHONPATH=src .venv/bin/python scripts/aggregate_validation.py \
  --items data/working/validation_build/cases_meta.json --url https://cpx-adj-web.vercel.app --pw <관리자암호> --mode full
```
산출: 블라인드 루브릭(AI vs 교수 차이+case-cluster CI)·ICC·블라인드 성공률·per-point recall+Fleiss·precision+harmful 게이트.
> ⚠️ **hybrid 집계**: hybrid 응답은 `mode='hybrid'`로 저장되고 `pick='eval'`=블라인드 평가분(1단계 루브릭)/`pick='browse'`=메모(정성). 현재 aggregate는 full/blind/recall만 인식 → **데이터 수집 후 hybrid 핸들링(pick='eval'을 blind로 처리) 추가 필요.** recall/precision은 full 응답에서만 나옴.

## 주의
- 사례·피드백 = **학교자산** → 외부 공유·캡처 자제 안내(설문 안내에 포함).
- 결과 보고 시 **과대주장 금지** — feasibility 파일럿(사례 작음). "AI가 전문가에 필적/대체" 단정 ❌.
- 조호영 등 **테스트 제출분은 이름으로 제외**하거나, 본격 시작 전 수집함 비우기.
- Claude 결제 풀리면 ②를 Claude로 1줄 교체 가능(현재 gpt-5.5가 최종).
