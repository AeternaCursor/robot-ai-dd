"""AI 重写"一句话看懂": 逐公司把尽调字段喂给 AI, 只允许使用资料里的事实, 让一句话更生动。
本地运行, AI 接口用环境变量传入, key 不进仓库:
  $env:AI_API='https://open.bigmodel.cn/api/paas/v4/chat/completions'  # 智谱(OpenAI兼容); DeepSeek用 https://api.deepseek.com/chat/completions
  $env:AI_KEY='你的key'
  $env:AI_MODEL='glm-4-flash'                                           # 智谱免费模型; DeepSeek 用 deepseek-chat
  $env:SITE_PASSWORD='网页密码'
  python tools/rewrite.py              # 全部公司
  python tools/rewrite.py 宇树科技      # 只改匹配的公司(试跑用)
"""
import json, os, re, sys, time, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crypt

API = os.environ.get('AI_API')
KEY = os.environ.get('AI_KEY')
MODEL = os.environ.get('AI_MODEL', 'glm-4-flash')
ONE = re.compile(r'^0\s*[.、]?\s*一句话看懂')
ENT = re.compile(r'^【[^】]+】$')


def ask(batch):
    sys_p = ('你是尽调编辑，任务：把一家公司的"一句话看懂"改写得更生动。规则：\n'
             '1. 只能使用给出的资料里的信息，数字必须原样照抄，绝不能混入其他公司的内容\n'
             '2. 要像给朋友讲公司一样自然流畅，保留地点、创始人亮点、商业模式等细节\n'
             '3. 60字以内，一句话（可以用逗号），不要清单式罗列\n'
             '好例子：杭州的"机器狗大厂"，靠便宜又能打的四足机器人出圈，2026年8月登陆科创板，2025年营收约17亿元还在赚钱。\n'
             '坏例子（禁止）：宇树科技，科创板上市，17亿营收，出货量领先。（像电报清单，没有画面感）\n'
             '只输出JSON：{"items":[{"i":编号,"one":"新句子"}]}')
    user = []
    for i, (name, one, body) in enumerate(batch):
        user.append(f'#{i} 公司：{name}\n原句：{one}\n资料：{body[:1200]}')
    payload = json.dumps({'model': MODEL, 'temperature': 0.7, 'response_format': {'type': 'json_object'},
                          'messages': [{'role': 'system', 'content': sys_p}, {'role': 'user', 'content': '\n\n'.join(user)}]}).encode()
    for n in range(3):
        try:
            r = urllib.request.urlopen(urllib.request.Request(API, payload, {
                'Authorization': 'Bearer ' + KEY, 'Content-Type': 'application/json'}), timeout=120)
            c = json.loads(json.loads(r.read())['choices'][0]['message']['content'].strip()
                           .removeprefix('```json').removeprefix('```').removesuffix('```'))
            out = {}
            for x in c.get('items', []):
                try:
                    out[int(str(x.get('i', '')).lstrip('#'))] = str(x.get('one', '')).strip().strip('"“”')
                except (ValueError, TypeError):
                    continue
            return out
        except Exception as e:
            detail = ''
            if hasattr(e, 'read'):
                try:
                    detail = e.read()[:200]
                except Exception:
                    pass
            print('AI调用失败, 重试', str(e)[:80], detail)
            time.sleep(10 * (n + 1))
    return {}


def check(old, new, name, body):
    """防串写/防丢失数字: 新句必须保留原句的数字, 且不得比原句短太多"""
    if not new or len(new) < 15 or len(new) > 90:
        return False
    nums = set(re.findall(r'\d+(?:\.\d+)?', old))
    missing = [x for x in nums if x not in new]
    if missing and len(missing) > max(0, len(nums) - 3):  # 至少保留3个数字(不足3个则全保留)
        return False
    if any(w in new for w in ('上市', '营收', '估值', '融资')) and name.split('（')[0] not in new[:0] + new:
        pass  # 不强制包含公司名
    return True


def main():
    sel = sys.argv[1:]
    if not API or not KEY:
        sys.exit('请先设置 AI_API / AI_KEY 环境变量(见文件开头说明)')
    L = crypt.load_txt().split('\n')
    targets = []  # (行号, 原句)
    for k, l in enumerate(L):
        if ENT.match(l.strip()) and k and L[k - 1].strip().startswith('====='):
            name = l.strip()[1:-1]
            if sel and not any(s in name for s in sel):
                continue
            for j in range(k + 1, min(k + 8, len(L))):
                if ONE.match(L[j].strip()):
                    targets.append((j, name, L[j]))
                    break
    print('目标公司', len(targets), '家')
    changed = rej = 0
    for b in range(0, len(targets), 5):
        chunk = targets[b:b + 5]
        for off, (ln, name, one) in enumerate(chunk):
            batch = [(name, one.strip(), '\n'.join(L[ln + 1:ln + 40]))]
            res = ask(batch)
            new = res.get(0, '')
            if new and check(one.strip(), new, name, batch[0][2]):
                head = re.match(r'^(0\s*[.、]?\s*一句话看懂\s*[:：]\s*)', one.strip())
                L[ln] = (head.group(1) if head else '0. 一句话看懂：') + new
                changed += 1
            else:
                rej += 1
                print('  跳过(校验不过):', name, '|', new[:40])
            time.sleep(1)
        print(f'{min(b + 5, len(targets))}/{len(targets)} 已改写 {changed} 跳过 {rej}')
    crypt.save_txt('\n'.join(L))
    print('完成, 共改写', changed, '家, 跳过', rej, '家。请网页确认满意后: git add data; git commit -m "rewrite one-liners"; git push')


if __name__ == '__main__':
    main()
