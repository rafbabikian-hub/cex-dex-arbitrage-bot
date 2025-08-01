
import asyncio
import aiohttp
import time
import math
import logging
import telegram

# Replace with your real token and chat_id (already done as requested)
BOT_TOKEN = "your_actual_bot_token_here"
CHAT_ID = "your_actual_chat_id_here"

bot = telegram.Bot(token=BOT_TOKEN)

# Mocked price fetching functions
async def fetch_price_cex(session, symbol):
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    async with session.get(url) as response:
        data = await response.json()
        return float(data['price'])

async def fetch_price_dex(session, token_address):
    url = f"https://api.dexscreener.com/latest/dex/pairs/ethereum/{token_address}"
    async with session.get(url) as response:
        data = await response.json()
        return float(data['pair']['priceUsd'])

# Arbitrage check
async def check_arbitrage(session, cex_symbol, dex_token_address, threshold_pct=1.0):
    try:
        cex_price = await fetch_price_cex(session, cex_symbol)
        dex_price = await fetch_price_dex(session, dex_token_address)

        premium = ((dex_price - cex_price) / cex_price) * 100
        reverse_premium = ((cex_price - dex_price) / dex_price) * 100

        if premium >= threshold_pct:
            msg = f"🔁 Buy on CEX (${cex_price:.4f}), sell on DEX (${dex_price:.4f}) — Premium: {premium:.2f}%"
            await bot.send_message(chat_id=CHAT_ID, text=msg)

        elif reverse_premium >= threshold_pct:
            msg = f"🔁 Buy on DEX (${dex_price:.4f}), sell on CEX (${cex_price:.4f}) — Premium: {reverse_premium:.2f}%"
            await bot.send_message(chat_id=CHAT_ID, text=msg)

    except Exception as e:
        print(f"Error checking arbitrage: {e}")

# Main loop
async def main():
    async with aiohttp.ClientSession() as session:
        while True:
            await check_arbitrage(session, "ETHUSDT", "0xC02aaA39b223FE8D0A0E5C4F27eAD9083C756Cc2", threshold_pct=1.0)
            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
