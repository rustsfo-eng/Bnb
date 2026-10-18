import asyncio
import os
import time
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

# التوكن الخاص بك
TOKEN = "8930862505:AAH5MntPMMGxy_oIKtAMuJ1Nv_LHYtUgxKQ"

# ⚙️ مسارات ملفات الصوت الكاملة
VOICE_1_PATH = "/storage/emulated/0/Download/New tele/MY BOT/voice2.ogg"
VOICE_2_PATH = "/storage/emulated/0/Download/New tele/MY BOT/voice1.ogg"

# نصوص الرسائل والروابط
TEXT_MSG_1 = "تريد تشوف رماناتي ولخوخه مالتي والجنطه شكلك تسوي واذا عاندتني انطيك بلوك"
LINK_MSG = "https://mybirds.org/a/21wmagsv افتح الرابط وحملة و سوي حساب حتى ادزلك الايدي مااكدر بعد شتهيت"
FINAL_MSG = "حمله وراسلني هنا 37454612 انتضركك"

# قاموس لحفظ خطوة كل مستخدم
user_steps = {}
# قاموس لحفظ وقت آخر رد أرسله البوت للمستخدم لمنع القفز السريع بين الخطوات
user_last_reply_time = {}
# مجموعة لحظر المعالجة المتزامنة في نفس الأجزاء من الثانية
processing_users = set()

# ⏳ مهلة الأمان بالثواني (مثلاً 5 ثوانٍ): أي رسالة يرسلها الشخص خلال 5 ثوانٍ من رد البوت، لن تغير الخطوة وستبقى ثابتة
COOLDOWN_TIME = 5 

async def handle_business_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.business_message:
        business_message = update.business_message
    elif update.edited_business_message:
        business_message = update.edited_business_message
    else:
        return

    # تجاهل الرسائل الصادرة منك
    if business_message.from_user and business_message.from_user.id == context.bot.id:
        return

    chat_id = business_message.chat_id
    business_conn_id = business_message.business_connection_id

    # حماية من التداخل الفوري للرسائل المتزامنة
    if chat_id in processing_users:
        return

    current_step = user_steps.get(chat_id, 1)

    # إذا كملت السلسلة قفل نهائي
    if current_step == 6:
        return

    # 🔥 الحل السحري لثبات الرد: التحقق من مهلة الأمان
    current_time = time.time()
    last_reply = user_last_reply_time.get(chat_id, 0)
    
    # إذا أرسل الشخص رسالة عشوائية متتالية بسرعة قبل مرور المهرة، البوت يتجاهلها تماماً ويبقى ثابتاً
    if current_time - last_reply < COOLDOWN_TIME:
        print(f"⏳ تم تجاهل رسالة متتالية من {chat_id} لضمان ثبات الخطوة {current_step}")
        return

    processing_users.add(chat_id)

    try:
        # 🎤 الخطوة 1: الفويس الأول فقط
        if current_step == 1:
            await context.bot.send_chat_action(chat_id=chat_id, action="record_voice", business_connection_id=business_conn_id)
            await asyncio.sleep(10)  # وقت الانتظار قبل الإرسال
            if os.path.exists(VOICE_1_PATH):
                with open(VOICE_1_PATH, "rb") as f:
                    await context.bot.send_voice(chat_id=chat_id, voice=f, business_connection_id=business_conn_id)
                print(f"✅ الخطوة 1: تم إرسال الفويس الأول إلى {chat_id}")
                user_steps[chat_id] = 2  # تجهيز الخطوة التالية
                user_last_reply_time[chat_id] = time.time()  # تسجيل وقت الرد
            else:
                print(f"❌ خطأ: الفويس الأول غير موجود في {VOICE_1_PATH}")

        # ✍️ الخطوة 2: النص الأول فقط
        elif current_step == 2:
            await context.bot.send_chat_action(chat_id=chat_id, action="typing", business_connection_id=business_conn_id)
            await asyncio.sleep(15)
            await context.bot.send_message(chat_id=chat_id, text=TEXT_MSG_1, business_connection_id=business_conn_id)
            print(f"✅ الخطوة 2: تم إرسال النص الأول إلى {chat_id}")
            user_steps[chat_id] = 3
            user_last_reply_time[chat_id] = time.time()

        # 🎤 الخطوة 3: الفويس الثاني فقط
        elif current_step == 3:
            await context.bot.send_chat_action(chat_id=chat_id, action="record_voice", business_connection_id=business_conn_id)
            await asyncio.sleep(15)
            if os.path.exists(VOICE_2_PATH):
                with open(VOICE_2_PATH, "rb") as f:
                    await context.bot.send_voice(chat_id=chat_id, voice=f, business_connection_id=business_conn_id)
                print(f"✅ الخطوة 3: تم إرسال الفويس الثاني إلى {chat_id}")
                user_steps[chat_id] = 4
                user_last_reply_time[chat_id] = time.time()
            else:
                print(f"❌ خطأ: الفويس الثاني غير موجود في {VOICE_2_PATH}")

        # 🔗 الخطوة 4: الرابط فقط
        elif current_step == 4:
            await context.bot.send_chat_action(chat_id=chat_id, action="typing", business_connection_id=business_conn_id)
            await asyncio.sleep(15)
            await context.bot.send_message(chat_id=chat_id, text=LINK_MSG, business_connection_id=business_conn_id)
            print(f"✅ الخطوة 4: تم إرسال الرابط إلى {chat_id}")
            user_steps[chat_id] = 5
            user_last_reply_time[chat_id] = time.time()

        # 🔒 الخطوة 5: الرسالة النهائية
        elif current_step == 5:
            await context.bot.send_chat_action(chat_id=chat_id, action="typing", business_connection_id=business_conn_id)
            await asyncio.sleep(8)
            await context.bot.send_message(chat_id=chat_id, text=FINAL_MSG, business_connection_id=business_conn_id)
            print(f"🔒 الخطوة 5: تم إرسال النص النهائي وقفل المحادثة لـ {chat_id}")
            user_steps[chat_id] = 6
            user_last_reply_time[chat_id] = time.time()

    except Exception as e:
        print(f"⚠️ حدث خطأ في النظام: {e}")
    finally:
        if chat_id in processing_users:
            processing_users.remove(chat_id)

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_business_message))
    print("🚀 تم تفعيل قفل الوقت الذكي! الردود ثابتة ومستحيل تتداخل الحين...")
    application.run_polling()

if __name__ == "__main__":
    main()