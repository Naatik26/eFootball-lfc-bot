import os
import logging
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ContextTypes, ConversationHandler, MessageHandler, filters
)
from telegram.constants import ChatMemberStatus

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 6764890600  # Replace with your actual admin ID
CHANNELS = ["liverpuluzofficial", "efootball_lfc", "efootball26_uz"]

# Conversation states
(
    CHECK_SUB, MENU,
    REG_NAME, REG_USERNAME, REG_KONAMI,
    REG_TEAMNAME, REG_POWER, REG_PHONE,
    CONFIRM_SEND, RESULT_UPLOAD, CONTACT_ADMIN
) = range(11)

# Data storage (in production use a database)
participants = {}
approved = set()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message with channel subscription buttons"""
    text = (
        "Assalom-u Aleykum! eFootball simulator o’yini bo’yicha turnirga qo’shilish uchun "
        "o’z ma’lumotlaringizni ushbu bot orqali tashkilotchilarga yuboring!\n\n"
        "💬 Guruhimiz: @EFOOTBALL26_UZ\n"
        "🔔 KANALIMIZ: @EFOOTBALL_LFC"
    )
    keyboard = [
        [InlineKeyboardButton(f"@{channel}", url=f"https://t.me/{channel}")]
        for channel in CHANNELS
    ]
    keyboard.append([InlineKeyboardButton("✅ Tekshirish", callback_data="check_subs")])
    await update.message.reply_text(
        text, 
        reply_markup=InlineKeyboardMarkup(keyboard),
        disable_web_page_preview=True
    )
    return CHECK_SUB

async def check_subs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check if user is subscribed to all channels"""
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    
    for channel in CHANNELS:
        try:
            member = await context.bot.get_chat_member(f"@{channel}", user_id)
            if member.status not in [
                ChatMemberStatus.MEMBER, 
                ChatMemberStatus.ADMINISTRATOR, 
                ChatMemberStatus.OWNER
            ]:
                await query.edit_message_text(
                    "Iltimos, barcha kanallarga obuna bo'ling va qayta urinib ko'ring!",
                    reply_markup=query.message.reply_markup
                )
                return CHECK_SUB
        except Exception as e:
            logger.error(f"Channel check error for @{channel}: {e}")
            await query.edit_message_text(
                f"@{channel} kanalini tekshirishda xatolik. Iltimos, keyinroq urinib ko'ring."
            )
            return ConversationHandler.END

    await query.edit_message_text("✅ Ajoyib, barcha kanallarga obuna bo'lgansiz! Davom etamiz...")
    await show_menu(query.message, context)
    return MENU

async def show_menu(msg, context: ContextTypes.DEFAULT_TYPE):
    """Show main menu after successful subscription check"""
    kb = [
        [InlineKeyboardButton("1. Ro’yhatdan o’tish", callback_data="reg")],
        [InlineKeyboardButton("2. Turnir haqida ma’lumot", callback_data="info")],
        [InlineKeyboardButton("3. Ishtirokchilar ro’yhati", callback_data="list")],
        [InlineKeyboardButton("4. Uchrashuv natijasini yuborish", callback_data="submit_result")],
        [InlineKeyboardButton("5. Admin bilan aloqa", callback_data="contact_admin")],
    ]
    await msg.reply_text("🏆 Asosiy menyu:", reply_markup=InlineKeyboardMarkup(kb))

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle main menu selections"""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "reg":
        # Check if already registered
        user_id = query.from_user.id
        if user_id in participants:
            await query.message.reply_text(
                "ℹ️ Siz allaqachon ro'yxatdan o'tgansiz! "
                "Agar ma'lumotlaringizni o'zgartirmoqchi bo'lsangiz, "
                "iltimos admin bilan bog'laning: @efootball_admin"
            )
            return MENU
            
        await query.message.reply_text(
            "✍️ Ro'yxatdan o'tish jarayoni boshlandi!\n\n"
            "Ismingiz va Familiyangizni kiriting (Misol: Alijon Valiyev):"
        )
        return REG_NAME
        
    elif data == "info":
        info_text = (
            "⚽️ eFootball Championship Turniri\n\n"
            "📅 Sana: 2023-yil 15-20 Dekabr\n"
            "🕒 Vaqt: 18:00 - 22:00\n"
            "📍 Joy: Onlayn Platforma\n\n"
            "🔹 Har bir o‘yin 10 daqiqa\n"
            "🔹 Guruh bosqichi va pley-off\n"
            "🔹 Sovrinlar pooli: 5 000 000 so‘m\n\n"
            "Batafsil: @EFOOTBALL26_UZ"
        )
        await query.message.reply_text(info_text)
        return MENU
        
    elif data == "list":
        if not approved:
            await query.message.reply_text("⚠️ Hozircha tasdiqlangan ishtirokchilar mavjud emas.")
            return MENU
            
        names = []
        for uid in approved:
            if uid in participants and "name" in participants[uid]:
                names.append(f"• {participants[uid]['name']}")
        
        if not names:
            await query.message.reply_text("⚠️ Tasdiqlangan ishtirokchilar topilmadi.")
            return MENU
            
        response = "✅ Tasdiqlangan ishtirokchilar ro'yxati:\n\n" + "\n".join(names)
        await query.message.reply_text(response)
        return MENU
        
    elif data == "submit_result":
        await query.message.reply_text(
            "Uchrashuv natijasini quyidagi formatda yuboring:\n\n"
            "«Raqib ismi» 3:2 [Sizning hisobingiz oldin]\n\n"
            "Misol: Liverpool 2:1"
        )
        return RESULT_UPLOAD
        
    elif data == "contact_admin":
        await query.message.reply_text(
            "✉️ Savol va takliflaringiz bo'lsa adminga murojaat qiling:\n"
            f"👤 Admin: @efootball_admin\n"
            f"📞 Telefon: +998901234567"
        )
        return MENU
        
    return MENU

# ================= REGISTRATION FLOW =================
async def register_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle full name input for registration"""
    user_id = update.message.from_user.id
    name = update.message.text.strip()
    
    # Validate name format
    if len(name) < 5 or not re.match(r"^[a-zA-Z' -]+ [a-zA-Z' -]+$", name):
        await update.message.reply_text(
            "❌ Noto'g'ri format! Iltimos, ism va familiyangizni to'liq kiriting.\n"
            "Misol: Alijon Valiyev\n\n"
            "Qaytadan kiriting:"
        )
        return REG_NAME
    
    # Store in context for later steps
    context.user_data['registration'] = {
        'user_id': user_id,
        'name': name
    }
    
    await update.message.reply_text(
        "🆔 Konami ID (o'yindagi foydalanuvchi nomi) ni kiriting:\n\n"
        "Misol: BestPlayer2023"
    )
    return REG_USERNAME

