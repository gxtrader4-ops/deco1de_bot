import os
import json
import re
import requests
from flask import Flask, request
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# কনফিগারেশন ও টোকেন
BOT_TOKEN = "8457189144:AAE7TmIXDqzcGxoLPKo4w6pA_Sj2NUJm3gs"
ADMIN_ID = 8419760844
ADMIN_USERNAME = "NIROB_GX_LEADER"

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
app = Flask(__name__)

# ডাটাবেজ ফাইল ম্যানেজমেন্ট
DB_FILE = "bot_database.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return {"users": [], "banned": []}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"users": [], "banned": []}

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# ইউজার রোল অনুযায়ী কিবোর্ড
def get_main_keyboard(user_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    if user_id == ADMIN_ID:
        markup.row(KeyboardButton("📊 Admin Stats"), KeyboardButton("🛠️ Admin Help"))
    markup.row(KeyboardButton("🔓 Obfuscate HTML"), KeyboardButton("🔗 Link to Real HTML"))
    markup.row(KeyboardButton("📄 HTML to Real HTML"))
    return markup

# শতভাগ নিখুঁত ক্লিন এইচটিএমএল এক্সট্রাকশন এবং এনকোডিং ফিক্স
def extract_pure_html(raw_content):
    if not raw_content:
        return ""

    # ক্ষতিকারক বা অবফাসকেটেড স্ক্রিপ্ট ট্যাগ রিমুভ
    clean_code = re.sub(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>', '', raw_content, flags=re.IGNORECASE)
    
    # টাইটেলের কোডিং বা ভাঙা ফন্ট ফিক্স
    def clean_title(match):
        title_text = match.group(1)
        cleaned_text = re.sub(r'[^\x00-\x7F]+', '', title_text).strip()
        if not cleaned_text:
            cleaned_text = "GX Cleaned Live Source"
        return f"<title>{cleaned_text}</title>"
    
    clean_code = re.sub(r'<title>(.*?)</title>', clean_title, clean_code, flags=re.IGNORECASE | re.DOTALL)

    # ডকটাইপ এবং স্ট্রাকচার চেক
    if not re.search(r'<!DOCTYPE\s+html', clean_code, re.IGNORECASE):
        clean_code = f"<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n    <meta charset=\"UTF-8\">\n    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n    <title>GX Cleaned Real Source</title>\n</head>\n<body>\n{clean_code}\n</body>\n</html>"

    return clean_code.strip()

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    db = load_db()
    
    if user_id in db["banned"] and user_id != ADMIN_ID:
        bot.reply_to(message, "❌ দুঃখিত, এই বট ব্যবহারের জন্য আপনাকে ব্যান করা হয়েছে!")
        return

    if user_id not in db["users"]:
        db["users"].append(user_id)
        save_db(db)

    welcome_msg = (
        f"👋 স্বাগতম GX HTML Decoder বোটে!\n\n"
        f"ডেভেলপার: @{ADMIN_USERNAME}\n"
        f"আপনার সিকিউরড বা অবফাসকেটেড ফাইল বা লিংক থেকে ১০০% আসল ও ক্লিন কোড পেতে ফাইল বা লিংক পাঠান।"
    )
    
    bot.send_message(message.chat.id, welcome_msg, reply_markup=get_main_keyboard(user_id))

@bot.message_handler(func=lambda message: True, content_types=['text', 'document'])
def handle_incoming_message(message):
    user_id = message.from_user.id
    db = load_db()
    
    if user_id in db["banned"] and user_id != ADMIN_ID:
        return

    if message.text:
        text = message.text.strip()
        
        if text == "📊 Admin Stats" and user_id == ADMIN_ID:
            total_users = len(db["users"])
            total_banned = len(db["banned"])
            bot.reply_to(message, f"📊 **Bot Statistics:**\n\n👤 Total Users: {total_users}\n🚫 Banned Users: {total_banned}")
            return
            
        elif text == "🛠️ Admin Help" and user_id == ADMIN_ID:
            help_text = (
                "🛠️ **Admin Commands Help:**\n\n"
                "/ban [user_id] - ইউজার ব্যান করতে\n"
                "/unban [user_id] - ইউজার আনব্যান করতে"
            )
            bot.reply_to(message, help_text)
            return
            
        elif text in ["🔓 Obfuscate HTML", "🔗 Link to Real HTML", "📄 HTML to Real HTML"]:
            bot.reply_to(message, "📥 অনুগ্রহ করে আপনার সিকিউরড ফাইলটি ডকুমেন্ট হিসেবে পাঠান অথবা সরাসরি লিংক/কোড পেস্ট করুন।")
            return

        if text.startswith('/ban ') and user_id == ADMIN_ID:
            try:
                b_id = int(text.replace('/ban ', '').strip())
                if b_id not in db["banned"]:
                    db["banned"].append(b_id)
                    save_db(db)
                    bot.reply_to(message, f"✅ User {b_id} successfully banned.")
            except ValueError:
                bot.reply_to(message, "❌ সঠিক ইউজার আইডি দিন।")
            return
            
        elif text.startswith('/unban ') and user_id == ADMIN_ID:
            try:
                u_id = int(text.replace('/unban ', '').strip())
                if u_id in db["banned"]:
                    db["banned"].remove(u_id)
                    save_db(db)
                    bot.reply_to(message, f"✅ User {u_id} successfully unbanned.")
            except ValueError:
                bot.reply_to(message, "❌ সঠিক ইউজার আইডি দিন।")
            return

    raw_html = ""
    file_name = "real_clean_source.html"

    # ফাইল আপলোড হলে সঠিক এনকোডিংয়ে রিড করা
    if message.document:
        doc = message.document
        if not doc.file_name.endswith(('.html', '.htm', '.txt')):
            bot.reply_to(message, "❌ অনুগ্রহ করে শুধুমাত্র বৈধ .html ফাইল আপলোড করুন!")
            return
        
        file_name = f"real_clean_{doc.file_name}"
        file_info = bot.get_file(doc.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # ইউটিএফ-৮ এবং অন্যান্য এনকোডিং ট্রাই করা যাতে ভেঙে না যায়
        try:
            raw_html = downloaded_file.decode('utf-8')
        except UnicodeDecodeError:
            try:
                raw_html = downloaded_file.decode('latin1')
            except:
                raw_html = downloaded_file.decode('utf-8', errors='ignore')

    elif message.text:
        text = message.text.strip()
        if text.startswith("http://") or text.startswith("https://"):
            bot.reply_to(message, "⏳ লিংক থেকে রিয়েল সোর্স কোড ফেচ করা হচ্ছে...")
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
                response = requests.get(text, headers=headers, timeout=15)
                response.encoding = 'utf-8' # রেসপন্স এনকোডিং ফিক্সড
                if response.status_code == 200:
                    raw_html = response.text
                    file_name = "real_live_source.html"
                else:
                    bot.reply_to(message, f"❌ সার্ভার থেকে রেসপন্স পাওয়া যায়নি। Status Code: {response.status_code}")
                    return
            except Exception as e:
                bot.reply_to(message, f"❌ লিংক ফেচ করতে সমস্যা হয়েছে: {str(e)}")
                return
        else:
            raw_html = text

    if raw_html:
        bot.reply_to(message, "⏳ কোড পার্স করে একদম ক্লিন ও রিডেবল আসল HTML তৈরি করা হচ্ছে...")

        final_html = extract_pure_html(raw_html)

        output_path = f"/tmp/{file_name}"
        # ফাইল লেখার সময় utf-8 এনকোডিং নিশ্চিত করা হলো যাতে ক্যারেক্টার নষ্ট না হয়
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(final_html)

        with open(output_path, "rb") as f:
            bot.send_document(
                message.chat.id,
                f,
                caption=f"✅ সফলভাবে সমস্ত ক্রিপ্টিক কোড ও জঞ্জাল রিমুভ করে আসল ক্লিন HTML দেওয়া হলো!\nDeveloper: @{ADMIN_USERNAME}"
            )
        
        if os.path.exists(output_path):
            os.remove(output_path)

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "OK", 200
    return "Invalid Content-Type", 403

@app.route("/")
def index():
    render_url = os.environ.get("RENDER_EXTERNAL_URL")
    if render_url:
        webhook_url = f"{render_url}/{BOT_TOKEN}"
        bot.remove_webhook()
        bot.set_webhook(url=webhook_url)
    return f"Nirob GX Decoder Bot active! Owner: @{ADMIN_USERNAME}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
