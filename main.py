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
matched_questions = {}  # chat_id: [question_texts]
paused = {}  # chat_id: bool

BUTTONS = [["Так", "Ні", "Точно не впевнений"], ["Продовжити", "Пауза"], ["Почати заново", "Зупинити", "Збіги"]]
START_KEYBOARD = ReplyKeyboardMarkup(BUTTONS, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    paused[chat_id] = False

    if chat_id not in pairs:
        pairs[chat_id] = [user_id]
        await update.message.reply_text("Чекаємо на другого гравця...", reply_markup=START_KEYBOARD)
    elif user_id not in pairs[chat_id]:
        pairs[chat_id].append(user_id)
        await update.message.reply_text("🎉 Гравці з'єднані! Починаємо гру.", reply_markup=START_KEYBOARD)
        await send_next_question(chat_id, context)
    else:
        await update.message.reply_text("Ти вже в грі!", reply_markup=START_KEYBOARD)

async def send_next_question(chat_id, context):
    if paused.get(chat_id):
        return

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

    if chat_id not in pairs:
        await update.message.reply_text("Почніть гру командою /start")
        return

    if text == "пауза":
        paused[chat_id] = True
        await update.message.reply_text("⏸️ Гру призупинено. Натисніть 'Продовжити' щоб відновити гру.")
        return
    elif text == "продовжити":
        if paused.get(chat_id):
            paused[chat_id] = False
            await update.message.reply_text("▶️ Гру відновлено.")
            await send_next_question(chat_id, context)
        else:
            await update.message.reply_text("Гра вже активна.")
        return
    elif text == "зупинити":
        await show_matches(chat_id, context)
        reset_game(chat_id)
        await update.message.reply_text("⛔ Гру завершено. Щоб почати нову, натисніть 'Почати заново'.")
        return
    elif text == "почати заново":
        reset_game(chat_id)
        pairs[chat_id] = [user_id]
        await update.message.reply_text("🔄 Починаємо спочатку! Очікуємо на двох гравців...", reply_markup=START_KEYBOARD)
        return
    elif text == "збіги":
        await show_matches(chat_id, context)
        return

    if text not in ["так", "ні", "точно не впевнений"]:
        return

    if chat_id not in asked_questions or chat_id not in pairs:
        return

    if paused.get(chat_id):
        await update.message.reply_text("⏸️ Гру на паузі. Натисніть 'Продовжити' щоб відновити гру.")
        return

    q_id = asked_questions[chat_id][-1]
    answers[chat_id][q_id][user_id] = text

    if len(answers[chat_id][q_id]) < 2:
        await update.message.reply_text("Очікуємо відповідь іншого гравця...")
        return

    vals = list(answers[chat_id][q_id].values())
    q_text = QUESTIONS[q_id]
    if vals[0] == vals[1]:
        await context.bot.send_message(chat_id, f"✅ Збіг! Обоє відповіли {vals[0]}.")
        matched_questions.setdefault(chat_id, []).append(q_text)
    else:
        await context.bot.send_message(chat_id, f"❌ Немає збігу.")

    await send_next_question(chat_id, context)

async def show_matches(chat_id, context):
    matches = matched_questions.get(chat_id, [])
    if not matches:
        await context.bot.send_message(chat_id, "Поки що немає збігів 💔")
    else:
        result = "💖 Питання зі збігом:\n" + "\n".join(f"• {q}" for q in matches)
        await context.bot.send_message(chat_id, result)

def reset_game(chat_id):
    asked_questions.pop(chat_id, None)
    answers.pop(chat_id, None)
    matched_questions.pop(chat_id, None)
    paused[chat_id] = False

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/start — почати гру\n/help — допомога\nКнопки: Так, Ні, Точно не впевнений, Пауза, Продовжити, Зупинити, Почати заново, Збіги")

if __name__ == '__main__':
    app = ApplicationBuilder().token("8194716705:AAG8dvxKlRggAlCzMrzSIEX7xm1v0cubAGE").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_response))

    app.run_polling()
