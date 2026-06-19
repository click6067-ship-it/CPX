"""
adjudication 집계 — H2 검증 최종 분석.
실행(실제):  PYTHONPATH=src .venv/bin/python scripts/aggregate_adjudication.py \
              --items data/working/survey_build/items_meta.json \
              --results submissions.json        # 또는 --url <U> --pw <P> (배포서버서 직접)
실행(데모):  PYTHONPATH=src .venv/bin/python scripts/aggregate_adjudication.py --demo

산출:
  - 판정자 일치도 Fleiss kappa (전문가지적/②지적 별도) + 단순 일치율
  - 항목별 다수결 합의(gold), tie(합의실패) 표시
  - recall(전문가 피드백 재현율): 전체 strict/lenient + 카테고리별 + 페어-부트스트랩 95% CI
  - precision/F1 (②지적 타당성, --with-ai로 ②지적 포함 시)
  - 불일치 항목 목록(교수 재검토용)

⚠️ 파일럿·dev_tune. excluded(=사례품질 아님) 다수결은 분모서 제외. 과대주장 금지.
"""
import json, sys, argparse, urllib.request
from collections import Counter, defaultdict
import numpy as np

EXPERT_OPTS = ["caught", "partial", "missed", "excluded"]
AI_OPTS = ["in_expert", "valid_extra", "invalid"]
RNG = np.random.default_rng(0)


def kappa_label(k):
    return ("almost perfect" if k > .8 else "substantial" if k > .6 else "moderate" if k > .4
            else "fair" if k > .2 else "slight" if k > 0 else "poor")


def fleiss_kappa(rows_counts):
    """rows_counts: list of category-count vectors(각 항목 합=raters n). 항목별 n 동일 가정(full overlap)."""
    M = np.array(rows_counts, dtype=float)
    if M.size == 0 or M.sum() == 0:
        return None, 0
    N, k = M.shape
    n = M.sum(axis=1)
    if not np.all(n == n[0]) or n[0] < 2:   # 모든 판정자가 모든 항목 판정 + ≥2명
        return None, int(N)
    n = n[0]
    P_i = (np.sum(M ** 2, axis=1) - n) / (n * (n - 1))
    P_bar = P_i.mean()
    p_j = M.sum(axis=0) / (N * n)
    P_e = np.sum(p_j ** 2)
    if P_e >= 1:
        return 1.0, int(N)
    return float((P_bar - P_e) / (1 - P_e)), int(N)


def consensus(verdicts):
    """다수결. 동률이면 (label, True=tie)."""
    c = Counter(v for v in verdicts if v)
    if not c:
        return None, False
    top = c.most_common()
    if len(top) > 1 and top[0][1] == top[1][1]:
        return top[0][0], True
    return top[0][0], False


def load_subs(args):
    if args.url:
        raw = urllib.request.urlopen(f"{args.url}/api/results?pw={args.pw}", timeout=30).read()
        d = json.loads(raw)
        return d.get("submissions", d if isinstance(d, list) else [])
    d = json.loads(open(args.results, encoding="utf-8").read())
    return d.get("submissions", d) if isinstance(d, dict) else d


