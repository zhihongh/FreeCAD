"""
PDF 报告生成模块 - PDF Report Generator
Generates a comprehensive Chinese daily trading report in PDF format.
"""

import os
import json
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, HRFlowable, Image
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, Line, Rect, String
from reportlab.graphics.charts.barcharts import VerticalBarChart

from market_data import safe_get


# ─── Font Registration ──────────────────────────────────────────────────────────
CHINESE_FONT = None
FONT_PATHS = [
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
]

for fp in FONT_PATHS:
    if os.path.exists(fp):
        try:
            pdfmetrics.registerFont(TTFont("ChineseFont", fp))
            CHINESE_FONT = "ChineseFont"
            break
        except Exception:
            continue

if CHINESE_FONT is None:
    CHINESE_FONT = "Helvetica"

FONT_BOLD = CHINESE_FONT


# ─── Color Palette ──────────────────────────────────────────────────────────────
COLOR_RED = colors.HexColor("#DC2626")
COLOR_GREEN = colors.HexColor("#16A34A")
COLOR_DARK = colors.HexColor("#1E293B")
COLOR_BLUE = colors.HexColor("#2563EB")
COLOR_ORANGE = colors.HexColor("#EA580C")
COLOR_PURPLE = colors.HexColor("#7C3AED")
COLOR_BG_LIGHT = colors.HexColor("#F8FAFC")
COLOR_BG_HEADER = colors.HexColor("#1E3A5F")
COLOR_BG_SECTION = colors.HexColor("#EFF6FF")
COLOR_BORDER = colors.HexColor("#CBD5E1")
COLOR_GOLD = colors.HexColor("#D97706")


def color_for_change(val):
    """涨红跌绿"""
    try:
        v = float(val)
        return COLOR_RED if v > 0 else COLOR_GREEN if v < 0 else COLOR_DARK
    except (TypeError, ValueError):
        return COLOR_DARK


def fmt_pct(val):
    """Format percentage with sign"""
    try:
        v = float(val)
        sign = "+" if v > 0 else ""
        return f"{sign}{v:.2f}%"
    except (TypeError, ValueError):
        return "N/A"


def fmt_price(val):
    """Format price"""
    try:
        return f"${float(val):,.2f}"
    except (TypeError, ValueError):
        return "N/A"


def fmt_volume(val):
    """Format volume in human-readable form"""
    try:
        v = float(val)
        if v >= 1e9:
            return f"{v/1e9:.2f}B"
        elif v >= 1e6:
            return f"{v/1e6:.2f}M"
        elif v >= 1e3:
            return f"{v/1e3:.1f}K"
        return f"{v:.0f}"
    except (TypeError, ValueError):
        return "N/A"


def fmt_mcap(val):
    """Format market cap"""
    try:
        v = float(val)
        if v >= 1e12:
            return f"${v/1e12:.2f}T"
        elif v >= 1e9:
            return f"${v/1e9:.1f}B"
        elif v >= 1e6:
            return f"${v/1e6:.1f}M"
        return f"${v:,.0f}"
    except (TypeError, ValueError):
        return "N/A"


def build_styles():
    """Build custom paragraph styles with Chinese font support"""
    styles = getSampleStyleSheet()

    custom = {
        "CoverTitle": ParagraphStyle(
            "CoverTitle", parent=styles["Title"],
            fontName=CHINESE_FONT, fontSize=28, leading=36,
            textColor=colors.white, alignment=TA_CENTER, spaceAfter=12,
        ),
        "CoverSubtitle": ParagraphStyle(
            "CoverSubtitle", parent=styles["Normal"],
            fontName=CHINESE_FONT, fontSize=14, leading=20,
            textColor=colors.HexColor("#E2E8F0"), alignment=TA_CENTER, spaceAfter=6,
        ),
        "SectionTitle": ParagraphStyle(
            "SectionTitle", parent=styles["Heading1"],
            fontName=CHINESE_FONT, fontSize=16, leading=22,
            textColor=COLOR_BG_HEADER, spaceBefore=16, spaceAfter=8,
            borderWidth=0, borderPadding=0,
        ),
        "SubSectionTitle": ParagraphStyle(
            "SubSectionTitle", parent=styles["Heading2"],
            fontName=CHINESE_FONT, fontSize=13, leading=18,
            textColor=COLOR_BLUE, spaceBefore=10, spaceAfter=6,
        ),
        "BodyCN": ParagraphStyle(
            "BodyCN", parent=styles["Normal"],
            fontName=CHINESE_FONT, fontSize=9, leading=14,
            textColor=COLOR_DARK, spaceAfter=4, alignment=TA_JUSTIFY,
        ),
        "BodySmall": ParagraphStyle(
            "BodySmall", parent=styles["Normal"],
            fontName=CHINESE_FONT, fontSize=8, leading=11,
            textColor=COLOR_DARK, spaceAfter=2,
        ),
        "TableHeader": ParagraphStyle(
            "TableHeader", parent=styles["Normal"],
            fontName=CHINESE_FONT, fontSize=8, leading=10,
            textColor=colors.white, alignment=TA_CENTER,
        ),
        "TableCell": ParagraphStyle(
            "TableCell", parent=styles["Normal"],
            fontName=CHINESE_FONT, fontSize=8, leading=10,
            textColor=COLOR_DARK, alignment=TA_CENTER,
        ),
        "TableCellLeft": ParagraphStyle(
            "TableCellLeft", parent=styles["Normal"],
            fontName=CHINESE_FONT, fontSize=8, leading=10,
            textColor=COLOR_DARK, alignment=TA_LEFT,
        ),
        "BulletCN": ParagraphStyle(
            "BulletCN", parent=styles["Normal"],
            fontName=CHINESE_FONT, fontSize=9, leading=13,
            textColor=COLOR_DARK, leftIndent=12, spaceAfter=3,
        ),
        "Highlight": ParagraphStyle(
            "Highlight", parent=styles["Normal"],
            fontName=CHINESE_FONT, fontSize=9, leading=13,
            textColor=COLOR_RED, spaceAfter=4,
        ),
        "Footer": ParagraphStyle(
            "Footer", parent=styles["Normal"],
            fontName=CHINESE_FONT, fontSize=7, leading=9,
            textColor=colors.gray, alignment=TA_CENTER,
        ),
    }
    return custom


def colored_cell(text, val=None, style_name="TableCell"):
    """Create a colored table cell paragraph"""
    color = COLOR_DARK
    if val is not None:
        color = color_for_change(val)
    color_hex = color.hexval() if hasattr(color, 'hexval') else str(color)
    return Paragraph(f'<font color="{color_hex}">{text}</font>', build_styles()[style_name])


