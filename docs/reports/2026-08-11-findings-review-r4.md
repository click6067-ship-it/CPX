# CPX 발현소견 검토표 4라운드 — 기술보고서

> 👤 **사람용 문서**입니다(미래의 나 포함). Claude 운영 정본이 아니라 *서사·이력* 기록입니다.
> **의도**: 인용 검증 파이프라인에서 나온 실제 결함 4건의 증상·근본원인·해결을 시각과 함께 남겨,
> 같은 함정을 다시 밟지 않게 한다.
> **언제**: 2026-08-11 (KST) 단일 세션, 17:00경 ~ 18:35경
> **작성**: 2026-08-11 20:30 (KST)
> **대상 레포**: `~/ghq/github.com/click6067-ship-it/CPX` (공개) · 커밋 `04e86f5`

---

## 1. 요약

부산대 CPX AI 프로젝트의 **발현소견 교재근거 검토표**(설사·변비)를 4라운드로 개정하면서,
인용 검증 도구 `scripts/findings_review.py`에서 **조용히 틀리고 있던 결함 1건**과
**내가 새로 만든 결함 2건**을 발견하고 고쳤다.

가장 무거운 것은 **인용 페이지 산출 버그**다. 도구는 "사람이 페이지를 옮겨 적으면 반드시 틀리니
기계가 원문 위치에서 직접 딴다"는 설계 의도로 만들어졌는데, **그 기계가 틀리고 있었다.**
기존 인용 150건 중 **54건(36%)의 페이지가 실제보다 앞으로 밀려 있었다.**
아무도 몰랐던 이유는 명확하다 — 인용 대조는 100% 통과하고 있었기 때문이다.
**대조가 검사하는 것은 "문장이 교재에 있는가"뿐이고, "페이지가 맞는가"는 검사 대상이 아니었다.**

| 항목 | 결과 |
|---|---|
| 인용 페이지 오류 | **150건 중 54건(36%)** → 수정, 교차검증 143/143 일치 |
| `--snap` 과확장 회귀 | 도입 → 8건 개선·다수 악화 확인 → **되돌림** → 조건 축소 후 재적용(8건만 변경) |
| Codex exec 실패 | `/tmp`에서 실행 → "Not inside a trusted directory" → repo 루트에서 재실행 |
| "인용 대조 통과 ≠ 임상 타당" | 3라운드 BLOCKER 2건 + 이번 자체발견 1건으로 **실증** |
| 최종 검증 | 검토표 **202/202 인용 대조 통과**, yaml 라벨 누락 0·미등록 출처 0 |

---

## 2. 시스템 구조 (무엇으로 이루어졌나)

```
ontology/{diarrhea,constipation}.yaml     ← 정본(질환 카드·라벨·근거)
        │  yaml_to_cypher.py / yaml_to_html.py / graph_shot.js / ontology_report.py
        ↓
ontology/*.cypher · docs/*-graph.html · docs/*-graph.png · docs/ontology-*.html   (거울, 한 방향 렌더)

data/working/findings/{diarrhea,constipation}_findings.json   ← 검토표 데이터 (gitignored)
        │  scripts/findings_review.py  ← 인용 기계대조 + book/page 재취득 + HTML 렌더
        ↓
data/working/findings/*.html            (교수 검증용 표, gitignored)

~/ghq/.../cpx-agent/data/raw/textbook/  ← 교재 코퍼스 (비공개·저작권, 레포 밖)
        Harrison PART1~20 · Rosen 8th · Tintinalli 8th · Sabiston 19th · Bates · Robbins …
```

핵심 설계 원칙 두 가지:

1. **인용문을 사람이 옮겨 적지 않는다.** `textbook_mine.py`로 원문에서 잘라내고,
   `findings_review.py`가 코퍼스와 기계 대조한다.
2. **book·page는 사람 입력을 신뢰하지 않는다.** 대조 성공 시 기계가 원문 위치에서 다시 딴다.

이번 보고서의 1번 결함은 **바로 그 2번 원칙을 구현한 코드**에 있었다.

---

## 3. 작동 원리 (어떻게 도나)

`findings_review.py`의 인용 대조는 **squash 키 비교**다.

- PDF 추출물에는 행말 절음(`abdomi- nal`), 행 바꿈 지점의 단어 중간 공백(`com monly`),
  소프트하이픈(U+00AD), 그리고 페이지 마커 `[[p213]]`가 문장 중간에 섞여 있다.
