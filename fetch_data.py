from datetime import datetime, timezone, timedelta
import json
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
        print(f"Session init warning: {e}")
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

def fetch_live_market_data():
    session = get_nse_session()
    
    # Endpoint 1: NSE F&O OI Spurts (Live OI Analysis)
    oi_url = "https://www.nseindia.com/api/live-analysis-oi-spurts-underlyings"
    # Endpoint 2: Most Active Securities by Volume
    vol_url = "https://www.nseindia.com/api/live-analysis-most-active-securities?index=volume"

    oi_gainers = []
    oi_losers = []
    vol_gainers = []

    # 1. Fetch Real OI Data
    try:
        res = session.get(oi_url, timeout=12)
        if res.status_code == 200:
            data = res.json().get("data", [])
            processed_stocks = []

            for item in data:
                symbol = item.get("symbol", "")
                ltp = float(item.get("underlyingValue", 0))
                prev_price = float(item.get("prevPrice", ltp))
                p_change = round(((ltp - prev_price) / prev_price * 100), 2) if prev_price > 0 else 0.0
                
                if "pChange" in item:
                    p_change = round(float(item.get("pChange", 0)), 2)

                oi_change = round(float(item.get("pChangeInOI", 0)), 2)
                volume = int(item.get("volume", 0))

                trend = calculate_trend(p_change, oi_change)

                processed_stocks.append({
                    "symbol": symbol,
                    "ltp": ltp,
                    "pChange": p_change,
                    "oiChange": oi_change,
                    "volChange": oi_change,
                    "volume": f"{volume:,}",
                    "trend": trend
                })

            # Top 10 OI Gainers & Losers
            oi_gainers = sorted(processed_stocks, key=lambda x: x["oiChange"], reverse=True)[:10]
            oi_losers = sorted(processed_stocks, key=lambda x: x["oiChange"])[:10]
    except Exception as e:
        print(f"Error fetching OI data: {e}")

    # 2. Fetch Real Volume Data
    try:
        res_vol = session.get(vol_url, timeout=12)
        if res_vol.status_code == 200:
            vol_data = res_vol.json().get("data", [])
            # Top 10 Most Active by Volume
            for item in vol_data[:10]:
                symbol = item.get("symbol", "")
                ltp = float(item.get("ltp", 0))
                p_change = round(float(item.get("pChange", 0)), 2)
                volume = int(item.get("totalTradedVolume", 0))
                vol_change = round(float(item.get("pChange", 0)), 1)

                vol_gainers.append({
                    "symbol": symbol,
                    "ltp": ltp,
                    "pChange": p_change,
                    "volChange": vol_change,
                    "volume": f"{volume:,}",
                    "trend": "High Volume"
                })
    except Exception as e:
        print(f"Error fetching Volume data: {e}")

    # Current IST Time (+5:30)
    ist_time = datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)
    formatted_time = ist_time.strftime("%I:%M:%S %p IST")

    output = {
        "last_updated": formatted_time,
        "oi_gainers": oi_gainers,
        "oi_losers": oi_losers,
        "volume_gainers": vol_gainers
    }

    with open("data.json", "w") as f:
        json.dump(output, f, indent=4)

    print(f"data.json updated with Top 10 stocks at {formatted_time}")

if __name__ == "__main__":
    fetch_live_market_data()
