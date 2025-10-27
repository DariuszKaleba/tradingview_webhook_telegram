import os
import json
import re
from datetime import datetime
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# ───────────── KONFIGURACJA TELEGRAM ─────────────
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# ───────────── FUNKCJA: WYSYŁANIE WIADOMOŚCI ─────────────
def send_to_telegram(text, symbol=None):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("⚠️ Brakuje TELEGRAM_TOKEN lub CHAT_ID (Render → Environment Variables)")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}

    # link do wykresu TradingView
    if symbol:
        tv_url = f"https://www.tradingview.com/chart/?symbol={str(symbol).replace(':', '').replace('/', '')}"
        payload["reply_markup"] = {
            "inline_keyboard": [[{"text": "📈 Otwórz wykres w TradingView", "url": tv_url}]]
        }

    try:
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code != 200:
            print("❌ Błąd wysyłania do Telegrama:", response.text)
        else:
            print("✅ Wiadomość wysłana do Telegrama")
    except Exception as e:
        print("❌ Telegram send error:", e)


# ───────────── FUNKCJA: WYCIĄGANIE JSON Z ŻĄDANIA ─────────────
def extract_json_from_request():
    """Obsługuje różne formaty danych z TradingView."""
    data = request.get_json(silent=True)
    if data:
        return data

    # Jeśli TradingView wysłał text/plain
    raw = request.data or b""
    text = raw.decode("utf-8", errors="ignore").strip()

    if not text:
        return None

    try:
        return json.loads(text)
    except Exception:
        # spróbuj znaleźć fragment JSON w tekście
        m = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass

    print("⚠️ Nie udało się sparsować danych:", text[:300])
    return None


# ───────────── FUNKCJA: OBSŁUGA WEBHOOKA ─────────────
def handle_webhook_data(data):
    print("📩 Odebrano webhook:", data)

    if not data:
        return jsonify({"status": "error", "message": "Invalid JSON"}), 400

    # Pobierz dane z TradingView
    symbol = data.get("symbol", "❓")
    price_raw = data.get("price", "❓")
    condition = (data.get("condition") or "").upper().strip()
    time_str = data.get("time", "")
    interval = data.get("interval", "")
    strategy = data.get("strategy", "")

    # Format czasu
    try:
        if "T" in time_str:
            t = datetime.strptime(time_str.replace("Z", ""), "%Y-%m-%dT%H:%M:%S")
            time_fmt = t.strftime("%Y-%m-%d %H:%M UTC")
        else:
            time_fmt = time_str
    except Exception:
        time_fmt = time_str or datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    # Format ceny
    try:
        price = float(str(price_raw).replace(",", "."))
        price_fmt = f"{price:,.2f}".replace(",", " ")
    except Exception:
        price_fmt = str(price_raw)

    # Emoji i kierunek
    if "BUY" in condition:
        emoji, cond_fmt = "🟢", "BUY"
    elif "SELL" in condition:
        emoji, cond_fmt = "🔴", "SELL"
    else:
        emoji, cond_fmt = "⚪", condition or "UNKNOWN"

    # Wiadomość do Telegrama
    message = (
        f"{emoji} <b>TradingView Alert</b>\n\n"
        f"📊 <b>Symbol:</b> {symbol}\n"
        f"💰 <b>Price:</b> {price_fmt}\n"
        f"📈 <b>Condition:</b> {emoji} {cond_fmt}\n"
        f"⏰ <b>Time:</b> {time_fmt}"
    )

    if interval:
        message += f"\n🕐 <b>Interval:</b> {interval}"
    if strategy:
        message += f"\n🧠 <b>Strategy:</b> {strategy}"

    send_to_telegram(message, symbol)
    return jsonify({"status": "ok"}), 200


# ───────────── ROUTES ─────────────
@app.route("/webhook", methods=["POST"])
def webhook():
    data = extract_json_from_request()
    if not data:
        return jsonify({"status": "error", "message": "Invalid JSON"}), 400
    return handle_webhook_data(data)


@app.route("/", methods=["GET", "POST", "HEAD"])
def root():
    if request.method == "GET":
        return "✅ TradingView Webhook → Telegram Bot działa!", 200
    elif request.method == "POST":
        data = extract_json_from_request()
        if not data:
            return jsonify({"status": "error", "message": "Invalid JSON"}), 400
        return handle_webhook_data(data)
    else:
        return ("", 200, {})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
