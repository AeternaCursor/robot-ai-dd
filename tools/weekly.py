"""每周更新: 抓重点公司和待核实条目相关公司的新闻(Google News RSS), 用 GitHub Models 判断是否有重要变化,
结果写入文档末尾的“本周更新记录”。不改动正文结论。需要环境变量 SITE_PASSWORD 和 GITHUB_TOKEN。"""
import datetime, email.utils, hashlib, json, os, re, sys, time, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crypt

ROOT = crypt.ROOT
SEEN = os.path.join(ROOT, 'data', 'seen.json')
API = 'https://models.github.ai/inference/chat/completions'
MODEL = os.environ.get('MODEL', 'openai/gpt-4o-mini')
LOG_TITLE = '本周更新记录（每周一自动生成）'
CJK = re.compile(r'[\u4e00-\u9fff]')
NOW = datetime.datetime.now(datetime.timezone.utc)
TODAY = (NOW + datetime.timedelta(hours=8)).date().isoformat()


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
        x = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=30).read()
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


def ask(batch):
    sys_p = ('你是尽调助理。只根据给出的新闻标题判断公司是否出现重要变化：融资、估值、上市/退市、营收利润、并购、裁员、诉讼处罚、'
             '重大客户或产品量产、高管变动，或能解答“待核实”条目的信息。严禁编造标题里没有的信息，数字必须原样来自标题。'
             '与公司无关、同名混淆、普通营销稿一律不选。只输出JSON：{"items":[{"company":"公司名","summary":"一句中文结论","news":[新闻编号],"resolves":"可解答的待核实条目编号或空"}]}，没有重要变化的公司不要列出。')
    user = []
    for c in batch:
        user.append(f"## {c['name']}\n背景：{' | '.join(c['info'])[:400]}\n" +
                    '\n'.join(f"[{i}] {n['date']} {n['src']}：{n['title']}" for i, n in enumerate(c['news'])))
    body = json.dumps({'model': MODEL, 'temperature': 0, 'response_format': {'type': 'json_object'},
                       'messages': [{'role': 'system', 'content': sys_p}, {'role': 'user', 'content': '\n\n'.join(user)}]}).encode()
    for n in range(4):
        try:
            r = urllib.request.urlopen(urllib.request.Request(API, body, {
                'Authorization': 'Bearer ' + os.environ['GITHUB_TOKEN'], 'Content-Type': 'application/json'}), timeout=120)
            return json.loads(json.loads(r.read())['choices'][0]['message']['content']).get('items', [])
        except Exception as e:
            detail = e.read()[:300] if hasattr(e, 'read') else ''
            print('AI调用失败, 稍后重试', e, detail)
            if getattr(e, 'code', 0) in (401, 403):
                return None
            time.sleep(30 * (n + 1))
    return None


def main():
    text = crypt.load_txt()
    L = text.split('\n')
    seen = set(json.load(open(SEEN))) if os.path.exists(SEEN) else set()
    h = lambda s: hashlib.sha1(s.encode()).hexdigest()[:16]
    cands = []
    for q, c in targets(L).items():
        ns = [n for n in news(q) if h(n['link']) not in seen]
        time.sleep(1)
        if ns:
            c['news'] = ns
            cands.append(c)
    print('目标公司有新新闻:', len(cands))
    lines, failed = [], []
    for i in range(0, len(cands), 6):
        batch = cands[i:i + 6]
        res = ask(batch)
        print(f'AI判断 {i + len(batch)}/{len(cands)}', '失败' if res is None else f'{len(res)}条')
        time.sleep(5)
        if res is None:
            failed += [c['name'] for c in batch]
            continue
        by = {c['name']: c for c in batch}
        for r in res:
            c = by.get(r.get('company')) or next((v for k, v in by.items() if r.get('company', '') in k or k in r.get('company', '')), None)
            if not c:
                continue
            refs = [c['news'][j] for j in r.get('news', []) if isinstance(j, int) and 0 <= j < len(c['news'])]
            if not refs:
                continue
            src = '；'.join(f"{n['src']} {n['date']} {n['link']}" for n in refs[:3])
            tag = f"（可能涉及待核实第{r['resolves']}条）" if r.get('resolves') else ''
            lines.append(f"- {c['name']}：{r.get('summary', '').strip()}{tag}（来源：{src}）")
        for c in batch:
            seen.update(h(n['link']) for n in c['news'])
    block = [f'—— {TODAY} 更新 ——']
    block += lines or ['- 本周重点公司未发现融资、上市、营收、估值等重要变化。']
    if failed:
        block.append('- 以下公司本周 AI 判断失败，下周重试：' + '、'.join(failed))
    block.append('')
    if not any(l.startswith(LOG_TITLE) for l in L):
        L += ['', '#' * 80, LOG_TITLE,
              '说明：由程序根据新闻标题自动筛选，未改动正文结论；请点开来源链接核对后再引用。', '#' * 80, '']
    k = next(k for k, l in enumerate(L) if l.startswith(LOG_TITLE))
    while not set(L[k].strip() or 'x') == {'#'}:
        k += 1
    L[k + 1:k + 1] = [''] + block
    crypt.save_txt('\n'.join(L))
    json.dump(sorted(seen), open(SEEN, 'w'))
    print('写入', len(lines), '条更新')


if __name__ == '__main__':
    main()
