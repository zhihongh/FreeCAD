#!/usr/bin/env python3
"""
定时报告生成调度器 - Scheduled Report Generator
像Grok一样每天定时自动生成报告。

支持多种调度方式:
1. Python schedule 库 (内置，直接运行)
2. crontab 配置 (系统级定时任务)
3. GitHub Actions (CI/CD定时触发)
4. systemd timer (Linux服务)

Usage:
    # 方式1: 直接运行Python调度器
    python schedule_report.py

    # 方式2: 生成crontab配置
    python schedule_report.py --setup-cron

    # 方式3: 运行一次(用于cron/CI)
    python schedule_report.py --run-once

    # 自定义时间
    python schedule_report.py --time "13:45"
"""

import argparse
import os
import sys
import time
import subprocess
from datetime import datetime

import schedule


REPORT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TIME = "13:45"  # 1:45 PM PDT (after market close at 1:00 PM PDT)


def run_report_generation():
    """执行报告生成"""
    now = datetime.now()
    print(f"\n{'='*60}")
    print(f"  🕐 定时任务触发: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(
            [sys.executable, os.path.join(REPORT_DIR, "generate_report.py"), "--save-data"],
            cwd=REPORT_DIR,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout
        )
        print(result.stdout)
        if result.returncode != 0:
            print(f"⚠️ 报告生成出错:\n{result.stderr}")
        else:
            print("✅ 定时报告生成成功!")

            # Log successful generation
            log_file = os.path.join(REPORT_DIR, "data", "schedule_log.txt")
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            with open(log_file, "a") as f:
                f.write(f"{now.strftime('%Y-%m-%d %H:%M:%S')} - Report generated successfully\n")

    except subprocess.TimeoutExpired:
        print("⚠️ 报告生成超时(>10分钟)")
    except Exception as e:
        print(f"❌ 报告生成失败: {e}")


def setup_crontab():
    """生成crontab配置"""
    python_path = sys.executable
    script_path = os.path.join(REPORT_DIR, "generate_report.py")

    # 1:45 PM PDT = 20:45 UTC (during DST) or 21:45 UTC (standard time)
    cron_line_dst = f"45 20 * * 1-5 cd {REPORT_DIR} && {python_path} {script_path} --save-data >> {REPORT_DIR}/data/cron.log 2>&1"
    cron_line_std = f"45 21 * * 1-5 cd {REPORT_DIR} && {python_path} {script_path} --save-data >> {REPORT_DIR}/data/cron.log 2>&1"

    print("\n📋 Crontab 配置 (复制以下内容到 crontab -e):\n")
    print("# 美股每日交易报告 - 周一至周五收盘后自动生成")
    print(f"# PDT (夏令时 3-11月):")
    print(f"{cron_line_dst}")
    print(f"# PST (冬令时 11-3月):")
    print(f"{cron_line_std}")
    print()

    print("🔧 快速设置命令:")
    print(f'  (crontab -l 2>/dev/null; echo "{cron_line_dst}") | crontab -')
    print()

    return cron_line_dst


def setup_systemd_timer():
    """生成systemd timer配置"""
    python_path = sys.executable
    script_path = os.path.join(REPORT_DIR, "generate_report.py")

    service_content = f"""[Unit]
Description=美股每日交易报告生成
After=network.target

[Service]
Type=oneshot
WorkingDirectory={REPORT_DIR}
ExecStart={python_path} {script_path} --save-data
StandardOutput=append:{REPORT_DIR}/data/systemd.log
StandardError=append:{REPORT_DIR}/data/systemd_error.log

[Install]
WantedBy=multi-user.target
"""

    timer_content = f"""[Unit]
Description=美股每日交易报告定时器
Requires=trading-report.service

[Timer]
OnCalendar=Mon..Fri *-*-* 13:45:00 America/Los_Angeles
Persistent=true

[Install]
WantedBy=timers.target
"""

    print("\n📋 Systemd Timer 配置:\n")
    print("1. 创建 service 文件: /etc/systemd/system/trading-report.service")
    print(service_content)
    print("2. 创建 timer 文件: /etc/systemd/system/trading-report.timer")
    print(timer_content)
    print("3. 启用命令:")
    print("   sudo systemctl enable trading-report.timer")
    print("   sudo systemctl start trading-report.timer")


