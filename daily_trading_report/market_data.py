"""
市场数据获取模块 - Market Data Fetching Module
Fetches real-time and historical market data using yfinance and web sources.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import warnings

warnings.filterwarnings("ignore")


# ─── Index & ETF Symbols ───────────────────────────────────────────────────────
MAJOR_INDICES = {
    "^IXIC": "纳斯达克综合指数 (NASDAQ)",
    "^GSPC": "标普500指数 (S&P 500)",
    "^SOX": "费城半导体指数 (SOX)",
    "^DJI": "道琼斯工业指数 (DJIA)",
    "^VIX": "恐慌指数 (VIX)",
    "^RUT": "罗素2000指数 (Russell 2000)",
}

SECTOR_ETFS = {
    "QQQ": "纳斯达克100 ETF",
    "SPY": "标普500 ETF",
    "SOXX": "半导体 ETF (iShares)",
    "SMH": "半导体 ETF (VanEck)",
    "XLK": "科技板块 ETF",
    "XLF": "金融板块 ETF",
    "XLE": "能源板块 ETF",
    "XLV": "医疗板块 ETF",
    "XLI": "工业板块 ETF",
    "XLU": "公用事业 ETF",
    "XLP": "消费必需品 ETF",
    "XLY": "非必需消费 ETF",
    "XLB": "材料板块 ETF",
    "XLRE": "房地产 ETF",
    "XLC": "通信服务 ETF",
    "ARKK": "ARK创新 ETF",
    "TAN": "太阳能 ETF",
    "ICLN": "清洁能源 ETF",
}

HOT_SECTOR_STOCKS = {
    "AI/半导体": ["NVDA", "AMD", "AVGO", "MRVL", "ALAB", "CRDO", "ARM", "TSM", "QCOM", "INTC"],
    "存储": ["MU", "WDC", "STX", "NXPI"],
    "服务器/数据中心": ["SMCI", "DELL", "HPE", "ANET"],
    "电力设备/能源": ["VST", "CEG", "NRG", "NEE", "FSLR"],
    "云计算/软件": ["MSFT", "AMZN", "GOOGL", "META", "ORCL", "CRM", "NOW", "SNOW"],
    "消费/零售": ["LULU", "NKE", "COST", "WMT", "TGT"],
    "金融科技": ["UPST", "PYPL", "COIN", "AFRM", "SOFI", "HOOD"],
    "电动车/新能源": ["TSLA", "RIVN", "LCID", "NIO", "LI"],
}

TRACKED_STOCKS = [
    "NVDA", "SMCI", "MU", "ALAB", "CRDO", "LULU", "UPST",
    "WDC", "STX", "TSLA", "AAPL", "GOOGL", "AMD",
]


def safe_get(val, default=0.0):
    """Safely get a numeric value."""
    try:
        if val is None or (isinstance(val, float) and np.isnan(val)):
            return default
        return float(val)
    except (TypeError, ValueError):
        return default


def fetch_index_data():
    """获取主要指数数据"""
    results = {}
    for symbol, name in MAJOR_INDICES.items():
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="5d")
            if hist.empty:
                continue

            info = ticker.fast_info
            current_price = safe_get(hist["Close"].iloc[-1])
            prev_close = safe_get(hist["Close"].iloc[-2]) if len(hist) > 1 else current_price
            change = current_price - prev_close
            change_pct = (change / prev_close * 100) if prev_close != 0 else 0

            week_hist = ticker.history(period="5d")
            week_change = 0
            if len(week_hist) >= 2:
                week_start = safe_get(week_hist["Close"].iloc[0])
                if week_start != 0:
                    week_change = (current_price - week_start) / week_start * 100

            results[symbol] = {
                "name": name,
                "price": current_price,
                "change": change,
                "change_pct": change_pct,
                "volume": safe_get(hist["Volume"].iloc[-1]),
                "high": safe_get(hist["High"].iloc[-1]),
                "low": safe_get(hist["Low"].iloc[-1]),
                "open": safe_get(hist["Open"].iloc[-1]),
                "week_change_pct": week_change,
            }
        except Exception as e:
            results[symbol] = {"name": name, "error": str(e)}
    return results


def fetch_sector_etf_data():
    """获取板块ETF数据"""
    results = {}
    symbols = list(SECTOR_ETFS.keys())
    try:
        data = yf.download(symbols, period="5d", group_by="ticker", progress=False, threads=True)
    except Exception:
        data = pd.DataFrame()

    for symbol in symbols:
        try:
            name = SECTOR_ETFS[symbol]
            if not data.empty and symbol in data.columns.get_level_values(0):
                sym_data = data[symbol].dropna()
                if sym_data.empty or len(sym_data) < 2:
                    raise ValueError("Insufficient data")
                current = safe_get(sym_data["Close"].iloc[-1])
                prev = safe_get(sym_data["Close"].iloc[-2])
                change_pct = (current - prev) / prev * 100 if prev != 0 else 0
                volume = safe_get(sym_data["Volume"].iloc[-1])

                week_start = safe_get(sym_data["Close"].iloc[0])
                week_change = (current - week_start) / week_start * 100 if week_start != 0 else 0
            else:
                t = yf.Ticker(symbol)
                hist = t.history(period="5d")
                if hist.empty or len(hist) < 2:
                    continue
                current = safe_get(hist["Close"].iloc[-1])
                prev = safe_get(hist["Close"].iloc[-2])
                change_pct = (current - prev) / prev * 100 if prev != 0 else 0
                volume = safe_get(hist["Volume"].iloc[-1])
                week_start = safe_get(hist["Close"].iloc[0])
                week_change = (current - week_start) / week_start * 100 if week_start != 0 else 0

            results[symbol] = {
                "name": name,
                "price": current,
                "change_pct": change_pct,
                "volume": volume,
                "week_change_pct": week_change,
            }
        except Exception as e:
            results[symbol] = {"name": SECTOR_ETFS[symbol], "error": str(e)}
    return results


def compute_technical_indicators(symbol, period="3mo"):
    """计算技术指标: RSI, MA, MACD, Bollinger Bands"""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)
        if hist.empty or len(hist) < 20:
            return None

        close = hist["Close"]
        volume = hist["Volume"]

        # RSI (14-day)
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))

        # Moving Averages
        ma5 = close.rolling(5).mean()
        ma10 = close.rolling(10).mean()
        ma20 = close.rolling(20).mean()
        ma50 = close.rolling(50).mean()

        # MACD
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9, adjust=False).mean()
        macd_hist = macd - signal

        # Bollinger Bands
        bb_mid = ma20
        bb_std = close.rolling(20).std()
        bb_upper = bb_mid + 2 * bb_std
        bb_lower = bb_mid - 2 * bb_std

        # Volume analysis
        avg_volume_20 = volume.rolling(20).mean()
        vol_ratio = volume.iloc[-1] / avg_volume_20.iloc[-1] if safe_get(avg_volume_20.iloc[-1]) != 0 else 1

        current = safe_get(close.iloc[-1])
        prev = safe_get(close.iloc[-2]) if len(close) > 1 else current

        # Breakout detection
        breakout_signals = []
        if current > safe_get(bb_upper.iloc[-1]):
            breakout_signals.append("突破布林上轨")
        if current < safe_get(bb_lower.iloc[-1]):
            breakout_signals.append("跌破布林下轨")
        if current > safe_get(ma50.iloc[-1]) and prev < safe_get(ma50.iloc[-2]):
            breakout_signals.append("突破50日均线")
        if len(ma5) > 1 and len(ma20) > 1:
            if safe_get(ma5.iloc[-1]) > safe_get(ma20.iloc[-1]) and safe_get(ma5.iloc[-2]) <= safe_get(ma20.iloc[-2]):
                breakout_signals.append("金叉(MA5×MA20)")
            if safe_get(ma5.iloc[-1]) < safe_get(ma20.iloc[-1]) and safe_get(ma5.iloc[-2]) >= safe_get(ma20.iloc[-2]):
                breakout_signals.append("死叉(MA5×MA20)")
        if safe_get(macd.iloc[-1]) > safe_get(signal.iloc[-1]) and safe_get(macd.iloc[-2]) <= safe_get(signal.iloc[-2]):
            breakout_signals.append("MACD金叉")
        if safe_get(macd.iloc[-1]) < safe_get(signal.iloc[-1]) and safe_get(macd.iloc[-2]) >= safe_get(signal.iloc[-2]):
            breakout_signals.append("MACD死叉")
        if vol_ratio > 2.0:
            breakout_signals.append(f"放量{vol_ratio:.1f}倍")

        # Support/Resistance
        recent_high = safe_get(close.rolling(20).max().iloc[-1])
        recent_low = safe_get(close.rolling(20).min().iloc[-1])

        return {
            "symbol": symbol,
            "price": current,
            "change_pct": (current - prev) / prev * 100 if prev != 0 else 0,
            "rsi": safe_get(rsi.iloc[-1]),
            "ma5": safe_get(ma5.iloc[-1]),
            "ma10": safe_get(ma10.iloc[-1]),
            "ma20": safe_get(ma20.iloc[-1]),
            "ma50": safe_get(ma50.iloc[-1]),
            "macd": safe_get(macd.iloc[-1]),
            "macd_signal": safe_get(signal.iloc[-1]),
            "macd_hist": safe_get(macd_hist.iloc[-1]),
            "bb_upper": safe_get(bb_upper.iloc[-1]),
            "bb_lower": safe_get(bb_lower.iloc[-1]),
            "bb_mid": safe_get(bb_mid.iloc[-1]),
            "volume": safe_get(volume.iloc[-1]),
            "avg_volume_20": safe_get(avg_volume_20.iloc[-1]),
            "vol_ratio": vol_ratio,
            "breakout_signals": breakout_signals,
            "support": recent_low,
            "resistance": recent_high,
            "high": safe_get(hist["High"].iloc[-1]),
            "low": safe_get(hist["Low"].iloc[-1]),
            "open": safe_get(hist["Open"].iloc[-1]),
        }
    except Exception as e:
        return {"symbol": symbol, "error": str(e)}


def fetch_stock_fundamentals(symbol):
    """获取股票基本面数据"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        return {
            "symbol": symbol,
            "name": info.get("shortName", symbol),
            "market_cap": info.get("marketCap", 0),
            "pe_ratio": info.get("trailingPE", None),
            "forward_pe": info.get("forwardPE", None),
            "eps": info.get("trailingEps", None),
            "revenue_growth": info.get("revenueGrowth", None),
            "profit_margins": info.get("profitMargins", None),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "52w_high": info.get("fiftyTwoWeekHigh", None),
            "52w_low": info.get("fiftyTwoWeekLow", None),
            "avg_volume": info.get("averageVolume", 0),
            "beta": info.get("beta", None),
            "dividend_yield": info.get("dividendYield", None),
            "target_price": info.get("targetMeanPrice", None),
            "recommendation": info.get("recommendationKey", None),
        }
    except Exception as e:
        return {"symbol": symbol, "error": str(e)}


