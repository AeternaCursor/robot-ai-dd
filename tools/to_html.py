import re, html, sys, datetime
# 用法: python to_html.py 输入.txt 输出.html [日期]
P, O = sys.argv[1], sys.argv[2]
DATE = sys.argv[3] if len(sys.argv) > 3 else datetime.date.today().isoformat()
L = open(P, encoding='utf-8').read().lstrip('\ufeff').split('\n')
skip = {'【传动与关节类】', '【感知类】', '【芯片类】', '【材料与连接类】', '【财务与资本市场类】'}
_CN = '一二三四五六七八九'
def cn(n):
    if n < 10:
        return _CN[n - 1]
    if n == 10:
        return '十'
    if n < 20:
        return '十' + _CN[n - 11]
    return '二十'
E = html.escape
body = []; toc = []  # toc: (level, id, title)
sec_open = False; ent_open = False; nsec = ncomp = 0
ent_buf = []  # 公司条目内的行, 收进"展开明细"折叠块
def close_ent():
    global ent_open, ent_buf
    if ent_open:
        ones = ''.join(h for c, h in ent_buf if c == 'one')
        rest = [(c, h) for c, h in ent_buf if c != 'one']
        inner = ones
        if rest:
            inner += (f'<details class="fld"><summary>展开尽调明细（{len(rest)} 项）</summary>'
                      f'<div class="fbody">{"".join(h for _, h in rest)}</div></details>')
        body.append(inner + '</div></details>')
        ent_open = False; ent_buf = []
def close_sec():
    global sec_open
    close_ent()
    if sec_open: body.append('</div></details>'); sec_open = False
def open_sec(title):
    global sec_open, nsec
    close_sec(); nsec += 1
    sid = f's{nsec}'
    toc.append((1, sid, title))
    cls = 'sec'
    if title.startswith('本周更新记录') or title.startswith('招聘动态'):
        cls += ' auto'
    grid = ' grid' if (title.startswith('板块') or title.startswith('第二部分')) else ''
    body.append(f'<details class="{cls}" id="{sid}"><summary><span class="sn">卷{cn(nsec)}</span><h2>{E(title)}</h2></summary><div class="sb{grid}">')
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
    line = f'<p{cls}>{t}</p>'
    if ent_open:
        ent_buf.append(('one' if cls == ' class="one"' else '', line))
    else:
        body.append(line)
    i += 1
close_sec()
nav = []
for lv, id_, ti in toc:
    if lv == 1:
        if nav and nav[-1] != '<ul>': pass
        nav.append(f'<li class="l1"><a href="#{id_}">{E(ti)}</a></li>')
    else:
        nav.append(f'<li class="l2"><a href="#{id_}">{E(ti)}</a></li>')
def sid_of(pre):
    return next((i for _, i, t in toc if t.startswith(pre)), '')
QUICK = [('公司速览', '各板块重点公司速览'), ('中国人形机器人', '板块一'), ('海外人形机器人', '板块二'),
         ('工业/自动驾驶', '板块三'), ('大模型', '板块四'), ('AI芯片算力', '板块五'), ('中国供应链', '板块六'),
         ('本周更新', '本周更新记录'), ('招聘动态', '招聘动态')]
