"""海外招聘动态: 抓各公司官网招聘系统(Ashby/Greenhouse/Lever/SmartRecruiters)的公开接口,
对比在招岗位变化, 写入文档末尾的"招聘动态"。不改动正文结论。
用法:
  python tools/jobs.py          正式运行(需要环境变量 SITE_PASSWORD)
  python tools/jobs.py --dry    只抓取并打印, 不写入文档
"""
import datetime, json, os, sys, time, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crypt

ROOT = crypt.ROOT
BOARDS = json.load(open(os.path.join(ROOT, 'data', 'boards.json'), encoding='utf-8'))
STATE = os.path.join(ROOT, 'data', 'jobs_state.json')
LOG_TITLE = '招聘动态（每周自动生成）'
TODAY = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=8)).date().isoformat()
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36'}
CAREER = {
    'ashby': 'https://jobs.ashbyhq.com/{}',
    'greenhouse': 'https://job-boards.greenhouse.io/{}',
    'lever': 'https://jobs.lever.co/{}',
    'smartrecruiters': 'https://jobs.smartrecruiters.com/{}',
}


def fetch(at, board):
    """返回 {岗位标题: True}, 失败返回 None"""
    try:
        if at == 'ashby':
            j = json.loads(_get(f'https://api.ashbyhq.com/posting-api/job-board/{board}'))
            return {x['title'].strip(): 1 for x in j.get('jobs', []) if x.get('title')}
        if at == 'greenhouse':
            try:
                j = json.loads(_get(f'https://boards-api.greenhouse.io/v0/boards/{board}/jobs'))
                if j.get('jobs'):
                    return {x['title'].strip(): 1 for x in j['jobs'] if x.get('title')}
            except Exception:
                pass
            h = _get(f'https://job-boards.greenhouse.io/{board}').decode('utf-8', 'ignore')
            return {t.strip(): 1 for t in set(__import__('re').findall(r'"title"\s*:\s*"([^"]+)"', h))}
        if at == 'lever':
            j = json.loads(_get(f'https://api.lever.co/v0/postings/{board}?mode=json'))
            return {x['text'].strip(): 1 for x in j if x.get('text')}
        if at == 'smartrecruiters':
            out = {}
            for skip in (0, 100, 200):
                j = json.loads(_get(f'https://api.smartrecruiters.com/v1/companies/{board}/postings?limit=100&offset={skip}'))
                c = j.get('content', [])
                out.update({x['name'].strip(): 1 for x in c if x.get('name')})
                if len(c) < 100:
                    break
            return out
    except Exception:
        return None
    return None


def _get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25).read()


def main():
    dry = '--dry' in sys.argv
    prev = json.load(open(STATE, encoding='utf-8')) if os.path.exists(STATE) else {}
    cur, fails, lines = {}, [], []
    for i, b in enumerate(BOARDS, 1):
        jobs = fetch(b['ats'], b['board'])
        if jobs is None:
            fails.append(b['name'])
            print(f'{i}/{len(BOARDS)} {b["name"]} 抓取失败')
            continue
        cur[b['name']] = sorted(jobs)
        link = CAREER[b['ats']].format(b['board'])
        old = prev.get(b['name'])
        if old is None:
            lines.append(f'- {b["name"]}：在招 {len(jobs)} 个岗位（首次记录）({link})')
        else:
            olds, adds = set(old), set(jobs) - set(old)
            gone = len(olds - set(jobs))
            if adds or gone:
                extra = ''
                if adds:
                    show = '、'.join(sorted(adds)[:5]) + (f' 等{len(adds)}个' if len(adds) > 5 else '')
                    extra = f'，新增：{show}'
                if gone:
                    extra += f'；下线 {gone} 个'
                lines.append(f'- {b["name"]}：在招 {len(jobs)} 个岗位（上周 {len(old)}）{extra}({link})')
        print(f'{i}/{len(BOARDS)} {b["name"]} {len(jobs)}个岗位')
    print('有变化:', len(lines), '失败:', len(fails))
    if dry:
        for l in lines:
            print(l)
        return
    block = [f'—— {TODAY} 招聘 ——']
    block += lines or ['- 本周各海外公司招聘岗位数量和岗位列表无明显变化。']
    if fails:
        block.append('- 以下公司本周抓取失败：' + '、'.join(fails))
    block.append('')
    text = crypt.load_txt()
    L = text.split('\n')
    if not any(l.startswith(LOG_TITLE) for l in L):
        L += ['', '#' * 80, LOG_TITLE,
              '说明：海外公司数据来自其官网招聘系统（Ashby/Greenhouse/Lever 等）的公开接口，每周对比在招岗位变化；中国公司条目由“Boss直聘手动更新”生成。岗位增减是业务扩张或收缩的参考信号。',
              '#' * 80, '']
    if block[0] in L:  # 同一天重跑: 旧记录合并新内容, 无新内容则不动
        s = L.index(block[0])
        e = s + 1
        while e < len(L) and not L[e].startswith('—— ') and set(L[e].strip() or 'x') != {'#'}:
            e += 1
        old = [x for x in L[s + 1:e] if x.startswith('- ') and '无明显变化' not in x and '抓取失败' not in x]
        fresh = [x for x in lines if x not in old]
        if not fresh:
            print('同日重跑无变化, 保持原记录')
            return
        block = [block[0]] + old + fresh + (['- 以下公司本周抓取失败：' + '、'.join(fails)] if fails else []) + ['']
        del L[s:e]
    k = next(k for k, l in enumerate(L) if l.startswith(LOG_TITLE))
    while not set(L[k].strip() or 'x') == {'#'}:
        k += 1
    L[k + 1:k + 1] = [''] + block
    crypt.save_txt('\n'.join(L))
    json.dump(cur, open(STATE, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)


if __name__ == '__main__':
    main()
