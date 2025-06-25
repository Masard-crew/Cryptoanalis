import requests
import matplotlib.pyplot as plt
from datetime import datetime
import pytz
import os

# === Konfigurasi Telegram ===
TELEGRAM_TOKEN = "8130743705:AAF9DQJD4LQgfNG8fAZSQfhnRP0wd8y6zx8"
CHAT_ID = "-1002538490178"

# === Konfigurasi Crypto ===
COINGECKO_API = 'https://api.coingecko.com/api/v3/coins/markets'
VS_CURRENCY = 'usd'
LIMIT = 30

NARRATIVES = {
    'AI': ['ai', 'artificial', 'neural'],
    'DeFi': ['defi', 'decentralized finance'],
    'Gaming': ['game', 'gaming', 'metaverse'],
    'Privacy': ['privacy', 'anon', 'zk'],
    'Layer 2': ['layer2', 'rollup', 'optimism', 'arbitrum'],
}
STABLECOINS = {'usdt','usdc','dai','busd','usdd','tusd','usdp'}

def get_crypto_data():
    params = {
        'vs_currency': VS_CURRENCY,
        'order': 'market_cap_desc',
        'per_page': LIMIT,
        'page': 1,
        'sparkline': False
    }
    return requests.get(COINGECKO_API, params=params).json()

def is_stablecoin(symbol):
    s = symbol.lower()
    return s in STABLECOINS or 'usd' in s

def detect_narrative(name):
    n = name.lower()
    for label, kws in NARRATIVES.items():
        for kw in kws:
            if kw in n:
                return label
    return 'Lainnya'

def classify(data):
    filtered = [c for c in data if not is_stablecoin(c['symbol'])]
    gainers = sorted(filtered, key=lambda x: x.get('price_change_percentage_24h', 0), reverse=True)[:5]
    losers = sorted(filtered, key=lambda x: x.get('price_change_percentage_24h', 0))[:5]
    return gainers, losers, filtered

def gen_bar(gainers, losers):
    names_g = [c['name'] for c in gainers]
    vals_g = [c['price_change_percentage_24h'] for c in gainers]
    names_l = [c['name'] for c in losers]
    vals_l = [c['price_change_percentage_24h'] for c in losers]

    fig, ax = plt.subplots(figsize=(10,6))
    ax.barh(names_g[::-1], vals_g[::-1], color='green')
    ax.barh(names_l[::-1], vals_l[::-1], color='red')
    ax.set_title("Top 5 Gainers & Losers (24 h)")
    ax.set_xlabel("Perubahan (%)")
    plt.tight_layout()
    path = 'chart_bar.png'
    fig.savefig(path)
    plt.close(fig)
    return path

def gen_pie(all_data):
    cnt = {}
    for c in all_data:
        n = detect_narrative(c['name'])
        cnt[n] = cnt.get(n, 0) + 1

    fig, ax = plt.subplots()
    ax.pie(list(cnt.values()), labels=list(cnt.keys()), autopct='%1.1f%%')
    ax.set_title("Distribusi Narasi Koin")
    plt.tight_layout()
    path = 'chart_pie.png'
    fig.savefig(path)
    plt.close(fig)
    return path

def send_photo(path, caption):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    with open(path, 'rb') as photo:
        requests.post(url, data={'chat_id': CHAT_ID, 'caption': caption}, files={'photo': photo})

def main():
    now = datetime.now(pytz.timezone('Asia/Jakarta')).strftime('%d %b %Y %H:%M')
    data = get_crypto_data()
    gainers, losers, all_data = classify(data)

    txt = f"📈 *Laporan Market Kripto*\n🕒 {now}\n\n"
    txt += "🏆 *Top 5 Gainers:*\n" + "\n".join(f"• {c['name']}: +{c['price_change_percentage_24h']:.2f}%" for c in gainers) + "\n\n"
    txt += "📉 *Top 5 Losers:*\n" + "\n".join(f"• {c['name']}: {c['price_change_percentage_24h']:.2f}%" for c in losers)

    narasi_cnt = {}
    for c in all_data:
        n = detect_narrative(c['name'])
        narasi_cnt[n] = narasi_cnt.get(n, 0) + 1
    txt2 = "📊 *Narasi Trending:*\n" + "\n".join(f"• {k}: {v} koin" for k, v in narasi_cnt.items())

    bpath = gen_bar(gainers, losers)
    ppath = gen_pie(all_data)
    send_photo(bpath, txt)
    send_photo(ppath, txt2)

if __name__ == "__main__":
    main()