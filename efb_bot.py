import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

BOT_TOKEN = os.environ.get("BOT_TOKEN")
)

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = "6764890600"  # admin foydalanuvchi ID sini yozing

CHANNELS = ["liverpuluzofficial", "efootball_lfc", "efootball26_uz"]

# holatlar (states)
(
    CHECK_SUB, MENU,
    REG_NAME, REG_USERNAME, REG_KONAMI,
    REG_TEAMNAME, REG_POWER, REG_PHONE,
    CONFIRM_SEND, RESULT_UPLOAD, CONTACT_ADMIN
) = range(11)

participants = {}  # foydalanuvchi ma'lumotlari
approved = set()   # qabul qilinganlar user_id lari

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "eFootball simulator o’yini bo’yicha turnirga qo’shilish uchun "
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
        if member.status in (ChatMember.LEFT, ChatMember.NOT_PARTICIPANT):
            await update.callback_query.answer("Iltimos, barcha kanallarga obuna bo‘ling!", show_alert=True)
            return START
    await update.callback_query.answer("✅ Ajoyib, davom etamiz!.")
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
        await update.callback_query.message.reply_text("🎮 Turnir haqida ma'lumot bu yerda!");
    elif data == "list":
        lines = []
        for uid in approved:
            d = participants.get(uid)
            if d:
                lines.append(f"{d['name']} (@{d['username']}), Team: {d['team']} (power {d['power']})")
        await update.callback_query.message.reply_text("\n".join(lines) or "Hali qabul qilinganlar yo‘q.")
    elif data == "submit_result":
        uid = update.effective_user.id
        if uid not in approved:
            await update.callback_query.message.reply_text("Siz hali qabul qilinmagan ishtirokchisiz.")
        else:
            await update.callback_query.message.reply_text("Natijangizni yuboring (faqat foto yoki video):")
            return RESULT_UPLOAD
    elif data == "contact_admin":
        await update.callback_query.message.reply_text("Admin bilan aloqa uchun xabar yozing:")
        return CONTACT_ADMIN
    return MENU

# Registration steps:
async def reg_name(update, context):
    participants[update.effective_user.id] = {"name": update.message.text}
    await update.message.reply_text("Telegram username (masalan @username):")
    return REG_USERNAME

async def reg_username(update, context):
    txt = update.message.text.strip()
    if not txt.startswith("@"):
        await update.message.reply_text("Iltimos, @ belgi bilan boshlang:")
        return REG_USERNAME
    participants[update.effective_user.id]["username"] = txt[1:]
    await update.message.reply_text("Konami ID ni yuboring:")
    return REG_KONAMI

async def reg_konami(update, context):
    participants[update.effective_user.id]["konami"] = update.message.text.strip()
    await update.message.reply_text("Jamoa nomi:")
    return REG_TEAMNAME

async def reg_teamname(update, context):
    participants[update.effective_user.id]["team"] = update.message.text.strip()
    await update.message.reply_text("Jamoaning umumiy kuchini kiriting (raqam):")
    return REG_POWER

async def reg_power(update, context):
    try:
        pw = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("Faqat raqam kiriting:")
        return REG_POWER
    participants[update.effective_user.id]["power"] = pw
    if pw < 3000:
        await update.message.reply_text(
            "⚠️ Kuch 3000 dan kam – turnirda qatnashish uchun yetarli emas.\n"
            "Savolingiz bo'lsa bosh menyu orqali admin bilan aloqaga chiqing."
        )
        return MENU
    await update.message.reply_text("Telefon raqamingizni yuboring (O'zbekiston yoki boshqa davlat):")
    return REG_PHONE

async def reg_phone(update, context):
    phone = update.message.text.strip()
    if not phone or any(c.isalpha() for c in phone):
        await update.message.reply_text("Iltimos telefon raqamni raqamlar bilan yuboring:")
        return REG_PHONE
    participants[update.effective_user.id]["phone"] = phone

    # confirm:
    d = participants[update.effective_user.id]
    text = (
        f"Ism: {d['name']}\nUsername: @{d['username']}\n"
        f"Konami ID: {d['konami']}\nTeam: {d['team']} (power {d['power']})\n"
        f"Telefon: {d['phone']}\n\n"
        "📤 Tasdiqlash uchun ma’lumotlarni admin ga yuborilsinmi?"
    )
    kb = [
        [InlineKeyboardButton("Ha, yuborilsin", callback_data="admin_confirm")],
        [InlineKeyboardButton("Bekor qilish", callback_data="cancel_reg")]
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))
    return CONFIRM_SEND

