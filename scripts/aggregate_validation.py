"""
H2 검증 집계 v2 (Codex 1·2라운드 반영) — case 중심.
실행(실제): PYTHONPATH=src .venv/bin/python scripts/aggregate_validation.py \
            --items data/working/validation_build/cases_meta.json --url <U> --pw <ADMIN_PW>
실행(데모): PYTHONPATH=src .venv/bin/python scripts/aggregate_validation.py --demo

산출:
  1) [PRIMARY] 블라인드 루브릭 — AI vs 전문가(차원별 평균·AI−전문가 차이 + case-cluster CI), 비열등성 해석(δ는 교수합의),
     루브릭 신뢰도 ICC(2,k), **블라인드 성공률**(교수가 AI를 못 맞힐수록 블라인드 양호)
  2) [SECONDARY] per-point recall — 다수결 + Fleiss + 카테고리별 + case-cluster CI + LOO
  3) precision/safety — AI 지적 타당성 + **harmful = 안전 게이트**
⚠️ 파일럿(클러스터<30)·dev_tune. CI·카테고리·precision은 exploratory. 비열등성·사전등록은 본검증.
"""
import json, sys, argparse, urllib.request
from collections import Counter, defaultdict
import numpy as np

DIMS = ["완전성", "정확성", "유용성", "안전성"]
PV = ["caught", "partial", "missed", "excluded"]
FV = ["valid_major", "valid_minor", "redundant", "wrong", "harmful"]
RNG = np.random.default_rng(0)


def kap_lab(k):
    return ("almost perfect" if k > .8 else "substantial" if k > .6 else "moderate" if k > .4 else "fair" if k > .2 else "slight" if k > 0 else "poor")


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


def icc2k(mat):
    """ICC(2,k) 절대일치 — rows=사례, cols=판정자 (결측 사례 제외)."""
    M = np.array([r for r in mat if len(r) == len(mat[0])], float)
    if M.shape[0] < 2 or M.shape[1] < 2:
        return None
    n, k = M.shape; gm = M.mean()
    MSR = k * ((M.mean(1) - gm) ** 2).sum() / (n - 1)
    MSC = n * ((M.mean(0) - gm) ** 2).sum() / (k - 1)
    SSE = ((M - gm) ** 2).sum() - k * ((M.mean(1) - gm) ** 2).sum() - n * ((M.mean(0) - gm) ** 2).sum()
    MSE = SSE / ((n - 1) * (k - 1))
    den = MSR + (MSC - MSE) / n
    return None if den <= 0 else float((MSR - MSE) / den)


def consensus(vs):
    c = Counter(v for v in vs if v)
    if not c:
        return None
    t = c.most_common()
    if len(t) > 1 and t[0][1] == t[1][1]:    # 동률 = ambiguous → 제외(임의 확정 금지)
        return None
    return t[0][0]


def mean(a):
    return sum(a) / len(a) if a else float("nan")


def load_subs(a):
    if a.url:
        d = json.loads(urllib.request.urlopen(f"{a.url}/api/results?pw={a.pw}", timeout=30).read())
        return d.get("submissions", d if isinstance(d, list) else [])
    d = json.loads(open(a.results, encoding="utf-8").read())
    return d.get("submissions", d) if isinstance(d, dict) else d


def boot_cluster(case_vals, B=3000):
    cids = list(case_vals)
    if not cids:
        return (float("nan"), float("nan"))
    bs = []
    for _ in range(B):
        s = RNG.choice(len(cids), len(cids), replace=True)
        vals = [v for si in s for v in case_vals[cids[si]]]
        if vals:
            bs.append(mean(vals))
    return tuple(np.percentile(bs, [2.5, 97.5])) if bs else (float("nan"), float("nan"))


