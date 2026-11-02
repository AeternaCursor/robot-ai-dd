# 机器人/具身智能/AI 公司尽调网页：使用说明

> 本说明就放在这个仓库里，任何设备打开仓库首页即可查看，不需要保存在电脑上。

## 一、怎么打开尽调网页

- 网址：https://aeternacursor.github.io/robot-ai-dd/
- 手机、平板、电脑的浏览器都能打开，不需要装任何软件。
- 打开后输入密码（密码由你本人保管：手机备忘录/纸条；GitHub 上只存加密版）。
- 勾选"在这台设备上记住密码"，下次在这台设备上打开就不用再输密码。公用电脑不要勾选。
- 想分享给别人，就把网址和密码一起发给对方。

## 二、网页怎么用

- **目录**：电脑上目录在左边；手机上点左上角"目录"按钮。点公司名会直接跳到这家公司。
- **搜索**：在顶部搜索框输入公司名或关键词（例如"融资""上市"），网页只显示相关公司。
- **折叠/展开板块**：点右上角按钮，可以一次收起或展开所有板块。
- **每周更新**：目录最下面"本周更新记录（每周一自动生成）"，最新一周排最上面，只保留最近 8 周。
- **招聘动态**：目录最下面"招聘动态（每周自动生成）"，看各公司在招岗位数量和本周新增岗位。岗位大量增加往往说明公司在扩张。

## 三、每周自动更新做了什么

- **时间**：每周一北京时间 0 点左右自动运行（GitHub 高峰时段可能晚几十分钟）。**不需要任何人开机或操作**。
- **新闻监控（约 170 家）**：从 Google 新闻抓各公司最近 7 天新闻，用关键词（融资、估值、上市、营收、并购、裁员、诉讼、量产、高管变动、招聘/扩招/校招等）挑出重要变化，标题原样引用并附来源链接，写进"本周更新记录"。不改动正文结论。
- **海外招聘监控（38 家，全自动）**：读取各公司官网招聘系统（Ashby/Greenhouse/Lever 等）公开接口，对比在招岗位变化，写进"招聘动态"。
- 某周没有重要变化时，会写"本周重点公司未发现……重要变化"。
- 费用：GitHub 免费额度足够用。

## 四、偶尔需要做的事

### 1. 想马上更新一次（不等周一）

1. 登录 GitHub，打开 https://github.com/AeternaCursor/robot-ai-dd/actions
2. 左边点 **weekly-update**，右边点 **Run workflow**，再点绿色 **Run workflow** 按钮。
3. 等变成绿色对勾（约 5 分钟），刷新网页。

（勾选"只重新生成网页，不抓新闻"= 只重建网页，不抓新数据）

### 2. 查看有没有失败

- 打开上面的 Actions 页面，**只看最上面最新一条**：绿勾=正常，红叉=有问题。旧记录只是历史，不用管。
- 偶尔失败一次不用管，下周照常。连续两次红叉再找人帮忙。

### 3. 修改网页密码

改密码需要在电脑上操作（需要先把本仓库下载到电脑）。流程见仓库里 `tools/crypt.py` 的 `repw` 命令：
1. 把仓库下载到电脑（Code → Download ZIP 解压，或用 git clone），安装 Python 和 cryptography
2. 运行 `python tools/crypt.py repw`（先输旧密码，再输两遍新密码，不丢任何更新记录）
3. 把新加密数据 `data/dd.txt.enc` 提交回仓库（或找 AI 助手帮忙）
4. 到 Settings → Secrets → Actions 把 `SITE_PASSWORD` 改成同一个新密码，再手动 Run workflow（勾选只重新生成网页）

### 4. 中国公司招聘动态（Boss直聘，手动可选）

工具在仓库 `tools/jobs_cn.py`，本机平时不保留。想跑时按下面步骤（也可直接让 AI 助手代跑）：

**第一步：把仓库下载回电脑**（PowerShell 里逐行运行）
```powershell
cd d:\Jump
git -c http.proxy=http://127.0.0.1:7897 -c http.sslBackend=openssl clone https://github.com/AeternaCursor/robot-ai-dd.git
cd robot-ai-dd
git config http.proxy http://127.0.0.1:7897
git config http.sslBackend openssl
```

