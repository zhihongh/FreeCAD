# 微信 + Discord 内容下载器 & 定时任务

自动化下载微信（通过你的 exe 工具）和 Discord 频道中的消息，保存为 Markdown / JSON 文件，支持 Windows 定时任务自动运行。

---

## 核心问题解答

### Q: Cursor 能帮我直接运行电脑上的 exe 文件吗？

**简短回答：不能。** Cursor 的 Cloud Agent 运行在远程云端服务器上，无法直接访问你本地电脑的文件或执行本地程序。

**但 Cursor 可以帮你：**
- 编写自动化脚本（就像本工具）
- 配置定时任务
- 你只需在**本地电脑**上运行一次设置，之后一切自动执行

### 解决方案：本地 Python 脚本 + Windows 定时任务

```
你的电脑 (本地运行)
  │
  ├─ task_runner.py          ← 统一调度器
  │    │
  │    ├─ 1. 运行 wechat_downloader.exe   ← 你的微信下载工具
  │    │
  │    └─ 2. 运行 discord_downloader.py    ← Discord 消息下载
  │
  └─ Windows 任务计划程序 ← 定时触发（如每6小时）
```

---

## 快速开始（5 分钟设置）

### 第 1 步：安装 Python 依赖

```bash
cd tools/discord_downloader
pip install -r requirements.txt
```

### 第 2 步：配置你的 exe 路径

编辑 `tasks_config.json`，把微信下载 exe 的路径改成你自己的：

```json
{
  "tasks": [
    {
      "name": "wechat",
      "enabled": true,
      "description": "下载微信内容",
      "type": "exe",
      "path": "C:\\Users\\你的用户名\\tools\\wechat_downloader.exe",
      "args": [],
      "working_directory": "C:\\Users\\你的用户名\\tools\\",
      "timeout_seconds": 300,
      "wait_after_seconds": 5
    },
    {
      "name": "discord",
      "enabled": true,
      "description": "下载 Discord 频道消息",
      "type": "python",
      "script": "discord_downloader.py",
      "args": ["--last-run"],
      "timeout_seconds": 600,
      "wait_after_seconds": 0
    }
  ]
}
```

**关键字段说明：**
- `path`：你的 exe 文件完整路径（注意用 `\\` 双反斜杠）
- `args`：传给 exe 的参数列表，如 `["--output", "C:\\data"]`
- `working_directory`：exe 运行时的工作目录
- `timeout_seconds`：超时时间（秒），防止 exe 卡住
- `enabled`：设为 `false` 可跳过该任务

### 第 3 步：设置 Discord Bot（如需下载 Discord）

