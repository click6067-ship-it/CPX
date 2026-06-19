# CPX H2 검증 설문 웹앱 (배포형, v3)

교수(판정자)가 **주소+암호만** 받아 사례별로 검증 → **중앙 자동수집**. 설계 근거: `docs/validation-design.md`(Codex 1·2라운드 반영).

- **Live:** https://cpx-adj-web.vercel.app  (암호 게이트 + noindex, CPX repo와 분리 배포=사례데이터 안 올라감)
- **스택:** Vercel 정적 + 서버리스(`/api/*`) + Blob 수집. ② 모델 = gemini-2.5-flash(모델-agnostic, 교체 가능).

## 사례별 흐름 (전부 화면에 표시, 생략 없음)
1. **사례 초안 전문**
2. **1단계 블라인드** — 두 검토 의견(전문가 vs AI, 같은 형식·무작위·익명)을 완전성/정확성/유용성/안전성 1~5로 평가 + "어느 쪽이 AI 같나"(블라인드 점검) + 읽음 확인. *(주분석)*
3. **2단계** — 공개 후, 교수 피드백 전문 + AI 리뷰 전체 보며 각 지적 caught/partial/missed/excluded.
4. **3단계** — AI 지적 각각 타당/중복/틀림/유해.

**모드 분리(코호트):** `?mode=blind`(1단계만) · `?mode=recall`(2·3단계) · 기본 `full`.

## 파일
| 파일 | 역할 |
|---|---|
| `index.html` | v3 UI(블라인드+공개+precision, BARS 앵커, 모드분리, 라디오, 재개) |
| `api/items.js` | 암호 맞으면 `cases` 전체 반환(게이트) |
| `api/submit.js` | 제출 전부 저장(pw 제외) → Blob |
| `api/results.js` | **ADMIN_PW**(판정자 암호와 분리) → 전 제출 취합 |
| `lib/data.js` | **토이(가상)**. 실데이터는 `build_validation_data.py`→ /tmp만 |

## 실데이터 전환 / 집계
```
PYTHONPATH=src .venv/bin/python scripts/build_validation_data.py --n=6 --model=gemini-2.5-flash
cp data/working/validation_build/data.js /tmp/cpx-adj-web/lib/data.js
(cd /tmp/cpx-adj-web && vercel env add SURVEY_PW production; vercel env add ADMIN_PW production; vercel --prod --yes)
# 집계: scripts/aggregate_validation.py --items data/working/validation_build/cases_meta.json --url <U> --pw <ADMIN_PW>
```
산출: blind 루브릭(AI vs 전문가·CI)+ICC+블라인드성공 / per-point recall+Fleiss+카테고리 / precision+harmful 게이트.

⚠️ 학교자산: 실데이터 git 커밋 금지. 현 단계 = feasibility/pilot(과대주장 금지).