**第二步：首次需要装依赖**（只装一次，以后跳过）
```powershell
pip install playwright
playwright install chromium
```

**第三步：运行工具**（把 密码 换成你的网页密码）
```powershell
$env:SITE_PASSWORD='你的网页密码'
python tools\jobs_cn.py              # 全部 43 家，约 10 分钟
python tools\jobs_cn.py 宇树科技      # 只跑某一家
```

**第四步：扫码登录（关键！）**
运行后会**自动弹出一个浏览器窗口**，显示 Boss直聘 登录页：
1. 手机打开 Boss直聘 App → 右上角 ➕ → 扫一扫 → 扫屏幕上的二维码 → 手机上点确认
2. **不要关闭那个浏览器窗口**，程序在它里面工作
3. 登录成功会记住，以后再跑不用重新扫

**第五步：等它跑完**
- 每家间隔几秒，会打印进度；结束后自动上传
- 然后到 Actions 页面点 Run workflow（勾选"只重新生成网页"），几分钟后网页的"招聘动态"就能看到
- 搜索页可能弹滑块验证，用鼠标拖一下即可

**注意**：每周最多跑一次（防账号被限制）；搜索结果可能含同名公司，仅供参考。用完后可把 `robot-ai-dd` 文件夹删掉，保持本机干净。

### 5. AI 接口配置（可选，用于全量改写"一句话看懂"）

网页已上线 5 家 AI 改写样稿；想让 AI 改写全部 523 家时，按此配置（一次性操作，约花 1 元）：

**第一步：申请 AI 接口（DeepSeek）**
1. 打开 https://platform.deepseek.com 注册/登录
2. 充值（10 元足够，实际改写 523 家约花 0.5~1 元）
3. 左侧 **API Keys** → 创建 → 复制 `sk-` 开头的 key

**第二步：运行改写工具**（仓库已下载到电脑的前提下，PowerShell 逐行）
```powershell
cd d:\Jump\robot-ai-dd
$env:SITE_PASSWORD='你的网页密码'
$env:AI_API='https://api.deepseek.com/chat/completions'
$env:AI_KEY='你复制的key'
$env:AI_MODEL='deepseek-chat'
python tools\rewrite.py              # 全部剩余公司(断点续跑, 跑过的自动跳过)
python tools\rewrite.py 宇树科技      # 只改一家试效果
```

**第三步：验收上线**
- 工具自带校验：新句必须保留原句数字、超长/过短自动拦截保留原句
- 跑完后让 AI 助手抽查 10 家防编造，确认后 `git add data; git commit -m "rewrite"; git push`，再 Run workflow（勾选只重新生成网页）

**安全**：key 只在命令行临时用，绝不写进文件/仓库；**用完立即回平台删除该 key**。另外不要用智谱 glm-4-flash 免费模型做这事（实测会编造事实）。

## 五、安全说明

- 仓库是公开的，但里面只有加密后的数据，没有密码看不到内容。
- 加密：AES-256-GCM + PBKDF2（30 万轮），解密在浏览器本地完成。
- **密码只存在你脑子里和手机备忘录里**，绝不放进仓库或发给不信任的人。
- 密码丢失 = 数据无法找回（加密的代价）。请务必备份在两处以上。
- 密码越长越安全，至少 10 位。

## 六、内容都在哪里

| 内容 | 位置 |
|---|---|
| 尽调网页（523 家 + 每周更新 + 招聘动态） | https://aeternacursor.github.io/robot-ai-dd/ |
| 本使用说明 | 本仓库 README（你正在看的页面） |
| 程序、加密数据、运行记录 | 全部在本仓库 https://github.com/AeternaCursor/robot-ai-dd |
| 523 家公司 Excel 汇总表（加密版） | 本仓库 `data/xlsx.enc`，用网页密码可解开 |
| 网页密码 | 只在你本人手里（GitHub 只存加密后的密钥副本） |

**本机不需要保存任何文件。** 需要改密码或跑中国招聘工具时，再把仓库临时下载到电脑即可。

想取回 Excel 汇总表：把仓库下载到电脑后运行 `python tools/crypt.py dec data/xlsx.enc 汇总表.xlsx`，输入网页密码即可。