def demo_data():
    """결정적 데모(가상). 4페어·전문가지적 10·②지적 3·판정자 3명."""
    meta = [
        {"id": "E0", "type": "EXPERT", "pair": "흉통_가상", "category": "CLINICAL_CONTENT", "case_quality": "Y"},
        {"id": "E1", "type": "EXPERT", "pair": "흉통_가상", "category": "CLINICAL_CONTENT", "case_quality": "Y"},
        {"id": "E2", "type": "EXPERT", "pair": "흉통_가상", "category": "INTERNAL_LOGIC", "case_quality": "Y"},
        {"id": "E3", "type": "EXPERT", "pair": "두통_가상", "category": "CLINICAL_CONTENT", "case_quality": "Y"},
        {"id": "E4", "type": "EXPERT", "pair": "두통_가상", "category": "STRUCTURAL", "case_quality": "Y"},
        {"id": "E5", "type": "EXPERT", "pair": "두통_가상", "category": "SCORING_VALIDITY", "case_quality": "Y"},
        {"id": "E6", "type": "EXPERT", "pair": "복통_가상", "category": "CLINICAL_CONTENT", "case_quality": "Y"},
        {"id": "E7", "type": "EXPERT", "pair": "복통_가상", "category": "SAFETY_OVERCLAIM", "case_quality": "Y"},
        {"id": "E8", "type": "EXPERT", "pair": "복통_가상", "category": "SP_LOGISTICS", "case_quality": "Y"},
        {"id": "E9", "type": "EXPERT", "pair": "발열_가상", "category": "CLINICAL_CONTENT", "case_quality": "Y"},
        {"id": "A0", "type": "AI", "pair": "흉통_가상", "category": "AI_FINDING", "case_quality": ""},
        {"id": "A1", "type": "AI", "pair": "두통_가상", "category": "AI_FINDING", "case_quality": ""},
        {"id": "A2", "type": "AI", "pair": "복통_가상", "category": "AI_FINDING", "case_quality": ""},
    ]
    # 3명 판정(대체로 일치, E2 tie, E8 excluded, A2 invalid 등)
    J = {
        "김교수": {"E0": "caught", "E1": "missed", "E2": "caught", "E3": "caught", "E4": "missed",
                 "E5": "caught", "E6": "caught", "E7": "missed", "E8": "excluded", "E9": "partial",
                 "A0": "in_expert", "A1": "valid_extra", "A2": "invalid"},
        "이교수": {"E0": "caught", "E1": "missed", "E2": "missed", "E3": "caught", "E4": "missed",
                 "E5": "caught", "E6": "partial", "E7": "missed", "E8": "excluded", "E9": "caught",
                 "A0": "in_expert", "A1": "valid_extra", "A2": "valid_extra"},
        "박교수": {"E0": "caught", "E1": "partial", "E2": "partial", "E3": "caught", "E4": "missed",
                 "E5": "caught", "E6": "caught", "E7": "missed", "E8": "excluded", "E9": "caught",
                 "A0": "in_expert", "A1": "invalid", "A2": "invalid"},
    }
    subs = [{"judge": j, "verdicts": [{"id": k, "verdict": v} for k, v in d.items()]} for j, d in J.items()]
    return meta, subs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--items"); ap.add_argument("--results")
    ap.add_argument("--url"); ap.add_argument("--pw", default="cpx-demo")
    ap.add_argument("--demo", action="store_true"); ap.add_argument("--boot", type=int, default=3000)
    args = ap.parse_args()

    if args.demo:
        meta, subs = demo_data()
        print("⚠️  데모 모드 — 가상 사례·가상 판정(파이프라인/수식 검증용, 실제 결과 아님)\n")
    else:
        if not args.items or not (args.results or args.url):
            ap.error("--items 와 (--results 또는 --url) 필요. (또는 --demo)")
        meta = json.loads(open(args.items, encoding="utf-8").read())
        subs = load_subs(args)

    M = {m["id"]: m for m in meta}
    judges = [s["judge"] for s in subs]
    # id -> {judge: verdict}
    by_item = defaultdict(dict)
    for s in subs:
        for v in s.get("verdicts", []):
            if v.get("verdict"):
                by_item[v["id"]][s["judge"]] = v["verdict"]

    exp_ids = [m["id"] for m in meta if m["type"] == "EXPERT"]
    ai_ids = [m["id"] for m in meta if m["type"] == "AI"]

    print("=" * 60)
    print(f"판정자 {len(judges)}명: {', '.join(judges)}")
    print(f"전문가지적 {len(exp_ids)}항목 · ②지적 {len(ai_ids)}항목")
    print("=" * 60)

    # ── 1) Fleiss kappa + 단순 일치율 ──
    def kappa_for(ids, opts, label):
        counts, agree, full = [], 0, 0
        for i in ids:
            vs = [by_item[i].get(j) for j in judges]
            vs = [v for v in vs if v]
            if len(vs) < 2:
                continue
            full += 1
            counts.append([sum(1 for v in vs if v == o) for o in opts])
            agree += 1 if len(set(vs)) == 1 else 0
        k, n = fleiss_kappa(counts)
        print(f"\n[{label}] (완전판정 {full}항목)")
        if k is None:
            print("  Fleiss kappa: 계산불가(판정자<2 또는 항목별 판정자 수 불일치)")
        else:
            print(f"  Fleiss kappa = {k:.3f} ({kappa_label(k)})")
        if full:
            print(f"  전원일치율   = {agree}/{full} = {agree/full:.0%}")
    kappa_for(exp_ids, EXPERT_OPTS, "판정자 일치도 — 전문가지적")
    if ai_ids:
        kappa_for(ai_ids, AI_OPTS, "판정자 일치도 — ②지적")

    # ── 2) 합의 + recall ──
    cons, ties = {}, []
    for i in exp_ids:
        lab, tie = consensus([by_item[i].get(j) for j in judges])
        cons[i] = lab
        if tie:
            ties.append(i)
    scored = [i for i in exp_ids if cons[i] in ("caught", "partial", "missed")]   # excluded/None 제외
    excl = [i for i in exp_ids if cons[i] == "excluded"]

    def recall(ids):
        if not ids:
            return None, None, 0
        c = sum(cons[i] == "caught" for i in ids)
        p = sum(cons[i] == "partial" for i in ids)
        return c / len(ids), (c + .5 * p) / len(ids), len(ids)

    print("\n" + "=" * 60)
    print("recall — ②가 전문가 피드백을 재현한 비율 (다수결 합의 기준)")
    print(f"  분석대상 {len(scored)}항목 (excluded {len(excl)} 제외, tie {len(ties)})")
    r_s, r_l, n = recall(scored)
    if n:
        # 페어-부트스트랩 CI(클러스터=페어)
        pairs = defaultdict(list)
        for i in scored:
            pairs[M[i]["pair"]].append(i)
        plist = list(pairs)
        boots = []
        for _ in range(args.boot):
            samp = RNG.choice(len(plist), len(plist), replace=True)
            ids = [i for s in samp for i in pairs[plist[s]]]
            cc = sum(cons[i] == "caught" for i in ids)
            boots.append(cc / len(ids) if ids else 0)
        lo, hi = np.percentile(boots, [2.5, 97.5])
        print(f"  ▶ strict recall (caught만)        = {r_s:.0%}  [95% CI {lo:.0%}–{hi:.0%}, 페어부트스트랩]")
        print(f"  ▶ lenient recall (partial 0.5)    = {r_l:.0%}")

    # 카테고리별
    bycat = defaultdict(list)
    for i in scored:
        bycat[M[i]["category"]].append(i)
    print("\n  카테고리별 strict recall:")
    for cat, ids in sorted(bycat.items(), key=lambda x: -len(x[1])):
        rs, rl, nn = recall(ids)
        print(f"    {cat:22s} {sum(cons[i]=='caught' for i in ids)}/{nn} = {rs:.0%}" + ("  (n작음 주의)" if nn < 5 else ""))

    # ── 3) precision/F1 (②지적) ──
    if ai_ids:
        ac = {i: consensus([by_item[i].get(j) for j in judges])[0] for i in ai_ids}
        scored_ai = [i for i in ai_ids if ac[i] in AI_OPTS]
        if scored_ai:
            valid = sum(ac[i] in ("in_expert", "valid_extra") for i in scored_ai)
            prec = valid / len(scored_ai)
            print("\n" + "=" * 60)
            print(f"precision — ②지적의 타당성 ({len(scored_ai)}항목)")
            print(f"  ▶ precision (in_expert+valid_extra) = {valid}/{len(scored_ai)} = {prec:.0%}")
            print(f"    (invalid/환각 {sum(ac[i]=='invalid' for i in scored_ai)})")
            if r_s is not None and (prec + r_s) > 0:
                f1 = 2 * prec * r_s / (prec + r_s)
                print(f"  ▶ F1 (strict recall × precision)    = {f1:.0%}")

    # ── 4) 불일치 항목(재검토용) ──
    dis = [i for i in exp_ids if len(set(v for v in (by_item[i].get(j) for j in judges) if v)) > 1]
    print("\n" + "=" * 60)
    print(f"판정 불일치 항목 {len(dis)}개 (교수 재검토 후보):")
    for i in dis[:15]:
        vs = {j: by_item[i].get(j) for j in judges}
        print(f"  {i} [{M[i]['pair']}/{M[i]['category']}] → {vs}" + ("  ⚠tie" if i in ties else ""))
    print("\n⚠️ 파일럿·dev_tune·다수결 자동집계. 보고 시 CI·n·과대주장 금지 명기.")


if __name__ == "__main__":
    main()
