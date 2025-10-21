import os
from flask import Flask, request, jsonify
import requests

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
    payload = {"chat_id": CHAT_ID, "text": text}

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
        print("⚠️ Brak danych JSON w żądaniu")
        return jsonify({'status': 'error', 'message': 'No JSON received'}), 400

    message = f"📈 TradingView Alert:\n{data}"
    send_to_telegram(message)
    return jsonify({'status': 'ok'}), 200


# Obsługa /webhook (główne wejście)
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json(silent=True)
    return handle_webhook_data(data)


# Obsługa / (GET i POST)
@app.route('/', methods=['GET', 'POST'])
def root():
    if request.method == 'GET':
        return "✅ TradingView Webhook → Telegram Bot działa!", 200
    elif request.method == 'POST':
        data = request.get_json(silent=True)
        return handle_webhook_data(data)


if __name__ == '__main__':
    # Render wymaga użycia portu z ENV zmiennej 'PORT'
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
