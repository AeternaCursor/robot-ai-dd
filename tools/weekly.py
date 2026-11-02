"""每周更新: 抓重点公司和待核实条目相关公司的新闻(Google News RSS),
用关键词筛出重要变化(融资、估值、上市、营收、并购、量产、诉讼、高管变动等),
新闻标题原样引用并附来源链接, 写入文档末尾的"本周更新记录"。不改动正文结论。
需要环境变量 SITE_PASSWORD。"""
import datetime, email.utils, hashlib, json, os, re, sys, time, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crypt

ROOT = crypt.ROOT
SEEN = os.path.join(ROOT, 'data', 'seen.json')
LOG_TITLE = '本周更新记录（每周一自动生成）'
CJK = re.compile(r'[\u4e00-\u9fff]')
NOW = datetime.datetime.now(datetime.timezone.utc)
TODAY = (NOW + datetime.timedelta(hours=8)).date().isoformat()

# 重要变化关键词(中英文)。命中的新闻标题才会收录, 标题原样引用不改动。
KEY = re.compile('|'.join([
    '融资', '募资', '估值', '上市', 'IPO', '递表', '招股', '退市', '停牌',
    '收购', '并购', '入股', '增资', '战略投资',
    '裁员', '破产', '清算', '倒闭', '重组',
    '营收', '净利', '利润', '财报', '季报', '年报', '亏损', '扭亏',
    '量产', '投产', '交付', '出货', '订单', '中标',
    '诉讼', '仲裁', '罚款', '处罚', '制裁', '禁令', '调查', '召回',
    '高管', 'CEO', 'CTO', '总裁', '辞任', '离职', '任命',
    '招聘', '扩招', '校招', '社招', '内推', '秋招', '春招',
    r'raises', r'funding', r'series [a-z]', r'valuation', r'\bIPO\b', r'acquir',
    r'merger', r'acquisition', r'layoff', r'bankrupt', r'revenue', r'profit',
    r'lawsuit', r'\bfines?\b', r'investigat', r'recall', r'ships\b', r'deliver',
    r'\bCEO\b', r'resign', r'hiring',
]), re.I)


def query_name(n):
    n = re.split(r'[（(]', n)[0].strip()
    w = n.split()
    if not w:
        return n
    if CJK.search(w[0]):
        return re.sub(r'(集团)?(股份)?有限公司$|股份公司$', '', w[0]) or w[0]
    out = []
    for x in w:
        if CJK.search(x) or (out and (x.strip(',') == w[0] or x.startswith(w[0]) or x.rstrip(',') in ('Inc.', 'Inc', 'Corp.', 'Ltd.', 'Holdings', 'Group'))):
            break
        out.append(x.rstrip(','))
    return ' '.join(out)


def targets(L):
    """返回 {搜索名: {'name':原名, 'info':[背景文字]}}"""
    t = {}
    def add(name, info):
        q = query_name(name)
        if len(q) >= 2:
            t.setdefault(q, {'name': name, 'info': []})['info'].append(info)
    i0 = next(k for k, l in enumerate(L) if l.startswith('各板块重点公司速览（每板块'))
    for k in range(i0 + 1, len(L)):
        s = L[k].strip()
        if s and set(s) == {'#'} and k > i0 + 3:
            break
        m = re.match(r'^-\s*(.+?)：(.*)$', s)
        if m:
            add(m.group(1), '重点公司速览：' + m.group(2))
    a0 = next(k for k, l in enumerate(L) if l.startswith('附录  待核实清单（全文汇总'))
    for k in range(a0, len(L)):
        m = re.match(r'^(\d+)\.\s*【([^】]+)】(.*)$', L[k].strip())
        if m and not (k + 1 < len(L) and L[k + 1].strip().startswith('→ 已核实')):
            add(m.group(2), f'待核实第{m.group(1)}条：{m.group(3)}')
    return t