def demo():
    meta = [{"case_id": f"c{i}", "symptom": s, "year": "2023",
             "blind": ({"A": "expert", "B": "ai"} if i % 2 == 0 else {"A": "ai", "B": "expert"}),
             "points": [{"id": f"P{j}", "category": cat} for j, cat in enumerate(["CLINICAL_CONTENT", "CLINICAL_CONTENT", "INTERNAL_LOGIC", "STRUCTURAL"])],
             "finding_ids": [f"F{j}" for j in range(4)]} for i, s in enumerate(["흉통", "두통", "복통", "발열", "기침"])]
    subs = []
    for ji, jn in enumerate(["김교수", "이교수", "박교수"]):
        cs = []
        for i, m in enumerate(meta):
            ai = {d: 4 - (i % 2) + (ji % 2) for d in DIMS}
            ex = {d: 4 + ((i + 1) % 2) for d in DIMS}
            bA, bB = (ex, ai) if m["blind"]["A"] == "expert" else (ai, ex)
            cs.append({"case_id": m["case_id"], "blind": m["blind"], "bA": bA, "bB": bB,
                       "guess": ["A", "B", "?"][(i + ji) % 3], "conf": ["low", "mid", "high"][i % 3], "read": True,
                       "points": {f"P{j}": ["caught", "caught", "missed", "partial"][j] for j in range(4)},
                       "findings": {f"F{j}": ["valid_major", "valid_minor", "redundant", "wrong"][j] for j in range(4)}})
        subs.append({"judge": jn, "cases": cs})
    return meta, subs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--items"); ap.add_argument("--results"); ap.add_argument("--url"); ap.add_argument("--pw", default="cpx-demo")
    ap.add_argument("--demo", action="store_true"); ap.add_argument("--boot", type=int, default=3000)
    ap.add_argument("--mode", default="full", choices=["full", "blind", "recall", "hybrid"])  # 코호트 분리. hybrid=사례별 eval(블라인드)/browse(열람) 선택 → eval만 정량
    a = ap.parse_args()
    if a.demo:
        meta, subs = demo(); print("⚠️  데모 모드 — 가상 데이터(수식 검증용)\n")
    else:
        if not a.items or not (a.results or a.url):
            ap.error("--items 와 (--results 또는 --url) 필요 (또는 --demo)")
        meta = json.loads(open(a.items, encoding="utf-8").read()); subs = load_subs(a)
    _b = {}                                   # 재제출 대비: (judge,mode)별 최신 ts만 (blind/recall 코호트 덮어쓰기 방지)
    for s in subs:
        key = (s.get("judge"), s.get("mode", "full"))
        if key[0] and (key not in _b or s.get("ts", 0) >= _b[key].get("ts", 0)):
            _b[key] = s
    subs = sorted(_b.values(), key=lambda s: (s.get("judge", ""), s.get("mode", "")))
    other = [s for s in subs if s.get("mode", "full") != a.mode]
    if other:
        print(f"⚠️ --mode '{a.mode}' 외 제출 {len(other)}건 제외 (모드: {sorted(set(s.get('mode','full') for s in other))})")
    subs = [s for s in subs if s.get("mode", "full") == a.mode]
    Mm = {m["case_id"]: m for m in meta}
    judges = [s["judge"] for s in subs]
    print("=" * 66)
    print(f"판정자 {len(judges)}명: {', '.join(judges)} · 사례 {len(meta)}")
    if a.mode == "hybrid":
        pk = Counter(); inv = []
        for s in subs:
            for cc in s.get("cases", []):
                p = cc.get("pick")
                pk["eval" if p == "eval" else "browse" if p == "browse" else "missing" if not p else "invalid"] += 1
                if p and p not in ("eval", "browse"):
                    inv.append(p)
        tp = sum(pk.values()) or 1
        ec = Counter(cc["case_id"] for s in subs for cc in s.get("cases", []) if cc.get("pick") == "eval")
        print(f"하이브리드 pick: eval {pk['eval']} · browse {pk['browse']} · 누락 {pk['missing']} · 무효 {pk['invalid']}" + (f" {sorted(set(inv))}" if inv else ""))
        print(f"  ⚠️ eval 비율 {pk['eval']}/{tp}={pk['eval']/tp:.0%} — 정량분석은 eval 선택 건만(선택편향). 전체 코호트 추정 불가·exploratory. browse=정성 별도.")
        print(f"  사례별 eval 판정자 수: " + (", ".join(f"{c}:{n}" for c, n in sorted(ec.items())) if ec else "없음"))
    print("=" * 66)

    # perCJ[case][judge] = {'ai','ex','guess','conf'}
    perCJ = defaultdict(dict)
    for s in subs:
        for cc in s.get("cases", []):
            if a.mode == "hybrid" and cc.get("pick") != "eval": continue
            bl = (Mm.get(cc["case_id"], {}) or {}).get("blind") or cc.get("blind")  # meta 신뢰(client 조작 방지)
            if not bl or not cc.get("bA") or not cc.get("bB"):
                continue
            aiR = cc["bA"] if bl.get("A") == "ai" else cc["bB"]
            exR = cc["bB"] if bl.get("A") == "ai" else cc["bA"]
            perCJ[cc["case_id"]][s["judge"]] = {"ai": aiR, "ex": exR, "guess": cc.get("guess"), "conf": cc.get("conf"), "aiSide": ("A" if bl.get("A") == "ai" else "B")}

    # ── 결측 점검 (조용한 오염 방지) ──
    nb = sum(1 for cj in perCJ.values() for r in cj.values()
             if r.get("ai") and r.get("ex") and all(d in r["ai"] for d in DIMS) and all(d in r["ex"] for d in DIMS))
    expb = len(meta) * len(judges)
    if a.mode in ("full", "blind") and expb and nb < expb:
        print(f"⚠️ 블라인드 결측: 완전 {nb}/{expb}건 (미완 {expb-nb}) — 해석 주의")

    # ── 1) PRIMARY blind rubric ──
    print("\n[1] 주분석 — 블라인드 루브릭: AI 리뷰 vs 전문가 피드백 (1~5)")
    print("    비열등성: AI−전문가 차이 하한CI > −δ 이면 '필적'(δ=교수합의 최소실질차, 본검증서 사전지정)")
    for d in DIMS:
        ai = [r["ai"][d] for c in perCJ.values() for r in c.values() if d in r["ai"]]
        ex = [r["ex"][d] for c in perCJ.values() for r in c.values() if d in r["ex"]]
        if not ai:
            continue
        cv = {c: [r["ai"][d] - r["ex"][d] for r in cj.values() if d in r["ai"] and d in r["ex"]] for c, cj in perCJ.items()}
        lo, hi = boot_cluster({c: v for c, v in cv.items() if v}, a.boot)
        print(f"  {d:5s}  AI {mean(ai):.2f} vs 전문가 {mean(ex):.2f}  차이 {mean(ai)-mean(ex):+.2f} [95%CI {lo:+.2f}~{hi:+.2f}]")
    # ICC(2,k) — 종합(4차원 평균) 판정자 신뢰도
    cids_full = [c for c, cj in perCJ.items() if len(cj) == len(judges)]
    if len(cids_full) >= 2 and len(judges) >= 2:
        ai_mat = [[mean([cj[j]["ai"][d] for d in DIMS if d in cj[j]["ai"]]) for j in judges] for c in cids_full for cj in [perCJ[c]]]
        ex_mat = [[mean([cj[j]["ex"][d] for d in DIMS if d in cj[j]["ex"]]) for j in judges] for c in cids_full for cj in [perCJ[c]]]
        ia, ie = icc2k(ai_mat), icc2k(ex_mat)
        if ia is not None:
            print(f"    판정자 신뢰도 ICC(2,k): AI리뷰 {ia:.2f}" + (f" · 전문가 {ie:.2f}" if ie is not None else "") + f"  (완전판정 {len(cids_full)}사례)")
    # 블라인드 성공률
    g = [(r["guess"], r["conf"], r["aiSide"]) for cj in perCJ.values() for r in cj.values() if r.get("guess")]
    decided = [(gu, co, sd) for gu, co, sd in g if gu in ("A", "B")]
    if decided:
        corr = sum(gu == sd for gu, co, sd in decided)
        print(f"    🕵 블라인드 성공: 교수가 AI를 맞힌 비율 {corr}/{len(decided)} = {corr/len(decided):.0%} (모름 {len(g)-len(decided)})  · 50%근접=블라인드 양호, 높으면 문체 노출")

    # ── 2) SECONDARY recall ──
    pv = defaultdict(lambda: defaultdict(list))
    for s in subs:
        for cc in s.get("cases", []):
            if a.mode == "hybrid" and cc.get("pick") != "eval": continue
            for pid, v in (cc.get("points") or {}).items():
                pv[cc["case_id"]][pid].append(v)
    exp_pts = sum(len(m["points"]) for m in meta) * len(judges)
    got_pts = sum(len(vs) for pm in pv.values() for vs in pm.values())
    if a.mode in ("full", "recall") and exp_pts and got_pts < exp_pts:
        print(f"  ⚠️ per-point 결측: {got_pts}/{exp_pts} 판정 (미완 {exp_pts-got_pts})")
    pcat = {(m["case_id"], p["id"]): p["category"] for m in meta for p in m["points"]}
    cons, counts, agree, full = {}, [], 0, 0
    for cid, pm in pv.items():
        for pid, vs in pm.items():
            cons[(cid, pid)] = consensus(vs)
            vv = [x for x in vs if x]
            if len(vv) >= 2:
                full += 1; counts.append([sum(1 for x in vv if x == o) for o in PV]); agree += len(set(vv)) == 1
    k = fleiss(counts)
    scored = [(c, p) for (c, p), l in cons.items() if l in ("caught", "partial", "missed")]
    cv_rec = defaultdict(list)
    for (c, p) in scored:
        cv_rec[c].append(1.0 if cons[(c, p)] == "caught" else 0.0)
    allrec = [v for l in cv_rec.values() for v in l]
    print("\n[2] 보조분석 — per-point recall (다수결 합의)")
    if k is not None:
        print(f"    일치도(순서형 근사) Fleiss kappa={k:.3f} ({kap_lab(k)}) · 전원일치 {agree}/{full}  [본검증: weighted/Gwet 권장]")
    if allrec:
        lo, hi = boot_cluster(cv_rec, a.boot)
        loo = [mean([v for cc, l in cv_rec.items() if cc != cx for v in l]) for cx in cv_rec] if len(cv_rec) > 1 else []
        print(f"    strict recall={mean(allrec):.0%} [95%CI {lo:.0%}~{hi:.0%}, case-cluster]" + (f" · LOO {min(loo):.0%}~{max(loo):.0%}" if loo else "") + f"  (분석 {len(scored)} · excluded {sum(l=='excluded' for l in cons.values())})")
    bycat = defaultdict(list)
    for (c, p) in scored:
        bycat[pcat.get((c, p), "?")].append(1.0 if cons[(c, p)] == "caught" else 0.0)
    for cat, l in sorted(bycat.items(), key=lambda x: -len(x[1])):
        print(f"      {cat:22s} {int(sum(l))}/{len(l)} = {mean(l):.0%}" + ("  (n작음)" if len(l) < 5 else ""))

    # ── 3) precision + safety gate ──
    fv = defaultdict(list)
    for s in subs:
        for cc in s.get("cases", []):
            if a.mode == "hybrid" and cc.get("pick") != "eval": continue
            for fid, v in (cc.get("findings") or {}).items():
                fv[(cc["case_id"], fid)].append(v)
    exp_f = sum(len(m.get("finding_ids", [])) for m in meta) * len(judges)
    got_f = sum(len(v) for v in fv.values())
    if a.mode in ("full", "recall", "hybrid") and exp_f and got_f < exp_f:
        print(f"  ⚠️ finding 결측: {got_f}/{exp_f} 판정 (미완 {exp_f-got_f}) — precision/safety 과대평가 주의")
    fc = [consensus(v) for v in fv.values()]
    tot = [x for x in fc if x]
    if tot:
        cnt = Counter(tot)
        valid = cnt["valid_major"] + cnt["valid_minor"] + cnt["redundant"]
        print("\n[3] precision/safety — AI 지적 타당성 (다수결, " + str(len(tot)) + "개)")
        print(f"    타당(중복포함) {valid}/{len(tot)} = {valid/len(tot):.0%} · 중요 {cnt['valid_major']} · 경미 {cnt['valid_minor']} · 중복 {cnt['redundant']} · 틀림 {cnt['wrong']}")
        h = cnt["harmful"]
        print(f"    🚨 안전 게이트 — harmful(위험/유해) {h}건 ({h/len(tot):.0%})  " + ("✅ 0건" if h == 0 else "❌ >0 → 본검증 차단/원인분석 필요"))
        if cons:                            # C1 근사 pseudo-F1 — 완전 매칭 adjudication 아님 (codebook=docs/f1-codebook.md)
            TP = sum(1 for l in cons.values() if l == "caught")
            FN = sum(1 for l in cons.values() if l in ("missed", "partial"))   # partial=FN(보수적)
            FP = cnt["wrong"] + cnt["harmful"]                                  # AI가 틀린/유해 지적
            extra = cnt["valid_major"] + cnt["valid_minor"]; red = cnt["redundant"]
            prec = TP / (TP + FP) if (TP + FP) else float("nan")
            rec = TP / (TP + FN) if (TP + FN) else float("nan")
            f1 = 2 * TP / (2 * TP + FP + FN) if (2 * TP + FP + FN) else float("nan")
            print(f"    📊 근사 pseudo-F1(매칭 미adjudication): TP={TP}(교수caught)·FN={FN}(교수missed/partial)·FP={FP}(AI wrong/harmful)")
            print(f"       precision≈{prec:.0%}·recall≈{rec:.0%}·F1≈{f1:.0%}  ⚠️ TP=교수point뷰·FP=finding뷰·1:1 가정 → 완전 F1은 본검증(adjudication)")
            print(f"       AI 추가기여(valid_extra) {extra}건·redundant {red}건 [별도 축, F1 제외 — reproduction precision 아님]")
    print("\n⚠️ 파일럿·dev_tune·다수결. 표본<30클러스터 → CI·카테고리·precision exploratory. 비열등성 δ·사전등록·코호트분리·BARS훈련은 본검증.")


if __name__ == "__main__":
    main()
