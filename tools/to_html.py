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
*{box-sizing:border-box}body{margin:0;font:15px/1.7 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif;color:#222;background:#f6f7f9}
header{position:sticky;top:0;z-index:5;background:#1f3b63;color:#fff;padding:8px 12px;display:flex;gap:8px;align-items:center;flex-wrap:wrap}
header h1{font-size:16px;margin:0;flex:1 1 200px}#q{flex:1 1 220px;padding:7px 10px;border-radius:6px;border:0;font-size:15px}
header button{padding:6px 10px;border:0;border-radius:6px;background:#3d6fb0;color:#fff;cursor:pointer}
#wrap{display:flex}nav{width:300px;flex:none;height:calc(100vh - 50px);position:sticky;top:50px;overflow:auto;background:#fff;border-right:1px solid #ddd;font-size:13px}
nav ul{list-style:none;margin:0;padding:6px}nav li.l1{font-weight:bold;margin-top:8px}nav li.l2{padding-left:12px}nav a{color:#1f3b63;text-decoration:none}nav a:hover{text-decoration:underline}
main{flex:1;min-width:0;padding:12px 16px;max-width:1000px}
details.sec{background:#fff;border-radius:8px;margin:10px 0;box-shadow:0 1px 3px rgba(0,0,0,.08)}
details.sec>summary{cursor:pointer;padding:8px 12px;list-style:none}details.sec>summary h2{display:inline;font-size:18px;color:#1f3b63}
.sb{padding:0 12px 10px}details.ent{border:1px solid #e3e6ea;border-radius:6px;margin:6px 0}
details.ent>summary{cursor:pointer;padding:6px 10px;font-weight:bold;background:#f0f4fa}.eb{padding:4px 12px}
p{margin:4px 0;word-break:break-word}p.one{background:#fff8e1;padding:4px 8px;border-left:3px solid #f0b400}p.sub{font-weight:bold;color:#1f3b63;margin-top:10px}
p.vf{color:#2e7d32;padding-left:16px}p.note{color:#666}h3{color:#1f3b63;font-size:16px}mark{background:#ffeb3b}
.hide{display:none!important}#cnt{font-size:13px}
@media(max-width:800px){nav{position:fixed;left:0;top:50px;z-index:6;width:85%;display:none;box-shadow:2px 0 8px rgba(0,0,0,.3)}nav.on{display:block}main{padding:8px}}
@media(min-width:801px){#tg{display:none}}
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
<div id="wrap"><nav><ul>{''.join(nav)}</ul></nav><main>{''.join(body)}</main></div><script>{JS}</script></body></html>'''
open(O, 'w', encoding='utf-8').write(doc)
print('sections', nsec, 'companies', ncomp, 'size', len(doc))
print([ti for lv, _, ti in toc if lv == 1])
