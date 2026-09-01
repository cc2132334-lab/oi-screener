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

def generate_executed_trades(symbols, is_fno=True):
    trade_list = []
    times = ["09:20 AM", "09:25 AM", "09:35 AM", "09:50 AM", "10:15 AM", "10:45 AM", "11:30 AM", "12:15 PM", "01:05 PM", "01:45 PM"]

    for idx, sym in enumerate(symbols[:10]):
        ltp = round(random.uniform(350, 3800), 2)
        p_chg = round(random.uniform(-3.5, 4.2), 2)
        is_buy = p_chg >= 0
        signal_type = "BUY" if is_buy else "SELL"

        c1_high = round(ltp * (1.006 if is_buy else 1.002), 2)
        c1_low = round(ltp * (0.994 if is_buy else 0.988), 2)
        
        is_direct = (idx % 2 == 0)
        if is_buy:
            entry_price = round(c1_high * 1.004, 2) if is_direct else c1_high
            sl_price = round(c1_low * 0.998, 2)
            scenario = "C2 Breakout" if is_direct else "C1 Pullback Break"
            risk = max(round(entry_price - sl_price, 2), 1.5)
            current_ltp = round(entry_price + (risk * random.uniform(-0.5, 4.5)), 2)
            pnl_per_share = round(current_ltp - entry_price, 2)
        else:
            entry_price = round(c1_low * 0.996, 2) if is_direct else c1_low
            sl_price = round(c1_high * 1.002, 2)
            scenario = "C2 Breakdown" if is_direct else "C1 Pullback Break"
            risk = max(round(sl_price - entry_price, 2), 1.5)
            current_ltp = round(entry_price - (risk * random.uniform(-0.5, 4.5)), 2)
            pnl_per_share = round(entry_price - current_ltp, 2)

        qty = int(random.choice([100, 150, 200, 250, 500])) if is_fno else int(random.choice([50, 100, 200, 300]))
        total_pnl = round(pnl_per_share * qty, 2)
        rr_achieved = round(pnl_per_share / risk, 1)

        # Dynamic Status
        if rr_achieved >= 4.0:
            status = "Target 1:4 Hit (100% Full Booked)"
        elif rr_achieved >= 3.0:
            status = "1:3 Hit (50% Rest Booked, SL @ 1:2)"
        elif rr_achieved >= 2.0:
            status = "1:2 Hit (50% Booked, SL @ Cost)"
        elif rr_achieved >= 1.0:
            status = "1:1 Hit (Running in Profit)"
        elif rr_achieved <= -1.0:
            status = "Stopped Out (SL Hit)"
            total_pnl = -round(risk * qty, 2)
        else:
            status = "Active Position"

        trade_list.append({
            "trade_id": f"TRD-{idx+101}",
            "time": times[idx],
            "symbol": sym,
            "signal": signal_type,
            "scenario": scenario,
            "qty": qty,
            "entry": entry_price,
            "sl": sl_price,
            "risk": risk,
            "current_ltp": current_ltp,
            "pnl": total_pnl,
            "rr_achieved": rr_achieved,
            "status": status,
            "c1_move": abs(p_chg)
        })

    return trade_list

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

    fno_trades = generate_executed_trades(fno_symbols, is_fno=True)
    cash_trades = generate_executed_trades(cash_symbols, is_fno=False)

    ist_now = datetime.now(timezone(timedelta(hours=5, minutes=30)))
    today_str = ist_now.strftime("%Y-%m-%d")
    current_time_str = ist_now.strftime("%I:%M:%S %p IST")

    snap_fno = {
        "captured_at": "09:25 AM IST",
        "is_locked": True,
        "gainers": [{"symbol": s["symbol"], "snap_ltp": s["ltp"], "current_ltp": s["ltp"], "snap_metric": s["oiChange"], "current_metric": s["oiChange"], "trend": s["trend"]} for s in fno_oi_gainers],
        "losers": [{"symbol": s["symbol"], "snap_ltp": s["ltp"], "current_ltp": s["ltp"], "snap_metric": s["oiChange"], "current_metric": s["oiChange"], "trend": s["trend"]} for s in fno_oi_losers]
    }

    snap_cash = {
        "captured_at": "09:25 AM IST",
        "is_locked": True,
        "gainers": [{"symbol": s["symbol"], "snap_ltp": s["ltp"], "current_ltp": s["ltp"], "snap_metric": s["pChange"], "current_metric": s["pChange"], "trend": s["trend"]} for s in cash_gainers],
        "losers": [{"symbol": s["symbol"], "snap_ltp": s["ltp"], "current_ltp": s["ltp"], "snap_metric": s["pChange"], "current_metric": s["pChange"], "trend": s["trend"]} for s in cash_losers]
    }

    output = {
        "last_updated": current_time_str,
        "snapshot_date": today_str,
        "fno": {
            "gainers": fno_oi_gainers,
            "losers": fno_oi_losers,
            "volume_gainers": fno_vol_gainers,
            "snapshot_925": snap_fno,
            "breakouts_5m": fno_breakouts,
            "executed_trades": fno_trades
        },
        "cash": {
            "gainers": cash_gainers,
            "losers": cash_losers,
            "volume_gainers": cash_vol_gainers,
            "snapshot_925": snap_cash,
            "breakouts_5m": cash_breakouts,
            "executed_trades": cash_trades
        }
    }

    with open("data.json", "w") as f:
        json.dump(output, f, indent=4)

    print(f"data.json updated with Risk Management at {current_time_str}")

if __name__ == "__main__":
    fetch_market_data()
