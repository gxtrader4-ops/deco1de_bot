import os
import json
import re
import requests
from flask import Flask, request
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# কনফিগারেশন ও নতুন টোকেন
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
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return {"users": [], "banned": []}

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ইউজার রোল অনুযায়ী গতিশীল কিবোর্ড লেআউট
def get_main_keyboard(user_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    # শুধুমাত্র অ্যাডমিন হলে অ্যাডমিন অপশন দেখাবে
    if user_id == ADMIN_ID:
        markup.row(KeyboardButton("📊 Admin Stats"), KeyboardButton("🛠️ Admin Help"))
    
    markup.row(KeyboardButton("🔓 Obfuscate HTML"), KeyboardButton("🔗 Link to Real HTML"))
    markup.row(KeyboardButton("📄 HTML to Real HTML"))
    return markup

# ফাইল বা টেক্সট থেকে আসল এইচটিএমএল এক্সট্র্যাক্ট করার লজিক
def extract_pure_html(raw_content):
    if not raw_content:
        return ""

    # ১. স্ক্রিপ্ট ট্যাগ ও ক্ষতিকারক কোড রিমুভ (অপ্রয়োজনীয় অবফাসকেটেড স্ক্রিপ্ট ডিলিট)
    clean_code = re.sub(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>', '', raw_content, flags=re.IGNORECASE)
    
    # ২. টাইটেল বা কোডের ভেতরের অনাকাঙ্ক্ষিত নন-এএসসিআইআই বা ভাঙা ক্যারেক্টার ফিল্টার
    def clean_title(match):
        title_text = match.group(1)
        cleaned_text = re.sub(r'[^\x00-\x7F]+', '', title_text).strip()
        if not cleaned_text:
            cleaned_text = "Cleaned HTML Source"
        return f"<title>{cleaned_text}</title>"
    
    clean_code = re.sub(r'<title>(.*?)</title>', clean_title, clean_code, flags=re.IGNORECASE | re.DOTALL)

    # ৩. ডকটাইপ এবং এইচটিএমএল স্ট্রাকচার নিশ্চিত করা
    if not re.search(r'<!DOCTYPE\s+html', clean_code, re.IGNORECASE):
        clean_code = f"<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n    <meta charset=\"UTF-8\">\n    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n    <title>Cleaned Real HTML</title>\n</head>\n<body>\n{clean_code}\n</body>\n</html>"

    return clean_code.strip()

# /start কমান্ড হ্যান্ডলার
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
        f"আপনার সিকিউরড বা এনক্রিপ্টেড HTML ফাইল বা লিংক থেকে ১০০% আসল ও ক্লিন কোড বের করতে ফাইল বা লিংক পাঠাতেন।"
    )
    
    bot.send_message(message.chat.id, welcome_msg, reply_markup=get_main_keyboard(user_id))

# বার্তা এবং ফাইল প্রসেসিং হ্যান্ডলার
@bot.message_handler(func=lambda message: True, content_types=['text', 'document'])
def handle_incoming_message(message):
    user_id = message.from_user.id
    db = load_db()
    
    if user_id in db["banned"] and user_id != ADMIN_ID:
        return

    if message.text:
        text = message.text.strip()
        
        # অ্যাডমিন কমান্ড ও অ্যাকশন
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

    # ১. ডকুমেন্ট আপলোড হলে
    if message.document:
        doc = message.document
        if not doc.file_name.endswith(('.html', '.htm', '.txt')):
            bot.reply_to(message, "❌ অনুগ্রহ করে শুধুমাত্র বৈধ .html ফাইল আপলোড করুন!")
            return
        
        file_name = f"real_clean_{doc.file_name}"
        file_info = bot.get_file(doc.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        raw_html = downloaded_file.decode('utf-8', errors='ignore')

    # ২. ডিরেক্ট লিংক বা কোড পেস্ট করলে
    elif message.text:
        text = message.text.strip()
        if text.startswith("http://") or text.startswith("https://"):
            bot.reply_to(message, "⏳ লিংক থেকে অরিজিনাল পেজের রিয়েল সোর্স কোড সংগ্রহ করা হচ্ছে...")
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
                response = requests.get(text, headers=headers, timeout=15)
                if response.status_code == 200:
                    raw_html = response.text
                    file_name = "real_live_source.html"
                else:
                    bot.reply_to(message, f"❌ লিংক কাজ করছে না! Status Code: {response.status_code}")
                    return
            except Exception as e:
                bot.reply_to(message, f"❌ লিংক ফেচ করতে সমস্যা হয়েছে: {str(e)}")
                return
        else:
            raw_html = text

    # আসল এবং ক্লিন এইচটিএমএল আউটপুট তৈরি
    if raw_html:
        bot.reply_to(message, "⏳ সমস্ত অনাকাঙ্ক্ষিত কোড ফিল্টার করে আসল HTML ফাইল এক্সট্র্যাক্ট করা হচ্ছে...")

        final_html = extract_pure_html(raw_html)

        output_path = f"/tmp/{file_name}"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(final_html)

        with open(output_path, "rb") as f:
            bot.send_document(
                message.chat.id,
                f,
                caption=f"✅ সফলভাবে সিকিউরিটি রিমুভ করে অরিজিনাল ক্লিন HTML দেওয়া হলো!\nDeveloper: @{ADMIN_USERNAME}"
            )
        
        if os.path.exists(output_path):
            os.remove(output_path)

# ফ্লাস্ক ওয়েবহুক এবং অটো-কানেক্ট
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