def scan_volume_surge_stocks():
    """扫描放量异动股票"""
    all_stocks = set()
    for stocks in HOT_SECTOR_STOCKS.values():
        all_stocks.update(stocks)
    all_stocks.update(TRACKED_STOCKS)
    extra = ["PLTR", "IONQ", "RGTI", "MSTR", "SHOP", "PANW", "SNOW", "DDOG",
             "NET", "ZS", "CRWD", "FTNT", "UBER", "ABNB", "DASH", "RBLX",
             "U", "TTD", "ROKU", "SNAP", "PINS", "SOFI", "HOOD",
             "MARA", "RIOT", "CLSK", "CIFR", "HUT", "BITF"]
    all_stocks.update(extra)
    all_stocks = list(all_stocks)

    surge_stocks = []
    for symbol in all_stocks:
        try:
            tech = compute_technical_indicators(symbol, period="3mo")
            if tech and "error" not in tech:
                if tech["vol_ratio"] > 1.5 or len(tech["breakout_signals"]) > 0:
                    surge_stocks.append(tech)
        except Exception:
            continue

    surge_stocks.sort(key=lambda x: x.get("vol_ratio", 0), reverse=True)
    return surge_stocks[:15]


def fetch_hot_sector_data():
    """获取热门板块数据"""
    results = {}
    for sector, symbols in HOT_SECTOR_STOCKS.items():
        sector_data = []
        for sym in symbols:
            try:
                tech = compute_technical_indicators(sym, period="3mo")
                if tech and "error" not in tech:
                    fund = fetch_stock_fundamentals(sym)
                    tech["name"] = fund.get("name", sym) if "error" not in fund else sym
                    tech["market_cap"] = fund.get("market_cap", 0) if "error" not in fund else 0
                    sector_data.append(tech)
            except Exception:
                continue
        results[sector] = sector_data
    return results