def generate_github_actions():
    """生成GitHub Actions workflow"""
    workflow = """name: Daily Trading Report

on:
  schedule:
    # Run at 1:45 PM PDT (20:45 UTC) Monday-Friday
    - cron: '45 20 * * 1-5'
  workflow_dispatch:  # Allow manual trigger

jobs:
  generate-report:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.12'

    - name: Install dependencies
      run: |
        pip install -r daily_trading_report/requirements.txt
        sudo apt-get install -y fonts-wqy-microhei

    - name: Generate Report
      working-directory: daily_trading_report
      run: python generate_report.py --save-data

    - name: Upload Report
      uses: actions/upload-artifact@v4
      with:
        name: trading-report-${{ github.run_id }}
        path: daily_trading_report/reports/*.pdf
        retention-days: 30

    - name: Commit report to repo
      run: |
        git config user.name "Trading Report Bot"
        git config user.email "bot@trading-report.local"
        git add daily_trading_report/reports/ daily_trading_report/data/
        git diff --staged --quiet || git commit -m "Daily trading report $(date +%Y-%m-%d)"
        git push
"""

    workflow_dir = os.path.join(REPORT_DIR, "..", ".github", "workflows")
    os.makedirs(workflow_dir, exist_ok=True)
    workflow_path = os.path.join(workflow_dir, "daily_trading_report.yml")

    with open(workflow_path, "w") as f:
        f.write(workflow)

    print(f"\n✅ GitHub Actions workflow 已生成: {workflow_path}")
    print("  推送到GitHub后，将自动在每个交易日1:45 PM PDT生成报告")
    print("  也可以在GitHub Actions页面手动触发")

    return workflow_path


def main():
    parser = argparse.ArgumentParser(description="美股交易报告定时调度器")
    parser.add_argument("--time", type=str, default=DEFAULT_TIME,
                        help=f"Daily generation time (HH:MM, default: {DEFAULT_TIME})")
    parser.add_argument("--run-once", action="store_true",
                        help="Run once immediately and exit")
    parser.add_argument("--setup-cron", action="store_true",
                        help="Print crontab setup instructions")
    parser.add_argument("--setup-systemd", action="store_true",
                        help="Print systemd timer setup instructions")
    parser.add_argument("--setup-github-actions", action="store_true",
                        help="Generate GitHub Actions workflow")
    args = parser.parse_args()

    print("=" * 60)
    print("  美股每日交易报告 - 定时调度器")
    print("  Daily Trading Report - Scheduler")
    print("=" * 60)

    if args.run_once:
        print("\n🔄 立即执行一次报告生成...")
        run_report_generation()
        return

    if args.setup_cron:
        setup_crontab()
        return

    if args.setup_systemd:
        setup_systemd_timer()
        return

    if args.setup_github_actions:
        generate_github_actions()
        return

    # Default: Run the Python scheduler
    gen_time = args.time
    print(f"\n⏰ 已配置每日 {gen_time} 自动生成报告")
    print("  (周一至周五，美股收盘后)")
    print("  按 Ctrl+C 停止\n")

    # Schedule the job for weekdays only
    def weekday_job():
        if datetime.now().weekday() < 5:  # Mon=0, Fri=4
            run_report_generation()
        else:
            print(f"  📅 今日为周末，跳过报告生成")

    schedule.every().day.at(gen_time).do(weekday_job)

    # Also run immediately if requested
    print(f"🔄 调度器已启动，下次执行: {gen_time}")
    print(f"  当前时间: {datetime.now().strftime('%H:%M:%S')}")

    try:
        while True:
            schedule.run_pending()
            time.sleep(30)
    except KeyboardInterrupt:
        print("\n\n👋 调度器已停止")


if __name__ == "__main__":
    main()