chips = ''.join(f'<a class="chip" href="#{sid_of(p)}">{n}</a>' for n, p in QUICK if sid_of(p))
CSS = '''
@property --a{syntax:'<angle>';initial-value:0deg;inherits:false}
:root{--bg:#e9e2cd;--panel:rgba(252,249,240,.80);--line:rgba(96,86,64,.30);--txt:#37322a;--txt2:#837b6a;--acc:#5a5245;--acc2:#8a7f6a;--gold:#a8834a;--cn:#b8442c;--cn2:#cf5a3e;--gold2:#8a6a35;--ok:#4e7a55}
.kai,h1,h2,.ht,.sn,footer,.sub,#hint{font-family:"KaiTi","STKaiti","Kaiti SC","FangSong",serif}
*{box-sizing:border-box}html{background:var(--bg);scroll-behavior:smooth}
body{margin:0;font:15px/1.75 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif;color:var(--txt);overflow-x:hidden}
::selection{background:rgba(184,68,44,.30);color:#37322a}
::-webkit-scrollbar{width:10px;height:10px}::-webkit-scrollbar-track{background:#e0d8c2}
::-webkit-scrollbar-thumb{background:linear-gradient(180deg,#8a7f6a,#5a5245);border-radius:5px;box-shadow:0 0 6px rgba(90,82,69,.35)}
body::before{content:"";position:fixed;inset:-40%;z-index:-2;pointer-events:none;background:
radial-gradient(700px 500px at 12% 6%,rgba(74,66,50,.10),transparent 60%),
radial-gradient(800px 600px at 90% 16%,rgba(184,68,44,.05),transparent 60%),
radial-gradient(900px 700px at 50% 106%,rgba(74,66,50,.13),transparent 62%),
radial-gradient(700px 500px at 6% 86%,rgba(120,100,70,.07),transparent 60%);animation:aur 24s ease-in-out infinite alternate}
@keyframes aur{to{transform:translate(3%,-4%) scale(1.07)}}
body::after{content:"";position:fixed;inset:0;z-index:-1;pointer-events:none;opacity:.7;background:
repeating-linear-gradient(0deg,transparent 0 3px,rgba(120,105,80,.035) 3px 4px),
repeating-linear-gradient(90deg,transparent 0 79px,rgba(120,105,80,.05) 79px 80px);
-webkit-mask:radial-gradient(130% 100% at 50% 0%,#000 40%,transparent 100%)}
#fx{position:fixed;inset:0;z-index:-1;pointer-events:none}
#moon{position:fixed;top:84px;right:9%;width:120px;height:120px;border-radius:50%;z-index:-1;pointer-events:none;
background:radial-gradient(circle at 38% 34%,#faf7ee,#e8e0c8 55%,#cfc4a4 100%);
box-shadow:0 0 60px rgba(160,140,100,.28),0 0 130px rgba(120,105,80,.16);
opacity:.9;animation:breath 11s ease-in-out infinite}
#moon::after{content:"";position:absolute;left:14%;top:52%;width:26%;height:20%;border-radius:50%;background:rgba(150,135,100,.30);filter:blur(3px);
box-shadow:34px -26px 0 -6px rgba(150,135,100,.24),-22px -38px 0 -10px rgba(150,135,100,.18)}
@keyframes breath{50%{box-shadow:0 0 90px rgba(160,140,100,.40),0 0 170px rgba(120,105,80,.24)}}
.mist{position:fixed;height:110px;width:430px;border-radius:50%;filter:blur(46px);z-index:-1;pointer-events:none;
background:rgba(252,249,238,.62);animation:drift linear infinite}
.m1{top:26%;animation-duration:75s}
.m2{top:52%;width:560px;height:130px;background:rgba(184,68,44,.06);animation-duration:105s;animation-delay:-40s}
.m3{top:12%;width:360px;background:rgba(252,249,238,.5);animation-duration:90s;animation-delay:-70s}
@keyframes drift{from{transform:translateX(-35vw)}to{transform:translateX(135vw)}}
#mt{position:fixed;left:0;right:0;bottom:0;height:32vh;z-index:-1;pointer-events:none}
#mt svg{width:100%;height:100%;display:block}
#scan{display:none}
header{position:sticky;top:0;z-index:9;display:flex;gap:10px;align-items:center;flex-wrap:wrap;padding:10px 18px;
background:rgba(238,233,218,.88);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);border-bottom:1px solid var(--line);box-shadow:0 2px 14px rgba(90,80,60,.12)}
header::before{content:"";position:absolute;left:6px;top:5px;width:16px;height:16px;border-left:2px solid var(--cn2);border-top:2px solid var(--cn2);opacity:.75}
header::after{content:"";position:absolute;right:6px;bottom:5px;width:16px;height:16px;border-right:2px solid var(--acc);border-bottom:2px solid var(--acc);opacity:.75}
.live{display:flex;align-items:center;gap:6px;font:600 10px/1 ui-monospace,Consolas,monospace;color:#6b6152;
border:1px solid rgba(96,86,64,.4);border-radius:4px;padding:4px 7px;letter-spacing:2px;
box-shadow:inset 0 0 8px rgba(96,86,64,.08);animation:pulse 2s infinite}
.live i{width:6px;height:6px;border-radius:50%;background:var(--cn2);box-shadow:0 0 8px rgba(184,68,44,.5);animation:pulse 1.2s infinite}
@keyframes pulse{50%{opacity:.45}}
header h1{font-size:16px;margin:0;flex:1 1 180px;font-weight:700;letter-spacing:.5px;
background:linear-gradient(90deg,#3a352c,#8a6a35 85%);-webkit-background-clip:text;background-clip:text;color:transparent}
#q{flex:1 1 220px;padding:8px 14px;border-radius:999px;border:1px solid var(--line);font-size:14px;color:var(--txt);
background:rgba(255,252,244,.7);outline:none;transition:.25s}
#q::placeholder{color:var(--txt2)}#q:focus{border-color:var(--cn2);box-shadow:0 0 0 3px rgba(184,68,44,.15),0 0 14px rgba(168,131,74,.18);background:#fffcf4}
header button{padding:7px 13px;border:1px solid var(--line);border-radius:999px;background:rgba(255,252,244,.6);color:var(--txt);cursor:pointer;font-size:13px;transition:.25s;font-family:"KaiTi","STKaiti",serif;letter-spacing:2px}
header button:hover{background:linear-gradient(90deg,#5a5245,var(--cn2));border-color:transparent;color:#fff;box-shadow:0 4px 16px rgba(90,82,69,.35)}
#cnt{font:600 11px/1 ui-monospace,Consolas,monospace;color:#8a5a30;white-space:nowrap;letter-spacing:1px}
#wrap{display:flex;position:relative;z-index:1}
nav{width:300px;flex:none;height:calc(100vh - 52px);position:sticky;top:52px;overflow:auto;
background:rgba(240,235,220,.82);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);
border-right:1px solid var(--line);font-size:13px;padding-bottom:30px}
nav::-webkit-scrollbar{width:6px}nav::-webkit-scrollbar-thumb{background:rgba(96,86,64,.3);border-radius:3px}
nav ul{list-style:none;margin:0;padding:10px}
nav li.l1{font-weight:700;margin-top:14px;font-family:"KaiTi","STKaiti",serif}nav li.l1>a{color:#3a352c;display:flex;align-items:center;gap:7px}
nav li.l1>a::before{content:"";width:7px;height:7px;border-radius:2px;flex:none;background:linear-gradient(135deg,#5a5245,var(--cn2));animation:pulse 3s infinite}
nav li.l2{padding-left:20px}
nav a{color:var(--txt2);text-decoration:none;display:block;padding:3px 8px;border-radius:6px;transition:.18s;border-left:1px solid transparent}
nav a:hover{color:#3a352c;background:rgba(96,86,64,.10);border-left-color:var(--cn2)}
main{flex:1;min-width:0;padding:18px 22px 60px;max-width:1000px}
details.sec{position:relative;background:var(--panel);border-radius:14px;margin:16px 0;box-shadow:0 10px 30px rgba(90,80,60,.16);overflow:visible;transition:.3s}
details.sec::before{content:"";position:absolute;inset:0;border-radius:14px;padding:1px;pointer-events:none;
background:linear-gradient(135deg,rgba(96,86,64,.50),rgba(96,86,64,.12) 35%,rgba(184,68,44,.28));
-webkit-mask:linear-gradient(#000 0 0) content-box,linear-gradient(#000 0 0);-webkit-mask-composite:xor;mask-composite:exclude;transition:.4s}
details.sec:hover{transform:translateY(-2px);box-shadow:0 18px 44px rgba(90,80,60,.22)}
details.sec:hover::before{background:conic-gradient(from var(--a),transparent 0 62%,#5a5245 78%,#b8442c 86%,transparent 94%);animation:rot 2.6s linear infinite}
@keyframes rot{to{--a:360deg}}
details.sec>summary{cursor:pointer;padding:13px 40px 13px 18px;list-style:none;position:relative}
details.sec>summary::-webkit-details-marker{display:none}
details.sec>summary h2{display:inline;font-size:19px;font-weight:700;letter-spacing:1px;vertical-align:middle;
background:linear-gradient(90deg,#3a352c,#6b5c3f);-webkit-background-clip:text;background-clip:text;color:transparent}
.sn{display:inline-block;font-size:13px;color:#5a5245;border:1px solid rgba(96,86,64,.45);
border-radius:4px;padding:3px 8px;margin-right:10px;vertical-align:2px;letter-spacing:3px;
box-shadow:inset 0 0 8px rgba(96,86,64,.08)}
details.sec>summary::before{content:"▸";position:absolute;right:16px;top:12px;color:#5a5245;transition:transform .3s}
details.sec[open]>summary::before{transform:rotate(90deg)}
details.sec>summary::after{content:"";position:absolute;left:12px;right:12px;bottom:0;height:1px;
background:linear-gradient(90deg,transparent,rgba(96,86,64,.55),rgba(184,68,44,.35),transparent);box-shadow:0 2px 0 rgba(96,86,64,.12)}
.sb{padding:4px 18px 14px}
details.ent{position:relative;border:1px solid rgba(96,86,64,.14);border-left:2px solid rgba(96,86,64,.38);border-radius:8px;margin:7px 0;background:rgba(252,249,240,.55);transition:.22s}
details.ent:hover{border-left-color:var(--cn2);background:rgba(240,233,214,.9);box-shadow:0 6px 18px rgba(90,80,60,.18);transform:translateX(3px)}
details.ent>summary{cursor:pointer;padding:8px 12px;font-weight:600;color:#3a352c;list-style:none}
details.ent>summary::-webkit-details-marker{display:none}
details.ent>summary::before{content:"◆";font-size:9px;color:var(--cn2);margin-right:8px;vertical-align:1px}
details.ent[open]>summary{color:#8a4a2a}
details.ent[open]>summary::before{color:var(--cn2)}
.eb{padding:2px 14px 10px}
details.fld{margin:9px 0 2px;border:1px dashed rgba(96,86,64,.42);border-radius:8px;background:rgba(252,249,240,.45)}
details.fld>summary{cursor:pointer;padding:6px 12px;color:#6b5c3f;font-size:13px;list-style:none;letter-spacing:2px;font-family:"KaiTi","STKaiti",serif;user-select:none;transition:.2s}
details.fld>summary::-webkit-details-marker{display:none}
details.fld>summary:hover{color:var(--cn)}
details.fld>summary::before{content:"▸";color:var(--cn2);margin-right:8px;font-size:11px}
details.fld[open]>summary::before{content:"▾"}
details.fld .fbody{padding:2px 12px 8px}
p{margin:5px 0;word-break:break-word}
p.one{background:linear-gradient(90deg,rgba(168,131,74,.14),rgba(168,131,74,.03));padding:7px 12px;border-radius:8px;border-left:3px solid var(--cn2);color:#4a4234}
p.sub{font-weight:700;color:#6b5c3f;margin-top:12px;letter-spacing:1px;font-family:"KaiTi","STKaiti",serif}
p.vf{color:var(--ok);padding-left:14px}
p.note{color:var(--txt2);font-size:13.5px}
h3{color:#6b5c3f;font-size:16.5px;font-weight:700;margin:20px 0 6px;display:flex;align-items:center;gap:9px;letter-spacing:2px;font-family:"KaiTi","STKaiti",serif}
h3::before{content:"";width:26px;height:2px;flex:none;background:linear-gradient(90deg,var(--cn2),#a8834a,transparent)}
a{color:#8a5a35;text-decoration:none;border-bottom:1px dotted rgba(138,90,53,.5)}
a:hover{color:var(--cn);border-bottom-style:solid}
mark{background:linear-gradient(180deg,transparent 50%,rgba(255,200,40,.75) 50%);color:#3a352c;padding:0 1px;border-radius:2px}
b{color:#2b2620}
.hide{display:none!important}
footer{padding:28px 16px 44px;text-align:center;color:var(--txt2);font-size:12.5px;letter-spacing:4px}
footer::after{content:"▌";color:var(--cn2);animation:pulse 1s infinite;margin-left:4px}
#hero{padding:54px 20px 10px;text-align:center;position:relative}
#hero .ht{font-size:34px;font-weight:700;letter-spacing:6px;line-height:1.35;
background:linear-gradient(105deg,#3a352c 15%,#6b5c3f 55%,#b8442c 95%);-webkit-background-clip:text;background-clip:text;color:transparent}
#hero .hd{font-size:14px;letter-spacing:3px;color:#837b6a;margin:16px 0 26px;font-family:"KaiTi","STKaiti",serif}
#hero .hd em{font-style:normal;color:var(--cn);text-shadow:none}
.vtext{position:absolute;top:58px;writing-mode:vertical-rl;letter-spacing:10px;font-family:"KaiTi","STKaiti",serif;
font-size:15px;color:rgba(96,86,64,.60);border-left:1px solid rgba(96,86,64,.30);padding-left:8px;user-select:none}
.vtext.l{left:calc(50% - 470px)} .vtext.r{right:calc(50% - 470px)}
.seal{position:absolute;top:46px;left:calc(50% + 300px);width:54px;height:54px;display:flex;align-items:center;justify-content:center;
border:3px solid var(--cn);border-radius:7px;color:var(--cn);font-family:"KaiTi","STKaiti",serif;font-size:20px;font-weight:700;
letter-spacing:0;writing-mode:vertical-rl;line-height:1;transform:rotate(7deg);
box-shadow:inset 0 0 12px rgba(184,68,44,.28),0 4px 16px rgba(90,80,60,.18);background:rgba(184,68,44,.06);animation:pulse 4s infinite}
.stats{display:flex;flex-wrap:wrap;gap:12px;justify-content:center;margin-bottom:26px}
.st{display:flex;flex-direction:column;gap:5px;padding:12px 22px;border-radius:12px;min-width:104px;
background:var(--panel);border:1px solid var(--line);box-shadow:0 8px 20px rgba(90,80,60,.14)}
.st b{font-size:22px;color:#3a352c;font-variant-numeric:tabular-nums}
.st span{font-size:12px;color:var(--txt2);letter-spacing:3px;font-family:"KaiTi","STKaiti",serif}
.chips{display:flex;flex-wrap:wrap;gap:9px;justify-content:center;padding-bottom:8px}
a.chip{padding:8px 16px;border:1px solid var(--line)!important;border-bottom:1px solid var(--line)!important;border-radius:999px;
font-size:13.5px;color:var(--txt);background:rgba(255,252,244,.6);transition:.22s;text-shadow:none;letter-spacing:2px;font-family:"KaiTi","STKaiti",serif}
a.chip:hover{color:#fff;background:linear-gradient(90deg,#5a5245,var(--cn2));border-color:transparent!important;
box-shadow:0 6px 18px rgba(90,82,69,.30);transform:translateY(-2px)}
#hint{text-align:center;font-size:12px;color:var(--txt2);letter-spacing:4px;margin:8px 0 2px;animation:pulse 3s infinite}
.sb.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:8px;padding:6px 18px 16px}
.sb.grid>p,.sb.grid>h3{grid-column:1/-1}
.sb.grid details.ent{margin:0}
details.sec.auto>summary h2{background:linear-gradient(90deg,#3a352c,#b8442c);-webkit-background-clip:text;background-clip:text;color:transparent}
details.sec.auto>summary .sn{border-color:rgba(184,68,44,.55);color:#a0442e;animation:pulse 2s infinite}
details.sec.auto::before{background:linear-gradient(135deg,rgba(184,68,44,.45),rgba(96,86,64,.12) 40%,rgba(184,68,44,.35))}
details.sec.auto .sb p{border-left:2px solid rgba(184,68,44,.45);background:rgba(240,233,214,.6);padding:7px 12px;border-radius:8px;margin:7px 0}
#top{position:fixed;right:18px;bottom:18px;z-index:15;width:46px;height:46px;border-radius:50%;cursor:pointer;
border:1px solid var(--line);background:rgba(240,235,220,.9);color:#5a5245;font-size:17px;
backdrop-filter:blur(8px);box-shadow:0 8px 20px rgba(90,80,60,.22);
opacity:0;pointer-events:none;transition:.3s}
#top.on{opacity:1;pointer-events:auto}
#top:hover{background:linear-gradient(135deg,#5a5245,var(--cn2));color:#fff;box-shadow:0 8px 24px rgba(90,82,69,.4)}
@media(max-width:800px){
nav{position:fixed;left:0;top:0;height:100vh;z-index:20;width:82%;transform:translateX(-103%);transition:transform .3s;box-shadow:10px 0 30px rgba(90,80,60,.28)}
nav.on{transform:none}
main{padding:10px 12px 50px}
.live{display:none}
#hero{padding:32px 12px 6px}#hero .ht{font-size:23px;letter-spacing:3px}.st{min-width:86px;padding:10px 14px}.st b{font-size:18px}
.vtext,.seal{display:none}
#moon{width:80px;height:80px;top:70px;right:6%}
#mt{height:20vh}
.sb.grid{grid-template-columns:1fr;padding:6px 12px 14px}
}
@media(min-width:801px){#tg{display:none}}
@media(prefers-reduced-motion:reduce){#scan{display:none}body::before{animation:none}html{scroll-behavior:auto}*{animation:none!important}}
'''
JS = '''
const q=document.getElementById('q'),ents=[...document.querySelectorAll('details.ent')],secs=[...document.querySelectorAll('details.sec')];
let tm;q.addEventListener('input',()=>{clearTimeout(tm);tm=setTimeout(run,250)});
function run(){const k=q.value.trim().toLowerCase();let n=0;
document.querySelectorAll('mark').forEach(m=>m.replaceWith(m.textContent));
const flds=document.querySelectorAll('details.fld');
if(!k){ents.forEach(e=>{e.classList.remove('hide');e.open=false});secs.forEach(s=>s.classList.remove('hide'));flds.forEach(f=>f.open=false);document.getElementById('cnt').textContent='';return}
ents.forEach(e=>{const hit=e.textContent.toLowerCase().includes(k);e.classList.toggle('hide',!hit);e.open=hit&&e.querySelector('summary').textContent.toLowerCase().includes(k)||false;if(hit)n++});
secs.forEach(s=>{const hasE=s.querySelector('details.ent:not(.hide)');const self=s.textContent.toLowerCase().includes(k);s.classList.toggle('hide',!self);if(self)s.open=true});
document.querySelectorAll('details.ent:not(.hide)').forEach(e=>{const f=e.querySelector('details.fld');if(f&&e.open)f.open=true});
document.getElementById('cnt').textContent='匹配公司 '+n+' 家';}
function go(id){const el=document.getElementById(id);if(!el)return;let p=el;while(p){if(p.tagName==='DETAILS'){p.open=true;p.classList.remove('hide')}p=p.parentElement}el.scrollIntoView();}
document.querySelectorAll('nav a, a.chip').forEach(a=>a.addEventListener('click',ev=>{ev.preventDefault();go(a.getAttribute('href').slice(1));document.querySelector('nav').classList.remove('on')}));
document.getElementById('tg').onclick=()=>document.querySelector('nav').classList.toggle('on');
document.getElementById('ex').onclick=()=>secs.forEach(s=>s.open=!s.open);
const tb=document.getElementById('top');addEventListener('scroll',()=>tb.classList.toggle('on',scrollY>500),{passive:true});
tb.onclick=()=>scrollTo({top:0,behavior:'smooth'});
;
if(!matchMedia('(prefers-reduced-motion: reduce)').matches){(function(){
const c=document.getElementById('fx');if(!c)return;const x=c.getContext('2d');let w,h,P=[];
function rs(){w=c.width=innerWidth;h=c.height=innerHeight;const n=Math.min(90,Math.floor(w*h/16000));P=[];
for(let i=0;i<n;i++)P.push({x:Math.random()*w,y:Math.random()*h,vx:(Math.random()-.5)*.4,vy:(Math.random()-.5)*.4,r:Math.random()*1.5+.5})}
rs();addEventListener('resize',rs);let vis=true;document.addEventListener('visibilitychange',()=>vis=!document.hidden);
(function tick(){if(vis){x.clearRect(0,0,w,h);
for(const p of P){p.x+=p.vx;p.y+=p.vy;if(p.x<0||p.x>w)p.vx*=-1;if(p.y<0||p.y>h)p.vy*=-1;
x.fillStyle=p.r>1.4?'rgba(184,68,44,.45)':'rgba(74,66,50,.40)';
x.beginPath();x.arc(p.x,p.y,p.r,0,6.283);x.fill()}
x.lineWidth=1;
for(let i=0;i<P.length;i++)for(let j=i+1;j<P.length;j++){const a=P[i],b=P[j],dx=a.x-b.x,dy=a.y-b.y,d2=dx*dx+dy*dy;
if(d2<16900){x.strokeStyle='rgba(74,66,50,'+(.16*(1-Math.sqrt(d2)/130)).toFixed(3)+')';
x.beginPath();x.moveTo(a.x,a.y);x.lineTo(b.x,b.y);x.stroke()}}}
requestAnimationFrame(tick)})()})()}
'''
doc = f'''<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>机器人 · 具身智能 · 公司尽调</title><style>{CSS}</style></head><body>
<header><button id="tg">目录</button><span class="live"><i></i>LIVE</span><h1>机器人 · 具身智能 · 公司尽调（{ncomp} 家，更新于 {DATE}）</h1><input id="q" placeholder="搜索公司名、关键词…"><span id="cnt"></span><button id="ex">折叠/展开板块</button></header>
<canvas id="fx"></canvas><div id="scan"></div>
<div id="moon"></div>
<div class="mist m1"></div><div class="mist m2"></div><div class="mist m3"></div>
<div id="mt"><svg viewBox="0 0 1440 320" preserveAspectRatio="none" aria-hidden="true">
<path fill="rgba(74,66,50,.16)" stroke="rgba(96,86,64,.30)" stroke-width="1" d="M0,225 L110,150 L235,215 L375,120 L520,205 L685,140 L845,210 L1005,130 L1165,200 L1305,155 L1440,215 L1440,320 L0,320 Z"/>
<path fill="rgba(74,66,50,.26)" stroke="rgba(96,86,64,.24)" stroke-width="1" d="M0,262 L155,195 L305,252 L475,168 L645,248 L825,182 L1005,252 L1165,190 L1325,242 L1440,205 L1440,320 L0,320 Z"/>
<path fill="rgba(74,66,50,.38)" d="M0,292 L185,245 L365,286 L565,226 L765,282 L965,235 L1165,287 L1335,252 L1440,278 L1440,320 L0,320 Z"/>
</svg></div>
<div id="wrap"><nav><ul>{''.join(nav)}</ul></nav><main>
<div id="hero">
<span class="vtext l">格物致知</span><span class="vtext r">明察秋毫</span><span class="seal">尽调</span>
<div class="ht">机器人 · 具身智能 · 公司尽调</div>
<div class="hd">「 <em>知己知彼，百战不殆</em> 」 —— 《孙子·谋攻》</div>
<div class="stats">
<div class="st"><b>{ncomp}</b><span>家公司</span></div>
<div class="st"><b>{nsec}</b><span>卷目录</span></div>
<div class="st"><b>{DATE[5:]}</b><span>近日更新</span></div>
<div class="st"><b>每周</b><span>卷宗常新</span></div>
</div>
<div class="chips">{chips}</div>
<div id="hint">卷目尽收于此 · 点击展开阅读</div>
</div>
{''.join(body)}</main></div>
<button id="top" title="回到顶部">▲</button>
<footer>格物致知 · 明察秋毫 · 卷宗每周一新 · 端到端加密</footer>
<script>{JS}</script></body></html>'''
open(O, 'w', encoding='utf-8').write(doc)
print('sections', nsec, 'companies', ncomp, 'size', len(doc))
print([ti for lv, _, ti in toc if lv == 1])