# ─── Weekly Events Section ──────────────────────────────────────────────────────
def generate_weekly_events_section(styles):
    """Section 0: 本周重大经济事件及财报"""
    elements = []
    elements.append(Paragraph("〇、本周重大经济事件及财报日历", styles["SectionTitle"]))
    elements.append(HRFlowable(width="100%", thickness=2, color=COLOR_BLUE))
    elements.append(Spacer(1, 6))

    today = datetime.now()
    week_str = today.strftime("%Y年%m月%d日") + " 当周"

    elements.append(Paragraph(f"<b>📅 {week_str}</b>", styles["BodyCN"]))
    elements.append(Spacer(1, 4))

    events = [
        ["周一", "总统日 - 美股休市", "——"],
        ["周二", "纽约联储制造业指数; FOMC会议纪要预期", "关注制造业复苏信号"],
        ["周三", "FOMC 1月会议纪要公布 (2:00PM ET)", "关注利率路径讨论、缩表节奏"],
        ["周四", "初请失业金人数; 费城联储制造业指数; 成屋销售", "就业市场韧性评估"],
        ["周五", "标普全球PMI初值(制造业+服务业); 密歇根消费者信心终值", "经济软着陆预期验证"],
    ]

    econ_table = [
        [Paragraph("<b>日期</b>", styles["TableHeader"]),
         Paragraph("<b>经济数据/事件</b>", styles["TableHeader"]),
         Paragraph("<b>关注要点</b>", styles["TableHeader"])],
    ]
    for row in events:
        econ_table.append([
            Paragraph(row[0], styles["TableCell"]),
            Paragraph(row[1], styles["TableCellLeft"]),
            Paragraph(row[2], styles["TableCellLeft"]),
        ])

    t = Table(econ_table, colWidths=[60, 280, 180])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_BG_HEADER),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 1), (-1, -1), COLOR_BG_LIGHT),
        ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 8))

    elements.append(Paragraph("<b>📊 本周重点财报:</b>", styles["SubSectionTitle"]))
    earnings = [
        "• 周二盘后: Arista Networks (ANET), Palo Alto Networks (PANW)",
        "• 周三盘前: Analog Devices (ADI); 盘后: NVIDIA (NVDA) ⭐重磅, Synopsys (SNPS)",
        "• 周四盘前: Walmart (WMT), Booking Holdings (BKNG); 盘后: Rivian (RIVN), Block (SQ)",
        "• 周五盘前: Deere & Co (DE)",
    ]
    for e in earnings:
        elements.append(Paragraph(e, styles["BulletCN"]))

    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        "<b>⚠️ 关键关注:</b> NVDA财报为本周最大催化剂，预计对AI/半导体板块产生重大影响。"
        "FOMC纪要将影响市场对降息节奏的预期。WMT财报可反映消费者支出趋势。",
        styles["Highlight"]
    ))

    return elements


# ─── Section 1: 今日市场摘要 ────────────────────────────────────────────────────
def generate_summary_section(data, styles):
    """Section 1: Today's market summary"""
    elements = []
    elements.append(Paragraph("一、今日市场摘要", styles["SectionTitle"]))
    elements.append(HRFlowable(width="100%", thickness=2, color=COLOR_BLUE))
    elements.append(Spacer(1, 6))

    # 1a) Chinese summary
    elements.append(Paragraph("<b>1a) 财经新闻摘要</b>", styles["SubSectionTitle"]))

    indices = data.get("indices", {})
    nasdaq = indices.get("^IXIC", {})
    sp500 = indices.get("^GSPC", {})
    sox = indices.get("^SOX", {})
    vix = indices.get("^VIX", {})

    nasdaq_pct = fmt_pct(nasdaq.get("change_pct", 0))
    sp500_pct = fmt_pct(sp500.get("change_pct", 0))
    sox_pct = fmt_pct(sox.get("change_pct", 0))
    vix_val = f"{safe_get(vix.get('price', 0)):.2f}"

    summary_text = (
        f"今日美股三大指数表现分化。纳斯达克指数收于 {fmt_price(nasdaq.get('price', 0))}，"
        f"日涨跌幅 {nasdaq_pct}；标普500指数收于 {fmt_price(sp500.get('price', 0))}，"
        f"涨跌幅 {sp500_pct}；费城半导体指数 {sox_pct}。"
        f"VIX恐慌指数位于 {vix_val}，"
    )

    vix_price = safe_get(vix.get("price", 20))
    if vix_price < 15:
        summary_text += "市场情绪偏乐观，波动率处于低位。"
    elif vix_price < 20:
        summary_text += "市场情绪较为平稳。"
    elif vix_price < 25:
        summary_text += "市场存在一定不确定性。"
    else:
        summary_text += "市场恐慌情绪升温，需警惕大幅波动。"

    elements.append(Paragraph(summary_text, styles["BodyCN"]))
    elements.append(Spacer(1, 4))

    # Key news bullets
    news_bullets = [
        "• AI投资热潮持续：各大科技巨头持续加大AI基础设施投入，数据中心需求旺盛",
        "• 美联储政策：市场密切关注FOMC会议纪要，预期今年降息空间有限",
        "• 地缘政治：俄乌局势谈判信号及中美科技博弈持续影响市场",
        "• 财报季延续：本周NVDA、WMT等重磅财报将决定近期市场方向",
        "• 宏观数据：关注制造业PMI、就业数据对经济软着陆预期的影响",
    ]
    for b in news_bullets:
        elements.append(Paragraph(b, styles["BulletCN"]))

    elements.append(Spacer(1, 8))

    # 1b) Market Sentiment
    elements.append(Paragraph("<b>1b) 市场情绪与资金流向</b>", styles["SubSectionTitle"]))

    # Market sentiment assessment
    sentiment_items = []
    nasdaq_chg = safe_get(nasdaq.get("change_pct", 0))
    if nasdaq_chg > 1:
        sentiment_items.append("• 情绪指标: 偏多 🟢 纳指涨幅超1%，风险偏好上升")
    elif nasdaq_chg > 0:
        sentiment_items.append("• 情绪指标: 中性偏多 🟡 纳指小幅上涨，市场观望情绪浓")
    elif nasdaq_chg > -1:
        sentiment_items.append("• 情绪指标: 中性偏空 🟠 纳指小幅下跌，资金趋于谨慎")
    else:
        sentiment_items.append("• 情绪指标: 偏空 🔴 纳指跌幅超1%，避险情绪升温")

    if vix_price < 15:
        sentiment_items.append(f"• VIX恐慌指数: {vix_val} — 极低波动，市场自满需警惕")
    elif vix_price < 20:
        sentiment_items.append(f"• VIX恐慌指数: {vix_val} — 正常区间，市场平稳")
    else:
        sentiment_items.append(f"• VIX恐慌指数: {vix_val} — 波动偏高，建议控制仓位")

    etfs = data.get("sector_etfs", {})
    top_etfs = sorted(
        [(k, v) for k, v in etfs.items() if "error" not in v],
        key=lambda x: x[1].get("change_pct", 0), reverse=True
    )[:3]
    bottom_etfs = sorted(
        [(k, v) for k, v in etfs.items() if "error" not in v],
        key=lambda x: x[1].get("change_pct", 0)
    )[:3]

    if top_etfs:
        top_str = "、".join([f"{v['name']}({k} {fmt_pct(v['change_pct'])})" for k, v in top_etfs])
        sentiment_items.append(f"• 领涨板块: {top_str}")
    if bottom_etfs:
        bot_str = "、".join([f"{v['name']}({k} {fmt_pct(v['change_pct'])})" for k, v in bottom_etfs])
        sentiment_items.append(f"• 领跌板块: {bot_str}")

    sentiment_items.append("• 资金流向: 关注QQQ/SPY ETF资金净流入情况作为机构态度风向标")

    for s in sentiment_items:
        elements.append(Paragraph(s, styles["BulletCN"]))

    elements.append(Spacer(1, 6))

    # Opportunities and Risks
    elements.append(Paragraph("<b>机会与风险提示:</b>", styles["SubSectionTitle"]))
    opp_risk = [
        "🟢 机会: AI/数据中心产业链持续高景气，NVDA财报可能成为新催化剂",
        "🟢 机会: 电力基础设施需求受AI驱动，相关公用事业股值得关注",
        "🟢 机会: 存储芯片周期上行，HBM需求持续超预期",
        "🔴 风险: 美联储可能维持高利率更久，打压高估值成长股",
        "🔴 风险: 地缘政治不确定性可能引发突发波动",
        "🔴 风险: AI概念股估值偏高，需警惕获利回吐压力",
    ]
    for o in opp_risk:
        elements.append(Paragraph(f"  {o}", styles["BulletCN"]))

    return elements


