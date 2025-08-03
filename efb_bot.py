
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ContextTypes, ConversationHandler, MessageHandler, filters
)
from telegram.constants import ChatMemberStatus

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 6764890600

CHANNELS = ["liverpuluzofficial", "efootball_lfc", "efootball26_uz"]

(
    CHECK_SUB, MENU,
    REG_NAME, REG_USERNAME, REG_KONAMI,
    REG_TEAMNAME, REG_POWER, REG_PHONE,
    CONFIRM_SEND, RESULT_UPLOAD, CONTACT_ADMIN
) = range(11)

participants = {}
approved = set()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Assalom-u Aleykum! eFootball simulator o’yini bo’yicha turnirga qo’shilish uchun "
        "o’z ma’lumotlaringizni ushbu bot orqali tashkilotchilarga yuboring!\n\n"
        "💬 Guruhimiz: @EFOOTBALL26_UZ\n"
        "🔔 KANALIMIZ: @EFOOTBALL_LFC"
    )
    keyboard = [
        [InlineKeyboardButton(f"@{ch}", url=f"https://t.me/{ch}")]
        for ch in CHANNELS
    ]
    keyboard.append([InlineKeyboardButton("✅ Tekshirish", callback_data="check_subs")])
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return CHECK_SUB

async def check_subs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    for ch in CHANNELS:
        member = await context.bot.get_chat_member(f"@{ch}", user_id)
        if member.status not in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            await update.callback_query.answer("Iltimos, barcha kanallarga obuna bo‘ling!", show_alert=True)
            return CHECK_SUB
    await update.callback_query.answer("✅ Ajoyib, davom etamiz!")
    await update.callback_query.message.delete()
    await show_menu(update.callback_query.message, context)
    return MENU

async def show_menu(msg, context):
    kb = [
        [InlineKeyboardButton("1. Ro’yhatdan o’tish", callback_data="reg")],
        [InlineKeyboardButton("2. Turnir haqida ma’lumot", callback_data="info")],
        [InlineKeyboardButton("3. Ishtirokchilar ro’yhati", callback_data="list")],
        [InlineKeyboardButton("4. Uchrashuv natijasini yuborish", callback_data="submit_result")],
        [InlineKeyboardButton("5. Admin bilan aloqa", callback_data="contact_admin")],
    ]
    await msg.reply_text("Asosiy menyu:", reply_markup=InlineKeyboardMarkup(kb))

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.callback_query.data
    await update.callback_query.answer()
    if data == "reg":
        await update.callback_query.message.reply_text("Ism Familiyangizni kiriting:")
        return REG_NAME
    elif data == "info":
        await update.callback_query.message.reply_text("🎮 Turnir haqida ma'lumot bu yerda!")
    elif data == "list":
        if approved:
            names = [participants[uid]["name"] for uid in approved]
            await update.callback_query.message.reply_text("✅ Ishtirokchilar:"
" + "\n".join(names))
        else:
            await update.callback_query.message.reply_text("Hali ishtirokchilar ro'yxati mavjud emas.")
    elif data == "submit_result":
        await update.callback_query.message.reply_text("Natijani kiriting:")
        return RESULT_UPLOAD
    elif data == "contact_admin":
        await update.callback_query.message.reply_text("Admin bilan aloqa: @admin_username")
    return MENU

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Bekor qilindi.")
    return ConversationHandler.END

def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHECK_SUB: [CallbackQueryHandler(check_subs)],
            MENU: [CallbackQueryHandler(menu_handler)],
            RESULT_UPLOAD: [MessageHandler(filters.TEXT & ~filters.COMMAND, cancel)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    logging.info("✅ Bot ishga tushdi")
    application.run_polling()

if __name__ == "__main__":
    main()
