"""
H2 검증 집계 v2 (Codex 재설계) — case 중심.
실행(실제): PYTHONPATH=src .venv/bin/python scripts/aggregate_validation.py \
            --items data/working/validation_build/cases_meta.json --url <U> --pw <ADMIN_PW>
실행(데모): PYTHONPATH=src .venv/bin/python scripts/aggregate_validation.py --demo

산출:
  1) [PRIMARY] case-level blind 루브릭 — AI 리뷰 vs 전문가 피드백 (차원별 평균, AI−전문가 차이 + case-cluster 부트스트랩 CI)
  2) [SECONDARY] per-point recall — 다수결 합의 + Fleiss kappa + 카테고리별 + case-cluster CI
  3) precision — AI 지적의 타당/중복/틀림/유해 비율
⚠️ 파일럿·dev_tune. CI는 case 클러스터(항목 아닌). 과대주장 금지.
"""
import json, sys, argparse, urllib.request
from collections import Counter, defaultdict
import numpy as np

DIMS = ["완전성", "정확성", "유용성", "안전성"]
PV = ["caught", "partial", "missed", "excluded"]
FV = ["valid_major", "valid_minor", "redundant", "wrong", "harmful"]
RNG = np.random.default_rng(0)


def kappa_label(k):
    return ("almost perfect" if k > .8 else "substantial" if k > .6 else "moderate" if k > .4
            else "fair" if k > .2 else "slight" if k > 0 else "poor")


def fleiss(counts):
    M = np.array(counts, float)
    if M.size == 0:
        return None
    n = M.sum(1)
    if not np.all(n == n[0]) or n[0] < 2:
        return None
    n = n[0]; N = M.shape[0]
    Pi = (np.sum(M ** 2, 1) - n) / (n * (n - 1))
    pj = M.sum(0) / (N * n); Pe = np.sum(pj ** 2)
    return 1.0 if Pe >= 1 else float((Pi.mean() - Pe) / (1 - Pe))


def consensus(vs):
    c = Counter(v for v in vs if v)
    if not c:
        return None, False
    t = c.most_common()
    return t[0][0], (len(t) > 1 and t[0][1] == t[1][1])


def mean(a):
    return sum(a) / len(a) if a else float("nan")


def load_subs(a):
    if a.url:
        d = json.loads(urllib.request.urlopen(f"{a.url}/api/results?pw={a.pw}", timeout=30).read())
        return d.get("submissions", d if isinstance(d, list) else [])
    d = json.loads(open(a.results, encoding="utf-8").read())
    return d.get("submissions", d) if isinstance(d, dict) else d


def demo():
    meta = [{"case_id": f"c{i}", "symptom": s, "year": "2023",
             "blind": ({"A": "expert", "B": "ai"} if i % 2 == 0 else {"A": "ai", "B": "expert"}),
             "points": [{"id": f"P{j}", "category": cat} for j, cat in enumerate(["CLINICAL_CONTENT", "CLINICAL_CONTENT", "INTERNAL_LOGIC", "STRUCTURAL"])],
             "finding_ids": [f"F{j}" for j in range(4)]}
            for i, s in enumerate(["흉통", "두통", "복통", "발열"])]
    subs = []
    for ji, jn in enumerate(["김교수", "이교수", "박교수"]):
        cs = []
        for i, m in enumerate(meta):
            ai_hi = {d: 4 + ((i + ji) % 2) for d in DIMS}      # AI 약간 낮게~비슷
            ex_hi = {d: 4 + ((i + 1) % 2) for d in DIMS}
            bA, bB = (ex_hi, ai_hi) if m["blind"]["A"] == "expert" else (ai_hi, ex_hi)
            pts = {f"P{j}": ["caught", "caught", "missed", "partial"][j] if (j + ji) % 4 else "caught" for j in range(4)}
            fnd = {f"F{j}": ["valid_major", "valid_minor", "redundant", "wrong"][j] for j in range(4)}
            cs.append({"case_id": m["case_id"], "blind": m["blind"], "bA": bA, "bB": bB, "points": pts, "findings": fnd})
        subs.append({"judge": jn, "cases": cs})
    return meta, subs


