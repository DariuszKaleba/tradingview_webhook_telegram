import os
import json
from flask import Flask, request, jsonify
import requests
from datetime import datetime

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")


def send_to_telegram(text, symbol=None):
    """Wysyła wiadomość do Telegrama z opcjonalnym przyciskiem TradingView"""
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("⚠️ Missing TELEGRAM_TOKEN or CHAT_ID environment variables")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
    }

    # 🔗 Dodaj przycisk "Otwórz wykres"
    if symbol:
        tradingview_url = f"https://www.tradingview.com/chart/?symbol={symbol.replace(':', '').replace('/', '')}"
        payload["reply_markup"] = {
            "inline_keyboard": [
                [{"text": "📈 Otwórz wykres w TradingView", "url": tradingview_url}]
            ]
        }

    try:
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code != 200:
            print("❌ Błąd wysyłania do Telegrama:", response.text)
        else:
            print("✅ Wiadomość wysłana do Telegrama")
    except Exception as e:
        print("❌ Telegram send error:", e)


def handle_webhook_data(data):
    print("📩 Odebrano webhook:", data)

    if not data:
        return jsonify({'status': 'error', 'message': 'Invalid or empty JSON'}), 400

    symbol = data.get('symbol', '❓')
    price = data.get('price', '❓')
    condition = str(data.get('condition', '')).upper()
    time_str = data.get('time', None)
    interval = data.get('interval', None)
    strategy = data.get('strategy', None)

    # 🕒 Formatowanie czasu
    if time_str:
        try:
            time_obj = datetime.strptime(time_str.replace('Z', ''), "%Y-%m-%dT%H:%M:%S")
            time_fmt = time_obj.strftime("%Y-%m-%d %H:%M UTC")
        except Exception:
            time_fmt = time_str
    else:
        time_fmt = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    # 💰 Format ceny
    try:
        price = float(price)
        price_fmt = f"{price:,.2f}".replace(",", " ")
    except Exception:
        price_fmt = price

    # 🔼/🔽 Emoji dla BUY/SELL
    if "BUY" in condition:
        emoji = "🟢"
        condition_fmt = f"{emoji} BUY"
    elif "SELL" in condition:
        emoji = "🔴"
        condition_fmt = f"{emoji} SELL"
    else:
        emoji = "⚪"
        condition_fmt = condition or "UNKNOWN"

    # 📩 Wiadomość Telegram
    message = (
        f"{emoji} <b>TradingView Alert</b>\n\n"
        f"📊 <b>Symbol:</b> {symbol}\n"
        f"💰 <b>Price:</b> {price_fmt}\n"
        f"📈 <b>Condition:</b> {condition_fmt}\n"
        f"⏰ <b>Time:</b> {time_fmt}"
    )

    if interval:
        message += f"\n🕐 <b>Interval:</b> {interval}"
    if strategy:
        message += f"\n🧠 <b>Strategy:</b> {strategy}"

    send_to_telegram(message, symbol)
    return jsonify({'status': 'ok'}), 200


@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json(silent=True)
    if not data:
        try:
            data = json.loads(request.data.decode('utf-8'))
        except Exception as e:
            print("❌ Błąd parsowania request.data:", e)
            print("📦 request.data =", request.data)
            return jsonify({'status': 'error', 'message': 'Invalid data format'}), 400
    return handle_webhook_data(data)


@app.route('/', methods=['GET', 'POST', 'HEAD'])
def root():
    if request.method == 'GET':
        return "✅ TradingView Webhook → Telegram Bot działa!", 200
    elif request.method == 'POST':
        data = request.get_json(silent=True)
        if not data:
            try:
                data = json.loads(request.data.decode('utf-8'))
            except Exception as e:
                print("❌ Błąd parsowania request.data:", e)
                print("📦 request.data =", request.data)
                return jsonify({'status': 'error', 'message': 'Invalid data format'}), 400
        return handle_webhook_data(data)
    elif request.method == 'HEAD':
        return ("", 200, {})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
