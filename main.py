import telebot
from telebot import types
import json
import os
from dotenv import load_dotenv

# تحميل المتغيرات من .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

DATA_FILE = "data.json"

# تحميل البيانات أو إنشاء ملف جديد
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"users": {}, "welcome": "أهلاً بك في البوت!", "menus": []}, f, ensure_ascii=False, indent=2)

def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# استقبال /start
@bot.message_handler(commands=['start'])
def start(message):
    data = load_data()
    user_id = str(message.from_user.id)

    # إذا المستخدم جديد
    if user_id not in data["users"]:
        data["users"][user_id] = {"balance": 0, "banned": False}
        save_data(data)

    if data["users"][user_id]["banned"]:
        bot.reply_to(message, "🚫 أنت محظور من استخدام هذا البوت.")
        return

    show_main_menu(message.chat.id)

def show_main_menu(chat_id):
    data = load_data()
    markup = types.InlineKeyboardMarkup()
    for idx, menu in enumerate(data["menus"]):
        markup.add(types.InlineKeyboardButton(menu["title"], callback_data=f"main_{idx}"))
    bot.send_message(chat_id, data["welcome"], reply_markup=markup)

def show_sub_menu(chat_id, menu_index):
    data = load_data()
    menu = data["menus"][menu_index]
    markup = types.InlineKeyboardMarkup()
    for idx, submenu in enumerate(menu["submenus"]):
        markup.add(types.InlineKeyboardButton(submenu["title"], callback_data=f"sub_{menu_index}_{idx}"))
    markup.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="back_main"))
    bot.send_message(chat_id, f"📂 {menu['title']}", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    data = load_data()
    if call.data.startswith("main_"):
        idx = int(call.data.split("_")[1])
        show_sub_menu(call.message.chat.id, idx)

    elif call.data.startswith("sub_"):
        menu_idx, sub_idx = map(int, call.data.split("_")[1:])
        submenu = data["menus"][menu_idx]["submenus"][sub_idx]
        markup = types.InlineKeyboardMarkup()
        for btn in submenu.get("buttons", []):
            markup.add(types.InlineKeyboardButton(btn["text"], url=btn["url"]))
        markup.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data=f"main_{menu_idx}"))

        if submenu.get("image"):
            bot.send_photo(call.message.chat.id, submenu["image"], caption=submenu["text"], reply_markup=markup)
        else:
            bot.send_message(call.message.chat.id, submenu["text"], reply_markup=markup)

    elif call.data == "back_main":
        show_main_menu(call.message.chat.id)

# أوامر الأدمن
@bot.message_handler(commands=['set_welcome'])
def set_welcome(message):
    if message.from_user.id != ADMIN_ID:
        return
    msg = bot.reply_to(message, "أرسل رسالة الترحيب الجديدة:")
    bot.register_next_step_handler(msg, save_welcome)

def save_welcome(message):
    data = load_data()
    data["welcome"] = message.text
    save_data(data)
    bot.reply_to(message, "✅ تم تحديث رسالة الترحيب.")

@bot.message_handler(commands=['add_balance'])
def add_balance(message):
    if message.from_user.id != ADMIN_ID:
        return
    msg = bot.reply_to(message, "أرسل ID المستخدم والمبلغ هكذا: 123456 10")
    bot.register_next_step_handler(msg, process_add_balance)

def process_add_balance(message):
    try:
        user_id, amount = message.text.split()
        data = load_data()
        if user_id not in data["users"]:
            bot.reply_to(message, "❌ المستخدم غير موجود.")
            return
        data["users"][user_id]["balance"] += float(amount)
        save_data(data)
        bot.send_message(user_id, f"💰 تم إضافة {amount}$ إلى حسابك.")
        bot.reply_to(message, "✅ تم إضافة الرصيد.")
    except:
        bot.reply_to(message, "❌ صيغة غير صحيحة.")

@bot.message_handler(commands=['remove_balance'])
def remove_balance(message):
    if message.from_user.id != ADMIN_ID:
        return
    msg = bot.reply_to(message, "أرسل ID المستخدم والمبلغ هكذا: 123456 5")
    bot.register_next_step_handler(msg, process_remove_balance)

