# xinwen-nl-alexa

荷兰新闻语音 MP3 定时生成器

## 功能

- 每日自动抓取 xinwen.nl 新闻
- 转换为中文语音 MP3
- 上传到 Google Drive

## 快速开始

### 1. 安装依赖

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 配置 Google Drive

项目支持两种认证方法; 二选一即可：

#### 1. 使用 Service Account（默认）

1. 前往 [Google Cloud Console](https://console.cloud.google.com/)
2. 创建项目 → 启用 Google Drive API
3. 创建 Service Account → 下载 JSON 凭证
4. 将凭证重命名为 `credentials.json` 放到项目根目录
5. 分享目标文件夹给 Service Account 邮箱（赋予编辑权限）

> 注意：服务账号自身没有存储配额，因此目标文件夹必须位于一个“共享云盘"(shared drive)。

#### 2. 使用 OAuth 用户授权

1. 在 Cloud Console 开启 Drive API，同样创建一个 OAuth 2.0 客户端 ID
   （应用类型选择 "桌面应用"）。
2. 下载生成的 `client_secrets.json` 文件到项目根目录。
3. 首次运行脚本时会自动弹出浏览器请求登录，凭证会保存在
   `~/.gdrive_token.pickle` 中供后续使用。

两种方式都可以与脚本中的 `FOLDER_ID` 变量搭配使用，后者
在不用共享云盘的情况下直接使用个人 Drive 配额更方便。
### 3. 测试运行

```bash
python main.py
```

### 4. 设置定时任务 (cron)

```bash
# 每天早上 8 点运行
0 8 * * * /path/to/venv/bin/python /path/to/main.py >> /path/to/cron.log 2>&1
```

## 文件结构

```
├── scraper.py      # 新闻爬虫
├── tts.py         # 语音合成
├── gdrive.py      # Google Drive 上传
├── main.py        # 主程序入口
├── credentials.json  # Google 凭证 (需要自己下载)
├── output/        # 生成的 MP3 文件
└── requirements.txt
```
