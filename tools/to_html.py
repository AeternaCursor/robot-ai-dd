import re, html, sys, datetime
# 用法: python to_html.py 输入.txt 输出.html [日期]
P, O = sys.argv[1], sys.argv[2]
DATE = sys.argv[3] if len(sys.argv) > 3 else datetime.date.today().isoformat()
L = open(P, encoding='utf-8').read().lstrip('\ufeff').split('\n')
skip = {'【传动与关节类】', '【感知类】', '【芯片类】', '【材料与连接类】', '【财务与资本市场类】'}
E = html.escape
body = []; toc = []  # toc: (level, id, title)
sec_open = False; ent_open = False; nsec = ncomp = 0
def close_ent():
    global ent_open
    if ent_open: body.append('</div></details>'); ent_open = False
def close_sec():
    global sec_open
    close_ent()
    if sec_open: body.append('</div></details>'); sec_open = False
def open_sec(title):
    global sec_open, nsec
    close_sec(); nsec += 1
    sid = f's{nsec}'
    toc.append((1, sid, title))
    body.append(f'<details class="sec" id="{sid}" open><summary><h2>{E(title)}</h2></summary><div class="sb">')
    sec_open = True
i = 0
while i < len(L):
    s = L[i].strip()
    nxt = L[i + 1].strip() if i + 1 < len(L) else ''
    # 大标题：#### 行包围
    if s and set(s) == {'#'}:
        if nxt and not set(nxt) <= {'#'} and i + 2 < len(L):
            title = nxt
            j = i + 2
            sub = []
            while j < len(L) and L[j].strip() and set(L[j].strip()) != {'#'}:
                sub.append(L[j].strip()); j += 1
            if j < len(L) and set(L[j].strip() or 'x') == {'#'}:
                open_sec(title)
                for x in sub: body.append(f'<p class="note">{E(x)}</p>')
                i = j + 1; continue
            if re.match(r'^第.部分', title):
                open_sec(title); i += 2; continue
        i += 1; continue
    m = re.match(r'^=+ ?(板块[^=]+?) ?=+$', s)
    if m:
        open_sec(m.group(1).strip()); i += 1; continue
    if s.startswith('附录') and '待核实清单' in s and sec_open is not None and i > 100:
        open_sec(s); i += 1; continue
    if s and set(s) == {'='}:
        close_ent(); i += 1; continue
    if re.match(r'^【[^】]+】$', s) and s not in skip and L[i - 1].strip().startswith('====='):
        close_ent(); ncomp += 1
        cid = f'c{ncomp}'
        toc.append((2, cid, s[1:-1]))
        body.append(f'<details class="ent" id="{cid}"><summary>{E(s[1:-1])}</summary><div class="eb">')
        ent_open = True; i += 1; continue
    if s.startswith('—— ') and s.endswith('——'):
        close_ent(); body.append(f'<h3>{E(s)}</h3>'); i += 1; continue
    if not s:
        i += 1; continue
    t = E(s)
    t = re.sub(r'(https?://[^\s，。；）)]+)', r'<a href="\1" target="_blank" rel="noopener">\1</a>', t)
    cls = ''
    if re.match(r'^0\s*[.、]?\s*一句话看懂', s): cls = ' class="one"'
    elif s.startswith('〔') or (s.startswith('【') and s in skip): cls = ' class="sub"'
    elif s.startswith('→'): cls = ' class="vf"'
    t = re.sub(r'^(\d\s*[.、．]?\s*[^：:]{1,14}[：:])', r'<b>\1</b>', t)
    body.append(f'<p{cls}>{t}</p>')
    i += 1
close_sec()
nav = []
for lv, id_, ti in toc:
    if lv == 1:
        if nav and nav[-1] != '<ul>': pass
        nav.append(f'<li class="l1"><a href="#{id_}">{E(ti)}</a></li>')
    else:
        nav.append(f'<li class="l2"><a href="#{id_}">{E(ti)}</a></li>')