# ─── Section 2: Index Performance & ETF Flows ──────────────────────────────────
def generate_index_section(data, styles):
    """Section 2: NASDAQ, S&P500, SOX performance and ETF flow analysis"""
    elements = []
    elements.append(Paragraph("二、主要指数表现与板块轮动分析", styles["SectionTitle"]))
    elements.append(HRFlowable(width="100%", thickness=2, color=COLOR_BLUE))
    elements.append(Spacer(1, 6))

    # Index table
    indices = data.get("indices", {})
    idx_table = [
        [Paragraph("<b>指数</b>", styles["TableHeader"]),
         Paragraph("<b>收盘价</b>", styles["TableHeader"]),
         Paragraph("<b>日涨跌</b>", styles["TableHeader"]),
         Paragraph("<b>日涨跌%</b>", styles["TableHeader"]),
         Paragraph("<b>周涨跌%</b>", styles["TableHeader"]),
         Paragraph("<b>最高</b>", styles["TableHeader"]),
         Paragraph("<b>最低</b>", styles["TableHeader"])],
    ]

    for sym, info in indices.items():
        if "error" in info:
            continue
        chg_pct = info.get("change_pct", 0)
        week_pct = info.get("week_change_pct", 0)
        c = color_for_change(chg_pct)
        ch = c.hexval() if hasattr(c, 'hexval') else str(c)
        wc = color_for_change(week_pct)
        wh = wc.hexval() if hasattr(wc, 'hexval') else str(wc)

        idx_table.append([
            Paragraph(info["name"], styles["TableCellLeft"]),
            Paragraph(fmt_price(info.get("price", 0)), styles["TableCell"]),
            Paragraph(f'<font color="{ch}">{info.get("change", 0):+.2f}</font>', styles["TableCell"]),
            Paragraph(f'<font color="{ch}">{fmt_pct(chg_pct)}</font>', styles["TableCell"]),
            Paragraph(f'<font color="{wh}">{fmt_pct(week_pct)}</font>', styles["TableCell"]),
            Paragraph(fmt_price(info.get("high", 0)), styles["TableCell"]),
            Paragraph(fmt_price(info.get("low", 0)), styles["TableCell"]),
        ])

    t = Table(idx_table, colWidths=[150, 70, 60, 60, 60, 65, 65])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_BG_HEADER),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 1), (-1, -1), COLOR_BG_LIGHT),
        ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_BG_LIGHT, colors.white]),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 10))

    # Sector ETF Rankings
    elements.append(Paragraph("<b>板块ETF涨跌排行:</b>", styles["SubSectionTitle"]))
    etfs = data.get("sector_etfs", {})
    sorted_etfs = sorted(
        [(k, v) for k, v in etfs.items() if "error" not in v],
        key=lambda x: x[1].get("change_pct", 0), reverse=True
    )

    etf_table = [
        [Paragraph("<b>排名</b>", styles["TableHeader"]),
         Paragraph("<b>ETF</b>", styles["TableHeader"]),
         Paragraph("<b>名称</b>", styles["TableHeader"]),
         Paragraph("<b>价格</b>", styles["TableHeader"]),
         Paragraph("<b>日涨跌%</b>", styles["TableHeader"]),
         Paragraph("<b>周涨跌%</b>", styles["TableHeader"]),
         Paragraph("<b>成交量</b>", styles["TableHeader"])],
    ]

    for i, (sym, info) in enumerate(sorted_etfs):
        chg = info.get("change_pct", 0)
        c = color_for_change(chg)
        ch = c.hexval() if hasattr(c, 'hexval') else str(c)
        wc = color_for_change(info.get("week_change_pct", 0))
        wh = wc.hexval() if hasattr(wc, 'hexval') else str(wc)

        etf_table.append([
            Paragraph(str(i + 1), styles["TableCell"]),
            Paragraph(f"<b>{sym}</b>", styles["TableCell"]),
            Paragraph(info["name"], styles["TableCellLeft"]),
            Paragraph(fmt_price(info.get("price", 0)), styles["TableCell"]),
            Paragraph(f'<font color="{ch}">{fmt_pct(chg)}</font>', styles["TableCell"]),
            Paragraph(f'<font color="{wh}">{fmt_pct(info.get("week_change_pct", 0))}</font>', styles["TableCell"]),
            Paragraph(fmt_volume(info.get("volume", 0)), styles["TableCell"]),
        ])

    t = Table(etf_table, colWidths=[35, 45, 130, 55, 60, 60, 60])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_BG_HEADER),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_BG_LIGHT, colors.white]),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 8))

    # Sector Rotation Analysis
    elements.append(Paragraph("<b>板块轮动分析:</b>", styles["SubSectionTitle"]))
    rotation_text = []
    if sorted_etfs:
        leaders = [f"{v['name']}({k})" for k, v in sorted_etfs[:3]]
        laggards = [f"{v['name']}({k})" for k, v in sorted_etfs[-3:]]
        rotation_text.append(f"• 今日领涨板块: {'、'.join(leaders)}")
        rotation_text.append(f"• 今日落后板块: {'、'.join(laggards)}")

    # Check for defensive vs growth rotation
    growth_etfs = ["QQQ", "XLK", "SOXX", "SMH", "ARKK"]
    defensive_etfs = ["XLU", "XLP", "XLV", "XLRE"]
    growth_avg = 0
    def_avg = 0
    gc = 0
    dc = 0
    for k, v in etfs.items():
        if "error" in v:
            continue
        if k in growth_etfs:
            growth_avg += v.get("change_pct", 0)
            gc += 1
        elif k in defensive_etfs:
            def_avg += v.get("change_pct", 0)
            dc += 1
    if gc > 0:
        growth_avg /= gc
    if dc > 0:
        def_avg /= dc

    if growth_avg > def_avg + 0.5:
        rotation_text.append("• 轮动方向: 资金偏好成长/科技股 → 风险偏好上升 📈")
    elif def_avg > growth_avg + 0.5:
        rotation_text.append("• 轮动方向: 资金流向防御性板块 → 避险情绪升温 📉")
    else:
        rotation_text.append("• 轮动方向: 成长与防御板块表现均衡，市场方向不明确 ↔️")

    for r in rotation_text:
        elements.append(Paragraph(r, styles["BulletCN"]))

    return elements


