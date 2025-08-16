import os
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

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
def all_actions_keyboard():
    keyboard = [
        [InlineKeyboardButton("Help", callback_data='help')],
        [InlineKeyboardButton("Info", callback_data='info')],
        [InlineKeyboardButton("ID", callback_data='id')]
    ]
    return InlineKeyboardMarkup(keyboard)

# ====== Текст всех возможных команд ======
def get_possible_moves():
    return (
        "📋 Доступные команды:\n"
        "/start — показать меню\n"
        "/help — список команд\n"
        "/info — твой ID и username\n"
        "/id <username> — получить ID пользователя\n\n"
        "💡 Советы:\n"
        "- Чтобы узнать свой ID, напиши /info\n"
        "- Чтобы узнать ID другого пользователя, напиши /id @username\n"
        "- Можно нажимать кнопки в меню вместо команд"
    )

# ====== /start ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    saved_ids[str(user.id)] = user.username
    save_ids(saved_ids)
    await update.message.reply_text(
        f"Привет, {user.first_name}!\n{get_possible_moves()}",
        reply_markup=all_actions_keyboard()
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
    elif query.data == 'info':
        text = (
            f"Твой ID: {user.id}\n"
            f"Твой username: @{user.username}\n\n"
            "Этот бот был создан @uskoglazik, если есть претензии — пишите."
        )
    elif query.data == 'id':
        text = "Чтобы узнать ID:\n- Свой: /info\n- Другого пользователя: /id @username"
    else:
        text = "Выбери действие."

    await query.edit_message_text(text, reply_markup=all_actions_keyboard())

# ====== /help ======
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_possible_moves(), reply_markup=all_actions_keyboard())

# ====== /info ======
async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    saved_ids[str(user.id)] = user.username
    save_ids(saved_ids)
    await update.message.reply_text(
        f"Твой ID: {user.id}\n"
        f"Твой username: @{user.username}\n\n"
        "Этот бот был создан @uskoglazik, если есть претензии — пишите.",
        reply_markup=all_actions_keyboard()
    )

# ====== /id ======
async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Использование: /id @username", reply_markup=all_actions_keyboard())
        return

    username = context.args[0].lstrip("@")
    for uid, uname in saved_ids.items():
        if uname and uname.lower() == username.lower():
            await update.message.reply_text(f"ID пользователя @{uname}: {uid}", reply_markup=all_actions_keyboard())
            return

    await update.message.reply_text(f"ID для @{username} не найден. Сначала этот пользователь должен взаимодействовать с ботом.", reply_markup=all_actions_keyboard())

# ====== Мини-вебсервер для Render (встроенный Python) ======
class PingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(f"Bot is running! Saved IDs: {len(saved_ids)}".encode())

def run_web():
    server = HTTPServer(("0.0.0.0", PORT), PingHandler)
    server.serve_forever()

# ====== Запуск вебсервера в отдельном потоке ======
threading.Thread(target=run_web, daemon=True).start()

# ====== Запуск бота ======
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("info", info_command))
app.add_handler(CommandHandler("id", id_command))
app.add_handler(CallbackQueryHandler(button))

app.run_polling()
