import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

TOKEN = os.getenv("BOT_TOKEN", "8303815205:AAFmhAC2zCC79gGcctIwcs2u5S_yV_ZOFvY")

saved_ids = []

# ==== Мини-сервер для Render ====
class PingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

def run_web():
    port = int(os.environ.get("PORT", 8080))
    HTTPServer(("0.0.0.0", port), PingHandler).serve_forever()

# ==== /start с кнопками ====
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

# ==== Обработка кнопок ====
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'help':
        await query.edit_message_text(
            "/start - меню с кнопками\n"
            "/help - список команд\n"
            "/info - твой ID и username\n"
            "/id - получить ID пересланного пользователя или по @username\n"
            "После получения ID можно сохранять его или получать советы"
        )
    elif query.data == 'info':
        user = query.from_user
        await query.edit_message_text(
            f"Твой ID: {user.id}\n"
            f"Твой username: @{user.username}"
        )
    elif query.data == 'tips':
        await query.edit_message_text(
            "Советы для работы с ботом:\n"
            "- Используй /id в ответ на сообщение, чтобы узнать ID пользователя.\n"
            "- Чтобы узнать свой ID, отправь команду /info.\n"
            "- Сохраняй интересные ID с помощью кнопки 'Save ID'.\n"
            "- Используй /help для быстрого списка команд.\n"
            "- Экспериментируй с кнопками меню для быстрого доступа к функциям."
        )
    elif query.data == 'save_id':
        last_msg = context.user_data.get("last_id")
        if last_msg:
            if last_msg not in saved_ids:
                saved_ids.append(last_msg)
                await query.edit_message_text(f"ID {last_msg} сохранён!")
            else:
                await query.edit_message_text(f"ID {last_msg} уже сохранён!")
        else:
            await query.edit_message_text("Сначала получи ID с помощью /id.")

# ==== /id команда ====
async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result_text = ""
    user_id = None
    # Если переслано сообщение
    if update.message.reply_to_message:
        user = update.message.reply_to_message.from_user
        user_id = user.id
        result_text = f"ID пользователя {user.first_name} (@{user.username}): {user.id}"
    # Если указан @username
    elif context.args:
        username = context.args[0].lstrip('@')
        try:
            member = await context.bot.get_chat_member(update.effective_chat.id, username)
            user_id = member.user.id
            result_text = f"ID пользователя @{username}: {member.user.id}"
        except:
            result_text = f"Не могу найти ID для @{username}."
    else:
        await update.message.reply_text("Используй: /id в ответ на сообщение или /id @username")
        return

    context.user_data["last_id"] = user_id

    keyboard = [
        [InlineKeyboardButton("Info", callback_data='info')],
        [InlineKeyboardButton("Help", callback_data='help')],
        [InlineKeyboardButton("Start", callback_data='start')],
        [InlineKeyboardButton("Save ID", callback_data='save_id')],
        [InlineKeyboardButton("Tips", callback_data='tips')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(result_text, reply_markup=reply_markup)

# ==== Запуск ====
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(CommandHandler("id", get_id))
app.add_handler(CommandHandler("info", lambda u,c: button(u,c)))  # Info через команду /info

threading.Thread(target=run_web, daemon=True).start()
app.run_polling()
