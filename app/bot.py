import logging
import json
import os
import random
import requests
import itertools
import time
from datetime import datetime
from telegram import Update, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

load_dotenv()  # Загружает переменные окружения из .env файла
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')  # Получаем токен из переменных окружения

# Структура данных по умолчанию для нового чата
DEFAULT_CHAT_DATA = {
    "users": {},          # id: username
    "handsome_stats": {}, # id: count (красавчики)
    "pidor_stats": {},    # id: count (пидоры)
    "last_handsome": {    # последний красавчик
        "user_id": None,
        "date": ""
    },
    "last_pidor": {       # последний пидор
        "user_id": None,
        "date": ""
    }
}

# Загрузка данных
def load_data():
    if os.path.exists('/db_user/users.json'):
        with open('/db_user/users.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# Сохранение данных
def save_data(data):
    with open('/db_user/users.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Инициализация данных
data = load_data()

def get_chat_data(chat_id):
    """Получаем данные чата или создаем новые"""
    if str(chat_id) not in data:
        data[str(chat_id)] = DEFAULT_CHAT_DATA.copy()
        save_data(data)
    return data[str(chat_id)]


# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    commands_list = [
        "/reg - зарегистрироваться в этом чате",
        "/delete - удалить регистрацию из этого чата",
        "/run - выбрать красавчика дня в этом чате",
        "/pidor - выбрать пидора дня в этом чате",
        "/stats - статистика красавчиков этого чата",
        "/pidorstats - статистика пидоров этого чата"
    ]
    await update.message.reply_text("🎮 Доступные команды (работают только в этом чате):\n\n" + "\n".join(commands_list))

# Команда /reg
async def reg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    chat_data = get_chat_data(chat_id)
    
    user_id = str(update.message.from_user.id)
    username = update.message.from_user.username
    full_name = f"{update.message.from_user.first_name} {update.message.from_user.last_name or ''}".strip()
    if not username:
        await update.message.reply_text("❌ У вас должен быть username в Telegram!")
        return
        

    if user_id in chat_data["users"]:
        # Используем send_message вместо reply_text
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"ℹ️ {full_name}, вы уже зарегистрированы в этом чате как @{username}!"
        )
    else:
        chat_data["users"][user_id] = username 
        save_data(data)
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"✅ {full_name}, вы успешно зарегистрированы как @{username}!"
        )


# Команда /delete
async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    chat_data = get_chat_data(chat_id)
    
    user_id = str(update.message.from_user.id)
    
    if user_id in chat_data["users"]:
        del chat_data["users"][user_id]
        if user_id in chat_data["handsome_stats"]:
            del chat_data["handsome_stats"][user_id]
        if user_id in chat_data["pidor_stats"]:
            del chat_data["pidor_stats"][user_id]
        save_data(data)
        await update.message.reply_text("✅ Ваш аккаунт удалён из этого чата!")
    else:
        await update.message.reply_text("❌ Вы не зарегистрированы в этом чате!")