CSS = '''
:root{--bg:#070b16;--panel:rgba(255,255,255,.045);--line:rgba(120,160,255,.16);--txt:#dbe4f5;--txt2:#8fa3c8;--acc:#4f8cff;--acc2:#22d3ee;--gold:#f5b544;--ok:#34d399}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;font:15px/1.75 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif;color:var(--txt);background:var(--bg);overflow-x:hidden}
body::before{content:"";position:fixed;inset:-40%;z-index:-2;pointer-events:none;background:
radial-gradient(600px 400px at 15% 10%,rgba(79,140,255,.16),transparent 60%),
radial-gradient(700px 500px at 85% 20%,rgba(34,211,238,.10),transparent 60%),
radial-gradient(800px 600px at 50% 100%,rgba(124,58,237,.12),transparent 60%);animation:aur 26s ease-in-out infinite alternate}
@keyframes aur{to{transform:translate(3%,-4%) scale(1.06)}}
body::after{content:"";position:fixed;inset:0;z-index:-1;pointer-events:none;opacity:.5;background:
repeating-linear-gradient(0deg,transparent 0 39px,rgba(140,170,255,.03) 39px 40px),
repeating-linear-gradient(90deg,transparent 0 39px,rgba(140,170,255,.03) 39px 40px)}
header{position:sticky;top:0;z-index:9;display:flex;gap:8px;align-items:center;flex-wrap:wrap;padding:10px 14px;background:rgba(10,15,30,.72);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);border-bottom:1px solid var(--line)}
header h1{font-size:15px;margin:0;flex:1 1 200px;font-weight:700;letter-spacing:.3px;background:linear-gradient(90deg,#fff,#bcd4ff 70%);-webkit-background-clip:text;background-clip:text;color:transparent}
#q{flex:1 1 220px;padding:8px 12px;border-radius:999px;border:1px solid var(--line);font-size:14px;color:var(--txt);background:rgba(255,255,255,.06);outline:none;transition:.25s}
#q::placeholder{color:var(--txt2)}#q:focus{border-color:var(--acc);box-shadow:0 0 0 3px rgba(79,140,255,.22);background:rgba(255,255,255,.09)}
header button{padding:7px 12px;border:1px solid var(--line);border-radius:999px;background:rgba(255,255,255,.05);color:var(--txt);cursor:pointer;font-size:13px;transition:.25s}
header button:hover{background:linear-gradient(90deg,var(--acc),var(--acc2));border-color:transparent;color:#fff;box-shadow:0 4px 14px rgba(79,140,255,.35)}
#cnt{font-size:12px;color:var(--acc2);white-space:nowrap}
#wrap{display:flex}
nav{width:300px;flex:none;height:calc(100vh - 52px);position:sticky;top:52px;overflow:auto;background:rgba(12,18,36,.6);backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);border-right:1px solid var(--line);font-size:13px;padding-bottom:30px}
nav::-webkit-scrollbar{width:8px}nav::-webkit-scrollbar-thumb{background:rgba(120,160,255,.25);border-radius:4px}
nav ul{list-style:none;margin:0;padding:10px}
nav li.l1{font-weight:700;margin-top:12px}nav li.l1>a{color:#e8efff;display:flex;align-items:center;gap:6px}
nav li.l1>a::before{content:"";width:6px;height:6px;border-radius:2px;flex:none;background:linear-gradient(135deg,var(--acc),var(--acc2));box-shadow:0 0 8px rgba(79,140,255,.8)}
nav li.l2{padding-left:18px}
nav a{color:var(--txt2);text-decoration:none;display:block;padding:3px 6px;border-radius:6px;transition:.18s}
nav a:hover{color:#fff;background:rgba(79,140,255,.14)}
main{flex:1;min-width:0;padding:16px 20px 60px;max-width:1000px}
details.sec{background:var(--panel);border:1px solid var(--line);border-radius:14px;margin:14px 0;box-shadow:0 10px 30px rgba(0,0,0,.35);overflow:hidden;transition:border-color .3s}
details.sec:hover{border-color:rgba(120,160,255,.35)}
details.sec>summary{cursor:pointer;padding:12px 16px;list-style:none;position:relative}
details.sec>summary::-webkit-details-marker{display:none}
details.sec>summary h2{display:inline;font-size:17px;font-weight:700;letter-spacing:.3px;background:linear-gradient(90deg,#fff,#a8c6ff);-webkit-background-clip:text;background-clip:text;color:transparent}
details.sec>summary::before{content:"▸";position:absolute;right:14px;top:11px;color:var(--acc2);transition:transform .25s}
details.sec[open]>summary::before{transform:rotate(90deg)}
details.sec>summary::after{content:"";position:absolute;left:0;right:0;bottom:0;height:1px;background:linear-gradient(90deg,transparent,rgba(79,140,255,.5),transparent)}
.sb{padding:4px 16px 14px}
details.ent{border:1px solid transparent;border-left:2px solid rgba(120,160,255,.25);border-radius:8px;margin:6px 0;background:rgba(255,255,255,.03);transition:.22s}
details.ent:hover{border-left-color:var(--acc2);background:rgba(79,140,255,.08);box-shadow:0 4px 16px rgba(0,0,0,.3)}
details.ent>summary{cursor:pointer;padding:7px 12px;font-weight:600;color:#eaf1ff;list-style:none}
details.ent>summary::-webkit-details-marker{display:none}
details.ent>summary::before{content:"◆";font-size:9px;color:var(--acc);margin-right:7px;vertical-align:1px}
details.ent[open]>summary{color:var(--acc2)}
.eb{padding:2px 14px 10px}
p{margin:5px 0;word-break:break-word}
p.one{background:linear-gradient(90deg,rgba(245,181,68,.14),rgba(245,181,68,.03));padding:7px 12px;border-radius:8px;border-left:3px solid var(--gold);color:#f4e9cf}
p.sub{font-weight:700;color:#9db9ff;margin-top:12px;letter-spacing:.5px}
p.vf{color:var(--ok);padding-left:14px}
p.note{color:var(--txt2);font-size:13.5px}
h3{color:#9db9ff;font-size:15.5px;font-weight:700;margin:18px 0 6px;display:flex;align-items:center;gap:8px}
h3::before{content:"";width:18px;height:2px;flex:none;background:linear-gradient(90deg,var(--acc),transparent)}
a{color:var(--acc2);text-decoration:none;border-bottom:1px dotted rgba(34,211,238,.5)}
a:hover{color:#7ef0ff;border-bottom-style:solid}
mark{background:linear-gradient(180deg,transparent 55%,rgba(255,214,64,.85) 55%);color:#fff;padding:0 1px;border-radius:2px}
b{color:#fff}
.hide{display:none!important}
footer{padding:24px 16px 40px;text-align:center;color:var(--txt2);font-size:12px;letter-spacing:1px}
@media(max-width:800px){
nav{position:fixed;left:0;top:0;height:100vh;z-index:20;width:82%;transform:translateX(-102%);transition:transform .3s;box-shadow:8px 0 30px rgba(0,0,0,.5)}
nav.on{transform:none}
main{padding:10px 12px 50px}
}
@media(min-width:801px){#tg{display:none}}
@media(prefers-reduced-motion:reduce){body::before{animation:none}html{scroll-behavior:auto}}
'''
JS = '''
const q=document.getElementById('q'),ents=[...document.querySelectorAll('details.ent')],secs=[...document.querySelectorAll('details.sec')];
let tm;q.addEventListener('input',()=>{clearTimeout(tm);tm=setTimeout(run,250)});
function run(){const k=q.value.trim().toLowerCase();let n=0;
document.querySelectorAll('mark').forEach(m=>m.replaceWith(m.textContent));
if(!k){ents.forEach(e=>{e.classList.remove('hide');e.open=false});secs.forEach(s=>s.classList.remove('hide'));document.getElementById('cnt').textContent='';return}
ents.forEach(e=>{const hit=e.textContent.toLowerCase().includes(k);e.classList.toggle('hide',!hit);e.open=hit&&e.querySelector('summary').textContent.toLowerCase().includes(k)||false;if(hit)n++});
secs.forEach(s=>{const hasE=s.querySelector('details.ent:not(.hide)');const self=s.textContent.toLowerCase().includes(k);s.classList.toggle('hide',!self);if(self)s.open=true});
document.getElementById('cnt').textContent='匹配公司 '+n+' 家';}
function go(id){const el=document.getElementById(id);if(!el)return;let p=el;while(p){if(p.tagName==='DETAILS'){p.open=true;p.classList.remove('hide')}p=p.parentElement}el.scrollIntoView();}
document.querySelectorAll('nav a').forEach(a=>a.addEventListener('click',ev=>{ev.preventDefault();go(a.getAttribute('href').slice(1));document.querySelector('nav').classList.remove('on')}));
document.getElementById('tg').onclick=()=>document.querySelector('nav').classList.toggle('on');
document.getElementById('ex').onclick=()=>secs.forEach(s=>s.open=!s.open);
'''
doc = f'''<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>机器人/具身智能/AI 公司尽调</title><style>{CSS}</style></head><body>
<header><button id="tg">目录</button><h1>机器人/具身智能/AI 公司尽调（{ncomp} 家，更新于 {DATE}）</h1><input id="q" placeholder="搜索公司名、关键词…"><span id="cnt"></span><button id="ex">折叠/展开板块</button></header>
<div id="wrap"><nav><ul>{''.join(nav)}</ul></nav><main>{''.join(body)}</main></div>
<footer>ROBOT / EMBODIED AI · DUE DILIGENCE · 每周自动更新 · 端到端加密</footer>
<script>{JS}</script></body></html>'''
open(O, 'w', encoding='utf-8').write(doc)
print('sections', nsec, 'companies', ncomp, 'size', len(doc))
print([ti for lv, _, ti in toc if lv == 1])
