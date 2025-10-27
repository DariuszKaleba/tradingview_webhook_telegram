import os
from flask import Flask, request, jsonify
import requests
import json

app = Flask(__name__)

# Wczytaj dane z Render Environment Variables
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")


def send_to_telegram(text):
    """Wysyła wiadomość do Telegrama"""
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("⚠️ Missing TELEGRAM_TOKEN or CHAT_ID environment variables")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}

    try:
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code != 200:
            print("❌ Błąd wysyłania do Telegrama:", response.text)
        else:
            print("✅ Wiadomość wysłana do Telegrama")
    except Exception as e:
        print("❌ Telegram send error:", e)


def handle_webhook_data(data):
    """Przetwarza dane z webhooka"""
    print("📩 Odebrano webhook:", data)
    if not data:
        print("⚠️ Brak danych JSON w żądaniu lub błędny format")
        return jsonify({'status': 'error', 'message': 'Invalid or empty JSON'}), 400

    # Pobierz dane
    symbol = data.get('symbol', '❓')
    price = data.get('price', '❓')
    condition = data.get('condition', 'No condition')
    time = data.get('time', '❓')

    # Ładne formatowanie wiadomości
    message = (
        f"📈 <b>TradingView Alert</b>\n"
        f"Symbol: <b>{symbol}</b>\n"
        f"Price: <b>{price}</b>\n"
        f"Condition: {condition}\n"
        f"Time: {time}"
    )

    send_to_telegram(message)
    return jsonify({'status': 'ok'}), 200


@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json(silent=True)
    if not data:
        # Jeśli TradingView nie wysłało JSON-a poprawnie, spróbuj sparsować ręcznie
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
