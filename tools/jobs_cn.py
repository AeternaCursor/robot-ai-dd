"""中国公司招聘动态(手动运行): 用你自己的 Boss直聘 账号在本机浏览器里搜索各公司在招岗位,
写入文档"招聘动态"板块并自动上传。只在个人电脑上、每周最多跑一次, 降低账号风险。
用法:
  python tools/jobs_cn.py            更新全部公司
  python tools/jobs_cn.py 宇树科技    只更新指定公司
首次使用: 1) pip install playwright   2) playwright install chromium
"""
import datetime, json, os, random, subprocess, sys, time, urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crypt

ROOT = crypt.ROOT
CN = json.load(open(os.path.join(ROOT, 'data', 'cn_companies.json'), encoding='utf-8'))
STATE = os.path.join(ROOT, 'data', 'jobs_cn_state.json')
PROFILE = os.path.join(ROOT, '.pw')
LOG_TITLE = '招聘动态（每周自动生成）'
MARK = '—— {} Boss直聘（手动） ——'
TODAY = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=8)).date().isoformat()
SEARCH = 'https://www.zhipin.com/web/geek/job?query={}'


def run(companies):
    from playwright.sync_api import sync_playwright
    prev = json.load(open(STATE, encoding='utf-8')) if os.path.exists(STATE) else {}
    cur, fails, lines = {}, [], []
    with sync_playwright() as p:
        kw = {'channel': 'chrome', 'headless': False}
        try:
            browser = p.chromium.launch_persistent_context(PROFILE, viewport={'width': 1400, 'height': 900}, args=['--disable-blink-features=AutomationControlled'], **kw)
        except Exception:
            browser = p.chromium.launch_persistent_context(PROFILE, viewport={'width': 1400, 'height': 900}, headless=False)
        page = browser.pages[0] if browser.pages else browser.new_page()
        # 登录检查
        page.goto(SEARCH.format('机器人'), timeout=60000)
        for i in range(60):
            if page.locator('.job-card-wrapper').count() > 0:
                break
            if i == 0:
                print('未登录。请在打开的浏览器窗口里用手机 Boss直聘 App 扫码登录(等待最多 5 分钟)…')
            page.wait_for_timeout(5000)
        else:
            browser.close()
            sys.exit('一直没登录成功, 结束。重新运行再试。')
        print('登录成功, 开始抓取', len(companies), '家公司…')
        for n_, name in enumerate(companies, 1):
            try:
                page.goto(SEARCH.format(urllib.parse.quote(name)), timeout=60000)
                page.wait_for_selector('.job-card-wrapper', timeout=15000)
                page.wait_for_timeout(2500)
                cards = page.locator('.job-card-wrapper')
                total = cards.count()
                tt = page.locator('.job-total').inner_text() if page.locator('.job-total').count() else ''
                titles = sorted(set(cards.locator('.job-name').all_inner_texts()))
                cur[name] = titles
                old = prev.get(name)
                link = f'(https://www.zhipin.com/web/geek/job?query={urllib.parse.quote(name)})'
                if old is None:
                    lines.append(f'- {name}（Boss直聘）：在招约 {total} 个岗位（首次记录，搜索词=公司名，可能含同名公司）{link}')
                else:
                    adds = set(titles) - set(old)
                    if adds or total != len(old):
                        show = '、'.join(sorted(adds)[:3]) + (f' 等{len(adds)}个' if len(adds) > 3 else '')
                        extra = f'，新增：{show}' if adds else ''
                        lines.append(f'- {name}（Boss直聘）：在招约 {total} 个岗位（上次约 {len(old)}）{extra} {tt and "（" + tt.strip() + "）" or ""}{link}')
                print(f'{n_}/{len(companies)} {name} {total}个岗位')
            except Exception as e:
                fails.append(name)
                print(f'{n_}/{len(companies)} {name} 失败: {str(e)[:80]}')
            page.wait_for_timeout(random.randint(6000, 11000))
        browser.close()
    # 写入文档
    block = [MARK.format(TODAY)]
    block += lines or ['- 本次抓取没有可用结果。']
    if fails:
        block.append('- 以下公司本次抓取失败：' + '、'.join(fails))
    block.append('')
    text = crypt.load_txt()
    L = text.split('\n')
    if not any(l.startswith(LOG_TITLE) for l in L):
        L += ['', '#' * 80, LOG_TITLE,
              '说明：海外公司数据来自其官网招聘系统的公开接口；中国公司条目由本机 Boss直聘 手动更新，搜索词为公司名，可能混入同名公司岗位，仅供参考。',
              '#' * 80, '']
    if block[0] in L:
        s = L.index(block[0])
        e = s + 1
        while e < len(L) and not L[e].startswith('—— ') and set(L[e].strip() or 'x') != {'#'}:
            e += 1
        del L[s - 1 if L[s - 1] == '' else s:e]
    k = next(k for k, l in enumerate(L) if l.startswith(LOG_TITLE))
    while not set(L[k].strip() or 'x') == {'#'}:
        k += 1
    L[k + 1:k + 1] = [''] + block
    crypt.save_txt('\n'.join(L))
    prev.update(cur)
    json.dump(prev, open(STATE, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('写入', len(lines), '条, 正在上传…')
    r = subprocess.run('git add data && git commit -m "cn jobs update" && git push', shell=True, cwd=ROOT)
    if r.returncode:
        print('自动上传失败, 请手动运行: cd', ROOT, '然后 git add data / git commit -m "cn jobs" / git push')
    else:
        print('已上传。网页要过几分钟才会重新生成, 可到 Actions 页手动 Run workflow(勾选只重新生成网页)。')


if __name__ == '__main__':
    sel = sys.argv[1:]
    names = [c for c in CN if c in sel] if sel else CN
    if sel and not names:
        sys.exit(f'没有找到公司, 可选: {CN}')
    run(names)
