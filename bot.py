from flask import Flask, request

from telegram import Bot
import json
from src.upstox_api import list_expiries, get_put_call_option_chain, UpstoxAPIError
from src.config import UNDERLYINGS

credentials = json.load(open('credentials.json','r',encoding='utf-8'))

app = Flask(__name__)
TELEGRAM_TOKEN = credentials['telegram_bot_token']
UPSTOX_TOKEN = credentials['upstox_access_token']
OWNER_ID = credentials['owner_id']
bot = Bot(token=TELEGRAM_TOKEN)
bot.set_webhook("https://charred-outrage-expansion.ngrok-free.dev/webhook")

def _check_id(update):
    user_id= update.get("message",{}).get("from",{}).get("id","")
    assert user_id == OWNER_ID, "ID does not match. You are not the owner"


@app.route('/webhook', methods=['POST'],)
async def webhook():
    update = request.get_json()
    print(update)
    chat_id = update['message']['chat']['id']
    try:
        _check_id(update)
    except AssertionError as e:
        await bot.send_message(chat_id=chat_id, text=str(e))
        return 'OK'

    message = update['message']['text']
    
    # Check for instruments
    underlyings_lower = {k.lower(): v for k, v in UNDERLYINGS.items()}
    matched = False
    for name, instrument_key in underlyings_lower.items():
        if name in message.lower():
            matched = True
            try:
                expiries = list_expiries(UPSTOX_TOKEN, instrument_key)
                if expiries:
                    expiry = expiries[0]
                    chain = get_put_call_option_chain(UPSTOX_TOKEN, instrument_key, expiry)
                    if not chain.empty and 'spot' in chain.columns:
                        spot = chain['spot'].dropna().iloc[0]
                        await bot.send_message(chat_id=chat_id, text=f"{name.upper()}: Spot price is {spot}")
                    else:
                        await bot.send_message(chat_id=chat_id, text=f"Could not fetch spot price for {name.upper()}")
                else:
                    await bot.send_message(chat_id=chat_id, text=f"No expiries found for {name.upper()}")
            except UpstoxAPIError as e:
                await bot.send_message(chat_id=chat_id, text=f"Error fetching data for {name.upper()}: {str(e)}")
            break  # Only respond to the first match
    
    if not matched:
        valid = ", ".join(UNDERLYINGS.keys())
        await bot.send_message(chat_id=chat_id, text=f"No matching underlying found. Available: {valid}")
    
    return 'OK'


if __name__ == '__main__':
    app.run(port=5000)