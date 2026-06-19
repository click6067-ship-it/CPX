"""
교수 adjudication을 *쉽게* — 단일 HTML 앱 생성(한 문항씩 버튼 클릭, 서버 불필요).
실행: PYTHONPATH=src .venv/bin/python scripts/build_adjudication_html.py
입력: data/working/adjudication/adjudication_batch1_J1.csv (생성기 산출)
출력: data/working/adjudication/adjudicate.html  ← 이 파일 하나를 교수 3명에게 이메일.

교수: 열기 → 이름 입력 → 한 문항씩(전문가 지적 + AI 잠정판정 미리 선택됨) 확인/수정 → 결과 내려받기(JSON) → 회신.
localStorage 자동저장(중간에 닫아도 이어서). 폰 가능. case_quality=N(운영/SP)는 기본 제외.
"""
import csv, json
from pathlib import Path

import sys
OUT = Path("data/working/adjudication")
_pos = [a for a in sys.argv[1:] if not a.startswith("--")]
SRC = _pos[0] if _pos else str(OUT / "adjudication_batch1_J1.csv")
INCLUDE_AI = "--with-ai" in sys.argv     # 기본: 전문가지적(recall)만 → 가벼움. precision은 나중에.
MAX_PAIRS = next((int(a.split("=")[1]) for a in sys.argv if a.startswith("--pairs=")), None)
rows = list(csv.DictReader(open(SRC, encoding="utf-8-sig")))
if MAX_PAIRS:
    keep = list(dict.fromkeys(r["pair"] for r in rows))[:MAX_PAIRS]
    rows = [r for r in rows if r["pair"] in keep]

items = []
for i, r in enumerate(rows):
    if r["row_type"] == "EXPERT_POINT" and r["case_quality"] == "Y":
        items.append({"id": f"E{i}", "type": "EXPERT", "pair": r["pair"], "item": r["item"],
                      "cat": r["category"], "cand": r["ai_candidate"], "tent": r["ai_tentative"]})
if INCLUDE_AI:
    for i, r in enumerate(rows):
        if r["row_type"] == "AI_FINDING":
            items.append({"id": f"A{i}", "type": "AI", "pair": r["pair"], "item": r["item"]})

