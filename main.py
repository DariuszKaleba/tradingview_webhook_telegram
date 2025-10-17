import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Wczytaj dane z Render Environment Variables
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': 'No JSON received'}), 400

    message = f"📈 TradingView Alert:\n{data}"
    send_to_telegram(message)
    return jsonify({'status': 'ok'}), 200

def send_to_telegram(text):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("⚠️ Missing TELEGRAM_TOKEN or CHAT_ID environment variables")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print("❌ Telegram send error:", e)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
