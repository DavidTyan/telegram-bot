import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

TOKEN = os.getenv("BOT_TOKEN", "8303815205:AAFmhAC2zCC79gGcctIwcs2u5S_yV_ZOFvY")

# ==== Мини-сервер для Render ====
class PingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

def run_web():
    port = int(os.environ.get("PORT", 8080))
    HTTPServer(("0.0.0.0", port), PingHandler).serve_forever()

# ==== Команда /start с кнопками ====
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

# ==== Обработка нажатий кнопок ====
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

# ==== Запуск ====
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))

# Запускаем HTTP-сервер в отдельном потоке
threading.Thread(target=run_web, daemon=True).start()

# Запускаем бота
app.run_polling()
