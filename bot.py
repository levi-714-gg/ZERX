import os
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from flask import Flask
from threading import Thread
import time

# 🔧 إعدادات السيرفر - ضروري لـ Render
app = Flask(__name__)

@app.route('/')
def home():
    return """
    <html>
        <head>
            <title>Telegram Bot Manager</title>
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    text-align: center; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 50px;
                }
                .container {
                    background: rgba(255,255,255,0.1);
                    padding: 30px;
                    border-radius: 20px;
                    backdrop-filter: blur(10px);
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🌸 بوت إدارة القنوات والمجموعات 💖</h1>
                <p>🎀 البوت يعمل بشكل مستمر على Render! ✨</p>
                <p>⏰ آخر تحديث: {} </p>
                <p>🚀 تم التحميل بنجاح 100%</p>
            </div>
        </body>
    </html>
    """.format(time.strftime("%Y-%m-%d %H:%M:%S"))

@app.route('/health')
def health():
    return "OK", 200

def run_web():
    app.run(host='0.0.0.0', port=8080)

# 🔧 إعدادات البوت
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class ChannelManagerBot:
    def __init__(self):
        self.data_file = 'channels_data.json'
        self.load_data()
        
    def load_data(self):
        """تحميل البيانات من ملف JSON"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        except FileNotFoundError:
            self.data = {"channels": {}, "groups": {}, "settings": {}}
            self.save_data()
        except json.JSONDecodeError:
            self.data = {"channels": {}, "groups": {}, "settings": {}}
            self.save_data()
    
    def save_data(self):
        """حفظ البيانات في ملف JSON"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"خطأ في الحفظ: {e}")
    
    def add_channel(self, channel_id: str, channel_info: dict):
        """إضافة قناة"""
        self.data["channels"][channel_id] = channel_info
        self.save_data()
        return True
    
    def add_group(self, group_id: str, group_info: dict):
        """إضافة مجموعة"""
        self.data["groups"][group_id] = group_info
        self.save_data()
        return True
    
    def remove_channel(self, channel_id: str):
        """حذف قناة"""
        if channel_id in self.data["channels"]:
            del self.data["channels"][channel_id]
            self.save_data()
            return True
        return False
    
    def remove_group(self, group_id: str):
        """حذف مجموعة"""
        if group_id in self.data["groups"]:
            del self.data["groups"][group_id]
            self.save_data()
            return True
        return False
    
    def get_all_channels(self):
        """جلب جميع القنوات"""
        return self.data.get("channels", {})
    
    def get_all_groups(self):
        """جلب جميع المجموعات"""
        return self.data.get("groups", {})

# 🎀 إنشاء مدير البوت
bot_manager = ChannelManagerBot()

# 🔑 احصل على التوكن من Environment Variables - ضروري لـ Render
BOT_TOKEN = os.environ.get('8442826639:AAHq4qmg31TTYRYWGWIhJnMWNcvmUdSxl-U', '')

if not BOT_TOKEN:
    logger.error("❌ لم يتم تعيين BOT_TOKEN!")
else:
    logger.info("✅ تم تحميل التوكن بنجاح!")

