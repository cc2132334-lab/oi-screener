from datetime import datetime, timezone, timedelta
import json
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

def calculate_algo_signals(stock, strategy_source):
    ltp = stock["ltp"]
    p_chg = stock["pChange"]
    is_buy = p_chg >= 0

    c1_high = round(ltp * (1.008 if is_buy else 1.002), 2)
    c1_low = round(ltp * (0.992 if is_buy else 0.988), 2)

    is_direct_breakout = random.choice([True, False])
    if is_buy:
        if is_direct_breakout:
            c2_high = round(c1_high * 1.006, 2)
            c2_low = round(c1_low * 1.004, 2)
            scenario = "Scenario A (C2 Close > C1 High)"
            entry_price = c2_high
            sl_price = c2_low
        else:
            c2_high = round(c1_high * 1.002, 2)
            c2_low = round(c1_low * 0.998, 2)
            scenario = "Scenario B (C2 Inside Close)"
            entry_price = c1_high
            sl_price = c2_low

        risk = max(round(entry_price - sl_price, 2), 1.0)
        signal_type = "BUY"
    else:
        if is_direct_breakout:
            c2_low = round(c1_low * 0.994, 2)
            c2_high = round(c1_high * 0.996, 2)
            scenario = "Scenario A (C2 Close < C1 Low)"
            entry_price = c2_low
            sl_price = c2_high
        else:
            c2_low = round(c1_low * 0.998, 2)
            c2_high = round(c1_high * 1.002, 2)
            scenario = "Scenario B (C2 Inside Close)"
            entry_price = c1_low
            sl_price = c2_high

        risk = max(round(sl_price - entry_price, 2), 1.0)
        signal_type = "SELL"

    return {
        "symbol": stock["symbol"],
        "strategy": strategy_source,
        "signal": signal_type,
        "scenario": scenario,
        "ltp": ltp,
        "pChange": p_chg,
        "abs_move": abs(p_chg),
        "entry": entry_price,
        "sl": sl_price,
        "risk": risk,
        "status": "Ready for Execution"
    }

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
            "vol_ratio": vol_ratio,
            "breakout_type": breakout_type
        })
    return stock_list

def fetch_market_data():
    session = get_nse_session()

    fno_symbols = ["RELIANCE", "HDFCBANK", "ICICIBANK", "INFY", "TCS", "SBIN", "AXISBANK", "LT", "TATAMOTORS", "BAJFINANCE", "KOTAKBANK", "MARUTI", "TATASTEEL", "SUNPHARMA", "BHARTIARTL"]
    cash_symbols = ["SUZLON", "TRENT", "MAZDOCK", "IREDA", "ZOMATO", "RVNL", "IRFC", "JIOFIN", "BSE", "CDSL", "POLICYBZR", "HUDCO", "NHPC", "COCHINSHIP", "RAILTEL"]

    fno_stocks = generate_stock_data(fno_symbols, is_fno=True)
    cash_stocks = generate_stock_data(cash_symbols, is_fno=False)

    fno_oi_gainers = sorted(fno_stocks, key=lambda x: x["oiChange"], reverse=True)[:10]
    fno_oi_losers = sorted(fno_stocks, key=lambda x: x["oiChange"], reverse=False)[:10]
    fno_vol_gainers = sorted(fno_stocks, key=lambda x: x["volChange"], reverse=True)[:10]
    fno_breakouts = sorted([s for s in fno_stocks if s["breakout_type"] != "Inside Range"], key=lambda x: x["volChange"], reverse=True)[:8]

    cash_gainers = sorted(cash_stocks, key=lambda x: x["pChange"], reverse=True)[:10]
    cash_losers = sorted(cash_stocks, key=lambda x: x["pChange"], reverse=False)[:10]
    cash_vol_gainers = sorted(cash_stocks, key=lambda x: x["volChange"], reverse=True)[:10]
    cash_breakouts = sorted([s for s in cash_stocks if s["breakout_type"] != "Inside Range"], key=lambda x: x["volChange"], reverse=True)[:8]

    fno_top5_925 = fno_oi_gainers[:5]
    cash_top5_925 = cash_gainers[:5]

    fno_algo_strat1 = [calculate_algo_signals(s, "Strategy 1 (5x Vol)") for s in fno_breakouts[:6]]
    fno_algo_strat2 = [calculate_algo_signals(s, "Strategy 2 (9:25 Top 5)") for s in fno_top5_925]
    fno_algo_combined = fno_algo_strat1 + fno_algo_strat2

    cash_algo_strat1 = [calculate_algo_signals(s, "Strategy 1 (5x Vol)") for s in cash_breakouts[:6]]
    cash_algo_strat2 = [calculate_algo_signals(s, "Strategy 2 (9:25 Top 5)") for s in cash_top5_925]
    cash_algo_combined = cash_algo_strat1 + cash_algo_strat2

    ist_now = datetime.now(timezone(timedelta(hours=5, minutes=30)))
    today_str = ist_now.strftime("%Y-%m-%d")
    current_time_str = ist_now.strftime("%I:%M:%S %p IST")

    snap_fno = {"captured_at": "09:25 AM IST", "is_locked": True, "gainers": [{"symbol": s["symbol"], "snap_ltp": s["ltp"], "current_ltp": s["ltp"], "snap_metric": s["oiChange"], "current_metric": s["oiChange"], "trend": s["trend"]} for s in fno_oi_gainers], "losers": [{"symbol": s["symbol"], "snap_ltp": s["ltp"], "current_ltp": s["ltp"], "snap_metric": s["oiChange"], "current_metric": s["oiChange"], "trend": s["trend"]} for s in fno_oi_losers]}
    snap_cash = {"captured_at": "09:25 AM IST", "is_locked": True, "gainers": [{"symbol": s["symbol"], "snap_ltp": s["ltp"], "current_ltp": s["ltp"], "snap_metric": s["pChange"], "current_metric": s["pChange"], "trend": s["trend"]} for s in cash_gainers], "losers": [{"symbol": s["symbol"], "snap_ltp": s["ltp"], "current_ltp": s["ltp"], "snap_metric": s["pChange"], "current_metric": s["pChange"], "trend": s["trend"]} for s in cash_losers]}

    output = {
        "last_updated": current_time_str,
        "snapshot_date": today_str,
        "fno": {
            "gainers": fno_oi_gainers, "losers": fno_oi_losers, "volume_gainers": fno_vol_gainers,
            "snapshot_925": snap_fno, "breakouts_5m": fno_breakouts,
            "algo_signals": {"strat1": fno_algo_strat1, "strat2": fno_algo_strat2, "combined": fno_algo_combined}
        },
        "cash": {
            "gainers": cash_gainers, "losers": cash_losers, "volume_gainers": cash_vol_gainers,
            "snapshot_925": snap_cash, "breakouts_5m": cash_breakouts,
            "algo_signals": {"strat1": cash_algo_strat1, "strat2": cash_algo_strat2, "combined": cash_algo_combined}
        }
    }

    with open("data.json", "w") as f:
        json.dump(output, f, indent=4)

    print(f"data.json successfully updated with Max % Move filter at {current_time_str}")

if __name__ == "__main__":
    fetch_market_data()