- 그래서 **공백·하이픈·페이지마커를 전부 지운 키**로 비교한다(`squash()`).
  100자 인용에서 우연 일치는 사실상 없다.

페이지 산출(`resolve()`)은 원래 이렇게 동작했다:

1. squash 코퍼스에서 인용의 위치 `i`(squash 좌표)를 찾는다.
2. `i`를 **원문 좌표로 되돌린다** — 원문을 앞에서부터 훑으며 비공백 문자를 세어 `i`번째 지점을 찾는다.
3. 그 지점 앞의 마지막 `[[pN]]` 마커를 페이지로 딴다.

**2번이 틀렸다.** 아래 4.1 참조.

---

## 4. 트러블슈팅 내역 (시간순)

| 시각(KST) | 증상 | 근본 원인 | 해결 |
|---|---|---|---|
| 17:05경 | 같은 인용을 `resolve()`는 Tintinalli **p1122**, `textbook_mine`은 **p1124**로 보고 | squash→원문 좌표 복원 시 `[[pN]]` 마커 글자를 함께 셈 (마커는 squash 코퍼스에 없음) | 마커 경계 기준 **누적 인덱스**로 교체 |
| 17:12경 | `verify()`의 "일치 @파일"과 `resolve()`의 출처가 다른 파일을 가리킴 | 두 함수가 서로 다른 파일 순회 순서를 씀 | 단일 `search_order()`로 통일 |
| 18:02경 | 인용이 단어 중간에서 시작·끝남 (`ience a sudden onset`) | 이전 세션이 원문에서 자를 때 경계를 안 맞춤 | `--snap` 도입 |
| 18:05경 | `--snap`이 **멀쩡한 인용을 악화** (표 인용 앞에 앞 문단이 붙음) | 모든 인용을 문장 경계로 확장 → 표는 문장부호가 없어 앞 본문까지 끌어옴 | **되돌리고** 조건 축소 |
| 18:14경 | `codex exec`가 2줄만 출력하고 종료 | `/tmp/cpx_evidence`에서 실행 → "Not inside a trusted directory" | repo 루트에서 재실행 |
| 18:20경 | Codex 4라운드가 **새 BLOCKER 1건** 보고 | 3라운드 BLOCKER를 고치려 만든 카드가 새 위험을 만듦 | 카드 재분리 |
| 18:26경 | 커밋 대상 yaml에 교재 영문 원문 1문장 유입 | 근거 서술에 인용을 그대로 붙임 | 한국어 요약으로 교체 후 재스캔 |

### 4.1 인용 페이지 산출 버그 (가장 무거움)

**증상.** `scripts/textbook_mine.py`와 `scripts/findings_review.py`가 **같은 인용에 대해 다른 페이지**를 냈다.

```
Tintinalli 8th — "Antibiotics may promote Shiga toxin release, …"
  textbook_mine  → p1124
  findings_review→ p1122
```

**근본 원인.** `resolve()`는 squash 좌표 `i`를 원문 좌표로 되돌리려고
원문을 앞에서부터 훑으며 `[\s-]`가 아닌 문자를 셌다.
그런데 **`squash()`는 `[[pN]]` 마커를 제거**하므로, squash 코퍼스에는 마커 글자가 없다.
반면 원문 훑기는 마커 글자(`[`,`[`,`p`,`1`,`2`,`4`,`]`,`]`)를 **비공백 문자로 세고 있었다.**

→ 마커 1개당 약 7자씩 카운트가 부풀고, 그만큼 **원문 위치가 앞으로 밀린다.**
→ 지나온 마커가 많을수록(= 뒷페이지일수록) 오차가 커진다.

실측:

```
이 지점까지 지나온 페이지 마커 수 = 1124개 → 누적 오차 약 7,868자 ≈ 2페이지
```

**영향 범위 (실측).**

```
인용 150건 중 페이지가 바뀌는 것 54건 (36%)
   차이 +1페이지: 43건
   차이 +3페이지:  3건
   차이 +4페이지:  5건
   차이 +5페이지:  3건
```

**항상 실제보다 앞으로 밀려 있었다**(차이가 전부 양수 = 올바른 페이지가 더 뒤).
책(book) 표기는 영향 없었다(0건 변경) — 파일 선택은 이 계산과 무관하기 때문.