def fetch_tracked_stock_details():
    """获取重点跟踪股票详细数据"""
    details = {}
    for sym in TRACKED_STOCKS:
        try:
            tech = compute_technical_indicators(sym, period="3mo")
            fund = fetch_stock_fundamentals(sym)
            if tech and "error" not in tech:
                tech.update({k: v for k, v in fund.items() if k not in tech and "error" not in str(v)})
                details[sym] = tech
            else:
                details[sym] = fund
        except Exception as e:
            details[sym] = {"symbol": sym, "error": str(e)}
    return details


def get_top_gainers_losers():
    """获取涨幅/跌幅榜前10"""
    all_stocks = set()
    for stocks in HOT_SECTOR_STOCKS.values():
        all_stocks.update(stocks)
    all_stocks.update(TRACKED_STOCKS)
    all_stocks = list(all_stocks)

    stock_perf = []
    symbols_str = all_stocks
    try:
        data = yf.download(symbols_str, period="2d", group_by="ticker", progress=False, threads=True)
        for sym in all_stocks:
            try:
                if sym in data.columns.get_level_values(0):
                    sym_data = data[sym].dropna()
                    if len(sym_data) >= 2:
                        current = safe_get(sym_data["Close"].iloc[-1])
                        prev = safe_get(sym_data["Close"].iloc[-2])
                        volume = safe_get(sym_data["Volume"].iloc[-1])
                        if prev != 0:
                            change_pct = (current - prev) / prev * 100
                            stock_perf.append({
                                "symbol": sym,
                                "price": current,
                                "change_pct": change_pct,
                                "volume": volume,
                            })
            except Exception:
                continue
    except Exception:
        pass

    stock_perf.sort(key=lambda x: x["change_pct"], reverse=True)
    gainers = stock_perf[:10]
    losers = stock_perf[-10:][::-1]
    return gainers, losers


def get_all_market_data():
    """获取所有市场数据 - Main entry point"""
    print("📊 正在获取市场数据...")

    print("  → 获取主要指数数据...")
    indices = fetch_index_data()

    print("  → 获取板块ETF数据...")
    sector_etfs = fetch_sector_etf_data()

    print("  → 获取涨跌排行...")
    gainers, losers = get_top_gainers_losers()

    print("  → 获取热门板块数据...")
    hot_sectors = fetch_hot_sector_data()

    print("  → 扫描放量异动...")
    volume_surge = scan_volume_surge_stocks()

    print("  → 获取重点跟踪股票...")
    tracked = fetch_tracked_stock_details()

    print("✅ 数据获取完成!")

    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "date": datetime.now().strftime("%Y年%m月%d日"),
        "indices": indices,
        "sector_etfs": sector_etfs,
        "gainers": gainers,
        "losers": losers,
        "hot_sectors": hot_sectors,
        "volume_surge": volume_surge,
        "tracked_stocks": tracked,
    }


if __name__ == "__main__":
    data = get_all_market_data()
    with open("data/market_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    print(f"Data saved. Keys: {list(data.keys())}")
