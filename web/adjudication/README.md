# CPX adjudication 설문 웹앱 (배포형)

교수(판정자)가 **주소만 받아** 한 문항씩 클릭으로 H2 검증 판정 → **중앙 자동수집**. 3명→N명 확장 OK.

- **Live:** https://cpx-adj-web.vercel.app  (암호 게이트 + noindex)
- **스택:** Vercel 정적 페이지 + 서버리스 함수(`/api/*`) + Vercel Blob(수집 저장). 프레임워크 없음.
- **배포 디렉터리:** 이 폴더(또는 `/tmp/cpx-adj-web`). CPX repo 본체와 분리 배포 → **사례 데이터 절대 안 올라감.**

## 구조
| 파일 | 역할 |
|---|---|
| `index.html` | 설문 UI(암호+이름 → 한 문항씩 → 자동제출). AI 잠정판정 미리선택, localStorage 재개, 폰 OK |
| `api/items.js` | 암호 맞으면 문항 반환(게이트). 틀리면 403 → 문항 노출 0 |
| `api/submit.js` | 판정 제출 → Blob 저장(random suffix=URL 추측불가) |
| `api/results.js` | 관리자(같은 암호) → 전 제출 취합 JSON (집계 스크립트 입력) |
| `lib/data.js` | 문항 + 암호. **현재 토이(가상). 실데이터는 PI 동의 후 교체** |

## 🔒 실데이터로 전환 (PI 동의 후)
1. **암호 설정:** `vercel env add SURVEY_PW production` (강한 암호) → 데모배너 사라지고 게이트 활성.
2. **문항 교체:** 실제 adjudication CSV → `lib/data.js` 재생성 (사례데이터라 **git 커밋 금지**, /tmp에서만).
3. **수집 초기화:** `vercel blob empty-store cpx-adj --yes`.
4. **재배포:** `vercel --prod --yes`.

## 집계
`/api/results?pw=<암호>` → JSON → 집계 스크립트가 **Fleiss kappa(일치도) + 다수결 합의 + 카테고리별 recall/F1 + CI** 산출.

⚠️ 토이 데이터 외 실제 사례 피드백은 학교자산 — 게이트 없이 배포 금지, git 커밋 금지.