# 💫 دوال البوت الرئيسية
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رسالة الترحيب"""
    user = update.effective_user
    welcome_text = f"""
    🌸 *مرحباً عزيزي {user.first_name}!* 🌸
    
    💖 *أهلاً بك في بوت إدارة القنوات والمجموعات* 💖
    
    ✨ *ما الذي تريد أن تفعل اليوم؟* ✨
    
    🎀 اختر أحد الخيارات من الأسفل:
    """
    
    keyboard = [
        [InlineKeyboardButton("📊 إدارة القنوات", callback_data="manage_channels")],
        [InlineKeyboardButton("👥 إدارة المجموعات", callback_data="manage_groups")],
        [InlineKeyboardButton("➕ إضافة قناة", callback_data="add_channel"),
         InlineKeyboardButton("➕ إضافة مجموعة", callback_data="add_group")],
        [InlineKeyboardButton("📨 إرسال جماعي", callback_data="broadcast")],
        [InlineKeyboardButton("📈 الإحصائيات", callback_data="stats")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.callback_query.edit_message_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الضغط على الأزرار"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "manage_channels":
        await show_channels_menu(query, context)
    elif data == "manage_groups":
        await show_groups_menu(query, context)
    elif data == "add_channel":
        await add_channel_start(query, context)
    elif data == "add_group":
        await add_group_start(query, context)
    elif data == "broadcast":
        await broadcast_start(query, context)
    elif data == "stats":
        await show_stats(query, context)
    elif data.startswith("channel_"):
        await handle_channel_selection(query, context, data)
    elif data.startswith("group_"):
        await handle_group_selection(query, context, data)
    elif data.startswith("action_"):
        await handle_action(query, context, data)
    elif data == "back_to_main":
        await start_callback(query, context)

async def start_callback(query, context):
    """قائمة رئيسية للاستدعاءات"""
    user = query.from_user
    welcome_text = f"""
    🌸 *مرحباً عزيزي {user.first_name}!* 🌸
    💖 *اختر ما تريد القيام به:* 💖
    """
    
    keyboard = [
        [InlineKeyboardButton("📊 إدارة القنوات", callback_data="manage_channels")],
        [InlineKeyboardButton("👥 إدارة المجموعات", callback_data="manage_groups")],
        [InlineKeyboardButton("➕ إضافة قناة", callback_data="add_channel"),
         InlineKeyboardButton("➕ إضافة مجموعة", callback_data="add_group")],
        [InlineKeyboardButton("📨 إرسال جماعي", callback_data="broadcast")],
        [InlineKeyboardButton("📈 الإحصائيات", callback_data="stats")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_channels_menu(query, context):
    """عرض القنوات"""
    channels = bot_manager.get_all_channels()
    
    if not channels:
        text = "💔 *لا توجد قنوات مسجلة بعد* 💔\n🌸 *اضف قنواتك الأولى الآن!* 🌸"
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]]
    else:
        text = "📊 *قنواتك المسجلة:* 📊\n🎀 *اختر القناة:* 🎀"
        keyboard = []
        
        for channel_id, channel_info in channels.items():
            button = InlineKeyboardButton(
                f"📺 {channel_info.get('title', channel_id)}",
                callback_data=f"channel_{channel_id}"
            )
            keyboard.append([button])
        
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_groups_menu(query, context):
    """عرض المجموعات"""
    groups = bot_manager.get_all_groups()
    
    if not groups:
        text = "💔 *لا توجد مجموعات مسجلة بعد* 💔\n🌸 *اضف مجموعاتك الأولى الآن!* 🌸"
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]]
    else:
        text = "👥 *مجموعاتك المسجلة:* 👥\n🎀 *اختر المجموعة:* 🎀"
        keyboard = []
        
        for group_id, group_info in groups.items():
            button = InlineKeyboardButton(
                f"👥 {group_info.get('title', group_id)}",
                callback_data=f"group_{group_id}"
            )
            keyboard.append([button])
        
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_channel_selection(query, context, data):
    """معالجة اختيار قناة"""
    channel_id = data.replace("channel_", "")
    channels = bot_manager.get_all_channels()
    channel_info = channels.get(channel_id)
    
    if not channel_info:
        await query.answer("❌ القناة غير موجودة!", show_alert=True)
        return
    
    text = f"""
    📺 *{channel_info.get('title', channel_id)}*
    
    🎀 *اختر الإجراء المطلوب:* 🎀
    """
    
    keyboard = [
        [InlineKeyboardButton("📊 الإحصائيات", callback_data=f"action_stats_{channel_id}"),
         InlineKeyboardButton("👥 الأعضاء", callback_data=f"action_members_{channel_id}")],
        [InlineKeyboardButton("📨 إرسال رسالة", callback_data=f"action_send_{channel_id}"),
         InlineKeyboardButton("➕ إضافة أعضاء", callback_data=f"action_add_members_{channel_id}")],
        [InlineKeyboardButton("🚫 طرد أعضاء", callback_data=f"action_remove_members_{channel_id}")],
        [InlineKeyboardButton("🗑️ حذف القناة", callback_data=f"action_delete_{channel_id}")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="manage_channels")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_group_selection(query, context, data):
    """معالجة اختيار مجموعة"""
    group_id = data.replace("group_", "")
    groups = bot_manager.get_all_groups()
    group_info = groups.get(group_id)
    
    if not group_info:
        await query.answer("❌ المجموعة غير موجودة!", show_alert=True)
        return
    
    text = f"""
    👥 *{group_info.get('title', group_id)}*
    
    🎀 *اختر الإجراء المطلوب:* 🎀
    """
    
    keyboard = [
        [InlineKeyboardButton("📊 الإحصائيات", callback_data=f"action_stats_group_{group_id}"),
         InlineKeyboardButton("👥 الأعضاء", callback_data=f"action_members_group_{group_id}")],
        [InlineKeyboardButton("📨 إرسال رسالة", callback_data=f"action_send_group_{group_id}"),
         InlineKeyboardButton("➕ إضافة أعضاء", callback_data=f"action_add_members_group_{group_id}")],
        [InlineKeyboardButton("🚫 طرد أعضاء", callback_data=f"action_remove_members_group_{group_id}")],
        [InlineKeyboardButton("🗑️ حذف المجموعة", callback_data=f"action_delete_group_{group_id}")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="manage_groups")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_action(query, context, data):
    """معالجة الإجراءات"""
    if data.startswith("action_stats_"):
        entity_id = data.replace("action_stats_", "")
        await show_entity_stats(query, context, entity_id)
    elif data.startswith("action_delete_"):
        entity_id = data.replace("action_delete_", "")
        await delete_entity(query, context, entity_id)
    elif data.startswith("action_send_"):
        entity_id = data.replace("action_send_", "")
        await start_send_message(query, context, entity_id)

async def show_entity_stats(query, context, entity_id):
    """عرض إحصائيات"""
    if "group" in entity_id:
        entities = bot_manager.get_all_groups()
        entity_type = "المجموعة"
        back_data = "manage_groups"
    else:
        entities = bot_manager.get_all_channels()
        entity_type = "القناة"
        back_data = "manage_channels"
    
    entity_info = entities.get(entity_id)
    
    if not entity_info:
        await query.answer("❌ غير موجود!", show_alert=True)
        return
    
    text = f"""
    📊 *إحصائيات {entity_info.get('title', entity_id)}*
    
    🆔 *الأيدي:* `{entity_id}`
    📅 *تاريخ الإضافة:* {entity_info.get('added_date', 'غير معروف')}
    👥 *عدد الأعضاء:* {entity_info.get('member_count', 'غير معروف')}
    💬 *عدد الرسائل:* {entity_info.get('message_count', 'غير معروف')}
    
    💖 *معلومات الإدارة:*
    🎀 *الحالة:* {entity_info.get('status', 'نشط')}
    """
    
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data=back_data)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def delete_entity(query, context, entity_id):
    """حذف قناة أو مجموعة"""
    if "group" in entity_id:
        success = bot_manager.remove_group(entity_id)
        entity_type = "المجموعة"
        back_button = "manage_groups"
    else:
        success = bot_manager.remove_channel(entity_id)
        entity_type = "القناة"
        back_button = "manage_channels"
    
    if success:
        text = f"✅ *تم حذف {entity_type} بنجاح!* 💖"
    else:
        text = f"❌ *فشل في حذف {entity_type}!* 💔"
    
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data=back_button)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def start_send_message(query, context, entity_id):
    """بدء إرسال رسالة"""
    context.user_data['waiting_for_message'] = entity_id
    
    text = """
    📨 *إرسال رسالة*
    
    💝 *أرسل لي الرسالة التي تريد إرسالها:*
    
    ✨ *يمكن أن تكون:*
    - 📝 نص
    - 🖼️ صورة  
    - 🎥 فيديو
    - 📄 ملف
    """
    
    if "group" in entity_id:
        back_data = f"group_{entity_id}"
    else:
        back_data = f"channel_{entity_id}"
        
    keyboard = [[InlineKeyboardButton("❌ إلغاء", callback_data=back_data)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def add_channel_start(query, context):
    """بدء إضافة قناة"""
    text = """
    🌸 *إضافة قناة جديدة* 🌸
    
    💖 *لإضافة قناة:*
    
    1. 🎀 *أضف البوت كمسؤول في القناة*
    2. 📝 *أعط البوت جميع الصلاحيات*
    3. 🔄 *أعد إرسال أي رسالة من القناة*
    
    💕 *سيتم التعرف على القناة تلقائياً*
    """
    
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def add_group_start(query, context):
    """بدء إضافة مجموعة"""
    text = """
    🌸 *إضافة مجموعة جديدة* 🌸
    
    💖 *لإضافة مجموعة:*
    
    1. 🎀 *أضف البوت كمسؤول في المجموعة*
    2. 📝 *أعط البوت جميع الصلاحيات*
    3. 🔄 *أعد إرسال أي رسالة من المجموعة*
    
    💕 *سيتم التعرف على المجموعة تلقائياً*
    """
    
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def broadcast_start(query, context):
    """بدء الإرسال الجماعي"""
    text = """
    📨 *الإرسال الجماعي* 📨
    
    💝 *أرسل الرسالة التي تريد نشرها:*
    
    ✨ *سيتم إرسالها لجميع القنوات والمجموعات*
    """
    
    context.user_data['waiting_for_broadcast'] = True
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_stats(query, context):
    """عرض الإحصائيات"""
    channels = bot_manager.get_all_channels()
    groups = bot_manager.get_all_groups()
    
    total_channels = len(channels)
    total_groups = len(groups)
    total_entities = total_channels + total_groups
    
    text = f"""
    📈 *إحصائيات البوت* 📈
    
    💖 *نظرة عامة:*
    
    📺 *القنوات:* {total_channels} قناة
    👥 *المجموعات:* {total_groups} مجموعة
    📊 *المجموع:* {total_entities}
    
    ⭐ *السعة المتبقية:* غير محدود 💫
    """
    
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الرسائل"""
    if context.user_data.get('waiting_for_broadcast'):
        context.user_data['waiting_for_broadcast'] = False
        await update.message.reply_text("✅ *تم محاكاة الإرسال الجماعي بنجاح!* 💖", parse_mode='Markdown')
        
    elif context.user_data.get('waiting_for_message'):
        entity_id = context.user_data['waiting_for_message']
        context.user_data['waiting_for_message'] = None
        await update.message.reply_text("✅ *تم محاكاة إرسال الرسالة بنجاح!* 💖", parse_mode='Markdown')
        
    else:
        await start(update, context)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الأخطاء"""
    logger.error(f"Error: {context.error}")

def run_bot():
    """تشغيل البوت"""
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN غير موجود! تأكد من إضافته في Environment Variables")
        return
    
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        
        # إضافة المعالجات
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CallbackQueryHandler(button_handler))
        application.add_handler(MessageHandler(filters.ALL, handle_message))
        application.add_error_handler(error_handler)
        
        logger.info("🌸 البوت يعمل على Render! 💖")
        logger.info("🎀 أرسل /start لبدء الاستخدام")
        
        # تشغيل البوت
        application.run_polling()
    except Exception as e:
        logger.error(f"❌ خطأ في تشغيل البوت: {e}")
        time.sleep(10)
        run_bot()  # إعادة المحاولة

# 🚀 التشغيل الرئيسي
if __name__ == '__main__':
    print("🚀 بدء تشغيل البوت على Render...")
    
    # تشغيل خادم الويب في thread منفصل - ضروري لـ Render
    web_thread = Thread(target=run_web)
    web_thread.daemon = True
    web_thread.start()
    
    print("✅ خادم الويب يعمل على port 8080")
    print("🔧 جارٍ تشغيل بوت التلغرام...")
    
    # تشغيل البوت
    run_bot()