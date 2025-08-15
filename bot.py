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

# ==== Клавиатура со всеми возможными действиями ====
def all_actions_keyboard():
    keyboard = [
        [InlineKeyboardButton("Help", callback_data='help')],
        [InlineKeyboardButton("Info", callback_data='info')],
        [InlineKeyboardButton("ID", callback_data='id')],
        [InlineKeyboardButton("Save ID", callback_data='save_id')],
        [InlineKeyboardButton("Saved IDs", callback_data='show_saved')],
        [InlineKeyboardButton("Tips", callback_data='tips')]
    ]
    return InlineKeyboardMarkup(keyboard)

# ==== /start с клавиатурой всех действий ====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"Привет, {user.first_name}!\nВот все возможные действия:",
        reply_markup=all_actions_keyboard()
    )

# ==== Обработка кнопок ====
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == 'help':
        text = (
            "/start - меню с кнопками\n"
            "/help - список команд\n"
            "/info - твой ID и username\n"
            "/id - получить ID пересланного пользователя или по @username\n"
            "После получения ID можно сохранять его или получать советы"
        )
    elif data == 'info':
        user = query.from_user
        text = (
            f"Твой ID: {user.id}\n"
            f"Твой username: @{user.username}\n"
            "Этот бот был создан @uskoglazik, если есть претензии — пишите."
        )
    elif data == 'id':
        text = "Используй команду /id в ответ на сообщение или /id @username, чтобы узнать ID пользователя."
    elif data == 'tips':
        text = (
            "Советы для работы с ботом:\n"
            "- Используй /id в ответ на сообщение, чтобы узнать ID пользователя.\n"
            "- Чтобы узнать свой ID, отправь команду /info.\n"
            "- Сохраняй интересные ID с помощью кнопки 'Save ID'.\n"
            "- Используй /help для быстрого списка команд.\n"
            "- Экспериментируй с кнопками меню для быстрого доступа к функциям."
        )
    elif data == 'save_id':
        last_id = context.user_data.get("last_id")
        if last_id:
            if last_id not in saved_ids:
                saved_ids.append(last_id)
                text = f"ID {last_id} сохранён!"
            else:
                text = f"ID {last_id} уже сохранён!"
        else:
            text = "Сначала получи ID с помощью /id."
    elif data == 'show_saved':
        if saved_ids:
            text = "Сохранённые ID:\n" + "\n".join(map(str, saved_ids))
        else:
            text = "Список сохранённых ID пуст."
    else:
        text = "Выбери действие."

    await query.edit_message_text(text, reply_markup=all_actions_keyboard())

# ==== /id команда ====
async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = None
    if update.message.reply_to_message:
        user = update.message.reply_to_message.from_user
        user_id = user.id
        text = f"ID пользователя {user.first_name} (@{user.username}): {user.id}"
    elif context.args:
        username = context.args[0].lstrip('@')
        try:
            member = await context.bot.get_chat_member(update.effective_chat.id, username)
            user_id = member.user.id
            text = f"ID пользователя @{username}: {member.user.id}"
        except:
            text = f"Не могу найти ID для @{username}."
    else:
        await update.message.reply_text("Используй: /id в ответ на сообщение или /id @username", reply_markup=all_actions_keyboard())
        return

    context.user_data["last_id"] = user_id
    await update.message.reply_text(text, reply_markup=all_actions_keyboard())

# ==== Запуск бота ====
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("id", get_id))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(CommandHandler("info", lambda u,c: button(u,c)))
app.add_handler(CommandHandler("help", lambda u,c: button(u,c)))

threading.Thread(target=run_web, daemon=True).start()
app.run_polling()
