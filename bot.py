import os
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters

# ====== Настройки ======
TOKEN = os.getenv("BOT_TOKEN", "8303815205:AAFmhAC2zCC79gGcctIwcs2u5S_yV_ZOFvY")
PORT = int(os.environ.get("PORT", 8080))
IDS_FILE = "saved_ids.json"

# ====== Работа с сохранёнными ID ======
def load_ids():
    if os.path.exists(IDS_FILE):
        with open(IDS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_ids(data):
    with open(IDS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

saved_ids = load_ids()

# ====== Клавиатура всех действий ======
def main_keyboard():
    keyboard = [
        [InlineKeyboardButton("Help", callback_data='help')],
        [InlineKeyboardButton("ID", callback_data='id')]
    ]
    return InlineKeyboardMarkup(keyboard)

def id_options_keyboard():
    keyboard = [
        [InlineKeyboardButton("My ID", callback_data='my_id')],
        [InlineKeyboardButton("Other's ID", callback_data='others_id')]
    ]
    return InlineKeyboardMarkup(keyboard)

# ====== Текст всех возможных команд ======
def get_possible_moves():
    return (
        "📋 Доступные команды:\n"
        "/start — показать меню\n"
        "/help — список команд\n"
        "/id — узнать ID (своё или через пересланное сообщение)\n\n"
        "💡 Советы:\n"
        "- Чтобы узнать свой ID, нажмите My ID\n"
        "- Чтобы узнать ID другого пользователя, нажмите Other's ID и перешлите сообщение от него"
    )

# ====== /start ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    saved_ids[str(user.id)] = user.username
    save_ids(saved_ids)
    await update.message.reply_text(
        f"Привет, {user.first_name}!\n{get_possible_moves()}",
        reply_markup=main_keyboard()
    )

# ====== Кнопки ======
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    saved_ids[str(user.id)] = user.username
    save_ids(saved_ids)
    await query.answer()

    if query.data == 'help':
        text = get_possible_moves()
        markup = main_keyboard()
    elif query.data == 'id':
        text = "Выберите вариант, чтобы узнать ID:"
        markup = id_options_keyboard()
    elif query.data == 'my_id':
        text = f"Ваш ID: {user.id}\nВаш username: @{user.username}"
        markup = main_keyboard()
    elif query.data == 'others_id':
        text = "Чтобы узнать ID другого пользователя, **перешлите мне сообщение от него**. Другой способ недоступен."
        markup = None  # Ожидаем пересланное сообщение
        context.user_data['awaiting_other_id'] = True
    else:
        text = "Выберите действие."
        markup = main_keyboard()

    await query.edit_message_text(text, reply_markup=markup)

# ====== /help ======
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_possible_moves(), reply_markup=main_keyboard())

# ====== Обработка сообщений для Other's ID ======
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    saved_ids[str(user.id)] = user.username
    save_ids(saved_ids)

    # Если ждем пересланное сообщение для Other's ID
    if context.user_data.get('awaiting_other_id'):
        context.user_data['awaiting_other_id'] = False
        fwd_user = update.message.forward_from

        if fwd_user:
            saved_ids[str(fwd_user.id)] = fwd_user.username
            save_ids(saved_ids)
            await update.message.reply_text(
                f"ID пользователя @{fwd_user.username}: {fwd_user.id}",
                reply_markup=main_keyboard()
            )
        else:
            await update.message.reply_text(
                "Это не пересланное сообщение. Пожалуйста, перешлите сообщение от пользователя, чей ID хотите узнать.",
                reply_markup=main_keyboard()
            )

# ====== Мини-вебсервер для Render ======
class PingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(f"Bot is running! Saved IDs: {len(saved_ids)}".encode())

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def run_web():
    server = HTTPServer(("0.0.0.0", PORT), PingHandler)
    print(f"Web server running on port {PORT}")  # для логов Render
    server.serve_forever()

# ====== Запуск вебсервера в отдельном потоке ======
threading.Thread(target=run_web, daemon=True).start()

# ====== Запуск бота ======
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.TEXT | filters.COMMAND | filters.ALL, message_handler))

app.run_polling()
