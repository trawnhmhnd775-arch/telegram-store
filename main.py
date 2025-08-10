import os
import json
from telebot import TeleBot, types
from dotenv import load_dotenv
from uuid import uuid4

# تحميل القيم من .env
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = TeleBot(TOKEN, parse_mode="HTML")
DATA_FILE = "data.json"

# تحميل أو إنشاء قاعدة البيانات
try:
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
except FileNotFoundError:
    data = {"users": {}, "welcome": "أهلاً بك في البوت!", "menus": []}

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def ensure_user(uid):
    uid = str(uid)
    if uid not in data["users"]:
        data["users"][uid] = {"balance": 0.0, "banned": False}
        save_data()
    return data["users"][uid]

def admin_only(func):
    def wrapper(message):
        if message.from_user.id != ADMIN_ID:
            bot.send_message(message.chat.id, "🚫 ليس لديك صلاحية.")
            return
        func(message)
    return wrapper

# ---------------- أوامر المستخدم ----------------

@bot.message_handler(commands=["start"])
def cmd_start(msg):
    user = ensure_user(msg.from_user.id)
    if user["banned"]:
        bot.send_message(msg.chat.id, "🚫 تم حظرك من البوت.")
        return
    markup = types.InlineKeyboardMarkup()
    for m in data["menus"]:
        markup.add(types.InlineKeyboardButton(m["title"], callback_data=f"main:{m['id']}"))
    markup.add(types.InlineKeyboardButton("💰 رصيدي", callback_data="balance"))
    bot.send_message(msg.chat.id, data["welcome"], reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "balance")
def cb_balance(call):
    user = ensure_user(call.from_user.id)
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, f"💵 رصيدك: {user['balance']}$")

@bot.callback_query_handler(func=lambda c: c.data.startswith("main:"))
def cb_main(call):
    menu_id = call.data.split(":")[1]
    menu = next((m for m in data["menus"] if m["id"] == menu_id), None)
    if not menu:
        bot.answer_callback_query(call.id, "❌ القائمة غير موجودة")
        return
    markup = types.InlineKeyboardMarkup()
    for s in menu.get("sub", []):
        markup.add(types.InlineKeyboardButton(s["title"], callback_data=f"sub:{menu_id}:{s['id']}"))
    bot.edit_message_text("اختر من القائمة:", call.message.chat.id, call.message.id, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("sub:"))
def cb_sub(call):
    _, menu_id, sub_id = call.data.split(":")
    menu = next((m for m in data["menus"] if m["id"] == menu_id), None)
    if not menu:
        return
    sub = next((s for s in menu.get("sub", []) if s["id"] == sub_id), None)
    if not sub:
        return
    markup = types.InlineKeyboardMarkup()
    for b in sub.get("buttons", []):
        markup.add(types.InlineKeyboardButton(b["text"], url=b["url"]))
    if sub.get("image"):
        bot.send_photo(call.message.chat.id, sub["image"], caption=sub["text"], reply_markup=markup)
    else:
        bot.send_message(call.message.chat.id, sub["text"], reply_markup=markup)

# ---------------- أوامر الأدمن ----------------

@bot.message_handler(commands=["set_welcome"])
@admin_only
def cmd_set_welcome(msg):
    bot.send_message(msg.chat.id, "أرسل رسالة الترحيب الجديدة:")
    bot.register_next_step_handler(msg, process_set_welcome)

def process_set_welcome(msg):
    data["welcome"] = msg.text
    save_data()
    bot.send_message(msg.chat.id, "✅ تم تعديل رسالة الترحيب.")

@bot.message_handler(commands=["add_balance"])
@admin_only
def cmd_add_balance(msg):
    bot.send_message(msg.chat.id, "أرسل: ID المستخدِم والمبلغ (مثال: 123456 5)")
    bot.register_next_step_handler(msg, process_add_balance)

def process_add_balance(msg):
    try:
        uid, amount = msg.text.split()
        amount = float(amount)
        ensure_user(uid)
        data["users"][uid]["balance"] += amount
        save_data()
        bot.send_message(msg.chat.id, "✅ تم إضافة الرصيد.")
        bot.send_message(int(uid), f"✅ تم إضافة {amount}$ لحسابك.")
    except:
        bot.send_message(msg.chat.id, "❌ خطأ في الإدخال.")

@bot.message_handler(commands=["remove_balance"])
@admin_only
def cmd_remove_balance(msg):
    bot.send_message(msg.chat.id, "أرسل: ID المستخدِم والمبلغ (مثال: 123456 5)")
    bot.register_next_step_handler(msg, process_remove_balance)

def process_remove_balance(msg):
    try:
        uid, amount = msg.text.split()
        amount = float(amount)
        ensure_user(uid)
        data["users"][uid]["balance"] -= amount
        save_data()
        bot.send_message(msg.chat.id, "✅ تم خصم الرصيد.")
        bot.send_message(int(uid), f"❌ تم خصم {amount}$ من حسابك.")
    except:
        bot.send_message(msg.chat.id, "❌ خطأ في الإدخال.")

@bot.message_handler(commands=["ban"])
@admin_only
def cmd_ban(msg):
    bot.send_message(msg.chat.id, "أرسل ID المستخدم للحظر:")
    bot.register_next_step_handler(msg, process_ban)

