from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import asyncio

TOKEN = "8705990627:AAEIx-y-6XdaSxD-uqBBm-WNm8cxHI0jLKU"
LOG_CHANNEL_ID = -1003880274713

pending_verification = {}
pending_presentation = {}

# 🚪 NUEVO MIEMBRO
async def new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for user in update.message.new_chat_members:
        user_id = user.id
        chat_id = update.effective_chat.id

        # Restringir totalmente
        await context.bot.restrict_chat_member(
            chat_id,
            user_id,
            permissions=ChatPermissions(can_send_messages=False)
        )

        pending_verification[user_id] = chat_id

        keyboard = [[InlineKeyboardButton("✅ Soy humano", callback_data=f"verify_{user_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(
            chat_id,
            f"🚔 Bienvenido {user.first_name}\n\n"
            "Pulsa el botón para verificar que eres humano.\n"
            "⏳ Tienes 5 minutos o serás expulsado.",
            reply_markup=reply_markup
        )

        await context.bot.send_message(
            LOG_CHANNEL_ID,
            f"#ENTRADA\n👤 {user.first_name}\n🆔 {user_id}"
        )

        asyncio.create_task(check_verification(context, chat_id, user_id))


# ⏳ COMPROBAR VERIFICACIÓN
async def check_verification(context, chat_id, user_id):
    await asyncio.sleep(300)

    if user_id in pending_verification:
        await context.bot.ban_chat_member(chat_id, user_id)
        await context.bot.send_message(chat_id, "❌ Expulsado por no verificar.")
        await context.bot.send_message(LOG_CHANNEL_ID, f"#NO_VERIFICADO\n🆔 {user_id}")
        pending_verification.pop(user_id, None)


# ✅ BOTÓN VERIFICACIÓN
async def verify_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    chat_id = query.message.chat.id

    if user_id in pending_verification:
        pending_verification.pop(user_id)

        # Permitir escribir
        await context.bot.restrict_chat_member(
            chat_id,
            user_id,
            permissions=ChatPermissions(can_send_messages=True)
        )

        pending_presentation[user_id] = chat_id

        await query.edit_message_text(
            "✅ Verificado.\n\n"
            "Ahora preséntate con:\n"
            "• De dónde eres\n"
            "• Foto de tu León MK2\n\n"
            "⏳ Tienes 1 hora."
        )

        await context.bot.send_message(LOG_CHANNEL_ID, f"#VERIFICADO\n🆔 {user_id}")

        asyncio.create_task(check_presentation(context, chat_id, user_id))


# ⏳ COMPROBAR PRESENTACIÓN
async def check_presentation(context, chat_id, user_id):
    await asyncio.sleep(3600)

    if user_id in pending_presentation:
        await context.bot.ban_chat_member(chat_id, user_id)
        await context.bot.send_message(chat_id, "❌ Expulsado por no presentarse.")
        await context.bot.send_message(LOG_CHANNEL_ID, f"#NO_PRESENTADO\n🆔 {user_id}")
        pending_presentation.pop(user_id, None)


# 💬 DETECTAR PRESENTACIÓN
async def user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id in pending_presentation:
        if update.message.photo or update.message.text:
            pending_presentation.pop(user_id)

            await context.bot.send_message(
                LOG_CHANNEL_ID,
                f"#PRESENTADO\n🆔 {user_id}"
            )


# 🚀 ARRANQUE
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_member))
app.add_handler(CallbackQueryHandler(verify_button))
app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, user_message))

print("🚔 MK2 Police funcionando...")

app.run_polling()