# Async CEX to DEX Arbitrage Scanner with Telegram Alerts

import ccxt.async_support as ccxt
import aiohttp
import asyncio
import time
from telegram import Bot

# Replace with your Telegram bot token and chat ID
TELEGRAM_TOKEN = '8164999338:AAH4AeVALQgQFs1rZoHBoqSYvUHfvIrbHIk'
CHAT_ID = '5970544537'
bot = Bot(token=TELEGRAM_TOKEN)

exchanges = {
    'bybit': ccxt.bybit(),
    'binance': ccxt.binance(),
    'gateio': ccxt.gateio()
}

async def get_dex_price(session, symbol):
    query = symbol.replace('/', '')
    url = f'https://api.dexscreener.com/latest/dex/search?q={query}'
    try:
        async with session.get(url) as resp:
            data = await resp.json()
            if 'pairs' in data and data['pairs']:
                return float(data['pairs'][0]['priceUsd'])
    except:
        return None
    return None

async def scan():
    async with aiohttp.ClientSession() as session:
        while True:
            tasks = []
            for ex_name, ex in exchanges.items():
                try:
                    markets = await ex.load_markets()
                    symbols = [s for s in markets if s.endswith('/USDT')]
                except:
                    continue
                for symbol in symbols:
                    tasks.append(check_pair(session, ex, ex_name, symbol))

            results = await asyncio.gather(*tasks)
            filtered = [r for r in results if r]
            top = sorted(filtered, key=lambda x: x['pct_diff'], reverse=True)[:5]
            for opp in top:
                msg = (f"💸 Arbitrage Opportunity:\n"
                       f"{opp['symbol']} | {opp['cex']} @ {opp['cex_price']} → DEX @ {opp['dex_price']}\n"
                       f"Spread: {opp['pct_diff']}%")
                await bot.send_message(chat_id=CHAT_ID, text=msg)
                print(msg)

            await asyncio.sleep(60)

async def check_pair(session, ex, ex_name, symbol):
    try:
        ticker = await ex.fetch_ticker(symbol)
        cex_price = ticker['ask']
        dex_price = await get_dex_price(session, symbol)
        if dex_price and cex_price:
            spread = dex_price - cex_price
            pct_diff = (spread / cex_price) * 100
            if spread > 0.01 and pct_diff > 1:
                return {
                    'symbol': symbol,
                    'cex': ex_name,
                    'cex_price': round(cex_price, 6),
                    'dex_price': round(dex_price, 6),
                    'spread': round(spread, 6),
                    'pct_diff': round(pct_diff, 2)
                }
    except:
        return None

if __name__ == '__main__':
    asyncio.run(scan())