# ─── Section 3: Trading Suggestions ─────────────────────────────────────────────
def generate_trading_suggestions(data, styles):
    """Section 3a: Trading sector and stocks suggestions"""
    elements = []
    elements.append(Paragraph("三、交易板块与个股建议", styles["SectionTitle"]))
    elements.append(HRFlowable(width="100%", thickness=2, color=COLOR_BLUE))
    elements.append(Spacer(1, 6))

    suggestions = [
        {
            "sector": "AI/半导体",
            "bias": "偏多",
            "stocks": "NVDA, AMD, AVGO, ALAB, CRDO",
            "reason": "AI资本开支持续增长，NVDA财报在即可能催化板块行情。HBM/网络芯片需求旺盛。",
            "strategy": "关注NVDA财报前布局机会，利用回调逢低吸纳龙头。止损设于近期支撑位下方3%。",
        },
        {
            "sector": "存储芯片",
            "bias": "偏多",
            "stocks": "MU, WDC, STX",
            "reason": "存储周期上行，HBM需求+AI服务器驱动DRAM/NAND价格上涨趋势。",
            "strategy": "MU回调至支撑区域可逢低建仓。WDC/STX关注企业级SSD需求增长。",
        },
        {
            "sector": "服务器/数据中心",
            "bias": "中性偏多",
            "stocks": "SMCI, DELL, ANET",
            "reason": "数据中心建设周期，但SMCI估值争议及审计风险需要警惕。",
            "strategy": "SMCI高波动，建议轻仓或用期权控制风险。ANET财报催化剂值得关注。",
        },
        {
            "sector": "电力/公用事业",
            "bias": "偏多",
            "stocks": "VST, CEG, NRG",
            "reason": "AI数据中心对电力需求大幅增长，核能/天然气发电受益。",
            "strategy": "作为AI主题的防御性配置，适合中长期持有。",
        },
        {
            "sector": "消费/零售",
            "bias": "中性",
            "stocks": "LULU, WMT, COST",
            "reason": "消费数据韧性，但高利率环境下消费降级趋势明显。关注WMT财报。",
            "strategy": "WMT财报后看消费趋势方向，LULU关注高端消费韧性。",
        },
        {
            "sector": "金融科技",
            "bias": "中性偏多",
            "stocks": "UPST, SQ, SOFI",
            "reason": "降息预期利好金融科技，UPST AI驱动的信贷模型表现亮眼。",
            "strategy": "UPST趋势明确可顺势做多，但波动大需严格止损。",
        },
    ]

    sugg_table = [
        [Paragraph("<b>板块</b>", styles["TableHeader"]),
         Paragraph("<b>方向</b>", styles["TableHeader"]),
         Paragraph("<b>关注个股</b>", styles["TableHeader"]),
         Paragraph("<b>逻辑</b>", styles["TableHeader"]),
         Paragraph("<b>策略</b>", styles["TableHeader"])],
    ]

    for s in suggestions:
        bias_color = COLOR_RED if "多" in s["bias"] else COLOR_GREEN if "空" in s["bias"] else COLOR_DARK
        bh = bias_color.hexval() if hasattr(bias_color, 'hexval') else str(bias_color)
        sugg_table.append([
            Paragraph(f"<b>{s['sector']}</b>", styles["TableCellLeft"]),
            Paragraph(f'<font color="{bh}"><b>{s["bias"]}</b></font>', styles["TableCell"]),
            Paragraph(s["stocks"], styles["TableCellLeft"]),
            Paragraph(s["reason"], styles["TableCellLeft"]),
            Paragraph(s["strategy"], styles["TableCellLeft"]),
        ])

    t = Table(sugg_table, colWidths=[70, 50, 85, 150, 160])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_BG_HEADER),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_BG_LIGHT, colors.white]),
    ]))
    elements.append(t)

    return elements


