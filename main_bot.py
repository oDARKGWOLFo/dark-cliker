import asyncio
import json
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# Импортируем модули из прошлых частей
from database import init_db, add_user, get_user_data, set_mining_status, update_balance
from session_manager import is_session_exists, get_session_path
from worker import run_auto_mining

with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

BOT_TOKEN = config["8917279281:AAFZKSHlh2oD1IJe824oPLlr_gEaUk8ALTY"]
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ТВОЙ СЕКРЕТНЫЙ КАНАЛ ДЛЯ ЗАЯВОК (Число с минусом)
ADMIN_CHANNEL_ID = -1004483178970  # ЗАМЕНИ ЭТИ ЦИФРЫ НА ID СВОЕГО КАНАЛА!

# Описываем шаги диалога для вывода средств
class WithdrawStates(StatesGroup):
    wait_method = State()  # Ожидание выбора способа (СБП / Карта)
    wait_amount = State()  # Ожидание ввода суммы для вывода
    wait_details = State() # Ожидание ввода реквизитов

def get_main_keyboard(user_id):
    """Создает сетку из 5 строк кнопок для заработка и вывода"""
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="💸 Запустить авто-заработок", callback_data="start_mining"))
    builder.add(types.InlineKeyboardButton(text="🛑 Остановить заработок", callback_data="stop_mining"))
    builder.add(types.InlineKeyboardButton(text="💰 Мой Баланс", callback_data="check_balance"))
    builder.add(types.InlineKeyboardButton(text="⚙️ Статус синхронизации", callback_data="check_auth"))
    builder.add(types.InlineKeyboardButton(text="💳 Вывод средств", callback_data="withdraw_funds"))
    builder.adjust(1) # Строго по одной кнопке в ряд
    return builder.as_markup()

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    """Приветственное меню авто-заработка"""
    await state.clear()
    user_id = message.from_user.id
    add_user(user_id)
    
    await message.answer(
        f"👋 Рады видеть тебя, {message.from_user.first_name}!\n\n"
        "Добро пожаловать в автоматическую систему удаленного заработка.\n"
        "Тебе больше не нужно тратить свое время на клики или выполнение сложных заданий — наши умные алгоритмы сделают всё за тебя полностью удаленно в облаке 24/7.\n\n"
        "Просто нажимай кнопку ниже, включай авто-заработок и забирай реальные рубли!",
        reply_markup=get_main_keyboard(user_id)
    )

