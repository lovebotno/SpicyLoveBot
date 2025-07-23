async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in pairs or len(pairs[chat_id]) < 2:
        await update.message.reply_text("Гра ще не почалась або недостатньо гравців.")
        return

    p1, p2 = pairs[chat_id]
    name1 = user_names.get(p1, "Гравець 1")
    name2 = user_names.get(p2, "Гравець 2")

    total = 0
    matches = 0
    summary = "📋 *Питання, на які був збіг:*\n\n"

    for q_id in asked_questions.get(chat_id, []):
        a1 = answers[chat_id][q_id].get(p1)
        a2 = answers[chat_id][q_id].get(p2)
        if a1 and a2:
            total += 1
            if a1 == a2:
                matches += 1
                summary += f"❓ *{QUESTIONS[q_id]}*\n{name1}: {a1}\n{name2}: {a2}\n\n"

    if matches == 0:
        summary += "Жодного збігу не було 🫣\n\n"

    percent = round((matches / total) * 100, 1) if total > 0 else 0
    summary += f"📊 *Збігів:* {matches} з {total} ({percent}%)"

    await context.bot.send_message(chat_id, summary, parse_mode="Markdown")