async def register_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Konami ID input"""
    username = update.message.text.strip()
    
    # Validate username
    if len(username) < 3:
        await update.message.reply_text(
            "❌ Konami ID kamida 3 belgidan iborat bo'lishi kerak!\n"
            "Qaytadan kiriting:"
        )
        return REG_USERNAME
    
    context.user_data['registration']['konami_id'] = username
    
    await update.message.reply_text(
        "🏷️ Jamoa nomini kiriting:\n\n"
        "Misol: Real Tashkent"
    )
    return REG_TEAMNAME

async def register_teamname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle team name input"""
    team_name = update.message.text.strip()
    
    if len(team_name) < 3:
        await update.message.reply_text(
            "❌ Jamoa nomi kamida 3 belgidan iborat bo'lishi kerak!\n"
            "Qaytadan kiriting:"
        )
        return REG_TEAMNAME
    
    context.user_data['registration']['team_name'] = team_name
    
    await update.message.reply_text(
        "⚡️ Jamoa kuchini (power) kiriting (1-99 oralig'ida):\n\n"
        "Misol: 87"
    )
    return REG_POWER

async def register_power(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle team power input"""
    power = update.message.text.strip()
    
    try:
        power_value = int(power)
        if power_value < 1 or power_value > 99:
            raise ValueError
    except ValueError:
        await update.message.reply_text(
            "❌ Noto'g'ri raqam! Iltimos, 1 dan 99 gacha butun son kiriting.\n"
            "Qaytadan kiriting:"
        )
        return REG_POWER
    
    context.user_data['registration']['power'] = power_value
    
    await update.message.reply_text(
        "📞 Telefon raqamingizni kiriting (Format: +998912345678):\n\n"
        "Misol: +998901234567"
    )
    return REG_PHONE

async def register_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle phone number input"""
    phone = update.message.text.strip()
    
    # Validate phone number
    if not re.match(r"^\+998\d{9}$", phone):
        await update.message.reply_text(
            "❌ Noto'g'ri format! Iltimos, quyidagi formatda kiriting:\n"
            "+998912345678\n\n"
            "Qaytadan kiriting:"
        )
        return REG_PHONE
    
    # Save all registration data
    reg_data = context.user_data['registration']
    reg_data['phone'] = phone
    user_id = reg_data['user_id']
    
    # Save to participants dictionary
    participants[user_id] = {
        'name': reg_data['name'],
        'konami_id': reg_data['konami_id'],
        'team_name': reg_data['team_name'],
        'power': reg_data['power'],
        'phone': reg_data['phone'],
        'status': 'pending'
    }
    
    # Prepare confirmation message
    confirm_text = (
        "✅ Ma'lumotlaringiz qabul qilindi! Tasdiqlash uchun:\n\n"
        f"👤 Ism-Familiya: {reg_data['name']}\n"
        f"🆔 Konami ID: {reg_data['konami_id']}\n"
        f"🏷️ Jamoa nomi: {reg_data['team_name']}\n"
        f"⚡️ Jamoa kuchi: {reg_data['power']}\n"
        f"📞 Telefon: {reg_data['phone']}\n\n"
        "Ma'lumotlaringiz to'g'rimi?"
    )
    
    keyboard = [
        [InlineKeyboardButton("✅ Ha, jo'natish", callback_data="confirm_send")],
        [InlineKeyboardButton("❌ Yo'q, qaytadan kiritish", callback_data="restart_reg")]
    ]
    
    await update.message.reply_text(
        confirm_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CONFIRM_SEND

async def confirm_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle registration confirmation"""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if query.data == "confirm_send":
        # Notify admin about new registration
        reg_data = participants[user_id]
        
        admin_text = (
            "🚀 Yangi ro'yxatdan o'tish!\n\n"
            f"👤 Foydalanuvchi: {query.from_user.full_name} (@{query.from_user.username})\n"
            f"🆔 ID: {user_id}\n\n"
            f"📝 Ma'lumotlar:\n"
            f"• Ism: {reg_data['name']}\n"
            f"• Konami ID: {reg_data['konami_id']}\n"
            f"• Jamoa: {reg_data['team_name']}\n"
            f"• Kuch: {reg_data['power']}\n"
            f"• Tel: {reg_data['phone']}\n\n"
            "Tasdiqlaysizmi?"
        )
        
        # Create approval buttons
        approve_btn = InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approve_{user_id}")
        reject_btn = InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_{user_id}")
        
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_text,
            reply_markup=InlineKeyboardMarkup([[approve_btn, reject_btn]])
        )
        
        await query.message.edit_text(
            "📬 So'rovingiz administratorga yuborildi!\n"
            "Tasdiqlanganingizdan so'ng siz bilan bog'lanamiz.\n\n"
            "⏳ Tasdiqlanishini kuting...",
            reply_markup=None
        )
    else:
        # Restart registration
        del participants[user_id]
        await query.message.edit_text(
            "🔄 Ro'yxatdan o'tishni qayta boshlaymiz...\n\n"
            "Ismingiz va Familiyangizni kiriting:"
        )
        return REG_NAME
    
    await show_menu(query.message, context)
    return MENU

async def handle_admin_approval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin approval/rejection of registrations"""
    query = update.callback_query
    await query.answer()
    
    action, user_id = query.data.split('_')
    user_id = int(user_id)
    
    if action == "approve":
        if user_id in participants:
            participants[user_id]['status'] = 'approved'
            approved.add(user_id)
            
            # Notify user
            await context.bot.send_message(
                chat_id=user_id,
                text="🎉 Tabriklaymiz! Ro'yxatdan o'tishingiz tasdiqlandi!\n\n"
                     "Turnir haqida batafsil ma'lumot @EFOOTBALL26_UZ kanalida e'lon qilinadi."
            )
            await query.edit_message_text(
                f"✅ {participants[user_id]['name']} ro'yxatdan o'tishi tasdiqlandi!",
                reply_markup=None
            )
        else:
            await query.edit_message_text(
                "❌ Foydalanuvchi topilmadi!",
                reply_markup=None
            )
    else:
        if user_id in participants:
            user_name = participants[user_id]['name']
            del participants[user_id]
            
            # Notify user
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text="❌ Afsuski, ro'yxatdan o'tishingiz tasdiqlanmadi.\n\n"
                         "Batafsil ma'lumot uchun admin bilan bog'laning: @efootball_admin"
                )
            except Exception:
                logger.warning(f"Could not notify user {user_id}")
            
            await query.edit_message_text(
                f"❌ {user_name} ro'yxatdan o'tishi rad etildi!",
                reply_markup=None
            )
        else:
            await query.edit_message_text(
                "❌ Foydalanuvchi topilmadi!",
                reply_markup=None
            )
    
    return ConversationHandler.END
# ================= END REGISTRATION FLOW =================

async def handle_result_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process match results submitted by users"""
    result = update.message.text
    user = update.message.from_user
    
    # Notify admin
    admin_msg = (
        "⚠️ Yangi natija keldi!\n\n"
        f"Foydalanuvchi: {user.full_name} (@{user.username})\n"
        f"Natija: {result}\n\n"
        "Tasdiqlaysizmi?"
    )
    
    await update.message.reply_text(
        "✅ Natijangiz qabul qilindi! Admin tasdiqlagach, hisobga olinadi."
    )
    
    # Send to admin
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=admin_msg
    )
    
    await show_menu(update.message, context)
    return MENU

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel any ongoing operation"""
    await update.message.reply_text("❌ Amal bekor qilindi.")
    # Clear temporary data
    if 'registration' in context.user_data:
        del context.user_data['registration']
    return ConversationHandler.END

def main():
    """Start the bot and set up handlers"""
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Conversation handler with all states
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHECK_SUB: [CallbackQueryHandler(check_subs)],
            MENU: [CallbackQueryHandler(menu_handler)],
            REG_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_name)],
            REG_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_username)],
            REG_TEAMNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_teamname)],
            REG_POWER: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_power)],
            REG_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_phone)],
            CONFIRM_SEND: [CallbackQueryHandler(confirm_send)],
            RESULT_UPLOAD: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_result_upload)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Add admin approval handler
    application.add_handler(CallbackQueryHandler(handle_admin_approval, pattern=r"^(approve|reject)_\d+$"))
    
    application.add_handler(conv_handler)
    logger.info("✅ Bot ishga tushdi. Polling rejimida...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()