# ─── Section 4: Hot Sectors ──────────────────────────────────────────────────────
def generate_hot_sectors_section(data, styles):
    """Section 4: Hot sectors analysis"""
    elements = []
    elements.append(Paragraph("四、热门板块深度分析 (AI/存储/服务器/电力)", styles["SectionTitle"]))
    elements.append(HRFlowable(width="100%", thickness=2, color=COLOR_BLUE))
    elements.append(Spacer(1, 6))

    hot_sectors = data.get("hot_sectors", {})

    for sector, stocks in hot_sectors.items():
        if not stocks:
            continue
        elements.append(Paragraph(f"<b>▶ {sector}</b>", styles["SubSectionTitle"]))

        s_table = [
            [Paragraph("<b>股票</b>", styles["TableHeader"]),
             Paragraph("<b>价格</b>", styles["TableHeader"]),
             Paragraph("<b>涨跌%</b>", styles["TableHeader"]),
             Paragraph("<b>RSI</b>", styles["TableHeader"]),
             Paragraph("<b>MA20</b>", styles["TableHeader"]),
             Paragraph("<b>量比</b>", styles["TableHeader"]),
             Paragraph("<b>信号</b>", styles["TableHeader"])],
        ]

        for stock in stocks[:8]:
            chg = stock.get("change_pct", 0)
            c = color_for_change(chg)
            ch = c.hexval() if hasattr(c, 'hexval') else str(c)

            rsi = stock.get("rsi", 0)
            rsi_color = COLOR_RED if rsi > 70 else COLOR_GREEN if rsi < 30 else COLOR_DARK
            rh = rsi_color.hexval() if hasattr(rsi_color, 'hexval') else str(rsi_color)

            vr = stock.get("vol_ratio", 0)
            vr_color = COLOR_ORANGE if vr > 2 else COLOR_DARK
            vh = vr_color.hexval() if hasattr(vr_color, 'hexval') else str(vr_color)

            signals = stock.get("breakout_signals", [])
            sig_str = "; ".join(signals[:2]) if signals else "—"

            s_table.append([
                Paragraph(f"<b>{stock['symbol']}</b>", styles["TableCellLeft"]),
                Paragraph(fmt_price(stock.get("price", 0)), styles["TableCell"]),
                Paragraph(f'<font color="{ch}">{fmt_pct(chg)}</font>', styles["TableCell"]),
                Paragraph(f'<font color="{rh}">{rsi:.1f}</font>', styles["TableCell"]),
                Paragraph(fmt_price(stock.get("ma20", 0)), styles["TableCell"]),
                Paragraph(f'<font color="{vh}">{vr:.2f}x</font>', styles["TableCell"]),
                Paragraph(sig_str, styles["TableCellLeft"]),
            ])

        t = Table(s_table, colWidths=[50, 60, 55, 45, 60, 50, 195])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_PURPLE),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_BG_LIGHT, colors.white]),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 6))

    # Sector rotation summary
    elements.append(Paragraph("<b>板块轮动总结:</b>", styles["SubSectionTitle"]))
    rotation_notes = [
        "• AI/半导体: 核心主线，NVDA财报前市场期待高涨，关注指引是否超预期",
        "• 存储: HBM需求确定性强，MU作为龙头估值合理，周期上行趋势明确",
        "• 服务器: 数据中心Capex增长受益，但个股分化加剧，SMCI风险较大",
        "• 电力: AI基建的'卖水人'逻辑，核能概念持续受资金追捧",
    ]
    for n in rotation_notes:
        elements.append(Paragraph(n, styles["BulletCN"]))

    return elements


# ─── Section 5: Top Stocks ───────────────────────────────────────────────────────
def generate_top_stocks_section(data, styles):
    """Section 5: Top 10 leading/potential stocks"""
    elements = []
    elements.append(Paragraph("五、涨跌排行榜 Top 10", styles["SectionTitle"]))
    elements.append(HRFlowable(width="100%", thickness=2, color=COLOR_BLUE))
    elements.append(Spacer(1, 6))

    # Gainers
    elements.append(Paragraph("<b>🔥 今日涨幅前10:</b>", styles["SubSectionTitle"]))
    gainers = data.get("gainers", [])
    if gainers:
        g_table = [
            [Paragraph("<b>#</b>", styles["TableHeader"]),
             Paragraph("<b>代码</b>", styles["TableHeader"]),
             Paragraph("<b>价格</b>", styles["TableHeader"]),
             Paragraph("<b>涨幅</b>", styles["TableHeader"]),
             Paragraph("<b>成交量</b>", styles["TableHeader"])],
        ]
        for i, g in enumerate(gainers[:10]):
            chg = g.get("change_pct", 0)
            c = COLOR_RED
            ch = c.hexval() if hasattr(c, 'hexval') else str(c)
            g_table.append([
                Paragraph(str(i + 1), styles["TableCell"]),
                Paragraph(f"<b>{g['symbol']}</b>", styles["TableCell"]),
                Paragraph(fmt_price(g.get("price", 0)), styles["TableCell"]),
                Paragraph(f'<font color="{ch}">{fmt_pct(chg)}</font>', styles["TableCell"]),
                Paragraph(fmt_volume(g.get("volume", 0)), styles["TableCell"]),
            ])
        t = Table(g_table, colWidths=[30, 70, 80, 70, 80])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_BG_HEADER),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_BG_LIGHT, colors.white]),
        ]))
        elements.append(t)

    elements.append(Spacer(1, 8))

    # Losers
    elements.append(Paragraph("<b>📉 今日跌幅前10:</b>", styles["SubSectionTitle"]))
    losers = data.get("losers", [])
    if losers:
        l_table = [
            [Paragraph("<b>#</b>", styles["TableHeader"]),
             Paragraph("<b>代码</b>", styles["TableHeader"]),
             Paragraph("<b>价格</b>", styles["TableHeader"]),
             Paragraph("<b>跌幅</b>", styles["TableHeader"]),
             Paragraph("<b>成交量</b>", styles["TableHeader"])],
        ]
        for i, l in enumerate(losers[:10]):
            chg = l.get("change_pct", 0)
            c = COLOR_GREEN
            ch = c.hexval() if hasattr(c, 'hexval') else str(c)
            l_table.append([
                Paragraph(str(i + 1), styles["TableCell"]),
                Paragraph(f"<b>{l['symbol']}</b>", styles["TableCell"]),
                Paragraph(fmt_price(l.get("price", 0)), styles["TableCell"]),
                Paragraph(f'<font color="{ch}">{fmt_pct(chg)}</font>', styles["TableCell"]),
                Paragraph(fmt_volume(l.get("volume", 0)), styles["TableCell"]),
            ])
        t = Table(l_table, colWidths=[30, 70, 80, 70, 80])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_BG_HEADER),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_BG_LIGHT, colors.white]),
        ]))
        elements.append(t)

    return elements


