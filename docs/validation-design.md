# H2 검증 설계 v2 (Codex 적대검수 반영) — 2026-06-19

> **H2:** "AI ②검토자가 전문가(교수) 피드백을 재현/필적하는가?"
> v1(per-point 분해→LLM매칭→인간 caught판정)을 Codex가 **REVISE**. 아래는 그 비판과 재설계.

## Codex가 깬 것 (v1의 결함)
1. **순환 측정** — LLM이 gold(전문가 지적)를 쪼개고 LLM이 매칭하면, 인간은 LLM이 만든 후보 공간 안에서만 판정. caught/missed가 모델·프롬프트 산물인지 교수 판정 산물인지 분리 안 됨.
2. **앵커링** — AI 후보 1개 + 잠정판정을 미리 보여주면 교수가 "이게 맞나?"에 끌려감(Tversky-Kahneman). 진짜 질문("AI 리뷰 전체가 이 결함을 잡았나")에서 이탈.
3. **정보 부족** — 1줄 지적+짧은 발췌로는 판정 불가 → IRR 붕괴. 출처참조 금지, 전체 맥락이 화면에.
4. **약한 주지표** — per-point recall은 부차(진단적 오류분석). 주지표는 **case-level blind 루브릭 비교**여야.
5. **precision 누락** — 전문가 피드백은 완전 gold가 아니라 observed. AI가 새로 낸 지적의 타당/유해성 평가 필요.
6. **가짜 정밀** — 81항목은 9사례에 nested. item-level bootstrap=pseudoreplication. **case-cluster** 부트스트랩/혼합모형으로.
7. **모델·사전등록** — 검증 전 모델 freeze, OSF 사전등록으로 연구자 자유도 차단.

## v2 설계 (구현됨)
**판정 단위 = 사례. 한 사례 = 페이지에 전부 표시(전문/생략 없음):** 초안 전문 · 리뷰 A/B 전문 · AI 리뷰 전체.

- **1단계 [PRIMARY] 블라인드 루브릭** — 같은 초안의 두 리뷰(하나는 전문가 피드백, 하나는 AI 리뷰)를 **무작위·익명**으로 제시. 교수가 어느 쪽이 AI인지 모른 채 각 리뷰를 **완전성·정확성·유용성·안전성(1~5)**로 평가. → AI가 전문가에 *필적*하는지 직접 측정(앵커링 제거).
- **2단계 [SECONDARY] per-point recall** — 어느 쪽이 AI였는지 공개 후, **AI 리뷰 전체를 보며** 교수 지적 각각을 caught/partial/missed/excluded. (후보 1개 강제 매칭 폐지 → 순환·앵커링 완화. LLM 분해는 enumerate 보조일 뿐, 교수가 전체를 보고 판정.)
- **3단계 precision** — AI가 낸 지적 각각: 타당·중요 / 타당·경미 / 전문가와 중복 / 틀림 / 위험·유해. → precision·false positive·harmful rate.

**지표:** (1) 차원별 AI−전문가 차이 + **case-cluster 부트스트랩 95% CI** (2) recall(다수결 합의)+Fleiss kappa+카테고리별 (3) precision/harmful. 판정자 N명 독립 → 일치도 보고.

**모델:** ②를 **gemini-2.5-pro로 격상**(flash-lite=부트스트랩이었음). harness는 **모델-agnostic**(데이터만 갈아끼움) → 모델 비교/교체 시 설문·골드 재사용.

## 남은 한계(정직히)
- 표본 작음(파일럿 ~9사례·3판정자) → 카테고리·precision은 **exploratory**. 본검증은 사례·판정자 확대.
- 인간-AI 산문 블라인드는 문체 차이로 완전하지 않음(문헌도 인정) → 한계로 명기.
- gold 분해가 아직 LLM 보조 → 향후 인간 codebook 고정 권장.
- 사전등록(OSF)·success threshold·locked_eval(15) 최종검증은 본검증 단계에서.

## 산출물
`scripts/build_validation_data.py`(case 데이터) · `web/adjudication/`(배포 설문) · `scripts/aggregate_validation.py`(집계). Codex 원문: 세션 로그.
