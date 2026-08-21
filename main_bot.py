import asyncio
import json
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Импортируем модули из прошлых частей
from database import init_db, add_user, get_user_data, set_mining_status
from session_manager import is_session_exists, get_session_path
from worker import run_auto_mining

# Загружаем токен бота из настроек config.json
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

BOT_TOKEN = config["TELEGRAM_BOT_TOKEN"]
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def get_main_keyboard(user_id):
    """Создает интерактивные кнопки меню"""
    builder = InlineKeyboardBuilder()
    user_data = get_user_data(user_id)
    
    # Меняем текст кнопки в зависимости от того, запущен майнинг прямо сейчас или нет
    if user_data["is_mining"] == 1:
        builder.add(types.InlineKeyboardButton(text="🛑 Остановить майнинг", callback_data="stop_mining"))
    else:
        builder.add(types.InlineKeyboardButton(text="🚀 Запустить авто-майнинг", callback_data="start_mining"))
        
    builder.add(types.InlineKeyboardButton(text="💰 Проверить Баланс", callback_data="check_balance"))
    builder.add(types.InlineKeyboardButton(text="🔑 Статус Авторизации", callback_data="check_auth"))
    
    # Выстраиваем кнопки в один столбец
    builder.adjust(1)
    return builder.as_markup()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Срабатывает при первом запуске бота пользователем"""
    user_id = message.from_user.id
    add_user(user_id) # Добавляем игрока в базу данных
    
    await message.answer(
        f"Привет, {message.from_user.first_name}!\n\n"
        "Добро пожаловать в панель управления авто-майнингом.\n"
        "Этот бот автоматически заходит в твои Mini Apps-доноры, "
        "имитирует действия человека и собирает видеорекламу Adsgram.\n\n"
        "Используй кнопки ниже для управления процессом:",
        reply_markup=get_main_keyboard(user_id)
    )

@dp.callback_query(lambda c: c.data == "start_mining")
async def process_start_mining(callback_query: types.CallbackQuery):
    """Срабатывает при нажатии на кнопку 'Запустить авто-майнинг'"""
    user_id = callback_query.from_user.id
    user_data = get_user_data(user_id)
    
    # 1. Проверяем, не запущен ли он уже
    if user_data["is_mining"] == 1:
        await callback_query.answer("⚠️ Майнинг уже выполняется в фоновом режиме!", show_alert=True)
        return
        
    # 2. Проверяем, загрузил ли пользователь файл сессии авторизации Telegram Web
    if not is_session_exists(user_id):
        session_file_name = f"session_{user_id}.json"
        await callback_query.message.answer(
            "❌ Ошибка запуска: отсутствует файл авторизации!\n\n"
            "Чтобы невидимый браузер на сервере мог зайти в Telegram Web от твоего лица, "
            f"тебе нужно загрузить в этот чат файл сессии с именем: `{session_file_name}`\n\n"
            "После загрузки файла нажмите кнопку запуска снова.",
            parse_mode="Markdown"
        )
        await callback_query.answer()
        return

    await callback_query.message.edit_text(
        "⏳ Фоновый автоматический майнинг запущен!\n"
        "Скрипт меняет IP через мобильные прокси и по очереди включает видеорекламу в твоих приложениях.\n"
        "Ожидайте начисления золота...",
        reply_markup=get_main_keyboard(user_id)
    )
    await callback_query.answer()
    
    # Запускаем фонового робота Playwright, чтобы сам бот не завис во время ожидания видеороликов
    asyncio.create_task(run_auto_mining(user_id))

@dp.callback_query(lambda c: c.data == "stop_mining")
async def process_stop_mining(callback_query: types.CallbackQuery):
    """Срабатывает при нажатии на кнопку 'Остановить майнинг'"""
    user_id = callback_query.from_user.id
    set_mining_status(user_id, 0) # Меняем статус в базе, робот worker.py увидит это на следующем шаге и выключится
    
    await callback_query.message.edit_text(
        "🛑 Сигнал на остановку отправлен. Робот завершит текущий просмотр и выключит браузер.",
        reply_markup=get_main_keyboard(user_id)
    )
    await callback_query.answer()

@dp.callback_query(lambda c: c.data == "check_balance")
async def process_check_balance(callback_query: types.CallbackQuery):
    """Срабатывает при нажатии на кнопку 'Проверить Баланс'"""
    user_id = callback_query.from_user.id
    user_data = get_user_data(user_id)
    
    status_text = "🟢 Активен" if user_data["is_mining"] == 1 else "🔴 Выключен"
    
    await callback_query.message.answer(
        f"💰 Твой личный игровой баланс:\n\n"
        f"🪙 Накоплено золота: {user_data['balance']} G\n"
        f"📊 Статус майнинга: {status_text}"
    )
    await callback_query.answer()

@dp.callback_query(lambda c: c.data == "check_auth")
async def process_check_auth(callback_query: types.CallbackQuery):
    """Срабатывает при нажатии на кнопку 'Статус Авторизации'"""
    user_id = callback_query.from_user.id
    if is_session_exists(user_id):
        await callback_query.message.answer("✅ Отлично! Файл сессии найден на сервере. Робот готов к работе.")
    else:
        session_file_name = f"session_{user_id}.json"
        await callback_query.message.answer(
            "⚠️ Файл сессии не найден.\n"
            f"Пожалуйста, загрузите документ с именем `{session_file_name}` в этот чат.",
            parse_mode="Markdown"
        )
    await callback_query.answer()

@dp.message(lambda message: message.document is not None)
async def handle_session_upload(message: types.Message):
    """Ловит отправленные файлы сессий и сохраняет их в нужную папку"""
    user_id = message.from_user.id
    document = message.document
    expected_name = f"session_{user_id}.json"
    
    # Проверяем, правильно ли пользователь назвал файл
    if document.file_name != expected_name:
        await message.answer(
            f"❌ Ошибка сохранения! Файл имеет неверное имя: `{document.file_name}`\n"
            f"Переименуй файл строго в: `{expected_name}` и отправь заново.",
            parse_mode="Markdown"
        )
        return
        
    # Скачиваем файл сессии на сервер в папку sessions/
    target_path = get_session_path(user_id)
    file_info = await bot.get_file(document.file_id)
    await bot.download_file(file_info.file_path, target_path)
    
    await message.answer(
        "🎉 Файл сессии успешно получен и сохранен на сервере!\n"
        "Теперь ты можешь нажать кнопку 'Запустить авто-майнинг'.",
        reply_markup=get_main_keyboard(user_id)
    )

async def main():
    # Инициализируем базу данных при запуске скрипта бота
    init_db()
    print("🤖 Главный Telegram-бот запущен и готов к работе...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