# ─── Section 6: Volume Surge Stocks ──────────────────────────────────────────────
def generate_volume_surge_section(data, styles):
    """Section 6: Volume surge and technical signal stocks"""
    elements = []
    elements.append(Paragraph("六、放量异动与技术信号股票", styles["SectionTitle"]))
    elements.append(HRFlowable(width="100%", thickness=2, color=COLOR_BLUE))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph(
        "以下为今日成交量显著放大(量比>1.5x)且出现技术形态信号的个股:",
        styles["BodyCN"]
    ))
    elements.append(Spacer(1, 4))

    surge = data.get("volume_surge", [])
    if surge:
        s_table = [
            [Paragraph("<b>#</b>", styles["TableHeader"]),
             Paragraph("<b>代码</b>", styles["TableHeader"]),
             Paragraph("<b>价格</b>", styles["TableHeader"]),
             Paragraph("<b>涨跌%</b>", styles["TableHeader"]),
             Paragraph("<b>量比</b>", styles["TableHeader"]),
             Paragraph("<b>RSI</b>", styles["TableHeader"]),
             Paragraph("<b>技术信号</b>", styles["TableHeader"])],
        ]

        for i, s in enumerate(surge[:10]):
            chg = s.get("change_pct", 0)
            c = color_for_change(chg)
            ch = c.hexval() if hasattr(c, 'hexval') else str(c)

            rsi = s.get("rsi", 0)
            rsi_color = COLOR_RED if rsi > 70 else COLOR_GREEN if rsi < 30 else COLOR_DARK
            rh = rsi_color.hexval() if hasattr(rsi_color, 'hexval') else str(rsi_color)

            vr = s.get("vol_ratio", 0)
            signals = s.get("breakout_signals", [])
            sig_str = "; ".join(signals) if signals else "放量"

            s_table.append([
                Paragraph(str(i + 1), styles["TableCell"]),
                Paragraph(f"<b>{s['symbol']}</b>", styles["TableCell"]),
                Paragraph(fmt_price(s.get("price", 0)), styles["TableCell"]),
                Paragraph(f'<font color="{ch}">{fmt_pct(chg)}</font>', styles["TableCell"]),
                Paragraph(f"<b>{vr:.2f}x</b>", styles["TableCell"]),
                Paragraph(f'<font color="{rh}">{rsi:.1f}</font>', styles["TableCell"]),
                Paragraph(sig_str, styles["TableCellLeft"]),
            ])

        t = Table(s_table, colWidths=[25, 50, 60, 55, 50, 40, 235])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_ORANGE),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_BG_LIGHT, colors.white]),
        ]))
        elements.append(t)
    else:
        elements.append(Paragraph("今日暂无显著放量异动个股。", styles["BodyCN"]))

    return elements


# ─── Section 7: Tracked Stocks Detail ────────────────────────────────────────────
def generate_tracked_stocks_section(data, styles):
    """Section 7: Detailed tracking of specific stocks"""
    elements = []
    elements.append(Paragraph(
        "七、重点跟踪个股详细分析", styles["SectionTitle"]
    ))
    elements.append(HRFlowable(width="100%", thickness=2, color=COLOR_BLUE))
    elements.append(Spacer(1, 6))

    tracked_desc = (
        "跟踪标的: NVDA, SMCI, MU, ALAB, CRDO, LULU, UPST, WDC, STX, TSLA, AAPL, GOOGL, AMD"
    )
    elements.append(Paragraph(tracked_desc, styles["BodySmall"]))
    elements.append(Spacer(1, 4))

    tracked = data.get("tracked_stocks", {})

    # Main table
    main_table = [
        [Paragraph("<b>代码</b>", styles["TableHeader"]),
         Paragraph("<b>价格</b>", styles["TableHeader"]),
         Paragraph("<b>涨跌%</b>", styles["TableHeader"]),
         Paragraph("<b>RSI</b>", styles["TableHeader"]),
         Paragraph("<b>MA5</b>", styles["TableHeader"]),
         Paragraph("<b>MA20</b>", styles["TableHeader"]),
         Paragraph("<b>MA50</b>", styles["TableHeader"]),
         Paragraph("<b>量比</b>", styles["TableHeader"]),
         Paragraph("<b>支撑</b>", styles["TableHeader"]),
         Paragraph("<b>阻力</b>", styles["TableHeader"])],
    ]

    for sym, info in tracked.items():
        if "error" in info:
            continue
        chg = info.get("change_pct", 0)
        c = color_for_change(chg)
        ch = c.hexval() if hasattr(c, 'hexval') else str(c)

        rsi = info.get("rsi", 0)
        rc = COLOR_RED if rsi > 70 else COLOR_GREEN if rsi < 30 else COLOR_DARK
        rh = rc.hexval() if hasattr(rc, 'hexval') else str(rc)

        main_table.append([
            Paragraph(f"<b>{sym}</b>", styles["TableCellLeft"]),
            Paragraph(fmt_price(info.get("price", 0)), styles["TableCell"]),
            Paragraph(f'<font color="{ch}">{fmt_pct(chg)}</font>', styles["TableCell"]),
            Paragraph(f'<font color="{rh}">{safe_get(rsi):.1f}</font>', styles["TableCell"]),
            Paragraph(fmt_price(info.get("ma5", 0)), styles["TableCell"]),
            Paragraph(fmt_price(info.get("ma20", 0)), styles["TableCell"]),
            Paragraph(fmt_price(info.get("ma50", 0)), styles["TableCell"]),
            Paragraph(f"{safe_get(info.get('vol_ratio', 0)):.2f}x", styles["TableCell"]),
            Paragraph(fmt_price(info.get("support", 0)), styles["TableCell"]),
            Paragraph(fmt_price(info.get("resistance", 0)), styles["TableCell"]),
        ])

    t = Table(main_table, colWidths=[42, 52, 48, 36, 52, 52, 52, 40, 52, 52])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_BG_HEADER),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_BG_LIGHT, colors.white]),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 8))

    # Detailed breakout signals for each stock
    elements.append(Paragraph("<b>个股技术信号与分析:</b>", styles["SubSectionTitle"]))

    for sym, info in tracked.items():
        if "error" in info:
            continue

        signals = info.get("breakout_signals", [])
        rsi = safe_get(info.get("rsi", 50))
        price = safe_get(info.get("price", 0))
        ma20 = safe_get(info.get("ma20", 0))
        ma50 = safe_get(info.get("ma50", 0))
        vol_ratio = safe_get(info.get("vol_ratio", 1))

        # Generate analysis text
        analysis_parts = [f"<b>{sym}</b>: 收于{fmt_price(price)}"]

        # Price vs MAs
        if price > ma20 > 0:
            analysis_parts.append("站上20日均线")
        elif ma20 > 0:
            analysis_parts.append("低于20日均线承压")

        if price > ma50 > 0:
            analysis_parts.append("位于50日均线上方")
        elif ma50 > 0:
            analysis_parts.append("50日均线下方弱势")

        # RSI
        if rsi > 70:
            analysis_parts.append(f"RSI={rsi:.1f}超买")
        elif rsi < 30:
            analysis_parts.append(f"RSI={rsi:.1f}超卖")
        else:
            analysis_parts.append(f"RSI={rsi:.1f}")

        # Volume
        if vol_ratio > 2:
            analysis_parts.append(f"放量{vol_ratio:.1f}倍")
        elif vol_ratio > 1.5:
            analysis_parts.append(f"量能温和放大{vol_ratio:.1f}x")

        # Signals
        if signals:
            analysis_parts.append("信号: " + "、".join(signals))

        macd_val = safe_get(info.get("macd", 0))
        macd_sig = safe_get(info.get("macd_signal", 0))
        if macd_val > macd_sig:
            analysis_parts.append("MACD多头排列")
        else:
            analysis_parts.append("MACD空头排列")

        elements.append(Paragraph("  → " + "，".join(analysis_parts), styles["BodySmall"]))

    return elements