n_exp = sum(1 for x in items if x["type"] == "EXPERT")
HTML = """<!doctype html><html lang=ko><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>CPX 사례 심사 검증</title><style>
*{box-sizing:border-box}body{font-family:-apple-system,system-ui,sans-serif;margin:0;background:#f4f6f9;color:#1a2233}
.wrap{max-width:680px;margin:0 auto;padding:16px}
.bar{height:8px;background:#e3e8ef;border-radius:8px;overflow:hidden;margin:10px 0}
.bar>i{display:block;height:100%;background:#2c7be5;width:0}
.card{background:#fff;border-radius:14px;padding:20px;box-shadow:0 1px 6px #0001;margin:12px 0}
.tag{display:inline-block;font-size:12px;background:#eef2f7;color:#5b6b82;border-radius:6px;padding:2px 8px;margin-right:6px}
.q{font-size:19px;font-weight:700;line-height:1.5;margin:10px 0}
.hint{font-size:14px;color:#5b6b82;background:#f8fafc;border-left:3px solid #2c7be5;padding:8px 10px;border-radius:6px;margin:10px 0}
.btns{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:12px}
button.opt{padding:14px;font-size:16px;border:2px solid #d7deea;background:#fff;border-radius:10px;cursor:pointer}
button.opt.sel{border-color:#2c7be5;background:#eaf2fe;font-weight:700}
.nav{display:flex;justify-content:space-between;margin-top:14px;gap:8px}
.nav button{padding:10px 18px;border-radius:8px;border:1px solid #ccc;background:#fff;cursor:pointer}
.note{width:100%;margin-top:8px;padding:8px;border:1px solid #d7deea;border-radius:8px;font-size:14px}
.dl{background:#2c7be5;color:#fff;border:none;font-weight:700}
small{color:#7a8aa0}.done{text-align:center;padding:30px}
</style></head><body><div class=wrap>
<h2>CPX 사례 심사 검증 <small id=pct></small></h2>
<div id=start class=card>
<p><b>판정자 성함</b>을 입력하고 시작하세요. (다른 분과 상의 없이 독립적으로)</p>
<p style="font-size:14px;color:#5b6b82">전문가가 단 지적을 <b>②AI가 잡았는지</b> 판정합니다. AI 잠정판정이 미리 선택돼 있으니 <b>동의하면 '다음', 아니면 고쳐</b> 주세요. 중간에 닫아도 이어집니다.</p>
<input class=note id=jname placeholder="예: 임선주"><button class="opt dl" style="margin-top:10px;grid-column:auto" onclick=start()>시작</button>
</div>
<div id=app style=display:none>
<div class=bar><i id=fill></i></div>
<div class=card id=card></div>
<div class=nav><button onclick=prev()>← 이전</button>
<button class=dl onclick=download()>결과 내려받기</button>
<button onclick=next()>다음 →</button></div>
<p><small>자동 저장됨. 다 하면 '결과 내려받기' → 받은 파일을 회신해 주세요.</small></p>
</div>
<div id=fin class=done style=display:none><h2>완료! 🎉</h2><p>아래 버튼으로 결과를 내려받아 회신해 주세요.</p>
<button class="opt dl" onclick=download()>결과 내려받기</button></div>
</div><script>
const ITEMS=__ITEMS__, NEXP=__NEXP__;
const OPT={EXPERT:[["caught","✅ 잡음"],["partial","🟡 부분"],["missed","❌ 못잡음"]],
          AI:[["in_expert","전문가에도 있음"],["valid_extra","✔ 타당한 추가지적"],["invalid","✖ 틀림/환각"]]};
let judge="",i=0,V={};
function K(){return "cpxadj_"+judge}
function start(){judge=document.getElementById('jname').value.trim();if(!judge)return alert('성함을 입력하세요');
 V=JSON.parse(localStorage.getItem(K())||'{}');document.getElementById('start').style.display='none';
 document.getElementById('app').style.display='block';i=ITEMS.findIndex(x=>!V[x.id]);if(i<0)i=0;render()}
function render(){const x=ITEMS[i];if(!x){return fin()}
 const opts=OPT[x.type];const cur=V[x.id]?V[x.id].v:(x.type==='EXPERT'?x.tent:'');
 let h=`<div><span class=tag>${x.pair}</span><span class=tag>${x.type==='EXPERT'?'전문가 지적':'②AI 지적'}</span>${x.cat?'<span class=tag>'+x.cat+'</span>':''}</div>
 <div class=q>${esc(x.item)}</div>`;
 if(x.type==='EXPERT'&&x.cand)h+=`<div class=hint>②가 잡은 것(AI 잠정): <b>${esc(x.cand)}</b><br><small>AI 잠정판정: ${x.tent} — 동의하면 그대로 '다음'</small></div>`;
 if(x.type==='AI')h+=`<div class=hint><small>②가 든 이 지적이 타당한가요?</small></div>`;
 h+=`<div class=btns>`+opts.map(o=>`<button class="opt ${cur===o[0]?'sel':''}" onclick="pick('${o[0]}')">${o[1]}</button>`).join('')+`</div>`;
 h+=`<input class=note id=nt placeholder="메모(선택)" value="${V[x.id]?esc(V[x.id].n||''):''}" oninput="V['${x.id}']&&(V['${x.id}'].n=this.value,save())">`;
 document.getElementById('card').innerHTML=h;
 const done=Object.keys(V).length;document.getElementById('fill').style.width=(done/ITEMS.length*100)+'%';
 document.getElementById('pct').textContent=`(${i+1}/${ITEMS.length} · 완료 ${done})`}
function pick(v){const x=ITEMS[i];V[x.id]={v,n:(V[x.id]?V[x.id].n:'')||(document.getElementById('nt')?document.getElementById('nt').value:'')};save();setTimeout(next,150)}
function save(){localStorage.setItem(K(),JSON.stringify(V))}
function next(){if(i<ITEMS.length-1){i++;render()}else fin()}
function prev(){if(i>0){i--;render()}}
function fin(){document.getElementById('app').style.display='none';document.getElementById('fin').style.display='block';
 document.getElementById('fill').style.width='100%'}
function download(){const out={judge,verdicts:ITEMS.map(x=>({id:x.id,pair:x.pair,type:x.type,item:x.item,verdict:(V[x.id]||{}).v||'',note:(V[x.id]||{}).n||''}))};
 const b=new Blob([JSON.stringify(out,null,2)],{type:'application/json'});const a=document.createElement('a');
 a.href=URL.createObjectURL(b);a.download='adjudication_'+judge+'.json';a.click()}
function esc(s){return (s||'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
</script></body></html>"""
HTML = HTML.replace("__ITEMS__", json.dumps(items, ensure_ascii=False)).replace("__NEXP__", str(n_exp))
(OUT / "adjudicate.html").write_text(HTML, encoding="utf-8")
print(f"✅ {OUT}/adjudicate.html · 전문가지적 {n_exp} + ②지적 {len(items)-n_exp} = {len(items)}문항")
print("→ 이 HTML 하나를 교수 3명에게 이메일. 각자 열기→이름→클릭→내려받기→회신.")
