"""加密/解密工具。
用法:
  python tools/crypt.py init 原始.txt      本地首次加密(会提示输入密码), 生成 data/dd.txt.enc
  python tools/crypt.py build             用环境变量 SITE_PASSWORD 解密数据, 生成加密网页 site/index.html
"""
import base64, gzip, json, os, subprocess, sys, tempfile, getpass, datetime
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENC_TXT = os.path.join(ROOT, 'data', 'dd.txt.enc')
SITE = os.path.join(ROOT, 'site')
ITER = 300000
b64 = lambda b: base64.b64encode(b).decode()


def _key(pw, salt):
    return PBKDF2HMAC(hashes.SHA256(), 32, salt, ITER).derive(pw.encode('utf-8'))


def encrypt(data: bytes, pw: str) -> str:
    salt, iv = os.urandom(16), os.urandom(12)
    ct = AESGCM(_key(pw, salt)).encrypt(iv, gzip.compress(data, 9), None)
    return json.dumps({'v': 1, 'iter': ITER, 'salt': b64(salt), 'iv': b64(iv), 'ct': b64(ct)})


def decrypt(blob: str, pw: str) -> bytes:
    d = json.loads(blob)
    k = PBKDF2HMAC(hashes.SHA256(), 32, base64.b64decode(d['salt']), d['iter']).derive(pw.encode('utf-8'))
    return gzip.decompress(AESGCM(k).decrypt(base64.b64decode(d['iv']), base64.b64decode(d['ct']), None))


def password():
    pw = os.environ.get('SITE_PASSWORD')
    if not pw:
        sys.exit('缺少环境变量 SITE_PASSWORD')
    return pw


def load_txt() -> str:
    return decrypt(open(ENC_TXT, encoding='utf-8').read(), password()).decode('utf-8')


def save_txt(text: str):
    open(ENC_TXT, 'w', encoding='utf-8').write(encrypt(text.encode('utf-8'), password()))


def build():
    pw = password()
    today = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=8)).date().isoformat()
    with tempfile.TemporaryDirectory() as t:
        p, o = os.path.join(t, 'a.txt'), os.path.join(t, 'a.html')
        open(p, 'w', encoding='utf-8').write(load_txt())
        subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'to_html.py'), p, o, today], check=True)
        html = open(o, 'rb').read()
    tpl = open(os.path.join(ROOT, 'tools', 'page.html'), encoding='utf-8').read()
    os.makedirs(SITE, exist_ok=True)
    open(os.path.join(SITE, 'index.html'), 'w', encoding='utf-8').write(tpl.replace('__BLOB__', encrypt(html, pw)))
    open(os.path.join(SITE, '.nojekyll'), 'w').close()
    print('site/index.html 已生成')


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'init':
        src = sys.argv[2]
        pw = getpass.getpass('请输入网页密码(输入时不显示): ')
        if len(pw) < 10:
            sys.exit('密码太短, 请至少 10 位')
        if getpass.getpass('请再输入一次: ') != pw:
            sys.exit('两次输入不一致')
        text = open(src, encoding='utf-8').read().lstrip('\ufeff')
        os.makedirs(os.path.dirname(ENC_TXT), exist_ok=True)
        open(ENC_TXT, 'w', encoding='utf-8').write(encrypt(text.encode('utf-8'), pw))
        assert decrypt(open(ENC_TXT, encoding='utf-8').read(), pw).decode('utf-8') == text
        print('完成: data/dd.txt.enc 已生成, 请把同一个密码填到 GitHub 的 SITE_PASSWORD')
    elif cmd == 'build':
        build()
    else:
        print(__doc__)
