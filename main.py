import logging
import random
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

logging.basicConfig(level=logging.INFO)

# Завантаження запитань
with open("questions.txt", "r", encoding="utf-8") as f:
    QUESTIONS = [line.strip() for line in f if line.strip()]

# Стан гравців
players = {}
pairs = {}  # chat_id: [user1_id, user2_id]
answers = {}  # chat_id: {question_id: {user_id: answer}}
asked_questions = {}  # chat_id: [question_ids]

START_KEYBOARD = ReplyKeyboardMarkup([["Так", "Ні"]], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if chat_id not in pairs:
        pairs[chat_id] = [user_id]
        await update.message.reply_text("Чекаємо на другого гравця...")
    elif user_id not in pairs[chat_id]:
        pairs[chat_id].append(user_id)
        await update.message.reply_text("🎉 Гравці з'єднані! Починаємо гру.")
        await send_next_question(chat_id, context)
    else:
        await update.message.reply_text("Ти вже в грі!")

async def send_next_question(chat_id, context):
    asked = asked_questions.get(chat_id, [])
    if len(asked) >= len(QUESTIONS):
        await context.bot.send_message(chat_id, "Гру завершено — питань більше нема ✨")
        return

    while True:
        q_id = random.randint(0, len(QUESTIONS) - 1)
        if q_id not in asked:
            break

    asked.append(q_id)
    asked_questions[chat_id] = asked
    q_text = QUESTIONS[q_id]

    if chat_id not in answers:
        answers[chat_id] = {}
    answers[chat_id][q_id] = {}

    await context.bot.send_message(chat_id, f"❓ {q_text}", reply_markup=START_KEYBOARD)

async def handle_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    text = update.message.text.strip().lower()

    if text not in ["так", "ні"]:
        return

    if chat_id not in asked_questions or chat_id not in pairs:
        return

    q_id = asked_questions[chat_id][-1]
    answers[chat_id][q_id][user_id] = text

    # Чекаємо на другу відповідь
    if len(answers[chat_id][q_id]) < 2:
        await update.message.reply_text("Очікуємо відповідь іншого гравця...")
        return

    vals = list(answers[chat_id][q_id].values())
    if vals[0] == vals[1]:
        await context.bot.send_message(chat_id, f"✅ Збіг! Обоє відповіли " + ("так." if vals[0] == "так" else "ні."))
    else:
        await context.bot.send_message(chat_id, f"❌ Немає збігу.")

    await send_next_question(chat_id, context)

if __name__ == '__main__':
    app = ApplicationBuilder().token("8194716705:AAG8dvxKlRggAlCzMrzSIEX7xm1v0cubAGE").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_response))

    app.run_polling()
