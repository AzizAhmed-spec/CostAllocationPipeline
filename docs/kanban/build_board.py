#!/usr/bin/env python3
"""Generate the kanban board views from tickets.json.

Usage (from the repo root):
    python3 docs/kanban/build_board.py

Reads  docs/kanban/tickets.json  (the single source of truth) and writes:
    docs/kanban/index.html   interactive board (open in a browser)
    docs/kanban/BOARD.md     column overview that renders on GitHub
    docs/kanban/TICKETS.md   every ticket with description and acceptance criteria
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = json.loads((HERE / "tickets.json").read_text(encoding="utf-8"))

COLUMNS = [
    ("backlog", "Backlog"),
    ("todo", "To Do"),
    ("progress", "In Progress"),
    ("review", "In Review"),
    ("done", "Done"),
]
EPIC_NAMES = {e["key"]: e["name"] for e in DATA["epics"]}


def validate():
    ids = {t["id"] for t in DATA["tickets"]}
    statuses = {k for k, _ in COLUMNS}
    for t in DATA["tickets"]:
        assert t["status"] in statuses, f'{t["id"]}: bad status {t["status"]}'
        assert t["epic"] in EPIC_NAMES, f'{t["id"]}: bad epic {t["epic"]}'
        assert t["acceptance"], f'{t["id"]}: no acceptance criteria'
        for d in t["depends"]:
            assert d in ids, f'{t["id"]}: unknown dependency {d}'


def build_tickets_md():
    out = [f'# {DATA["project"]}: tickets', "", DATA["goal"], ""]
    for epic in DATA["epics"]:
        out += [f'## {epic["name"]}', ""]
        for t in (x for x in DATA["tickets"] if x["epic"] == epic["key"]):
            status = dict(COLUMNS)[t["status"]]
            out += [
                f'### {t["id"]}: {t["title"]}',
                "",
                f'**Status:** {status} | **Priority:** {t["priority"]} | **Points:** {t["points"]}'
                + (f' | **Blocked:** {t["blocked"]}' if t.get("blocked") else ""),
                "",
                f'**Depends on:** {", ".join(t["depends"]) if t["depends"] else "none"}',
                "",
                "**Description**",
                "",
                t["description"],
                "",
                "**Acceptance criteria**",
                "",
            ]
            out += [f"- [ ] {a}" for a in t["acceptance"]]
            out.append("")
    (HERE / "TICKETS.md").write_text("\n".join(out), encoding="utf-8")


def build_board_md():
    cols = {k: [t for t in DATA["tickets"] if t["status"] == k] for k, _ in COLUMNS}
    total = sum(t["points"] for t in DATA["tickets"])
    done = sum(t["points"] for t in cols["done"])
    out = [
        f'# {DATA["project"]}: board',
        "",
        f'{len(DATA["tickets"])} tickets, {total} story points, {done} points done. '
        "Full descriptions and acceptance criteria are in [TICKETS.md](TICKETS.md). "
        "Open [index.html](index.html) in a browser for the interactive board.",
        "",
    ]
    header = " | ".join(f"{name} ({len(cols[k])})" for k, name in COLUMNS)
    out += [f"| {header} |", "|" + " --- |" * len(COLUMNS)]
    for i in range(max(len(v) for v in cols.values())):
        cells = []
        for k, _ in COLUMNS:
            if i < len(cols[k]):
                t = cols[k][i]
                flag = " (blocked)" if t.get("blocked") else ""
                cells.append(f'**{t["id"]}** {t["title"]} [{t["points"]}]{flag}')
            else:
                cells.append(" ")
        out.append("| " + " | ".join(cells) + " |")
    out += ["", "Numbers in square brackets are story points.", ""]
    (HERE / "BOARD.md").write_text("\n".join(out), encoding="utf-8")


def build_html():
    payload = json.dumps(
        {"project": DATA["project"], "goal": DATA["goal"], "epics": DATA["epics"],
         "columns": COLUMNS, "tickets": DATA["tickets"]},
        ensure_ascii=False,
    ).replace("</", "<\\/")
    (HERE / "index.html").write_text(HTML.replace("__DATA__", payload), encoding="utf-8")


HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>FinOps Allocation Board</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@500&family=IBM+Plex+Sans+Condensed:wght@600&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<style>
/* Layout: sticky summary header, five status columns that scroll sideways on small screens, detail drawer on the right. */
:root{
  --bg:#EEF1F3; --surface:#FFFFFF; --col:#E4E9ED; --ink:#15212B; --ink2:#4A5A67; --line:#D0D9DF;
  --accent:#0E6F66; --accent-ink:#FFFFFF; --warn:#A85F08; --ok:#2E7D4F; --hi:#B3362B; --med:#A85F08; --lo:#5B7183;
  --e-ARCH:#5B6BC0; --e-ING:#C2571A; --e-FOC:#0E8A7D; --e-MED:#7B4FB3; --e-ALL:#A8307A; --e-API:#2F7DB8; --e-OPS:#6B7A1F; --e-VAL:#8A6D12;
  --font:'IBM Plex Sans',system-ui,sans-serif; --display:'IBM Plex Sans Condensed','IBM Plex Sans',system-ui,sans-serif; --mono:'IBM Plex Mono',ui-monospace,monospace;
}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){
  --bg:#0F171D; --surface:#17222A; --col:#1B2831; --ink:#E6EDF1; --ink2:#9FB0BC; --line:#2A3A45;
  --accent:#3CC1B2; --accent-ink:#06211E; --warn:#E0A04A; --ok:#5BC083; --hi:#F08A80; --med:#E0A04A; --lo:#8FA4B4;
  --e-ARCH:#8E9BE6; --e-ING:#F0955C; --e-FOC:#46C4B6; --e-MED:#B58BE6; --e-ALL:#E57DBB; --e-API:#6BB3E6; --e-OPS:#B2C25A; --e-VAL:#D8B84F; color-scheme:dark}}
:root[data-theme="dark"]{
  --bg:#0F171D; --surface:#17222A; --col:#1B2831; --ink:#E6EDF1; --ink2:#9FB0BC; --line:#2A3A45;
  --accent:#3CC1B2; --accent-ink:#06211E; --warn:#E0A04A; --ok:#5BC083; --hi:#F08A80; --med:#E0A04A; --lo:#8FA4B4;
  --e-ARCH:#8E9BE6; --e-ING:#F0955C; --e-FOC:#46C4B6; --e-MED:#B58BE6; --e-ALL:#E57DBB; --e-API:#6BB3E6; --e-OPS:#B2C25A; --e-VAL:#D8B84F; color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 var(--font);padding-block:20px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}
header{display:flex;flex-wrap:wrap;gap:14px 28px;align-items:flex-end;justify-content:space-between;margin-bottom:14px}
h1{font:600 26px/1.1 var(--display);letter-spacing:.01em;margin:0 0 6px;text-wrap:balance}
.flow{margin:0;color:var(--ink2);font-size:13px;max-width:70ch}
.stats{display:flex;gap:22px;flex-wrap:wrap}
.stat b{display:block;font:500 20px/1 var(--mono);font-variant-numeric:tabular-nums}
.stat span{font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--ink2)}
.bar{height:6px;background:var(--col);border-radius:3px;overflow:hidden;margin:2px 0 14px}
.bar i{display:block;height:100%;background:var(--ok)}
.tools{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-bottom:14px}
.tools input[type=search]{font:inherit;color:var(--ink);background:var(--surface);border:1px solid var(--line);border-radius:6px;padding:6px 10px;min-width:180px}
.chip,.btn{font:inherit;font-size:12px;color:var(--ink);background:var(--surface);border:1px solid var(--line);border-radius:999px;padding:4px 10px;cursor:pointer;display:inline-flex;align-items:center;gap:6px}
.btn{border-radius:6px;padding:6px 10px}
.chip[aria-pressed=true]{background:var(--ink);color:var(--bg);border-color:var(--ink)}
.dot{width:8px;height:8px;border-radius:50%;background:var(--c,var(--ink2));flex:none}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.board{display:grid;grid-template-columns:repeat(5,minmax(250px,1fr));gap:12px;overflow-x:auto;padding-bottom:8px;align-items:start}
.colm{background:var(--col);border-radius:8px;padding:10px;min-height:120px;min-width:0}
.colm.over{outline:2px dashed var(--accent)}
.colh{display:flex;justify-content:space-between;align-items:baseline;margin:0 2px 10px;font:600 13px var(--display);letter-spacing:.06em;text-transform:uppercase}
.colh small{font:500 11px var(--mono);color:var(--ink2);letter-spacing:0}
.cards{display:flex;flex-direction:column;gap:8px}
.card{background:var(--surface);border:1px solid var(--line);border-radius:6px;padding:10px 11px;cursor:pointer;text-align:left;width:100%;font:inherit;color:inherit;min-width:0}
.card:hover{border-color:var(--accent)}
.card.drag{opacity:.4}
.top{display:flex;justify-content:space-between;gap:8px;align-items:center;margin-bottom:6px}
.id{font:500 11px var(--mono);color:var(--ink2)}
.ep{display:inline-flex;align-items:center;gap:5px;font-size:11px;color:var(--ink2)}
.ct{display:block;font-weight:500;overflow-wrap:anywhere}
.meta{display:flex;gap:10px;align-items:center;margin-top:8px;font-size:11px;color:var(--ink2);font-variant-numeric:tabular-nums}
.pr{display:inline-flex;align-items:center;gap:4px}
.blk{color:var(--warn);font-weight:600}
.empty{font-size:12px;color:var(--ink2);padding:8px 2px}
#ov{position:fixed;inset:0;background:rgba(0,0,0,.45);z-index:20}
#dr{position:fixed;top:0;right:0;bottom:0;width:min(560px,100%);background:var(--surface);z-index:21;overflow-y:auto;border-left:1px solid var(--line);padding-block:max(18px,env(safe-area-inset-top,0px)) max(18px,env(safe-area-inset-bottom,0px));padding-left:20px;padding-right:max(20px,env(safe-area-inset-right,0px))}
#dr h2{font:600 22px/1.2 var(--display);margin:6px 0 10px;text-wrap:balance}
#dr h3{font:600 11px var(--mono);text-transform:uppercase;letter-spacing:.1em;color:var(--ink2);margin:18px 0 6px}
#dr p{margin:0;max-width:65ch}
.row{display:flex;flex-wrap:wrap;gap:8px 14px;align-items:center;font-size:12px;color:var(--ink2)}
.ac{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:8px}
.ac label{display:flex;gap:9px;align-items:flex-start;cursor:pointer}
.ac input{margin-top:3px;accent-color:var(--accent)}
.ac input:checked+span{color:var(--ink2);text-decoration:line-through}
select{font:inherit;color:var(--ink);background:var(--surface);border:1px solid var(--line);border-radius:6px;padding:5px 8px}
.x{float:right}
.warnbox{margin-top:10px;font-size:13px;color:var(--warn);font-weight:500}
[hidden]{display:none!important}
@media (prefers-reduced-motion:no-preference){.card{transition:border-color .15s}}
</style>
</head>
<body>
<header>
  <div>
    <h1 id="title"></h1>
    <p class="flow" id="goal"></p>
  </div>
  <div class="stats" id="stats"></div>
</header>
<div class="bar" aria-hidden="true"><i id="prog"></i></div>
<div class="tools">
  <input type="search" id="q" placeholder="Search tickets" aria-label="Search tickets">
  <span id="chips" style="display:flex;flex-wrap:wrap;gap:6px"></span>
  <button class="btn" id="copy">Copy all as Markdown</button>
  <button class="btn" id="reset">Reset board</button>
  <span id="msg" class="id" role="status"></span>
</div>
<main class="board" id="board"></main>
<div id="ov" hidden></div>
<aside id="dr" role="dialog" aria-modal="true" aria-label="Ticket details" hidden></aside>
<script>
var D=__DATA__;
var KEY='finops-board-v1';
var st={status:{},ac:{}};
try{var s=JSON.parse(localStorage.getItem(KEY)||'null');if(s){st=s}}catch(e){}
function save(){try{localStorage.setItem(KEY,JSON.stringify(st))}catch(e){}}
function status(t){return st.status[t.id]||t.status}
function acs(t){var a=st.ac[t.id]||[];return t.acceptance.map(function(_,i){return !!a[i]})}
var epic={};D.epics.forEach(function(e){epic[e.key]=e.name});
var filter='all',query='',openId=null,ids={};D.tickets.forEach(function(t){ids[t.id]=t});
function esc(s){return String(s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
function pri(p){return p==='High'?'--hi':p==='Medium'?'--med':'--lo'}
function visible(t){
  if(filter!=='all'&&t.epic!==filter)return false;
  if(!query)return true;
  return (t.id+' '+t.title+' '+t.description).toLowerCase().indexOf(query)>-1;
}
function renderStats(){
  var tot=0,done=0,n=D.tickets.length,dn=0;
  D.tickets.forEach(function(t){tot+=t.points;if(status(t)==='done'){done+=t.points;dn++}});
  document.getElementById('stats').innerHTML=
   '<div class="stat"><b>'+n+'</b><span>Tickets</span></div>'+
   '<div class="stat"><b>'+done+'/'+tot+'</b><span>Points done</span></div>'+
   '<div class="stat"><b>'+Math.round(100*done/tot)+'%</b><span>Complete</span></div>';
  document.getElementById('prog').style.width=(100*done/tot)+'%';
}
function renderChips(){
  var h='<button class="chip" data-e="all" aria-pressed="'+(filter==='all')+'">All epics</button>';
  D.epics.forEach(function(e){h+='<button class="chip" data-e="'+e.key+'" aria-pressed="'+(filter===e.key)+'" style="--c:var(--e-'+e.key+')"><i class="dot"></i>'+esc(e.name)+'</button>'});
  document.getElementById('chips').innerHTML=h;
}
function renderBoard(){
  var h='';
  D.columns.forEach(function(c){
    var list=D.tickets.filter(function(t){return status(t)===c[0]&&visible(t)});
    var pts=list.reduce(function(a,t){return a+t.points},0);
    h+='<section class="colm" data-col="'+c[0]+'" aria-label="'+c[1]+'"><div class="colh"><span>'+c[1]+'</span><small>'+list.length+' · '+pts+' pts</small></div><div class="cards">';
    if(!list.length)h+='<div class="empty">No tickets</div>';
    list.forEach(function(t){
      var a=acs(t),dn=a.filter(Boolean).length;
      h+='<button class="card" draggable="true" data-id="'+t.id+'" style="--c:var(--e-'+t.epic+')">'+
        '<div class="top"><span class="id">'+t.id+'</span><span class="ep"><i class="dot"></i>'+esc(epic[t.epic])+'</span></div>'+
        '<span class="ct">'+esc(t.title)+'</span>'+
        '<div class="meta"><span class="pr"><i class="dot" style="background:var('+pri(t.priority)+')"></i>'+t.priority+'</span><span>'+t.points+' pts</span><span>'+dn+'/'+a.length+' criteria</span>'+(t.blocked?'<span class="blk">Blocked</span>':'')+'</div></button>';
    });
    h+='</div></section>';
  });
  document.getElementById('board').innerHTML=h;
}
function render(){renderStats();renderChips();renderBoard();if(openId)drawer(openId)}
function drawer(id){
  var t=ids[id];openId=id;var a=acs(t);
  var opts=D.columns.map(function(c){return '<option value="'+c[0]+'"'+(status(t)===c[0]?' selected':'')+'>'+c[1]+'</option>'}).join('');
  var deps=t.depends.length?t.depends.map(function(d){return '<button class="chip" data-open="'+d+'">'+d+' '+esc(ids[d].title)+'</button>'}).join(' '):'None';
  document.getElementById('dr').innerHTML=
   '<button class="btn x" id="close">Close</button>'+
   '<div class="row"><span class="id">'+t.id+'</span><span class="ep" style="--c:var(--e-'+t.epic+')"><i class="dot"></i>'+esc(epic[t.epic])+'</span></div>'+
   '<h2>'+esc(t.title)+'</h2>'+
   '<div class="row"><label>Status <select id="stsel">'+opts+'</select></label><span>Priority: '+t.priority+'</span><span>'+t.points+' points</span></div>'+
   (t.blocked?'<div class="warnbox">Blocked: '+esc(t.blocked)+'</div>':'')+
   '<h3>Description</h3><p>'+esc(t.description)+'</p>'+
   '<h3>Acceptance criteria</h3><ul class="ac">'+t.acceptance.map(function(x,i){return '<li><label><input type="checkbox" data-i="'+i+'"'+(a[i]?' checked':'')+'><span>'+esc(x)+'</span></label></li>'}).join('')+'</ul>'+
   '<h3>Depends on</h3><div class="row">'+deps+'</div>';
  document.getElementById('dr').hidden=false;document.getElementById('ov').hidden=false;
  document.getElementById('close').focus();
}
function closeDrawer(){openId=null;document.getElementById('dr').hidden=true;document.getElementById('ov').hidden=true}
function move(id,col){st.status[id]=col;save();render()}
document.addEventListener('click',function(e){
  var c=e.target.closest('.card');if(c){drawer(c.dataset.id);return}
  var ch=e.target.closest('.chip[data-e]');if(ch){filter=ch.dataset.e;render();return}
  var o=e.target.closest('[data-open]');if(o){drawer(o.dataset.open);return}
  if(e.target.id==='close'||e.target.id==='ov')closeDrawer();
});
document.addEventListener('keydown',function(e){if(e.key==='Escape'&&openId)closeDrawer()});
document.addEventListener('change',function(e){
  if(e.target.id==='stsel'){move(openId,e.target.value)}
  else if(e.target.matches('.ac input')){
    var a=st.ac[openId]||[];a[+e.target.dataset.i]=e.target.checked;st.ac[openId]=a;save();
    renderBoard();renderStats();
  }
});
document.getElementById('q').addEventListener('input',function(e){query=e.target.value.trim().toLowerCase();renderBoard()});
var dragId=null;
document.addEventListener('dragstart',function(e){var c=e.target.closest&&e.target.closest('.card');if(c){dragId=c.dataset.id;c.classList.add('drag');e.dataTransfer.setData('text/plain',dragId);e.dataTransfer.effectAllowed='move'}});
document.addEventListener('dragend',function(){dragId=null;render()});
document.addEventListener('dragover',function(e){var c=e.target.closest&&e.target.closest('.colm');if(c&&dragId){e.preventDefault();document.querySelectorAll('.colm').forEach(function(x){x.classList.toggle('over',x===c)})}});
document.addEventListener('drop',function(e){var c=e.target.closest&&e.target.closest('.colm');if(c&&dragId){e.preventDefault();move(dragId,c.dataset.col)}});
function md(){
  var out=['# '+D.project,'',D.goal,''];
  D.epics.forEach(function(ep){
    out.push('## '+ep.name,'');
    D.tickets.filter(function(t){return t.epic===ep.key}).forEach(function(t){
      out.push('### '+t.id+': '+t.title,'','Priority: '+t.priority+' | Points: '+t.points+' | Depends on: '+(t.depends.join(', ')||'none'),'',t.description,'','Acceptance criteria:');
      t.acceptance.forEach(function(a){out.push('- [ ] '+a)});out.push('');
    });
  });
  return out.join('\n');
}
function note(m){var el=document.getElementById('msg');el.textContent=m;setTimeout(function(){el.textContent=''},2500)}
document.getElementById('copy').addEventListener('click',function(){
  var text=md();
  var fallback=function(){var ta=document.createElement('textarea');ta.value=text;document.body.appendChild(ta);ta.select();try{document.execCommand('copy');note('Copied')}catch(e){note('Copy not available')}ta.remove()};
  if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(text).then(function(){note('Copied')},fallback)}else fallback();
});
document.getElementById('reset').addEventListener('click',function(){st={status:{},ac:{}};save();closeDrawer();render();note('Board reset')});
document.getElementById('title').textContent=D.project;
document.getElementById('goal').textContent=D.goal;
render();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    validate()
    build_tickets_md()
    build_board_md()
    build_html()
    print(f'Built board for {len(DATA["tickets"])} tickets in {HERE}')