def boot_cluster(case_vals, stat, B=3000):
    """case_vals: {case_id: [per-judge value]} → 클러스터(case) 부트스트랩 95% CI of stat(flatten)."""
    cids = list(case_vals)
    if not cids:
        return (float("nan"), float("nan"))
    bs = []
    for _ in range(B):
        samp = RNG.choice(len(cids), len(cids), replace=True)
        vals = [v for si in samp for v in case_vals[cids[si]]]
        if vals:
            bs.append(stat(vals))
    return tuple(np.percentile(bs, [2.5, 97.5])) if bs else (float("nan"), float("nan"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--items"); ap.add_argument("--results"); ap.add_argument("--url"); ap.add_argument("--pw", default="cpx-demo")
    ap.add_argument("--demo", action="store_true"); ap.add_argument("--boot", type=int, default=3000)
    a = ap.parse_args()
    if a.demo:
        meta, subs = demo(); print("⚠️  데모 모드 — 가상 데이터(수식 검증용)\n")
    else:
        if not a.items or not (a.results or a.url):
            ap.error("--items 와 (--results 또는 --url) 필요 (또는 --demo)")
        meta = json.loads(open(a.items, encoding="utf-8").read()); subs = load_subs(a)
    Mm = {m["case_id"]: m for m in meta}
    judges = [s["judge"] for s in subs]
    print("=" * 64)
    print(f"판정자 {len(judges)}명: {', '.join(judges)} · 사례 {len(meta)}")
    print("=" * 64)

    # ── 1) PRIMARY: blind 루브릭 (AI vs 전문가) ──
    by = defaultdict(list)  # case_id -> [(aiR, exR)]
    for s in subs:
        for cc in s.get("cases", []):
            bl = cc.get("blind") or (Mm.get(cc["case_id"], {}) or {}).get("blind")
            if not bl:
                continue
            aiR = cc.get("bA") if bl.get("A") == "ai" else cc.get("bB")
            exR = cc.get("bB") if bl.get("A") == "ai" else cc.get("bA")
            if aiR and exR:
                by[cc["case_id"]].append((aiR, exR))
    print("\n[1] 주 분석 — 블라인드 루브릭: AI 리뷰 vs 전문가 피드백 (1~5, 높을수록 우수)")
    print("    (교수가 어느 쪽이 AI인지 모르고 평가. AI−전문가 차이의 95% CI가 0 부근/이상이면 'AI가 전문가에 필적')")
    for d in DIMS:
        cv_ai = {c: [a[d] for a, e in l if d in a] for c, l in by.items()}
        cv_ex = {c: [e[d] for a, e in l if d in e] for c, l in by.items()}
        cv_diff = {c: [a[d] - e[d] for a, e in l if d in a and d in e] for c, l in by.items()}
        ai = [v for l in cv_ai.values() for v in l]; ex = [v for l in cv_ex.values() for v in l]
        if not ai:
            continue
        lo, hi = boot_cluster({c: v for c, v in cv_diff.items() if v}, mean, a.boot)
        print(f"  {d:5s}  AI {mean(ai):.2f}  vs  전문가 {mean(ex):.2f}   차이 {mean(ai)-mean(ex):+.2f}  [95%CI {lo:+.2f}~{hi:+.2f}]")

    # ── 2) SECONDARY: per-point recall ──
    pv = defaultdict(lambda: defaultdict(list))  # case -> pid -> [verdict]
    for s in subs:
        for cc in s.get("cases", []):
            for pid, v in (cc.get("points") or {}).items():
                pv[cc["case_id"]][pid].append(v)
    pcat = {(m["case_id"], p["id"]): p["category"] for m in meta for p in m["points"]}
    cons, counts, agree, full = {}, [], 0, 0
    for cid, pm in pv.items():
        for pid, vs in pm.items():
            lab, _ = consensus(vs); cons[(cid, pid)] = lab
            vv = [x for x in vs if x]
            if len(vv) >= 2:
                full += 1; counts.append([sum(1 for x in vv if x == o) for o in PV]); agree += len(set(vv)) == 1
    k = fleiss(counts)
    scored = [(c, p) for (c, p), l in cons.items() if l in ("caught", "partial", "missed")]
    cv_rec = defaultdict(list)
    for (c, p) in scored:
        cv_rec[c].append(1.0 if cons[(c, p)] == "caught" else 0.0)
    allrec = [v for l in cv_rec.values() for v in l]
    print("\n[2] 보조 분석 — per-point recall (전문가 지적을 AI가 잡았나, 다수결 합의)")
    if k is not None:
        print(f"    판정자 일치도 Fleiss kappa = {k:.3f} ({kappa_label(k)}) · 전원일치 {agree}/{full}")
    if allrec:
        lo, hi = boot_cluster(cv_rec, mean, a.boot)
        print(f"    strict recall = {mean(allrec):.0%}  [95%CI {lo:.0%}~{hi:.0%}, case-cluster]  (분석 {len(scored)} · excluded {sum(l=='excluded' for l in cons.values())})")
    bycat = defaultdict(list)
    for (c, p) in scored:
        bycat[pcat.get((c, p), "?")].append(1.0 if cons[(c, p)] == "caught" else 0.0)
    for cat, l in sorted(bycat.items(), key=lambda x: -len(x[1])):
        print(f"      {cat:22s} {int(sum(l))}/{len(l)} = {mean(l):.0%}" + ("  (n작음)" if len(l) < 5 else ""))

    # ── 3) precision: AI 지적 타당성 ──
    fv = defaultdict(list)
    for s in subs:
        for cc in s.get("cases", []):
            for fid, v in (cc.get("findings") or {}).items():
                fv[(cc["case_id"], fid)].append(v)
    fc = {k2: consensus(v)[0] for k2, v in fv.items()}
    tot = [x for x in fc.values() if x]
    if tot:
        cnt = Counter(tot)
        valid = cnt["valid_major"] + cnt["valid_minor"] + cnt["redundant"]
        print("\n[3] precision — AI가 낸 지적의 타당성 (다수결, " + str(len(tot)) + "개)")
        print(f"    타당(중복포함) {valid}/{len(tot)} = {valid/len(tot):.0%}  · 중요한 타당 {cnt['valid_major']} · 경미 {cnt['valid_minor']} · 중복 {cnt['redundant']}")
        print(f"    ⚠ 틀림 {cnt['wrong']} ({cnt['wrong']/len(tot):.0%}) · 유해 {cnt['harmful']} ({cnt['harmful']/len(tot):.0%})")
    print("\n⚠️ 파일럿·dev_tune·다수결. case-cluster CI. 표본 작음 → 카테고리·precision은 exploratory.")


if __name__ == "__main__":
    main()
