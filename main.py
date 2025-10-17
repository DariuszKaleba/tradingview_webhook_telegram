import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Wczytaj dane z Render Environment Variables
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")


@app.route('/webhook', methods=['POST'])
def webhook():
    """Odbiera webhook z TradingView i przesyła dane do Telegrama"""
    data = request.get_json(silent=True)
    print("📩 Odebrano webhook:", data)

    if not data:
        print("⚠️ Brak danych JSON w żądaniu")
        return jsonify({'status': 'error', 'message': 'No JSON received'}), 400

    # Format wiadomości
    message = f"📈 TradingView Alert:\n{data}"

    # Wyślij do Telegrama
    send_to_telegram(message)
    return jsonify({'status': 'ok'}), 200


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


@app.route('/', methods=['GET'])
def home():
    """Strona testowa"""
    return "✅ TradingView Webhook → Telegram Bot działa!", 200


if __name__ == '__main__':
    # Render wymaga użycia portu z ENV zmiennej 'PORT'
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
