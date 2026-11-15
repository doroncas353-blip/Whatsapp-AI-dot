import os
from flask import Flask, request
import requests
app = Flask(__name__)
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "rany123")
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
@app.route("/", methods=["GET"])
def home():
    return "WhatsApp AI Bot is running!", 200
@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    else:
        return "Verification failed", 403
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    try:
        if data and "entry" in data:
            for entry in data["entry"]:
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    messages = value.get("messages", [])
                    for msg in messages:
                        if msg.get("type") == "text":
                            from_number = msg["from"]
                            text = msg["text"]["body"]
                            ai_reply = get_ai_reply(text)
                            send_whatsapp_message(from_number, ai_reply)
    except Exception as e:
        print(f"Error: {e}")
    return "OK", 200
def get_ai_reply(user_text):
    if not GROQ_API_KEY:
        return "היי! הבוט עובד"
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        payload = {"model": "llama-3.1-8b-instant","messages": [{"role": "system", "content": "אתה עוזר AI ידידותי בעברית."},{"role": "user", "content": user_text}],"max_tokens": 500}
        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        result = resp.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        return "סליחה, תקלה ב-AI"
def send_whatsapp_message(to, text):
    if not WHATSAPP_TOKEN or not PHONE_NUMBER_ID:
        return
    url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
    payload = {"messaging_product": "whatsapp","to": to,"type": "text","text": {"body": text}}
    requests.post(url, json=payload, headers=headers)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