def process_remove_balance(message):
    try:
        user_id, amount = message.text.split()
        data = load_data()
        if user_id not in data["users"]:
            bot.reply_to(message, "❌ المستخدم غير موجود.")
            return
        data["users"][user_id]["balance"] -= float(amount)
        save_data(data)
        bot.send_message(user_id, f"💸 تم خصم {amount}$ من حسابك.")
        bot.reply_to(message, "✅ تم خصم الرصيد.")
    except:
        bot.reply_to(message, "❌ صيغة غير صحيحة.")

@bot.message_handler(commands=['ban'])
def ban_user(message):
    if message.from_user.id != ADMIN_ID:
        return
    msg = bot.reply_to(message, "أرسل ID المستخدم لحظره:")
    bot.register_next_step_handler(msg, process_ban)

def process_ban(message):
    user_id = message.text.strip()
    data = load_data()
    if user_id in data["users"]:
        data["users"][user_id]["banned"] = True
        save_data(data)
        bot.reply_to(message, "✅ تم حظر المستخدم.")
    else:
        bot.reply_to(message, "❌ المستخدم غير موجود.")

@bot.message_handler(commands=['unban'])
def unban_user(message):
    if message.from_user.id != ADMIN_ID:
        return
    msg = bot.reply_to(message, "أرسل ID المستخدم لفك الحظر:")
    bot.register_next_step_handler(msg, process_unban)

def process_unban(message):
    user_id = message.text.strip()
    data = load_data()
    if user_id in data["users"]:
        data["users"][user_id]["banned"] = False
        save_data(data)
        bot.reply_to(message, "✅ تم فك الحظر.")
    else:
        bot.reply_to(message, "❌ المستخدم غير موجود.")

# إدارة القوائم
@bot.message_handler(commands=['add_main_menu'])
def add_main_menu(message):
    if message.from_user.id != ADMIN_ID:
        return
    msg = bot.reply_to(message, "أرسل اسم القائمة الرئيسية:")
    bot.register_next_step_handler(msg, save_main_menu)

def save_main_menu(message):
    data = load_data()
    data["menus"].append({"title": message.text, "submenus": []})
    save_data(data)
    bot.reply_to(message, "✅ تم إضافة القائمة الرئيسية.")

@bot.message_handler(commands=['add_submenu'])
def add_submenu(message):
    if message.from_user.id != ADMIN_ID:
        return
    msg = bot.reply_to(message, "أرسل رقم القائمة الرئيسية:")
    bot.register_next_step_handler(msg, process_add_submenu_step1)

def process_add_submenu_step1(message):
    menu_index = int(message.text)
    msg = bot.reply_to(message, "أرسل اسم الزر الفرعي:")
    bot.register_next_step_handler(msg, process_add_submenu_step2, menu_index)

def process_add_submenu_step2(message, menu_index):
    title = message.text
    msg = bot.reply_to(message, "أرسل النص:")
    bot.register_next_step_handler(msg, process_add_submenu_step3, menu_index, title)

def process_add_submenu_step3(message, menu_index, title):
    text = message.text
    msg = bot.reply_to(message, "أرسل رابط الصورة أو اكتب 'لا' إذا لا يوجد:")
    bot.register_next_step_handler(msg, process_add_submenu_step4, menu_index, title, text)

def process_add_submenu_step4(message, menu_index, title, text):
    image = None if message.text.lower() == "لا" else message.text
    msg = bot.reply_to(message, "أرسل الأزرار بصيغة نص|رابط، سطر لكل زر، أو اكتب 'لا':")
    bot.register_next_step_handler(msg, process_add_submenu_final, menu_index, title, text, image)

def process_add_submenu_final(message, menu_index, title, text, image):
    buttons = []
    if message.text.lower() != "لا":
        for line in message.text.split("\n"):
            parts = line.split("|")
            if len(parts) == 2:
                buttons.append({"text": parts[0], "url": parts[1]})

    data = load_data()
    data["menus"][menu_index]["submenus"].append({
        "title": title,
        "text": text,
        "image": image,
        "buttons": buttons
    })
    save_data(data)
    bot.reply_to(message, "✅ تم إضافة القائمة الفرعية.")

bot.infinity_polling()            return
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