**해결.** 좌표 복원을 버리고, **마커 경계 기준 누적 인덱스**로 바꿨다.

`squash()`는 공백·하이픈·마커를 전부 지우는 문자 단위 변환이므로
`squash(a+b) == squash(a) + squash(b)`가 성립한다.
따라서 마커 사이 구간을 순서대로 squash해 길이를 누적하면,
각 마커가 squash 코퍼스의 어느 좌표에 놓이는지 **오차 없이** 얻는다.

```python
def page_index(rel):
    raw = _raw[rel]; idx, prev, cum = [], 0, 0
    for m in re.finditer(r"\[\[p(\d+)\]\]", raw):
        cum += len(squash(raw[prev:m.start()]))
        idx.append((cum, m.group(1)))
        prev = m.start()
    return idx
```

**검증.** 원문 공간에서 직접 계산하는 **독립 경로**(인용을 마커·공백·하이픈 허용 정규식으로
원문에서 직접 찾아 직전 마커를 딴 값)와 대조:

```
대조 143건 · 불일치 0건 · 매칭실패(스킵) 7건
```

> ⚠️ 첫 교차검증 시도는 **검증 스크립트 쪽이 틀려** 150건 중 68건 불일치로 나왔다.
> 원인은 검증 스크립트가 `resolve()`와 다른 파일 선택 순서를 써서
> **페이지 마커가 없는 통본**(`InternalMed_Harrison.txt`)을 보고 있었던 것.
> 검증 코드도 검증 대상만큼 틀릴 수 있다.

**배운 점.** 인용 대조가 100%였기 때문에 아무도 이 버그를 의심하지 않았다.
**대조가 보증하는 범위를 정확히 알아야 한다** — 대조는 *문장의 실재*만 보증하고,
*페이지의 정확성*은 보증하지 않았다. 검증 지표는 "무엇을 보증하지 않는가"까지 같이 적어야 한다.

### 4.2 `--snap` 과확장 — 고치려다 더 나빠진 사례

**증상.** 인용 87건이 머리 또는 꼬리가 문장부호 없이 끝났고, 그중 일부는
**단어 중간에서 잘려** 있었다: `ience a sudden onset`(=experience),
`ld be formally evaluated`(=should), `s cause painless, bright red bleeding`(=Internal hemorrhoids cause…).
기계 대조는 통과하지만 교수가 읽을 표에서 깨져 보이고, 그대로 재인용할 수도 없다.

**1차 시도(실패).** 모든 인용을 문장 경계까지 확장 → **159건 변경**.
소문자 시작/끝은 85건 → 19건으로 줄었으나, **표(table)에서 딴 인용이 앞 본문을 끌어왔다:**

```
전: Ranges from watery stools without constitutional symptoms to …
후: 30 The World Health Organization rec- ommends an … 1 causes more severe symptoms
```

표는 문장부호가 없으므로 "직전 문장 끝"을 찾으면 **엉뚱한 앞 문단**이 잡힌다.
→ **되돌렸다**(`cp` 백업에서 복원).

**2차 시도(성공).** 판단 기준을 바꿨다 — "문장부호가 없나"가 아니라
**"원문에서 앞/뒤 글자가 실제로 이어지나"**(= 진짜 절단인가):

```python
cut_head = s > 0 and raw[s-1].isalnum()
cut_tail = e < len(raw) and raw[e].isalnum()
if not (cut_head or cut_tail): return quote   # 멀쩡한 인용은 건드리지 않는다
```

**3차 보정.** 그래도 2건이 앞 문단을 끌어왔다(`EPIDEMIOLOGY ■ TRAVEL HISTORY Of the several million…`).
머리쪽 확장에 **90자 상한**(`HEAD_CAP`)을 두고, 넘으면 단어 경계까지만 되살리게 했다.

**최종 결과: 8건만 변경.** 전부 명백한 개선.

```
ience a sudden onset…            → experience a sudden onset…
ld be formally evaluated…        → should be formally evaluated…
s cause painless, bright red…    → Internal hemorrhoids cause painless, bright red…
```

**배운 점.** *결함을 고치는 변환은 결함이 있는 대상에만 적용해야 한다.*
"전체에 일괄 적용"은 고칠 것보다 망칠 것이 많을 수 있다.
그리고 **되돌릴 수 있게 백업을 먼저 떠 둔 것**이 이 회귀를 싸게 만들었다.

