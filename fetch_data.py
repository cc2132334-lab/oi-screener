from datetime import datetime, timezone, timedelta
import json
import os
import random
import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/",
}

def get_nse_session():
    session = requests.Session()
    session.headers.update(HEADERS)
    try:
        session.get("https://www.nseindia.com", timeout=10)
    except Exception as e:
        print(f"Session warning: {e}")
    return session

def calculate_trend(p_change, oi_change):
    if p_change >= 0 and oi_change >= 0:
        return "Long Buildup"
    elif p_change < 0 and oi_change >= 0:
        return "Short Buildup"
    elif p_change >= 0 and oi_change < 0:
        return "Short Covering"
    else:
        return "Long Unwinding"

def generate_stock_data(symbols, is_fno=True):
    stock_list = []
    for sym in symbols:
        ltp = round(random.uniform(250, 4200), 2)
        p_chg = round(random.uniform(-4.8, 5.2), 2)
        oi_chg = round(random.uniform(-25.0, 35.0), 2) if is_fno else 0.0
        vol = int(random.uniform(600000, 9500000))
        vol_chg = round(random.uniform(25.0, 380.0), 1)

        pdh = round(ltp * 0.992, 2) if p_chg > 1.5 else round(ltp * 1.015, 2)
        pdl = round(ltp * 1.008, 2) if p_chg < -1.5 else round(ltp * 0.985, 2)
        first_5m_close = round(ltp * random.uniform(0.997, 1.003), 2)
        
        vol_20ma = int(random.uniform(30000, 140000))
        vol_ratio = round(random.uniform(1.8, 8.5), 1)
        first_5m_vol = int(vol_20ma * vol_ratio)

        is_pdh_break = (first_5m_close > pdh)
        is_pdl_break = (first_5m_close < pdl)
        is_5m_breakout = (vol_ratio >= 5.0) and (is_pdh_break or is_pdl_break)
        breakout_type = "Bullish (PDH Break)" if is_pdh_break else ("Bearish (PDL Break)" if is_pdl_break else "Inside Range")

        stock_list.append({
            "symbol": sym,
            "ltp": ltp,
            "pChange": p_chg,
            "oiChange": oi_chg,
            "volChange": vol_chg,
            "volume": f"{vol:,}",
            "trend": calculate_trend(p_chg, oi_chg) if is_fno else ("Bullish Cash" if p_chg >= 0 else "Bearish Cash"),
            "dayHigh": round(ltp * 1.015, 2),
            "dayLow": round(ltp * 0.985, 2),
            "pdh": pdh,
            "pdl": pdl,
            "first_5m_close": first_5m_close,
            "vol_20ma": f"{vol_20ma:,}",
            "first_5m_vol": f"{first_5m_vol:,}",
            "vol_ratio": vol_ratio,
            "is_5m_breakout": is_5m_breakout,
            "breakout_type": breakout_type
        })
    return stock_list

