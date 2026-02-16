#!/usr/bin/env python3
"""
美股每日交易报告 - 主生成脚本
Daily Trading Report - Main Generator Script

Usage:
    python generate_report.py              # Generate today's report
    python generate_report.py --date 2026-02-16  # Generate for specific date
    python generate_report.py --output my_report.pdf  # Custom output path
"""

import argparse
import json
import os
import sys
from datetime import datetime

from market_data import get_all_market_data
from report_generator import generate_pdf_report


def main():
    parser = argparse.ArgumentParser(description="美股每日交易报告生成器")
    parser.add_argument("--date", type=str, help="Report date (YYYY-MM-DD)", default=None)
    parser.add_argument("--output", type=str, help="Output PDF path", default=None)
    parser.add_argument("--save-data", action="store_true", help="Save raw data as JSON")
    args = parser.parse_args()

    print("=" * 60)
    print("  美股每日交易报告生成器")
    print("  Daily Trading Report Generator")
    print("=" * 60)

    now = datetime.now()
    date_str = args.date or now.strftime("%Y-%m-%d")
    print(f"\n📅 报告日期: {date_str}")
    print(f"⏰ 生成时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Fetch all market data
    data = get_all_market_data()

    # Save raw data if requested
    if args.save_data:
        data_path = f"data/market_data_{date_str}.json"
        os.makedirs("data", exist_ok=True)
        with open(data_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        print(f"💾 数据已保存: {data_path}")

    # Generate PDF
    output = args.output or f"reports/daily_trading_report_{date_str.replace('-', '')}.pdf"
    pdf_path = generate_pdf_report(data, output)

    print()
    print("=" * 60)
    print(f"  ✅ 报告生成完成!")
    print(f"  📄 PDF文件: {pdf_path}")
    print(f"  📊 数据截止: {data.get('timestamp', 'N/A')}")
    print("=" * 60)

    return pdf_path


if __name__ == "__main__":
    main()