### 4.3 `codex exec` — "Not inside a trusted directory"

**증상.** 백그라운드 실행이 exit 0인데 출력이 2줄뿐.

```
Reading additional input from stdin...
Not inside a trusted directory and --skip-git-repo-check was not specified.
```

**원인.** `cd /tmp/cpx_evidence`에서 실행했다. Codex CLI는 신뢰 디렉터리(git repo) 밖에서 거부한다.
`< /dev/null`(stdin 닫기)은 규칙대로 지켰고, 그건 원인이 아니었다.

**해결.** repo 루트에서 실행. `CODEX_HOME`은 이미 `$ORCA_CODEX_HOME`으로 맞춰져 있어 401은 없었다.

**배운 점.** 기존 함정 목록(`stdin 닫기`, `CODEX_HOME 일치`)에 **"repo 루트에서 실행"**을 더한다.
프롬프트를 인자로 넘겨도 `Reading additional input from stdin...`은 정상 출력이니 그것만 보고 원인을 오판하지 말 것.

### 4.4 "인용 대조 통과 ≠ 임상적으로 맞다"의 실증

이 프로젝트에서 가장 값비싼 교훈이라 별도로 남긴다.

- **3라운드(2026-08-11 16:50경)**: 인용 대조 **150/150 통과** 상태에서
  Codex 임상타당성 검수가 **BLOCKER 2건**을 잡았다.
  ① 혈변만으로 경험적 항생제(STEC에서 HUS 위험) ② 배변협조장애에서 회장루 제시.
  둘 다 **교재에 실재하는 문장**이었다. 문제는 *그 문장을 어떤 소견·어떤 role에 붙였는가*였다.
- **4라운드(이번, 18:10경)**: 같은 유형을 **자체 발견**했다.
  약물유발 변비의 `required` 배경조건 "변비를 유발하는 약물의 복용력"에
  **병력청취 문장**(*"A good diet and medication history … are key."*)이 인용으로 붙어 있었다.
  기계 대조는 통과한다. 인용이 주장의 근거가 아닐 뿐이다.
- 회장루 항목에서는 **인용이 잘려 주장을 뒷받침하지 못하는** 변종도 나왔다 —
  한국어 소견명은 "정기 관장이나 **회장루**"인데 인용은 `…may require regular enemas`에서 끝나 있었다.
  원문 전체 문장에는 회장루가 실제로 있었으므로 **인용을 늘려** 해결했다.

**조치.** 검토표 HTML 상단 경고를 사실 기반으로 다시 썼다 —
"인용 대조 100%는 임상적으로 맞다는 뜻이 **아닙니다**. 실제로 2026-08-11 검수에서
대조 100% 상태로 환자 안전 BLOCKER 2건이 이 틈으로 통과했습니다."

### 4.5 분리가 새 위험을 만든 사례

3라운드 BLOCKER를 고치려고 `세균성 이질(Shigella·장출혈성 대장균)` 카드를 만들었다.
**그 카드가 4라운드의 새 BLOCKER가 됐다.**

> Shigella와 STEC를 하나의 질환으로 묶으면 혈변 양상, 발열, HUS 위험, **항생제 원칙이 서로 충돌**함
> — Codex 4라운드

실제로 Shigella 이질은 경우에 따라 항균치료 대상이지만 **STEC는 항생제 금기**(Shiga 독소 방출 촉진 → HUS).
한 카드에 두면 학생이 어느 쪽으로도 틀릴 수 있다. → 즉시 `stec_infection` 카드로 분리(설사 14→15).

**배운 점.** 카드를 쪼갤 때는 **쪼갠 결과가 서로 충돌하지 않는지**까지 봐야 한다.
안전 수정이 다음 라운드의 안전 결함을 만들 수 있다.

---

## 5. 변경로그 (git 시각 그대로, 최신 → 과거)