def news(q):
    zh = bool(CJK.search(q))
    p = {'q': f'"{q}" when:7d', 'hl': 'zh-CN' if zh else 'en-US', 'gl': 'CN' if zh else 'US', 'ceid': 'CN:zh-Hans' if zh else 'US:en'}
    url = 'https://news.google.com/rss/search?' + urllib.parse.urlencode(p)
    try:
        x = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=15).read()
    except Exception as e:
        print('RSS失败', q, e)
        return []
    out = []
    for it in ET.fromstring(x).iter('item'):
        try:
            d = email.utils.parsedate_to_datetime(it.findtext('pubDate'))
        except Exception:
            continue
        if (NOW - d).days > 8:
            continue
        out.append({'title': it.findtext('title', ''), 'link': it.findtext('link', ''),
                    'src': it.findtext('source', ''), 'date': (d + datetime.timedelta(hours=8)).date().isoformat()})
    return out[:10]


def main():
    text = crypt.load_txt()
    L = text.split('\n')
    seen = set(json.load(open(SEEN))) if os.path.exists(SEEN) else set()
    h = lambda s: hashlib.sha1(s.encode()).hexdigest()[:16]
    lines = []
    t0 = time.time()
    T = targets(L)
    for n_, (q, c) in enumerate(T.items(), 1):
        ns = [x for x in news(q) if h(x['link']) not in seen]
        hit = [x for x in ns if KEY.search(x['title'])][:3]
        if hit:
            pend = sorted(set(re.findall(r'待核实第(\d+)条', ' '.join(c['info']))), key=int)
            tag = f"（可能涉及待核实第{'、'.join(pend)}条）" if pend else ''
            for x in hit:
                lines.append(f"- {c['name']}：{x['title']}{tag}（来源：{x['src']} {x['date']} {x['link']}）")
            seen.update(h(x['link']) for x in ns)
        if n_ % 20 == 0:
            print(f'新闻 {n_}/{len(T)} 用时{int(time.time() - t0)}秒 已命中{len(lines)}条')
        if time.time() - t0 > 600:
            print('抓新闻超过10分钟, 剩余公司下周再查')
            break
    print('写入', len(lines), '条更新')
    block = [f'—— {TODAY} 更新 ——']
    block += lines or ['- 本周重点公司未发现融资、上市、营收、估值等重要变化。']
    block.append('')
    if not any(l.startswith(LOG_TITLE) for l in L):
        L += ['', '#' * 80, LOG_TITLE,
              '说明：由程序根据新闻标题自动筛选，未改动正文结论；请点开来源链接核对后再引用。', '#' * 80, '']
    if block[0] in L:  # 同一天重跑: 与当天旧记录合并, 不丢内容
        s = L.index(block[0])
        e = s + 1
        while e < len(L) and not L[e].startswith('—— ') and set(L[e].strip() or 'x') != {'#'}:
            e += 1
        old = [x for x in L[s + 1:e] if x.startswith('- ') and '未发现' not in x]
        fresh = [x for x in lines if x not in old]
        if not fresh:
            print('同日重跑无新内容, 保持原记录')
            return
        block = [block[0]] + old + fresh + ['']
        del L[s:e]
    k = next(k for k, l in enumerate(L) if l.startswith(LOG_TITLE))
    while not set(L[k].strip() or 'x') == {'#'}:
        k += 1
    L[k + 1:k + 1] = [''] + block
    L = trim(L, 8)
    crypt.save_txt('\n'.join(L))
    json.dump(sorted(seen), open(SEEN, 'w'))


def trim(L, keep=8):
    """只保留最近 keep 个日期块, 防止文档无限膨胀"""
    marks = [i for i, l in enumerate(L) if re.match(r'^—— \d{4}-\d{2}-\d{2} 更新 ——$', l)]
    for s in reversed(marks[:-keep]):
        e = s + 1
        while e < len(L) and not L[e].startswith('—— ') and set(L[e].strip() or 'x') != {'#'}:
            e += 1
        del L[s:e]
    return L


if __name__ == '__main__':
    main()
