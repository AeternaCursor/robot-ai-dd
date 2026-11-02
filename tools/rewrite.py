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
    sys_p = ('你是尽调编辑。对每家公司，只根据给出的资料，把"一句话看懂"改写得生动易记：口语化、有画面感、像给朋友讲一家公司，'
             '必须保留资料里的关键数字和核心结论（上市、营收、估值、卖点）。严禁使用资料里没有的信息，数字必须原样照抄。'
             '只输出JSON：{"items":[{"i":编号,"one":"新的一句话，60字以内，不用引号开头"}]}')
    user = []
    for i, (name, one, body) in enumerate(batch):
        user.append(f'#{i} 公司：{name}\n原句：{one}\n资料：{body[:1200]}')
    payload = json.dumps({'model': MODEL, 'temperature': 0.3, 'response_format': {'type': 'json_object'},
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
    changed = 0
    for b in range(0, len(targets), 10):
        chunk = targets[b:b + 10]
        batch = [(name, one.strip(), '\n'.join(L[ln + 1:ln + 40])) for ln, name, one in chunk]
        res = ask(batch)
        for i, one in res.items():
            if 0 <= i < len(chunk) and one:
                ln = chunk[i][0]
                head = re.match(r'^(0\s*[.、]?\s*一句话看懂\s*[:：]\s*)', chunk[i][2].strip())
                L[ln] = (head.group(1) if head else '0. 一句话看懂：') + one
                changed += 1
        print(f'{min(b + 10, len(targets))}/{len(targets)} 已改写 {changed}')
        time.sleep(2)
    crypt.save_txt('\n'.join(L))
    print('完成, 共改写', changed, '家。请网页确认满意后: git add data; git commit -m "rewrite one-liners"; git push')


if __name__ == '__main__':
    main()