async def cancel_reg(update, context):
    uid = update.effective_user.id
    participants.pop(uid, None)
    await update.callback_query.answer("Ro‘yxatdan o‘tish bekor qilindi.")
    await show_menu(update.callback_query.message, context)
    return MENU

async def admin_confirm(update, context):
    uid = update.effective_user.id
    data = participants.get(uid)
    if not data:
        await update.callback_query.answer("Ma’lumot topilmadi.")
        return MENU
    msg = (
        f"🆕 Yangi ariza:\n{data['name']} (@{data['username']})\n"
        f"Konami ID: {data['konami']}\nTeam: {data['team']} (power {data['power']})\n"
        f"Telefon: {data['phone']}\nUserID: {uid}"
    )
    kb = [
        [InlineKeyboardButton("Qabul qilish", callback_data=f"approve_{uid}")],
        [InlineKeyboardButton("So‘ralsin o‘zgartirish", callback_data=f"reject_{uid}")]
    ]
    await context.bot.send_message(chat_id=ADMIN_ID, text=msg, reply_markup=InlineKeyboardMarkup(kb))
    await update.callback_query.answer("Ma’lumot admin ga yuborildi.")
    await show_menu(update.callback_query.message, context)
    return MENU

async def approve_callback(update, context):
    uid = int(update.callback_query.data.split("_")[1])
    approved.add(uid)
    await context.bot.send_message(chat_id=uid, text="🎉 Siz turnirga qabul qilindingiz!")
    await update.callback_query.answer("Ishtirokchi qabul qilindi.")

async def reject_callback(update, context):
    uid = int(update.callback_query.data.split("_")[1])
    participants.pop(uid, None)
    await context.bot.send_message(chat_id=uid, text="❌ Ma’lumot yetarli emas, qayta yuboring.")
    await update.callback_query.answer("O'zgartirish so‘randi.")

async def result_upload(update, context):
    uid = update.effective_user.id
    if uid not in approved:
        return await update.message.reply_text("Siz ruxsatli ishtirokchi emassiz.")
    if not (update.message.photo or update.message.video):
        return await update.message.reply_text("Faqat foto yoki video yuboring.")
    caption = f"Natija: @{participants[uid]['username']} (power {participants[uid]['power']})"
    if update.message.photo:
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=update.message.photo[-1].file_id, caption=caption)
    else:
        await context.bot.send_video(chat_id=ADMIN_ID, video=update.message.video.file_id, caption=caption)
    await update.message.reply_text("✅ Natija adminga yuborildi.")
    return MENU

async def forward_message(update, context):
    uid = update.effective_user.id
    username = update.effective_user.username or uid
    await context.bot.send_message(chat_id=ADMIN_ID, text=f"From @{username}: {update.message.text}")
    await update.message.reply_text("Xabaringiz admin ga yetkazildi.")
    return MENU

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHECK_SUB: [CallbackQueryHandler(check_subs, pattern="check_subs")],
            MENU: [CallbackQueryHandler(menu_handler)],
            REG_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_name)],
            REG_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_username)],
            REG_KONAMI: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_konami)],
            REG_TEAMNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_teamname)],
            REG_POWER: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_power)],
            REG_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_phone)],
            CONFIRM_SEND: [
                CallbackQueryHandler(admin_confirm, pattern="admin_confirm"),
                CallbackQueryHandler(cancel_reg, pattern="cancel_reg"),
            ],
            CONTACT_ADMIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, forward_message)],
            RESULT_UPLOAD: [MessageHandler(filters.PHOTO | filters.VIDEO, result_upload)],
        },
        fallbacks=[CommandHandler("cancel", start)]
    )
    app.add_handler(conv)
    app.run_polling()

if __name__ == "__main__":
    main()