# Команда /run
async def run(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    chat_data = get_chat_data(chat_id)
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Если красавчик уже выбран сегодня
    if chat_data["last_handsome"].get("date") == today:
        handsome_user_id = chat_data["last_handsome"]["user_id"]
        
        # Получаем имя и username красавчика
        handsome_username = chat_data["users"].get(handsome_user_id, "Неизвестный пользователь")
        handsome_name = "Неизвестный"  # Запасной вариант

        # Пробуем получить имя из информации о пользователе
        try:
            if update.message.reply_to_message:  # Если команда была ответом на сообщение
                handsome_name = update.message.reply_to_message.from_user.first_name
            else:
                # Получаем информацию о пользователе через API
                user = await context.bot.get_chat_member(chat_id, int(handsome_user_id))
                handsome_name = user.user.first_name
                handsome_surname = user.user.last_name
                handsome_full_name = f"{handsome_name} {handsome_surname or ''}".strip()
        except Exception:
            pass
        
        # Формируем сообщение
        message = (
            f"ℹ️ Красавчик дня уже выбран в этом чате сегодня!\n"
            f"👤 Имя: {handsome_full_name}\n"
            f"👑 Username: @{handsome_username}\n"
            f"📅 Дата: {today}"
        )
        await update.message.reply_text(message)
        return
    users_list = list(chat_data["users"].keys())
    if not users_list:
        await update.message.reply_text("❌ В этом чате нет зарегистрированных участников!")
        return
        
    selected_id = random.choice(users_list)
    username = chat_data["users"][selected_id]
    full_name = f"{update.message.from_user.first_name} {update.message.from_user.last_name or ''}".strip()

    # Обновляем статистику
    chat_data["handsome_stats"][selected_id] = chat_data["handsome_stats"].get(selected_id, 0) + 1
    chat_data["last_handsome"] = {"user_id": selected_id, "date": today}
    save_data(data)


    await update.message.reply_text("КРУТИМ БАРАБАН")
    time.sleep(1)
    await update.message.reply_text("Ищем красавчика в этом чате")
    time.sleep(1)
    await update.message.reply_text("4 - Гадаем на бинарных опционах 📊")
    time.sleep(1)
    await update.message.reply_text("3 - Анализируем лунный гороскоп 🌖")
    time.sleep(1)
    await update.message.reply_text("2 - Лунная призма дай мне силу 💫")
    time.sleep(1)
    await update.message.reply_text("1 - СЕКТОР ПРИЗ НА БАРАБАНЕ 🎯")
    time.sleep(1)
    await update.message.reply_text(f"🎉 Сегодня красавчик дня -  (@{username})")


# Команда /pidor
async def pidor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    chat_data = get_chat_data(chat_id)
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Если пидор уже выбран сегодня
    if chat_data["last_pidor"].get("date") == today:
        pidor_user_id = chat_data["last_pidor"]["user_id"]
        
        # Получаем имя и username пидора
        pidor_username = chat_data["users"].get(pidor_user_id, "Неизвестный пользователь")
        pidor_name = "Неизвестный"  # Запасной вариант
        
        # Пробуем получить имя из информации о пользователе
        try:
            if update.message.reply_to_message:  # Если команда была ответом на сообщение
                pidor_name = update.message.reply_to_message.from_user.first_name
            else:
                # Получаем информацию о пользователе через API
                user = await context.bot.get_chat_member(chat_id, int(pidor_user_id))
                pidor_name = user.user.first_name
                pidor_surname = user.user.last_name
                pidor_full_name = f"{pidor_name} {pidor_surname or ''}".strip()
        except Exception:
            pass
        
        # Формируем сообщение
        message = (
            f"ℹ️ Пидор дня уже выбран в этом чате сегодня!\n"
            f"👤 Имя: {pidor_full_name}\n"
            f"🔹 Username: @{pidor_username}\n"
            f"📅 Дата: {today}"
        )
        await update.message.reply_text(message)
        return
    
    users_list = list(chat_data["users"].keys())
    if not users_list:
        await update.message.reply_text("❌ В этом чате нет зарегистрированных участников!")
        return
        
    selected_id = random.choice(users_list)
    username = chat_data["users"][selected_id]
    full_name = f"{update.message.from_user.first_name} {update.message.from_user.last_name or ''}".strip()

    # Обновляем статистику
    chat_data["pidor_stats"][selected_id] = chat_data["pidor_stats"].get(selected_id, 0) + 1
    chat_data["last_pidor"] = {"user_id": selected_id, "date": today}
    save_data(data)
    await update.message.reply_text("ВНИМАНИЕ 🔥")
    time.sleep(1)
    await update.message.reply_text("ФЕДЕРАЛЬНЫЙ 🔍 РОЗЫСК ПИДОРА 🚨")
    time.sleep(1)
    await update.message.reply_text("4 - спутник запущен 🚀")
    time.sleep(1)
    await update.message.reply_text("3 - сводки Интерпола проверены 🚓")
    time.sleep(1)
    await update.message.reply_text("2 - твои друзья опрошены 🙅")
    time.sleep(1)
    await update.message.reply_text("1 - твой профиль в соцсетях проанализирован 🙀")
    time.sleep(1)
    await update.message.reply_text(f"🎉 Сегодня ПИДОР 🌈 дня - (@{username})!")

# Команда /stats
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    chat_data = get_chat_data(chat_id)
    
    if not chat_data["handsome_stats"]:
        await update.message.reply_text("❌ В этом чате еще нет статистики красавчиков!")
        return
        
    stats_lines = []
    for user_id, count in chat_data["handsome_stats"].items():
        username = chat_data["users"].get(user_id, "unknown")
        stats_lines.append(f"👑 @{username}: {count} раз")
    
    stats_lines.sort(key=lambda x: int(x.split(": ")[1].split()[0]), reverse=True)
    
    message = "🏆 Топ красавчиков этого чата:\n\n" + "\n".join(stats_lines[:10])
    await update.message.reply_text(message)

# Команда /pidorstats
async def pidorstats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    chat_data = get_chat_data(chat_id)
    
    if not chat_data["pidor_stats"]:
        await update.message.reply_text("❌ В этом чате еще нет статистики пидоров!")
        return
        
    stats_lines = []
    for user_id, count in chat_data["pidor_stats"].items():
        username = chat_data["users"].get(user_id, "unknown")
        stats_lines.append(f"🌈 @{username}: {count} раз")
    
    stats_lines.sort(key=lambda x: int(x.split(": ")[1].split()[0]), reverse=True)
    
    message = "🃏 Топ пидоров этого чата:\n\n" + "\n".join(stats_lines[:10])
    await update.message.reply_text(message)

# Установка команд бота
async def set_commands(application):
    commands = [
        BotCommand("start", "Показать доступные команды"),
        BotCommand("reg", "Зарегистрироваться в этом чате"),
        BotCommand("delete", "Удалить регистрацию из этого чата"),
        BotCommand("run", "Выбрать красавчика дня в этом чате"),
        BotCommand("pidor", "Выбрать пидора дня в этом чате"),
        BotCommand("stats", "Статистика красавчиков этого чата"),
        BotCommand("pidorstats", "Статистика пидоров этого чата")
    ]
    await application.bot.set_my_commands(commands)

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Обработчики команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reg", reg))
    app.add_handler(CommandHandler("delete", delete))
    app.add_handler(CommandHandler("run", run))
    app.add_handler(CommandHandler("pidor", pidor))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("pidorstats", pidorstats))
    
    # Установка команд при запуске
    app.post_init = set_commands
    
    print("Бот запущен...")
    app.run_polling()

if __name__ == '__main__':
    main()