| 커밋 시각 (KST) | 해시 | 제목 |
|---|---|---|
| 2026-08-11 18:30:27 | `04e86f5` | fix(ontology): 임상안전 BLOCKER 3건 해소 + role 축 분리 + 인용 페이지 버그(36% 오류) 수정 |
| 2026-08-11 16:52:16 | `054c2b4` | docs: 다음 세션 인계 + 임상 타당성 검수 3라운드 기록 |
| 2026-08-11 16:24:35 | `f4dd4cc` | feat(scripts): 교재 인용 채굴기 + 발현소견 검토표 렌더러(인용 기계대조) |
| 2026-08-11 15:43:03 | `742e7ec` | feat(ontology): 설사·변비 온톨로지 신규 + Harrison 근거화 + 검수기록 내장 |
| 2026-07-01 17:28:32 | `4b296fd` | docs: README 온톨로지 차별점 현행화 |
| 2026-07-01 17:25:20 | `515a153` | docs: 엔티티 설계 확정 (Claude+Codex 블라인드) + 세션 worklog |

`04e86f5` 변경 규모: 14파일, +653 / −159.
검토표 산출물(`data/working/findings/*`)은 **저작권상 커밋하지 않았다**(gitignored).

---

## 6. 발전과정 (마일스톤 타임라인)

| 시각 (KST, 2026-08-11) | 마일스톤 |
|---|---|
| 15:43 | 설사·변비 온톨로지 신규(각 12질환) + Harrison 근거화 + 검수기록 내장 |
| 16:24 | 인용 채굴기 + 검토표 렌더러(인용 기계대조) 도입 |
| 16:50 | Codex 3라운드 임상타당성 검수 → **REVISE (BLOCKER 2 · MAJOR 94 · MINOR 9)** |
| 16:52 | 3라운드 결과 기록 + 다음 세션 인계 문서 작성 |
| ~17:05 | **인용 페이지 버그 발견** (같은 인용, 두 도구가 다른 페이지) |
| ~17:10 | 마커 경계 누적 인덱스로 수정 → 교차검증 143/143 |
| ~17:30 | `참고항목` 축 신설 (검사·치료·감별·역학을 findings에서 분리) |
| 17:58 | 1차 변환 실행 — 설사 12→14, 변비 12→13 |
| 18:02 | 2차 보정 — required 없음 사유 명시, 인용-주장 불일치 1건 자체 수정 |
| ~18:05 | `--snap` 1차(과확장) → 되돌림 → 조건 축소 후 재적용 (8건) |
| 18:13 | Codex 4라운드 브리프 생성 (인용문 + **내 '주의' 문구까지 제거**) |
| 18:14 | Codex 실행 실패(디렉터리 신뢰) → repo 루트에서 재실행 |
| 18:20 | 4라운드 결과 — **REVISE (BLOCKER 1 · MAJOR 122 · MINOR 4)**. 3라운드 BLOCKER 2건은 **재지적 없음** |
| 18:23 | 신규 BLOCKER 반영 — STEC 카드 분리 (설사 14→15) |
| 18:26 | 커밋 전 저작권 스캔 → yaml의 교재 영문 1문장을 한국어 요약으로 교체 |
| 18:30 | 커밋 `04e86f5` |
| ~18:35 | `origin/main` 푸시 (`054c2b4..04e86f5`) |

---

## 7. 발견된 이슈 / 개선점

| severity | 이슈 | 상태 |
|---|---|---|
| **HIGH** | 인용 페이지 36% 오류 (마커 글자 누적) | ✅ 수정 + 교차검증 143/143 |
| **HIGH** | 안전 수정(카드 분리)이 새 안전 결함을 생성 | ✅ 재분리로 해소. 함정으로 문서화 |
| **MED** | `verify()`/`resolve()` 파일 선택 순서 불일치 | ✅ `search_order()`로 통일 |
| **MED** | 인용이 단어 중간에서 절단 (8건) | ✅ `--snap`(조건부)으로 복원 |
| **MED** | 검증 스크립트 자체가 틀려 오탐 68건 | ✅ 파일 선택 순서 맞춰 재작성 |
| **LOW** | `codex exec` 디렉터리 신뢰 요구 | ✅ repo 루트 실행. 함정 목록 추가 |
| **LOW** | 커밋 대상 yaml에 교재 원문 유입 | ✅ 한국어 요약 교체 + 자동 스캔 |
| 🔴 **OPEN** | Codex 4라운드 **MAJOR 122 · MINOR 4 미반영** | `docs/next-session.md`에 3덩어리로 분류 인계 |
| 🔴 **OPEN** | 밀도 부족 — 질환당 발현소견 설사 3.7·변비 2.8 (참고표 18) | 다음 라운드 |
| 🔴 **OPEN** | Harrison **판(edition) 미확정** | 원본 PDF 대조 전까지 대외 인용 금지 |
| 🔴 **OPEN** | 공식 감별목록(기본진료수행지침) 미확보 | 질환 카드는 "임시 teaching set" |

