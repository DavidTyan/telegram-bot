from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
from aiohttp import web
import threading
import json
import os

TOKEN = "ТОКЕН_СЮДА"

# Файл для сохранения ID
IDS_FILE = "saved_ids.json"

# Загрузка сохранённых ID
def load_ids():
    if os.path.exists(IDS_FILE):
        with open(IDS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# Сохранение ID
def save_ids(data):
    with open(IDS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

saved_ids = load_ids()

# Все возможные действия
def get_possible_moves():
    return (
        "📋 Все доступные команды:\n"
        "/start — показать меню\n"
        "/help — список команд\n"
        "/info — твой ID и username\n"
        "/id <username> — получить ID пользователя\n\n"
        "💡 Подсказки:\n"
        "- Чтобы узнать свой ID, напиши /info\n"
        "- Чтобы узнать ID другого пользователя, напиши /id @username\n"
        "- Можно нажимать кнопки в меню вместо команд"
    )

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    saved_ids[str(user.id)] = user.username
    save_ids(saved_ids)

    keyboard = [
        [InlineKeyboardButton("Help", callback_data='help')],
        [InlineKeyboardButton("Info", callback_data='info')],
        [InlineKeyboardButton("ID", callback_data='id')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Привет, {user.first_name}!\n{get_possible_moves()}",
        reply_markup=reply_markup
    )

# Обработка кнопок
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    saved_ids[str(user.id)] = user.username
    save_ids(saved_ids)

    await query.answer()

    if query.data == 'help':
        await query.edit_message_text(get_possible_moves())
    elif query.data == 'info':
        await query.edit_message_text(
            f"Твой ID: {user.id}\n"
            f"Твой username: @{user.username}\n\n"
            "Этот бот был создан @uskoglazik, если есть претензии — пишите."
        )
    elif query.data == 'id':
        await query.edit_message_text(
            "Чтобы узнать ID:\n"
            "- Свой: /info\n"
            "- Другого пользователя: /id @username"
        )

# Команда /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_possible_moves())

# Команда /info
async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    saved_ids[str(user.id)] = user.username
    save_ids(saved_ids)
    await update.message.reply_text(
        f"Твой ID: {user.id}\n"
        f"Твой username: @{user.username}\n\n"
        "Этот бот был создан @uskoglazik, если есть претензии — пишите."
    )

# Команда /id
async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Использование: /id @username")
        return

    username = context.args[0].lstrip("@")
    for uid, uname in saved_ids.items():
        if uname and uname.lower() == username.lower():
            await update.message.reply_text(f"ID пользователя @{uname}: {uid}")
            return

    await update.message.reply_text(f"ID для @{username} не найден. Сначала этот пользователь должен взаимодействовать с ботом.")

# Мини-вебсервер для Render
async def handle(request):
    return web.Response(text="Bot is running!")

def run_web():
    app = web.Application()
    app.router.add_get("/", handle)
    web.run_app(app, port=8080)

# Запуск вебсервера в отдельном потоке
threading.Thread(target=run_web).start()

# Запуск бота
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("info", info_command))
app.add_handler(CommandHandler("id", id_command))
app.add_handler(CallbackQueryHandler(button))

app.run_polling()
