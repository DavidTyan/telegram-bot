from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

TOKEN = "8303815205:AAFmhAC2zCC79gGcctIwcs2u5S_yV_ZOFvY"

# Функция /start с кнопками
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("Help", callback_data='help')],
        [InlineKeyboardButton("Info", callback_data='info')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"Привет, {user.first_name}!\nВыберите действие:",
        reply_markup=reply_markup
    )

# Обработка нажатий кнопок
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'help':
        await query.edit_message_text(
            "/start - информация о тебе\n"
            "/help - список команд\n"
            "/info - твой ID и username"
        )
    elif query.data == 'info':
        user = query.from_user
        await query.edit_message_text(
            f"Твой ID: {user.id}\n"
            f"Твой username: @{user.username}"
        )

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))

app.run_polling()