**도구에 남은 개선 여지**
- 인용 대조는 *페이지 정확성*을 검사하지 않는다 → `resolve()`와 원문공간 독립계산을
  **상시 교차검증**하는 회귀 테스트를 넣으면 이번 같은 조용한 버그를 자동으로 잡는다.
- `_quote_note`가 "일치 @파일"만 알려주고 **페이지 신뢰도**는 말하지 않는다.
  마커 없는 통본에서만 매칭된 인용(`page=""`)은 표에서 시각적으로 구분하면 좋다.

---

## 8. 부록

### 8.1 검증 로그 (실측 출력)

```
$ .venv/bin/python scripts/findings_review.py data/working/findings/diarrhea_findings.json
질환 15개 · 소견 56/56 · 조건 17/17 · 참고항목 48/48 인용대조 통과

$ .venv/bin/python scripts/findings_review.py data/working/findings/constipation_findings.json
질환 13개 · 소견 37/37 · 조건 6/6 · 참고항목 38/38 인용대조 통과

ontology/diarrhea.yaml: 질환 15개 · 라벨 118 · 출처 4    (라벨 누락 0 · 미등록 출처 0 · 중복 0)
ontology/constipation.yaml: 질환 13개 · 라벨 123 · 출처 6

그래프: 설사 109노드·240엣지 / 변비 115노드·228엣지 — HTML·PNG 재생성 및 육안 확인
```

### 8.2 관련 파일

| 파일 | 역할 |
|---|---|
| `scripts/findings_review.py` | 인용 기계대조 · book/page 재취득 · `--snap` · HTML 렌더 |
| `scripts/textbook_mine.py` | 교재 원문에서 인용 후보 채굴 |
| `docs/verification-log.yaml` | 검수기록 **정본**(1~4라운드, status = PASS/FAIL/PARTIAL/NOT_RUN) |
| `docs/next-session.md` | 다음 세션 인계 (미반영 MAJOR 122건 분류 포함) |
| `ontology/{diarrhea,constipation}.yaml` | 질환 카드 정본 |
| 바탕화면 `CPX_설사변비_온톨로지_260811/` | Codex 검수 원문·입력 브리프·검토표 사본 (비공개 정본) |

### 8.3 Codex 검수 이력 요약

| 라운드 | 시각 | 판정 | 내용 |
|---|---|---|---|
| 1~2 | 2026-08-11 15:2x~15:43 | REVISE | BLOCKER 4 · MAJOR 14 · MINOR 4 (구조·근거등급) |
| 3 | 2026-08-11 ~16:50 | **REVISE** | BLOCKER 2 · MAJOR 94 · MINOR 9 (임상타당성) |
| 4 | 2026-08-11 ~18:20 | **REVISE** | BLOCKER 1 · MAJOR 122 · MINOR 4. **3라운드 BLOCKER는 재지적 없음** |

4라운드 브리프는 편향을 막기 위해 **교재 인용문 + 내가 붙인 '주의' 문구를 모두 제거**하고
구조만 넘겼다(무엇을 이미 고쳤는지 알려주지 않음).
그래서 "3라운드 BLOCKER 재지적 여부"가 **구조 수정이 실제로 먹혔는지의 진짜 검증**이 됐다.

### 8.4 재현 명령

```bash
cd ~/ghq/github.com/click6067-ship-it/CPX

# 인용 채굴
.venv/bin/python scripts/textbook_mine.py "검색어" --book rosen --n 6 --width 340

# 검증 + 렌더
.venv/bin/python scripts/findings_review.py data/working/findings/diarrhea_findings.json
.venv/bin/python scripts/findings_review.py <파일> --snap   # 단어중간 절단 복원(1회성)

# Codex 적대검수 (⚠️ 반드시 repo 루트에서, stdin 닫고)
export CODEX_HOME="${ORCA_CODEX_HOME:-$HOME/.codex}"
codex exec --model gpt-5.6-luna -c model_reasoning_effort=xhigh -s read-only "$(cat brief.md)" < /dev/null
```

---

> ⚠️ 이 보고서가 다루는 검토표의 임상 내용은 전부 `review_status: draft`이며 **지도교수 검증 전**이다.
> 의학적 정확성을 주장하지 않는다.
