"""
build_board.py

Validate docs/kanban/tickets.json and generate:
 - index.html (self-contained board)
 - BOARD.md
 - TICKETS.md

Uses Python 3 standard library only.
"""
import json
import os
import sys
from datetime import datetime

# Configuration
ROOT = os.path.dirname(__file__)
KANBAN_DIR = ROOT
TICKETS_PATH = os.path.join(KANBAN_DIR, 'tickets.json')

VALID_STATUSES = {'backlog': 'Backlog', 'todo': 'To Do', 'progress': 'In Progress', 'review': 'In Review', 'done': 'Done'}


def load_tickets(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def validate(data):
    errors = []
    # project and goal
    if 'project' not in data or not data['project']:
        errors.append('Missing project name')
    if 'goal' not in data or not data['goal']:
        errors.append('Missing goal')
    # epics
    epic_keys = {e['key'] for e in data.get('epics', [])}
    if not epic_keys:
        errors.append('No epics defined')
    # tickets
    ids = set()
    for t in data.get('tickets', [])[:]:
        ids.add(t.get('id'))
    if not ids:
        errors.append('No tickets found')

    for t in data.get('tickets', []):
        tid = t.get('id')
        if not tid:
            errors.append('Ticket missing id')
            continue
        # status
        status = t.get('status')
        if status not in VALID_STATUSES:
            errors.append(f"Ticket {tid} has invalid status '{status}'")
        # epic
        epic = t.get('epic')
        if epic not in epic_keys:
            errors.append(f"Ticket {tid} references unknown epic '{epic}'")
        # priority
        if t.get('priority') not in ('High', 'Medium', 'Low'):
            errors.append(f"Ticket {tid} has invalid priority '{t.get('priority')}'")
        # points
        pts = t.get('points')
        if not isinstance(pts, int) or pts < 0:
            errors.append(f"Ticket {tid} has invalid points '{pts}'")
        # depends
        for d in t.get('depends', []):
            if d and d not in ids:
                errors.append(f"Ticket {tid} depends on unknown ticket '{d}'")
        # acceptance
        ac = t.get('acceptance')
        if not isinstance(ac, list) or len(ac) == 0:
            errors.append(f"Ticket {tid} must have at least one acceptance criterion")
    return errors


def md_board(data):
    # Build BOARD.md table with columns for statuses
    columns = ['Backlog', 'To Do', 'In Progress', 'In Review', 'Done']
    status_map = {v: k for k, v in VALID_STATUSES.items()}
    buckets = {col: [] for col in columns}
    for t in data['tickets']:
        col = VALID_STATUSES.get(t['status'])
        if not col:
            col = 'Backlog'
        buckets[col].append(f"{t['id']} {t['title']} [{t['points']}]")
    # Build markdown
    md_lines = []
    md_lines.append(f"# Kanban board — {data.get('project')}\n")
    md_lines.append('| ' + ' | '.join(columns) + ' |')
    md_lines.append('|' + ' --- |' * len(columns))
    # max rows
    maxr = max(len(buckets[c]) for c in columns)
    for i in range(maxr):
        row = []
        for c in columns:
            row.append(buckets[c][i] if i < len(buckets[c]) else '')
        md_lines.append('| ' + ' | '.join(row) + ' |')
    md_lines.append('\nGenerated: ' + datetime.utcnow().isoformat() + 'Z')
    return '\n'.join(md_lines)


def md_tickets(data):
    # Group by epic
    epic_map = {e['key']: e['name'] for e in data['epics']}
    tickets_by_epic = {k: [] for k in epic_map}
    for t in data['tickets']:
        tickets_by_epic.setdefault(t['epic'], []).append(t)
    lines = []
    lines.append(f"# Tickets — {data.get('project')}\n")
    for key, name in epic_map.items():
        lines.append(f"## {key} {name}\n")
        ts = tickets_by_epic.get(key, [])
        if not ts:
            lines.append('_No tickets_\n')
            continue
        for t in ts:
            lines.append(f"### {t['id']} — {t['title']}")
            lines.append(f"- Status: {t['status']}")
            lines.append(f"- Priority: {t['priority']}")
            lines.append(f"- Points: {t['points']}")
            deps = t.get('depends') or []
            lines.append(f"- Depends: {', '.join(deps) if deps else 'None'}")
            if t.get('blocked'):
                lines.append(f"- Blocked: {t.get('blocked')}")
            lines.append('\n' + t.get('description', '').strip() + '\n')
            lines.append('Acceptance criteria:')
            for ac in t.get('acceptance', []):
                lines.append(f"- [ ] {ac}")
            lines.append('\n')
    lines.append('Generated: ' + datetime.utcnow().isoformat() + 'Z')
    return '\n'.join(lines)


def generate_index_html(data):
    # Embed tickets data into the page for a self-contained board
    tickets_json = json.dumps(data, ensure_ascii=False)
    html = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{data.get('project')} — Kanban</title>
<style>
:root{{--bg:#f6f8fa;--card:#fff;--muted:#6b7280;--accent:#0b5fff}}
@media (prefers-color-scheme: dark){{:root{{--bg:#0b1220;--card:#071021;--muted:#9aa4b2;--accent:#6ea8ff}}}}
body{{margin:0;font-family:system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;background:var(--bg);color:var(--muted)}}
.header{{padding:1rem;display:flex;align-items:center;gap:1rem}}
.board-container{{overflow:auto;padding:1rem}}
.board{{display:flex;gap:1rem;min-width:900px}}
.column{{background:rgba(255,255,255,0.04);border-radius:8px;padding:8px;flex:1;min-width:220px}}
.col-title{{font-weight:600;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center}}
.card{{background:var(--card);padding:8px;border-radius:6px;margin-bottom:8px;cursor:grab;color:inherit;box-shadow:0 1px 2px rgba(0,0,0,0.06)}}
.card.dragging{{opacity:0.6}}
.toolbar{{display:flex;gap:.5rem;align-items:center}}
.search{{padding:.5rem;border-radius:6px;border:1px solid rgba(0,0,0,0.08);min-width:200px}}
.detail{{position:fixed;right:1rem;top:4rem;bottom:1rem;width:320px;background:var(--card);padding:1rem;border-radius:8px;overflow:auto;box-shadow:0 6px 18px rgba(0,0,0,0.2);display:none}}
.progress{{height:10px;background:#e6eefc;border-radius:6px;overflow:hidden}}
.progress > i{{display:block;height:100%;background:var(--accent);width:0%}}
.chips{display:flex;gap:.5rem;flex-wrap:wrap}
.chip{padding:6px 10px;border-radius:999px;background:rgba(0,0,0,0.06);cursor:pointer}
.footer{padding:1rem}
@media (max-width:600px){.board{min-width:800px}}
</style>
</head>
<body>
<div class="header">
  <div style="flex:1">
    <h2 style="margin:0">{data.get('project')}</h2>
    <div style="font-size:0.9rem;color:var(--muted)">{data.get('goal')}</div>
  </div>
  <div class="toolbar">
    <input class="search" placeholder="Search tickets..." id="search">
    <div class="chips" id="epic-chips"></div>
    <button id="copy-md">Copy all as Markdown</button>
    <button id="reset">Reset</button>
  </div>
</div>
<div style="padding:0 1rem">
  <div class="progress" title="Overall progress"><i id="progress-bar"></i></div>
</div>
<div class="board-container">
  <div class="board" id="board"></div>
</div>
<div class="detail" id="detail"></div>
<div class="footer" id="footer"></div>
<script>
const DATA = {tickets_json};
const STATUS_ORDER = ['backlog','todo','progress','review','done'];
const STATUS_LABEL = {json.dumps(VALID_STATUSES)};
let state = null;

function loadState(){
  try{const s=localStorage.getItem('kanban_state');if(s){state=JSON.parse(s);return}}
  catch(e){console.warn('localStorage load failed',e)}
  // initial grouping by status
  state = {tickets: DATA.tickets.map(t=>Object.assign({},t))};
}

function saveState(){
  try{localStorage.setItem('kanban_state', JSON.stringify(state));}catch(e){console.warn('localStorage save failed',e)}
}

function render(){
  const board = document.getElementById('board');board.innerHTML='';
  const search = document.getElementById('search').value.toLowerCase();
  const epicFilter = new Set(Array.from(document.querySelectorAll('.chip.active')).map(el=>el.dataset.epic));

  const counts = {backlog:0,todo:0,progress:0,review:0,done:0};
  const points = {backlog:0,todo:0,progress:0,review:0,done:0};

  for(const s of STATUS_ORDER){
    const col = document.createElement('div');col.className='column';col.dataset.status=s;
    const title = document.createElement('div');title.className='col-title';
    const label = document.createElement('div');label.textContent = STATUS_LABEL[s] || s;title.appendChild(label);
    const meta = document.createElement('div');meta.style.fontSize='0.8rem';meta.style.color='var(--muted)';title.appendChild(meta);
    col.appendChild(title);
    const list = document.createElement('div');list.className='list';list.ondragover = ev=>ev.preventDefault();list.ondrop = ev=>onDrop(ev,s);

    for(const t of state.tickets.filter(tt=>tt.status===s)){
      if(search && !(t.id+t.title+t.description).toLowerCase().includes(search)) continue;
      if(epicFilter.size && !epicFilter.has(t.epic)) continue;
      const card = document.createElement('div');card.className='card';card.draggable=true;card.dataset.id=t.id;card.ondragstart=onDragStart;card.ondragend=onDragEnd;
      card.innerHTML = `<div style="font-weight:600">${t.id} ${t.title} <span style=\"float:right;color:var(--muted)\">[${t.points}]</span></div><div style=\"font-size:0.85rem;color:var(--muted)\">${t.priority} • ${t.epic}</div>`;
      card.onclick = ()=>openDetail(t.id);
      list.appendChild(card);
      counts[s] += 1; points[s] += (Number(t.points)||0);
    }
    meta.textContent = counts[s] + ' / ' + points[s] + 'pts';
    col.appendChild(list);
    board.appendChild(col);
  }
  // progress bar
  const total = STATUS_ORDER.reduce((acc,s)=>acc+points[s],0);
  const done = points['done']||0;
  const pct = total?Math.round(done/total*100):0;
  document.getElementById('progress-bar').style.width = pct+'%';
  document.getElementById('footer').textContent = `Cards: ${Object.values(counts).reduce((a,b)=>a+b,0)} • Points: ${total} • ${pct}% done`;
}

let dragId = null;
function onDragStart(ev){dragId = ev.target.dataset.id; ev.target.classList.add('dragging');}
function onDragEnd(ev){ev.target.classList.remove('dragging');}
function onDrop(ev, targetStatus){
  ev.preventDefault();
  const t = state.tickets.find(x=>x.id===dragId);
  if(!t) return;
  t.status = targetStatus;
  saveState(); render();
}

function openDetail(id){
  const t = state.tickets.find(x=>x.id===id); if(!t) return;
  const d = document.getElementById('detail'); d.style.display='block'; d.innerHTML='';
  const h = document.createElement('h3'); h.textContent = t.id + ' — ' + t.title; d.appendChild(h);
  const meta = document.createElement('div'); meta.style.color='var(--muted)'; meta.innerHTML = `<div>${t.priority} • ${t.epic} • ${STATUS_LABEL[t.status]||t.status}</div>`; d.appendChild(meta);
  d.appendChild(document.createElement('hr'));
  const desc = document.createElement('div'); desc.innerText = t.description; d.appendChild(desc);
  d.appendChild(document.createElement('hr'));
  const acTitle = document.createElement('div'); acTitle.textContent = 'Acceptance criteria'; d.appendChild(acTitle);
  const ul = document.createElement('div');
  t.acceptance.forEach((a,i)=>{ const cb = document.createElement('div'); cb.innerHTML = `<label><input type=checkbox data-ac="${i}"> ${a}</label>`; ul.appendChild(cb); });
  d.appendChild(ul);
  d.appendChild(document.createElement('hr'));
  const deps = document.createElement('div'); deps.innerHTML = '<b>Depends:</b> ' + (t.depends && t.depends.length? t.depends.join(', '):'None'); d.appendChild(deps);
  if(t.blocked) { const b = document.createElement('div'); b.style.color='crimson'; b.textContent = 'Blocked: '+t.blocked; d.appendChild(b); }
  // status selector
  const sel = document.createElement('select'); for(const s of Object.keys(STATUS_LABEL)){ const o = document.createElement('option'); o.value=s; o.textContent=STATUS_LABEL[s]; if(s===t.status) o.selected=true; sel.appendChild(o); }
  sel.onchange = ()=>{ t.status = sel.value; saveState(); render(); };
  d.appendChild(document.createElement('div')).appendChild(sel);
  const close = document.createElement('button'); close.textContent='Close'; close.onclick=()=>d.style.display='none'; d.appendChild(close);
}

function setupChips(){
  const container = document.getElementById('epic-chips');
  DATA.epics.forEach(e=>{
    const c = document.createElement('div'); c.className='chip'; c.textContent = e.key; c.dataset.epic = e.key; c.onclick = ()=>{ c.classList.toggle('active'); render(); }; container.appendChild(c);
  });
}

function copyAsMarkdown(){
  // Build a simple markdown representation
  let md = `# ${DATA.project} — Kanban\n\n`;
  for(const k of STATUS_ORDER){ md += '## ' + (STATUS_LABEL[k]||k) + '\n\n'; for(const t of state.tickets.filter(x=>x.status===k)){ md += `- ${t.id} ${t.title} [${t.points}]\n`; } md += '\n'; }
  navigator.clipboard.writeText(md).then(()=>alert('Copied markdown to clipboard')).catch(e=>{ prompt('Copy the markdown below', md); });
}

function resetState(){
  if(confirm('Reset board state to original positions?')){ localStorage.removeItem('kanban_state'); loadState(); render(); }
}

function init(){
  loadState(); setupChips(); render();
  document.getElementById('copy-md').onclick = copyAsMarkdown;
  document.getElementById('reset').onclick = resetState;
  document.getElementById('search').oninput = ()=>render();
}

init();
</script>
</body>
</html>
'''
    return html


def main():
    # find tickets
    if not os.path.exists(TICKETS_PATH):
        print('tickets.json not found at', TICKETS_PATH)
        sys.exit(2)
    data = load_tickets(TICKETS_PATH)
    errs = validate(data)
    if errs:
        print('Validation failed with errors:')
        for e in errs:
            print('-', e)
        sys.exit(3)
    # generate
    board_md = md_board(data)
    tickets_md = md_tickets(data)
    index_html = generate_index_html(data)
    # write outputs
    with open(os.path.join(KANBAN_DIR, 'BOARD.md'), 'w', encoding='utf-8') as f:
        f.write(board_md)
    with open(os.path.join(KANBAN_DIR, 'TICKETS.md'), 'w', encoding='utf-8') as f:
        f.write(tickets_md)
    with open(os.path.join(KANBAN_DIR, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(index_html)
    print('Generated BOARD.md, TICKETS.md, index.html in', KANBAN_DIR)

if __name__=='__main__':
    main()