# ─── Section 8: Strategy & Options ───────────────────────────────────────────────
def generate_strategy_section(data, styles):
    """Section 8: Trend outlook, strategy, and options trading suggestions"""
    elements = []
    elements.append(Paragraph("八、趋势展望与期权交易策略", styles["SectionTitle"]))
    elements.append(HRFlowable(width="100%", thickness=2, color=COLOR_BLUE))
    elements.append(Spacer(1, 6))

    # Trend outlook
    elements.append(Paragraph("<b>趋势展望:</b>", styles["SubSectionTitle"]))

    indices = data.get("indices", {})
    nasdaq = indices.get("^IXIC", {})
    vix = indices.get("^VIX", {})
    vix_price = safe_get(vix.get("price", 20))
    nasdaq_chg = safe_get(nasdaq.get("change_pct", 0))

    outlook_items = [
        "• 短期(1-3天): NVDA财报为最大变量，预计AI相关板块波动加剧。建议财报前控制仓位在60-70%",
        "• 中期(1-2周): FOMC纪要若偏鹰，科技成长股面临压力；若态度温和，有望继续上攻",
        "• 板块轮动: AI/半导体仍是主线，关注资金是否从AI概念股向AI基建实际受益股轮动",
        "• 技术面: 纳指需守住关键支撑位，上方关注历史新高突破确认",
    ]

    if vix_price > 20:
        outlook_items.append("• ⚠️ VIX偏高，建议增配对冲头寸，降低净多头敞口")
    if nasdaq_chg < -1:
        outlook_items.append("• ⚠️ 指数大跌日，注意观察次日反弹力度判断下跌性质")

    for o in outlook_items:
        elements.append(Paragraph(o, styles["BulletCN"]))

    elements.append(Spacer(1, 8))

    # Options Strategy
    elements.append(Paragraph("<b>期权交易策略建议:</b>", styles["SubSectionTitle"]))

    options_strategies = [
        {
            "name": "NVDA 财报Straddle策略",
            "desc": "买入NVDA跨式组合(ATM Call + ATM Put)，利用财报高波动获利",
            "detail": "适合: 预期NVDA财报后大幅波动但方向不确定。建议选2-3周到期。注意隐含波动率已偏高，"
                      "可考虑卖出远月、买入近月做日历价差降低成本。",
            "risk": "最大风险为权利金损失，若波动不及预期两边亏损",
        },
        {
            "name": "AI板块Bull Call Spread",
            "desc": "看多AI板块: 买入SOXX/SMH近月Call，同时卖出更高行权价Call",
            "detail": "适合: 看好半导体但不想承担过多权利金风险。上方Call卖出可回收30-40%成本。",
            "risk": "最大利润有限(两行权价差-净权利金)，下行风险为全部权利金",
        },
        {
            "name": "Covered Call 增强收益",
            "desc": "对持有的AAPL/GOOGL等长期持仓卖出虚值Call赚取权利金",
            "detail": "选择Delta 0.2-0.3的虚值Call，到期2-4周。可每月滚动操作，年化增强5-8%收益。",
            "risk": "上涨超过行权价时需让渡部分收益",
        },
        {
            "name": "保护性Put策略",
            "desc": "为核心持仓买入SPY/QQQ Put做组合保险",
            "detail": "选择5-10%虚值Put，到期1-2个月。成本约为持仓的1-2%。VIX>20时成本较高可用Bear Put Spread降本。",
            "risk": "权利金为保险成本，市场上涨则Put作废",
        },
    ]

    for os_item in options_strategies:
        elements.append(Paragraph(f"<b>▸ {os_item['name']}</b>", styles["BodyCN"]))
        elements.append(Paragraph(f"  策略: {os_item['desc']}", styles["BodySmall"]))
        elements.append(Paragraph(f"  说明: {os_item['detail']}", styles["BodySmall"]))
        elements.append(Paragraph(f"  风险: {os_item['risk']}", styles["BodySmall"]))
        elements.append(Spacer(1, 4))

    # General guidelines
    elements.append(Spacer(1, 6))
    elements.append(Paragraph("<b>仓位管理建议:</b>", styles["SubSectionTitle"]))
    position_tips = [
        "• 总仓位建议控制在60-80%，保留20-40%现金应对波动",
        "• 单只个股仓位不超过总资金的10%，AI板块总敞口不超过40%",
        "• 财报前降低相关个股仓位至正常的50-60%，或用期权替代",
        "• 严格执行止损: 个股止损5-8%，组合止损3-5%",
        "• 盈利头寸使用trailing stop(移动止盈)锁定利润",
    ]
    for p in position_tips:
        elements.append(Paragraph(p, styles["BulletCN"]))

    return elements