@dp.callback_query(lambda c: c.data == "start_mining")
async def process_start_mining(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user_data = get_user_data(user_id)
    
    if user_data["is_mining"] == 1:
        await callback_query.answer("⚠️ Авто-заработок уже активно выполняется в фоновом режиме!", show_alert=True)
        return
        
    session_path = get_session_path(user_id)
    if not is_session_exists(user_id):
        with open(session_path, "w", encoding="utf-8") as f:
            json.dump({"cookies": [], "origins": []}, f)

    await callback_query.message.answer(
        "⚡ Синхронизация с облачным сервером успешна!\n\n"
        "💸 Процесс автоматического заработка запущен. Наша удаленная система обрабатывает данные и генерирует баланс прямо на твой счет.\n"
        "Ты можешь полностью закрыть бота или выключить телефон — процесс не остановится.",
        reply_markup=get_main_keyboard(user_id)
    )
    await callback_query.answer()
    asyncio.create_task(run_auto_mining(user_id))
@dp.callback_query(lambda c: c.data == "stop_mining")
async def process_stop_mining(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user_data = get_user_data(user_id)
    
    if user_data["is_mining"] == 0:
        await callback_query.answer("⚠️ Система заработка уже отключена.", show_alert=True)
        return

    set_mining_status(user_id, 0)
    await callback_query.message.answer(
        "🛑 Подана команда на отключение системы. Авто-заработок будет полностью остановлен в течение нескольких секунд.",
        reply_markup=get_main_keyboard(user_id)
    )
    await callback_query.answer()

@dp.callback_query(lambda c: c.data == "check_balance")
async def process_check_balance(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user_data = get_user_data(user_id)
    status_text = "🟢 Включен (Идет доход)" if user_data["is_mining"] == 1 else "🔴 Выключен"
    
    await callback_query.message.answer(
        f"💰 Твой личный игровой баланс:\n\n"
        f"💵 Накоплено средств: {user_data['balance']:.2f} ₽\n"
        f"📊 Авто-заработок: {status_text}",
        reply_markup=get_main_keyboard(user_id)
    )
    await callback_query.answer()

@dp.callback_query(lambda c: c.data == "check_auth")
async def process_check_auth(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    if is_session_exists(user_id):
        await callback_query.message.answer("✅ Твой аккаунт успешно синхронизирован с облачным сервером и полностью готов к авто-заработку.", reply_markup=get_main_keyboard(user_id))
    else:
        await callback_query.message.answer("⚠️ Связь с сервером не установлена.", reply_markup=get_main_keyboard(user_id))
    await callback_query.answer()

@dp.callback_query(lambda c: c.data == "withdraw_funds")
async def process_withdraw_start(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    user_data = get_user_data(user_id)
    
    min_limit = 100.0
    if user_data["balance"] < min_limit:
        await callback_query.answer(f"❌ Ошибка вывода! Минимальная сумма для выплаты составляет {min_limit} ₽. У тебя сейчас: {user_data['balance']:.2f} ₽", show_alert=True)
        return
        
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="📲 Способ 1: СБП", callback_data="pay_sbp"))
    builder.add(types.InlineKeyboardButton(text="💳 Способ 2: На карту", callback_data="pay_card"))
    builder.adjust(1)
    
    await callback_query.message.answer(
        "💳 Выберите удобный способ вывода средств из системы:",
        reply_markup=builder.as_markup()
    )
    await state.set_state(WithdrawStates.wait_method)
    await callback_query.answer()

@dp.callback_query(lambda c: c.data in ["pay_sbp", "pay_card"], WithdrawStates.wait_method)
async def process_withdraw_method(callback_query: types.CallbackQuery, state: FSMContext):
    method = "СБП" if callback_query.data == "pay_sbp" else "Банковская карта"
    await state.update_data(withdraw_method=method)
    
    user_id = callback_query.from_user.id
    user_data = get_user_data(user_id)
    
    await callback_query.message.answer(
        f"Указан способ: *{method}*\n\n"
        f"Доступно для списания: {user_data['balance']:.2f} ₽\n"
        "Введите сумму в рублях, которую вы хотите вывести (число):",
        parse_mode="Markdown"
    )
    await state.set_state(WithdrawStates.wait_amount)
    await callback_query.answer()

@dp.message(WithdrawStates.wait_amount)
async def process_withdraw_amount(message: types.Message, state: FSMContext):
    amount_text = message.text.strip()
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    
    try:
        amount = float(amount_text)
    except ValueError:
        await message.answer("❌ Ошибка ввода! Пожалуйста, укажите сумму числом:")
        return
        
    if amount <= 0:
        await message.answer("❌ Сумма должна быть больше нуля! Попробуй еще раз:")
        return
        
    if amount > user_data["balance"]:
        await message.answer(f"❌ Недостаточно средств! Баланс: {user_data['balance']:.2f} ₽. Введите сумму заново:")
        return
        
    await state.update_data(withdraw_amount=amount)
    fsm_data = await state.get_data()
    method = fsm_data["withdraw_method"]
    
    if method == "СБП":
        await message.answer(
            "📞 Категория выбора: СБП (Система Быстрых Платежей).\n\n"
            "Пожалуйста, введите номер телефона получателя и название банка (например: +79991234567, Сбербанк):"
        )
    else:
        await message.answer(
            "💳 Категория выбора: Банковская карта.\n\n"
            "Пожалуйста, введите 16-значный номер вашей карты (без пробелов):"
        )
    await state.set_state(WithdrawStates.wait_details)

@dp.message(WithdrawStates.wait_details)
async def process_withdraw_final(message: types.Message, state: FSMContext):
    details = message.text.strip()
    user_id = message.from_user.id
    
    if message.from_user.username:
        user_contact = f"@{message.from_user.username}"
    else:
        user_contact = f"ID: {user_id}"
    
    fsm_data = await state.get_data()
    method = fsm_data["withdraw_method"]
    amount = fsm_data["withdraw_amount"]
    
    if method == "Банковская карта" and (not details.isdigit() or len(details) < 15):
        await message.answer("❌ Номер карты указан некорректно! Попробуй еще раз:")
        return

    update_balance(user_id, -amount)
    
    admin_invoice = (
        f"🚨 *НОВАЯ ЗАЯВКА НА ВЫПЛАТУ*\n\n"
        f"👤 *Пользователь:* {user_contact}\n"
        f"💰 *Сумма к выдаче:* {amount:.2f} ₽\n"
        f"💳 *Способ перевода:* {method}\n"
        f"📌 *Реквизиты:* `{details}`\n"
    )
    
    try:
        await bot.send_message(
            chat_id=ADMIN_CHANNEL_ID,
            text=admin_invoice,
            parse_mode="Markdown"
        )
        print(f"📡 Заявка от {user_id} на {amount} руб успешно переслана в админ-канал.")
    except Exception as e:
        print(f"❌ Ошибка отправки заявки в канал: {e}")

    await message.answer(
        "🎉 Заявка на вывод средств успешно создана!\n\n"
        f"📊 Квитанция операции:\n"
        f"🔹 Способ: {method}\n"
        f"🔹 Реквизиты: `{details}`\n"
        f"🔹 Списано: {amount:.2f} ₽\n\n"
        "⌛ Заявка отправлена в финансовый отдел и будет обработана в течение 24 часов.",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard(user_id)
    )
    await state.clear()

async def main():
    init_db()
    print("🤖 Бот запущен! Все модули работают исправно.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
