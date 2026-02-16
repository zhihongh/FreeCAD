# Discord 频道消息下载器

自动下载 Discord 频道中的消息，保存为 Markdown 和/或 JSON 文件。支持定时运行，方便定期归档 Discord 上的文章和讨论内容。

## 关于 Cursor / Cloud Agent 的说明

**重要提示：** Cursor 的 Cloud Agent 运行在远程云端服务器上，**无法**直接在你的本地电脑上执行 exe 文件或访问本地应用程序。

但是，你可以：

1. **使用本工具在本地电脑上运行** — 将此工具下载到本地，配合 Windows 任务计划程序或 Linux cron 定时执行
2. **在 Cursor 中编辑和调试代码** — 使用 Cursor 作为编辑器来修改和完善脚本
3. **在本地终端中手动运行** — 直接在本地命令行中执行 Python 脚本

## 工作原理

本工具通过 Discord Bot API 来读取频道消息（不需要运行 exe 文件）：

```
Discord 服务器 → Discord Bot API → 本脚本 → Markdown/JSON 文件
```

## 安装步骤

### 1. 安装 Python 依赖

```bash
cd tools/discord_downloader
pip install -r requirements.txt
```

### 2. 创建 Discord Bot

1. 打开 [Discord Developer Portal](https://discord.com/developers/applications)
2. 点击 "New Application"，输入名称（如 "消息下载器"）
3. 进入左侧 **Bot** 页面
4. 点击 "Reset Token" 获取 Bot Token（**请妥善保管，不要泄露**）
5. 在 "Privileged Gateway Intents" 下启用 **MESSAGE CONTENT INTENT**
6. 进入左侧 **OAuth2 → URL Generator**
   - Scopes: 选择 `bot`
   - Bot Permissions: 选择 `Read Message History`、`View Channels`
7. 复制生成的 URL，在浏览器中打开，将 Bot 邀请到你的 Discord 服务器

### 3. 配置 Token

复制 `.env.example` 为 `.env`，填入你的 Bot Token：

```bash
cp .env.example .env
# 编辑 .env 文件，将 your_bot_token_here 替换为实际的 token
```

### 4. 配置频道（可选）

编辑 `downloader_config.json`：

```json
{
  "output_dir": "discord_exports",
  "format": "both",
  "channels": [123456789012345678, 987654321098765432],
  "max_messages_per_run": 5000,
  "include_attachments": true,
  "include_embeds": true,
  "include_reactions": true
}
```

- `channels`：要下载的频道 ID 列表。留空 `[]` 则下载 Bot 可访问的所有频道
- `format`：输出格式，可选 `"markdown"`、`"json"` 或 `"both"`
- `output_dir`：输出目录

**如何获取频道 ID：** 在 Discord 中开启开发者模式（设置 → 高级 → 开发者模式），然后右键点击频道，选择"复制频道 ID"。

## 使用方法

### 基本用法

```bash
# 下载所有可访问频道的消息
python discord_downloader.py

# 下载指定频道
python discord_downloader.py --channel 123456789012345678

# 下载多个指定频道
python discord_downloader.py --channel 111111111 --channel 222222222

# 只下载某个日期之后的消息
python discord_downloader.py --since 2025-01-01

# 只下载上次运行后的新消息（推荐用于定时任务）
python discord_downloader.py --last-run

# 列出所有可访问的频道
python discord_downloader.py --list-channels
```

### 输出示例

下载的消息会保存在 `discord_exports/` 目录下：

```
discord_exports/
├── general_20250216_080000.md      # Markdown 格式
├── general_20250216_080000.json    # JSON 格式
├── announcements_20250216_080000.md
└── announcements_20250216_080000.json
```

## 定时下载设置

### Windows：使用任务计划程序

**方法一：自动创建（推荐）**

以管理员身份运行 `setup_task_scheduler.bat`，会自动创建每 6 小时执行一次的定时任务。

**方法二：手动创建**

1. 按 `Win+R`，输入 `taskschd.msc` 打开任务计划程序
2. 点击右侧 "创建基本任务"
3. 设置名称："Discord消息下载"
4. 触发器：选择 "每天" 或自定义间隔
5. 操作：选择 "启动程序"，浏览选择 `run_download.bat`
6. 勾选 "当用户未登录时也运行"
7. 完成

### Linux / macOS：使用 cron

```bash
# 使脚本可执行
chmod +x run_download.sh

# 编辑 crontab
crontab -e

# 添加以下行（每6小时运行一次）：
0 */6 * * * /absolute/path/to/discord_downloader/run_download.sh

# 或者每天早上8点运行：
0 8 * * * /absolute/path/to/discord_downloader/run_download.sh
```

## 常见问题

### Q: Cursor 能直接帮我运行本地的 exe 文件吗？

**A:** 不能。Cursor 的 AI 助手（包括 Cloud Agent）运行在云端服务器上，无法直接访问或执行你电脑上的程序。但你可以：
- 让 Cursor 帮你**编写**自动化脚本（就像本工具）
- 在本地终端中自己运行这些脚本
- 使用系统自带的定时任务功能来自动执行

### Q: 需要一直开着电脑吗？

**A:** 是的，定时任务需要电脑处于开机状态。如果你希望 24/7 运行，可以考虑：
- 部署到云服务器（如 AWS、Azure、阿里云）
- 使用 GitHub Actions 定时触发
- 使用 Raspberry Pi 等低功耗设备

### Q: Bot Token 安全吗？

**A:** Bot Token 就像密码，请务必：
- 不要将 `.env` 文件提交到 Git（已在 `.gitignore` 中排除）
- 不要在公开场合分享 Token
- 如果 Token 泄露，立即在 Discord Developer Portal 中重置

### Q: 能下载私信（DM）吗？

**A:** Bot 不能访问用户的私信。本工具仅支持下载 Bot 被邀请到的服务器中的频道消息。

## 文件说明

| 文件 | 说明 |
|------|------|
| `discord_downloader.py` | 主程序 |
| `requirements.txt` | Python 依赖 |
| `downloader_config.json` | 下载配置 |
| `.env.example` | 环境变量模板 |
| `run_download.bat` | Windows 定时任务脚本 |
| `run_download.sh` | Linux/macOS 定时任务脚本 |
| `setup_task_scheduler.bat` | Windows 任务计划自动创建脚本 |
