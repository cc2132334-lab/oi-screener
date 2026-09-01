from datetime import datetime
import json
import random
import time


def calculate_trend(p_change, oi_change):
    if p_change >= 0 and oi_change >= 0:
        return "Long Buildup"
    elif p_change < 0 and oi_change >= 0:
        return "Short Buildup"
    elif p_change >= 0 and oi_change < 0:
        return "Short Covering"
    else:
        return "Long Unwinding"


def generate_market_data():
    symbols = [
        "RELIANCE",
        "HDFCBANK",
        "ICICIBANK",
        "INFY",
        "TCS",
        "SBIN",
        "AXISBANK",
        "LT",
        "TATAMOTORS",
        "BAJFINANCE",
        "KOTAKBANK",
        "MARUTI",
        "TATASTEEL",
        "SUNPHARMA",
        "BHARTIARTL",
    ]

    stocks = []
    for sym in symbols:
        ltp = round(random.uniform(400, 3800), 2)
        p_change = round(random.uniform(-4.5, 4.5), 2)
        oi_change = round(random.uniform(-18.0, 28.0), 2)
        vol_change = round(random.uniform(15.0, 350.0), 1)
        volume = int(random.uniform(800000, 9500000))
        trend = calculate_trend(p_change, oi_change)

        stocks.append(
            {
                "symbol": sym,
                "ltp": ltp,
                "pChange": p_change,
                "oiChange": oi_change,
                "volChange": vol_change,
                "volume": f"{volume:,}",
                "trend": trend,
            }
        )

    # Sort data for screener categories
    oi_gainers = sorted(stocks, key=lambda x: x["oiChange"], reverse=True)[:6]
    oi_losers = sorted(stocks, key=lambda x: x["oiChange"])[:6]
    vol_gainers = sorted(stocks, key=lambda x: x["volChange"], reverse=True)[:6]

    # Current IST Time
    now_ist = datetime.utcnow()
    # Adding approximate IST offset for display (+5:30)
    hour = (now_ist.hour + 5) + ((now_ist.minute + 30) // 60)
    minute = (now_ist.minute + 30) % 60
    second = now_ist.second
    formatted_time = f"{hour:02d}:{minute:02d}:{second:02d} IST"

    output = {
        "last_updated": formatted_time,
        "oi_gainers": oi_gainers,
        "oi_losers": oi_losers,
        "volume_gainers": vol_gainers,
    }

    with open("data.json", "w") as f:
        json.dump(output, f, indent=4)

    print("data.json successfully generated!")


if __name__ == "__main__":
    generate_market_data()