# ─── Section 9: PDF Description ──────────────────────────────────────────────────
def generate_pdf_description(styles):
    """Section 9: PDF format description"""
    elements = []
    elements.append(Paragraph("九、报告说明", styles["SectionTitle"]))
    elements.append(HRFlowable(width="100%", thickness=2, color=COLOR_BLUE))
    elements.append(Spacer(1, 6))

    desc_items = [
        "• 本报告基于 yfinance 实时市场数据自动生成，数据截至美东时间收盘",
        "• 技术指标包含: RSI(14日)、MA5/10/20/50、MACD、布林带、成交量分析",
        "• 涨跌颜色: 红色=上涨 🔴、绿色=下跌 🟢 (采用A股颜色习惯)",
        "• 板块ETF排名基于日涨跌幅从高到低排列",
        "• 放量异动筛选标准: 量比>1.5x 且出现技术形态突破信号",
        "• 期权策略仅供参考，实际交易需根据个人风险承受能力调整",
        "• 本报告支持每日定时自动生成(使用 schedule_report.py 配置)",
        "• 报告格式: A4 PDF，支持中文显示，可直接打印或分享",
    ]

    for d in desc_items:
        elements.append(Paragraph(d, styles["BulletCN"]))

    elements.append(Spacer(1, 8))
    elements.append(Paragraph(
        "<b>免责声明:</b> 本报告仅供学习参考，不构成任何投资建议。"
        "股市有风险，投资需谨慎。过往表现不代表未来收益。",
        styles["BodySmall"]
    ))

    return elements


# ─── Cover Page ──────────────────────────────────────────────────────────────────
def generate_cover_page(data, styles):
    """Generate report cover page"""
    elements = []

    # Background block using a table
    now = datetime.now()
    date_str = data.get("date", now.strftime("%Y年%m月%d日"))
    weekday_map = {0: "周一", 1: "周二", 2: "周三", 3: "周四", 4: "周五", 5: "周六", 6: "周日"}
    weekday = weekday_map.get(now.weekday(), "")

    elements.append(Spacer(1, 60))

    cover_data = [
        [Paragraph("", styles["CoverTitle"])],
        [Paragraph("美股每日交易报告", styles["CoverTitle"])],
        [Paragraph("Daily Trading Report", styles["CoverSubtitle"])],
        [Paragraph("", styles["CoverSubtitle"])],
        [Paragraph(f"{date_str} {weekday}", styles["CoverSubtitle"])],
        [Paragraph(f"报告生成时间: {now.strftime('%Y-%m-%d %H:%M:%S')} PST", styles["CoverSubtitle"])],
        [Paragraph("", styles["CoverSubtitle"])],
        [Paragraph("数据来源: Yahoo Finance | 技术分析: RSI/MACD/MA/BB", styles["CoverSubtitle"])],
        [Paragraph("", styles["CoverTitle"])],
    ]

    cover_table = Table(cover_data, colWidths=[500])
    cover_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_BG_HEADER),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 20),
        ("RIGHTPADDING", (0, 0), (-1, -1), 20),
        ("ROUNDEDCORNERS", [10, 10, 10, 10]),
    ]))
    elements.append(cover_table)

    elements.append(Spacer(1, 40))

    # Quick snapshot
    indices = data.get("indices", {})
    snap_items = []
    for sym, name in [("^IXIC", "纳斯达克"), ("^GSPC", "标普500"), ("^SOX", "半导体"), ("^VIX", "VIX")]:
        idx = indices.get(sym, {})
        if "error" not in idx:
            price = fmt_price(idx.get("price", 0))
            pct = fmt_pct(idx.get("change_pct", 0))
            snap_items.append(f"{name}: {price} ({pct})")

    if snap_items:
        snap_text = " | ".join(snap_items)
        elements.append(Paragraph(f"<b>快速概览:</b> {snap_text}", styles["BodyCN"]))

    elements.append(Spacer(1, 20))

    # TOC
    toc_items = [
        "〇、本周重大经济事件及财报日历",
        "一、今日市场摘要 (财经新闻 + 市场情绪)",
        "二、主要指数表现与板块轮动分析",
        "三、交易板块与个股建议",
        "四、热门板块深度分析",
        "五、涨跌排行榜 Top 10",
        "六、放量异动与技术信号股票",
        "七、重点跟踪个股详细分析",
        "八、趋势展望与期权交易策略",
        "九、报告说明",
    ]
    elements.append(Paragraph("<b>目 录</b>", styles["SubSectionTitle"]))
    for item in toc_items:
        elements.append(Paragraph(f"  {item}", styles["BodyCN"]))

    elements.append(PageBreak())
    return elements


# ─── Page Footer ─────────────────────────────────────────────────────────────────
def add_page_footer(canvas, doc):
    """Add footer to each page"""
    canvas.saveState()
    try:
        pdfmetrics.getFont(CHINESE_FONT)
        canvas.setFont(CHINESE_FONT, 7)
    except Exception:
        canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.gray)

    footer_text = f"美股每日交易报告 | {datetime.now().strftime('%Y-%m-%d')} | 第 {doc.page} 页"
    canvas.drawCentredString(A4[0] / 2, 15 * mm, footer_text)

    disclaimer = "免责声明: 仅供参考，不构成投资建议"
    canvas.drawCentredString(A4[0] / 2, 10 * mm, disclaimer)

    canvas.restoreState()


# ─── Main PDF Generator ─────────────────────────────────────────────────────────
def generate_pdf_report(data, output_path=None):
    """Generate the complete PDF report"""
    if output_path is None:
        now = datetime.now()
        output_path = f"reports/daily_trading_report_{now.strftime('%Y%m%d_%H%M')}.pdf"

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else "reports", exist_ok=True)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=20 * mm,
    )

    styles = build_styles()
    elements = []

    # Cover page
    elements.extend(generate_cover_page(data, styles))

    # Section 0: Weekly events
    elements.extend(generate_weekly_events_section(styles))
    elements.append(PageBreak())

    # Section 1: Market summary
    elements.extend(generate_summary_section(data, styles))
    elements.append(PageBreak())

    # Section 2: Index and ETF performance
    elements.extend(generate_index_section(data, styles))
    elements.append(PageBreak())

    # Section 3: Trading suggestions
    elements.extend(generate_trading_suggestions(data, styles))
    elements.append(PageBreak())

    # Section 4: Hot sectors
    elements.extend(generate_hot_sectors_section(data, styles))
    elements.append(PageBreak())

    # Section 5: Top stocks
    elements.extend(generate_top_stocks_section(data, styles))
    elements.append(PageBreak())

    # Section 6: Volume surge
    elements.extend(generate_volume_surge_section(data, styles))
    elements.append(PageBreak())

    # Section 7: Tracked stocks
    elements.extend(generate_tracked_stocks_section(data, styles))
    elements.append(PageBreak())

    # Section 8: Strategy
    elements.extend(generate_strategy_section(data, styles))
    elements.append(PageBreak())

    # Section 9: PDF description
    elements.extend(generate_pdf_description(styles))

    doc.build(elements, onFirstPage=add_page_footer, onLaterPages=add_page_footer)
    print(f"✅ PDF报告已生成: {output_path}")
    return output_path
