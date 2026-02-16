# 美股每日交易报告生成器 📊

Daily Trading Report Generator — 自动生成中文美股盘后分析PDF报告

## 功能概述

每个交易日收盘后自动生成包含以下内容的PDF报告：

| 章节 | 内容 |
|------|------|
| 〇 | 本周重大经济事件及财报日历 |
| 一 | 今日市场摘要 (财经新闻 + 市场情绪 + 资金流向) |
| 二 | 主要指数表现与板块轮动分析 (NASDAQ/S&P500/SOX/ETF排行) |
| 三 | 交易板块与个股建议 |
| 四 | 热门板块深度分析 (AI/存储/服务器/电力) |
| 五 | 涨跌排行榜 Top 10 |
| 六 | 放量异动与技术信号股票 (量比>1.5x) |
| 七 | 重点跟踪个股详细分析 (NVDA/SMCI/MU/ALAB/CRDO/LULU/UPST/WDC/STX/TSLA/AAPL/GOOGL/AMD) |
| 八 | 趋势展望与期权交易策略 |
| 九 | 报告说明 |

## 技术指标

- **RSI** (14日相对强弱指标)
- **MA** (5/10/20/50日移动均线)
- **MACD** (指数平滑移动均线)
- **布林带** (Bollinger Bands)
- **成交量分析** (量比、放量检测)
- **突破信号** (金叉/死叉、均线突破、布林带突破)

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 生成今日报告
python generate_report.py

# 生成并保存原始数据
python generate_report.py --save-data

# 指定输出路径
python generate_report.py --output my_report.pdf
```

## 定时生成 (像Grok一样每天自动产生)

### 方式1: GitHub Actions (推荐)

已配置好 `.github/workflows/daily_trading_report.yml`，推送到GitHub后：
- 自动在每个交易日 **1:45 PM PDT** 生成报告
- 可在 GitHub Actions 页面手动触发
- 报告自动保存为 artifact 并提交到仓库

### 方式2: Python 调度器

```bash
# 启动定时调度器 (默认1:45 PM)
python schedule_report.py

# 自定义时间
python schedule_report.py --time "14:00"

# 立即运行一次
python schedule_report.py --run-once
```

### 方式3: Crontab

```bash
# 查看crontab配置
python schedule_report.py --setup-cron

# 快速安装
(crontab -l 2>/dev/null; echo "45 20 * * 1-5 cd /path/to/daily_trading_report && python3 generate_report.py --save-data") | crontab -
```

### 方式4: Systemd Timer

```bash
python schedule_report.py --setup-systemd
```

## 数据来源

- **Yahoo Finance** (via yfinance) — 实时行情、历史数据、基本面
- 涨跌颜色采用 **A股习惯**: 红涨绿跌 🔴🟢

## 文件结构

```
daily_trading_report/
├── generate_report.py    # 主入口 - 生成报告
├── market_data.py        # 市场数据获取模块
├── report_generator.py   # PDF报告生成模块
├── schedule_report.py    # 定时调度器
├── requirements.txt      # Python依赖
├── reports/              # 生成的PDF报告
└── data/                 # 原始数据JSON
```

## 免责声明

本报告仅供学习参考，不构成任何投资建议。股市有风险，投资需谨慎。