def process_ban(msg):
    uid = msg.text.strip()
    ensure_user(uid)
    data["users"][uid]["banned"] = True
    save_data()
    bot.send_message(msg.chat.id, "🚫 تم حظر المستخدم.")
    bot.send_message(int(uid), "🚫 تم حظرك من البوت.")

@bot.message_handler(commands=["unban"])
@admin_only
def cmd_unban(msg):
    bot.send_message(msg.chat.id, "أرسل ID المستخدم لفك الحظر:")
    bot.register_next_step_handler(msg, process_unban)

def process_unban(msg):
    uid = msg.text.strip()
    ensure_user(uid)
    data["users"][uid]["banned"] = False
    save_data()
    bot.send_message(msg.chat.id, "✅ تم فك الحظر عن المستخدم.")
    bot.send_message(int(uid), "✅ تم فك الحظر عنك.")

@bot.message_handler(commands=["add_main_menu"])
@admin_only
def cmd_add_main_menu(msg):
    bot.send_message(msg.chat.id, "أرسل اسم الزر الرئيسي:")
    bot.register_next_step_handler(msg, process_add_main_menu)

def process_add_main_menu(msg):
    new_menu = {"id": str(uuid4()), "title": msg.text, "sub": []}
    data["menus"].append(new_menu)
    save_data()
    bot.send_message(msg.chat.id, "✅ تم إضافة القائمة الرئيسية.")

@bot.message_handler(commands=["add_submenu"])
@admin_only
def cmd_add_submenu(msg):
    if not data["menus"]:
        bot.send_message(msg.chat.id, "❌ لا توجد قوائم رئيسية.")
        return
    text = "اختر ID القائمة الرئيسية:\n"
    for m in data["menus"]:
        text += f"{m['title']} - {m['id']}\n"
    bot.send_message(msg.chat.id, text)
    bot.register_next_step_handler(msg, process_select_main_for_sub)

def process_select_main_for_sub(msg):
    menu_id = msg.text.strip()
    menu = next((m for m in data["menus"] if m["id"] == menu_id), None)
    if not menu:
        bot.send_message(msg.chat.id, "❌ القائمة غير موجودة.")
        return
    bot.send_message(msg.chat.id, "أرسل اسم الزر الفرعي:")
    bot.register_next_step_handler(msg, lambda m: process_submenu_title(m, menu_id))

def process_submenu_title(msg, menu_id):
    title = msg.text
    bot.send_message(msg.chat.id, "أرسل نص المحتوى:")
    bot.register_next_step_handler(msg, lambda m: process_submenu_text(m, menu_id, title))

def process_submenu_text(msg, menu_id, title):
    text = msg.text
    bot.send_message(msg.chat.id, "أرسل صورة (أو اكتب 'لا' لتخطي):")
    bot.register_next_step_handler(msg, lambda m: process_submenu_image(m, menu_id, title, text))

def process_submenu_image(msg, menu_id, title, text):
    image = None
    if msg.content_type == "photo":
        image = msg.photo[-1].file_id
    elif msg.text.lower() != "لا":
        image = msg.text
    bot.send_message(msg.chat.id, "أرسل الأزرار السفلية (نص,رابط) لكل زر في سطر، أو اكتب 'لا':")
    bot.register_next_step_handler(msg, lambda m: process_submenu_buttons(m, menu_id, title, text, image))

def process_submenu_buttons(msg, menu_id, title, text, image):
    buttons = []
    if msg.text.lower() != "لا":
        lines = msg.text.split("\n")
        for line in lines:
            parts = line.split(",")
            if len(parts) == 2:
                buttons.append({"text": parts[0].strip(), "url": parts[1].strip()})
    menu = next((m for m in data["menus"] if m["id"] == menu_id), None)
    if not menu:
        return
    menu["sub"].append({
        "id": str(uuid4()),
        "title": title,
        "text": text,
        "image": image,
        "buttons": buttons
    })
    save_data()
    bot.send_message(msg.chat.id, "✅ تم إضافة القائمة الفرعية.")

@bot.message_handler(commands=["delete_menu"])
@admin_only
def cmd_delete_menu(msg):
    bot.send_message(msg.chat.id, "أرسل ID القائمة أو الفرعية للحذف:")
    bot.register_next_step_handler(msg, process_delete_menu)

def process_delete_menu(msg):
    menu_id = msg.text.strip()
    # حذف قائمة رئيسية
    for i, m in enumerate(data["menus"]):
        if m["id"] == menu_id:
            data["menus"].pop(i)
            save_data()
            bot.send_message(msg.chat.id, "✅ تم حذف القائمة الرئيسية.")
            return
        # حذف فرعية
        for j, s in enumerate(m.get("sub", [])):
            if s["id"] == menu_id:
                m["sub"].pop(j)
                save_data()
                bot.send_message(msg.chat.id, "✅ تم حذف القائمة الفرعية.")
                return
    bot.send_message(msg.chat.id, "❌ لم يتم العثور على ID.")

# ---------------- منع الرسائل النصية ----------------
@bot.message_handler(func=lambda m: True)
def block_text(msg):
    if msg.from_user.id == ADMIN_ID and msg.text.startswith("/"):
        return
    bot.send_message(msg.chat.id, "❌ استخدم الأزرار فقط.")

print("✅ Bot is running...")
bot.infinity_polling()