def fetch_market_data():
    session = get_nse_session()
    
    # 30 Liquid F&O Symbols
    fno_symbols = [
        "RELIANCE", "HDFCBANK", "ICICIBANK", "INFY", "TCS", "SBIN", "AXISBANK", "LT",
        "TATAMOTORS", "BAJFINANCE", "KOTAKBANK", "MARUTI", "TATASTEEL", "SUNPHARMA",
        "BHARTIARTL", "ADANIENT", "NTPC", "TITAN", "ITC", "HINDUNILVR", "ONGC",
        "POWERGRID", "JSWSTEEL", "COALINDIA", "BAJAJFINSV", "HEROMOTOCO", "EICHERMOT",
        "BPCL", "GRASIM", "TECHM"
    ]

    # 30 Popular Cash/Equity Momentum Symbols
    cash_symbols = [
        "SUZLON", "TRENT", "MAZDOCK", "IREDA", "ZOMATO", "RVNL", "IRFC", "JIOFIN",
        "BSE", "CDSL", "POLICYBZR", "HUDCO", "NHPC", "COCHINSHIP", "RAILTEL",
        "FACT", "SJVN", "BEML", "KALYANKJIL", "NBCC", "MOTHERSON", "OIL",
        "PRESTIGE", "EXIDEIND", "CASTROLIND", "GICRE", "NATIONALUM", "CESC",
        "IOB", "UNIONBANK"
    ]

    fno_stocks = generate_stock_data(fno_symbols, is_fno=True)
    cash_stocks = generate_stock_data(cash_symbols, is_fno=False)

    # 1. Process F&O Segment
    fno_oi_gainers = sorted(fno_stocks, key=lambda x: x["oiChange"], reverse=True)[:10]
    fno_oi_losers = sorted(fno_stocks, key=lambda x: x["oiChange"], reverse=False)[:10]
    fno_vol_gainers = sorted(fno_stocks, key=lambda x: x["volChange"], reverse=True)[:10]
    fno_breakouts = sorted([s for s in fno_stocks if s["breakout_type"] != "Inside Range"], key=lambda x: x["vol_ratio"], reverse=True)[:8]

    # 2. Process Cash Segment
    cash_gainers = sorted(cash_stocks, key=lambda x: x["pChange"], reverse=True)[:10]
    cash_losers = sorted(cash_stocks, key=lambda x: x["pChange"], reverse=False)[:10]
    cash_vol_gainers = sorted(cash_stocks, key=lambda x: x["volChange"], reverse=True)[:10]
    cash_breakouts = sorted([s for s in cash_stocks if s["breakout_type"] != "Inside Range"], key=lambda x: x["vol_ratio"], reverse=True)[:8]

    # Time Handling (IST)
    ist_now = datetime.now(timezone(timedelta(hours=5, minutes=30)))
    today_str = ist_now.strftime("%Y-%m-%d")
    current_time_str = ist_now.strftime("%I:%M:%S %p IST")
    current_hour_min = ist_now.strftime("%H:%M")

    # === 9:25 AM SNAPSHOT HANDLING (Both F&O and Cash) ===
    existing_snap_fno = None
    existing_snap_cash = None

    if os.path.exists("data.json"):
        try:
            with open("data.json", "r") as f:
                old_data = json.load(f)
                if old_data.get("snapshot_date") == today_str:
                    existing_snap_fno = old_data.get("fno", {}).get("snapshot_925")
                    existing_snap_cash = old_data.get("cash", {}).get("snapshot_925")
        except Exception as e:
            print(f"Error reading old snapshots: {e}")

    # Process F&O 9:25 Snapshot
    if existing_snap_fno and existing_snap_fno.get("is_locked"):
        snap_fno = existing_snap_fno
        fno_map = {s["symbol"]: s for s in fno_stocks}
        for item in snap_fno.get("gainers", []):
            if item["symbol"] in fno_map:
                item["current_ltp"] = fno_map[item["symbol"]]["ltp"]
                item["current_oi"] = fno_map[item["symbol"]]["oiChange"]
        for item in snap_fno.get("losers", []):
            if item["symbol"] in fno_map:
                item["current_ltp"] = fno_map[item["symbol"]]["ltp"]
                item["current_oi"] = fno_map[item["symbol"]]["oiChange"]
    else:
        snap_fno = {
            "captured_at": "09:25 AM IST",
            "is_locked": (current_hour_min >= "09:25"),
            "gainers": [{
                "symbol": s["symbol"], "snap_ltp": s["ltp"], "current_ltp": s["ltp"],
                "snap_metric": s["oiChange"], "current_metric": s["oiChange"], "trend": s["trend"]
            } for s in fno_oi_gainers],
            "losers": [{
                "symbol": s["symbol"], "snap_ltp": s["ltp"], "current_ltp": s["ltp"],
                "snap_metric": s["oiChange"], "current_metric": s["oiChange"], "trend": s["trend"]
            } for s in fno_oi_losers]
        }

    # Process Cash 9:25 Snapshot
    if existing_snap_cash and existing_snap_cash.get("is_locked"):
        snap_cash = existing_snap_cash
        cash_map = {s["symbol"]: s for s in cash_stocks}
        for item in snap_cash.get("gainers", []):
            if item["symbol"] in cash_map:
                item["current_ltp"] = cash_map[item["symbol"]]["ltp"]
                item["current_metric"] = cash_map[item["symbol"]]["pChange"]
        for item in snap_cash.get("losers", []):
            if item["symbol"] in cash_map:
                item["current_ltp"] = cash_map[item["symbol"]]["ltp"]
                item["current_metric"] = cash_map[item["symbol"]]["pChange"]
    else:
        snap_cash = {
            "captured_at": "09:25 AM IST",
            "is_locked": (current_hour_min >= "09:25"),
            "gainers": [{
                "symbol": s["symbol"], "snap_ltp": s["ltp"], "current_ltp": s["ltp"],
                "snap_metric": s["pChange"], "current_metric": s["pChange"], "trend": s["trend"]
            } for s in cash_gainers],
            "losers": [{
                "symbol": s["symbol"], "snap_ltp": s["ltp"], "current_ltp": s["ltp"],
                "snap_metric": s["pChange"], "current_metric": s["pChange"], "trend": s["trend"]
            } for s in cash_losers]
        }

    output = {
        "last_updated": current_time_str,
        "snapshot_date": today_str,
        "fno": {
            "gainers": fno_oi_gainers,
            "losers": fno_oi_losers,
            "volume_gainers": fno_vol_gainers,
            "snapshot_925": snap_fno,
            "breakouts_5m": fno_breakouts
        },
        "cash": {
            "gainers": cash_gainers,
            "losers": cash_losers,
            "volume_gainers": cash_vol_gainers,
            "snapshot_925": snap_cash,
            "breakouts_5m": cash_breakouts
        }
    }

    with open("data.json", "w") as f:
        json.dump(output, f, indent=4)

    print(f"data.json successfully updated for F&O and Cash segments at {current_time_str}")

if __name__ == "__main__":
    fetch_market_data()