1. 打开 [Discord Developer Portal](https://discord.com/developers/applications)
2. 点击 "New Application" → 输入名称
3. 进入 **Bot** 页面 → 点击 "Reset Token" → 复制 Token
4. 启用 **MESSAGE CONTENT INTENT**（在 Privileged Gateway Intents 下）
5. 进入 **OAuth2 → URL Generator**
   - Scopes: 选 `bot`
   - Bot Permissions: 选 `Read Message History`、`View Channels`
6. 复制生成的 URL，浏览器打开，邀请 Bot 到你的服务器

配置 Token：

```bash
# 复制模板
copy .env.example .env

# 编辑 .env，填入你的 Bot Token
# DISCORD_BOT_TOKEN=你的token
```

### 第 4 步：测试运行

```bash
# 预览会执行什么（不实际运行）
python task_runner.py --dry-run

# 只测试微信下载
python task_runner.py --task wechat

# 只测试 Discord 下载
python task_runner.py --task discord

# 运行所有任务
python task_runner.py
```

### 第 5 步：设置定时任务

**双击 `setup_scheduled_tasks.bat`**（以管理员身份运行），选择运行频率即可。

或者手动设置：
1. 按 `Win + R` → 输入 `taskschd.msc` → 回车
2. 右侧点击 "创建基本任务"
3. 名称：`WeChatDiscordDownloader`
4. 触发器：每天 / 每小时 等
5. 操作：启动程序 → 浏览选择 `run_all_tasks.bat`
6. 完成

---

## 详细使用说明

### task_runner.py - 统一任务调度器

核心脚本，可以依次运行多个任务（exe、Python 脚本、shell 命令）。

```bash
python task_runner.py                          # 运行所有任务
python task_runner.py --dry-run                # 预览模式
python task_runner.py --task wechat            # 只运行微信任务
python task_runner.py --task discord            # 只运行 Discord 任务
python task_runner.py --config my_config.json  # 使用自定义配置
```

**支持的任务类型：**

| 类型 | 说明 | 配置字段 |
|------|------|----------|
| `exe` | 运行 Windows exe / bat / cmd 文件 | `path`, `args`, `working_directory` |
| `python` | 运行 Python 脚本 | `script`, `args` |
| `shell` | 运行 shell 命令 | `command`, `working_directory` |

### discord_downloader.py - Discord 消息下载

```bash
python discord_downloader.py                        # 下载所有频道
python discord_downloader.py --channel 123456789    # 指定频道
python discord_downloader.py --since 2025-01-01     # 指定起始日期
python discord_downloader.py --last-run             # 只下载新消息
python discord_downloader.py --list-channels        # 列出可用频道
```

配置频道 ID：编辑 `downloader_config.json`

```json
{
  "output_dir": "discord_exports",
  "format": "both",
  "channels": [123456789012345678],
  "max_messages_per_run": 5000
}
```

**获取频道 ID：** Discord 设置 → 高级 → 开启"开发者模式" → 右键频道 → "复制频道 ID"

---

## 输出内容

### 下载的文件

```
discord_exports/
├── general_20260216_080000.md        # Markdown 格式
├── general_20260216_080000.json      # JSON 格式
├── announcements_20260216_080000.md
└── announcements_20260216_080000.json
```

### 运行日志

```
logs/
├── task_runner_20260216.log             # 文字日志
├── run_20260216_080000.json             # JSON 运行报告
└── run_20260216_140000.json
```

---

## 高级配置示例

### 只运行微信下载（不用 Discord）

```json
{
  "tasks": [
    {
      "name": "wechat",
      "enabled": true,
      "type": "exe",
      "path": "C:\\tools\\wechat_downloader.exe",
      "args": ["--output", "C:\\data\\wechat"],
      "timeout_seconds": 300
    },
    {
      "name": "discord",
      "enabled": false,
      "type": "python",
      "script": "discord_downloader.py",
      "args": ["--last-run"]
    }
  ]
}
```

### 添加更多自定义任务

```json
{
  "tasks": [
    {
      "name": "wechat",
      "enabled": true,
      "type": "exe",
      "path": "C:\\tools\\wechat_downloader.exe",
      "timeout_seconds": 300,
      "wait_after_seconds": 5
    },
    {
      "name": "backup",
      "enabled": true,
      "description": "备份下载的内容",
      "type": "shell",
      "command": "xcopy /s /y discord_exports\\ D:\\backup\\discord\\",
      "timeout_seconds": 120
    },
    {
      "name": "discord",
      "enabled": true,
      "type": "python",
      "script": "discord_downloader.py",
      "args": ["--last-run"],
      "timeout_seconds": 600
    }
  ],
  "settings": {
    "stop_on_error": false
  }
}
```

---

## 常见问题

### Q: 我只想用微信 exe，不需要 Discord 下载

把 `tasks_config.json` 中 Discord 任务的 `enabled` 改为 `false` 即可。

### Q: exe 运行时需要图形界面/窗口怎么办？

如果你的 exe 需要 GUI 交互（比如弹窗确认），定时任务无法自动处理。需要确认你的 exe 支持命令行模式（静默模式），通常通过参数如 `--silent` 或 `--headless`。

### Q: 任务运行失败怎么排查？

1. 查看 `logs/` 目录下的日志文件
2. 用 `python task_runner.py --dry-run` 检查配置
3. 用 `python task_runner.py --task wechat` 单独测试
4. 检查 exe 路径是否正确（注意 `\\` 双反斜杠）

### Q: 可以在 Mac / Linux 上用吗？

可以。`task_runner.py` 和 `discord_downloader.py` 是跨平台的 Python 脚本。只需把 exe 类型换成 shell 或 python，使用 cron 代替 Task Scheduler：

```bash
chmod +x run_download.sh
crontab -e
# 添加: 0 */6 * * * /path/to/run_download.sh
```

### Q: Bot Token 安全吗？

- `.env` 文件已被 `.gitignore` 排除，不会提交到 Git
- 不要在公开场合分享 Token
- 如果泄露，在 Discord Developer Portal 立即重置

---

## 文件说明

| 文件 | 说明 |
|------|------|
| `task_runner.py` | **统一任务调度器** — 依次运行 exe + Python 脚本 |
| `tasks_config.json` | 任务配置（定义运行什么、怎么运行） |
| `discord_downloader.py` | Discord 消息下载器 |
| `downloader_config.json` | Discord 下载配置（频道、格式等） |
| `requirements.txt` | Python 依赖列表 |
| `.env.example` | 环境变量模板（Bot Token） |
| `run_all_tasks.bat` | Windows 批处理 — 运行所有任务 |
| `setup_scheduled_tasks.bat` | Windows 一键创建定时任务 |
| `run_download.bat` | Windows 批处理 — 只运行 Discord 下载 |
| `run_download.sh` | Linux/macOS 脚本 — 只运行 Discord 下载 |
