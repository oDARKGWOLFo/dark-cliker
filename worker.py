cat << 'EOF' > worker.py
import os
import time
import random
import asyncio
from pyrogram import Client
from pyrogram.raw.functions.messages import RequestAppWebView
from pyrogram.raw.types import InputBotAppShortName
import requests

# ПРЯМАЯ ССЫЛКА НА ВАШ CONFIG.JSON НА GITHUB
# (Нажмите кнопку "Raw" на GitHub и скопируйте получившийся URL)
RAW_CONFIG_URL = "https://githubusercontent.com"

# --- ЛИЧНЫЕ НАСТРОЙКИ ДЛЯ СЕССИИ TELEGRAM ---
# Получите их один раз на сайте my.telegram.org для авторизации вашего аккаунта
API_ID = 1234567                 
API_HASH = "your_api_hash_here"  
APP_SHORT_NAME = "app"           # Короткое имя Mini App из BotFather

def get_github_config():
    """Скачивает конфиг с GitHub"""
    try:
        response = requests.get(RAW_CONFIG_URL, timeout=10)
        if response.status_code == 200:
            return response.json()
        print(f"⚠️ Не удалось прочитать конфиг с GitHub. Код: {response.status_code}")
    except Exception as e:
        print(f"🔴 Ошибка при запросе к GitHub: {e}")
    return None

async def main():
    # Загружаем настройки первый раз для проверки
    config = get_github_config()
    if not config:
        print("❌ Ошибка загрузки начальной конфигурации. Скрипт остановлен.")
        return

    # Запускаем клиент Pyrogram под вашим аккаунтом
    async with Client("my_account", api_id=API_ID, api_hash=API_HASH) as app:
        print("✅ Авторизация в аккаунте успешна! Бот-воркер запущен.")
        round_counter = 1
        
        while True:
            print(f"\n--- Круг №{round_counter} ---")
            
            # Обновляем конфиг перед каждым кругом, чтобы подхватывать изменения на лету
            live_config = get_github_config()
            if live_config:
                config = live_config

            try:
                # Получаем токен бота из конфига GitHub
                bot_token = config.get("TELEGRAM_BOT_TOKEN")
                if not bot_token:
                    print("⚠️ В конфиге GitHub отсутствует TELEGRAM_BOT_TOKEN!")
                    await asyncio.sleep(10)
                    continue
                
                # Извлекаем Username бота из его токена (первая часть до двоеточия)
                # Это избавит от необходимости писать Username вручную
                bot_id = bot_token.split(":")[0]
                
                # Извлекаем список доноров
                donors = config.get("MINI_APPS_DONORS", [])
                if not donors:
                    print("⚠️ Список MINI_APPS_DONORS пуст! Нечего открывать.")
                    await asyncio.sleep(10)
                    continue
                
                # Берем первую ссылку из списка доноров
                target_url = donors[0]

                # 1. Программно открываем Mini App в Telegram для авторизации
                peer = await app.resolve_peer(int(bot_id))
                app_short = InputBotAppShortName(bot_id=peer, short_name=APP_SHORT_NAME)
                
                await app.invoke(
                    RequestAppWebView(
                        peer=peer,
                        app=app_short,
                        platform="android",
                        write_allowed=True
                    )
                )
                print(f"🔗 Успешно авторизовались в Mini App бота с ID: {bot_id}")

                # 2. Имитируем переход встроенного браузера по ссылке донора
                headers = {
                    "User-Agent": "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
                }
                
                response = requests.get(target_url, headers=headers, timeout=15)
                if response.status_code == 200:
                    print(f"鼠标 Виртуальный клик выполнен. Страница открыта: {target_url}")
                
                # 3. Ожидание от 120 до 180 секунд (симуляция удержания экрана пользователем)
                view_time = random.randint(120, 180)
                print(f"⏳ Удержание страницы... Ожидание {view_time} секунд.")
                await asyncio.sleep(view_time)

                # 4. Закрываем текущую сессию
                print("❌ Круг просмотра завершен.")

                # 5. Пауза перед новым кругом — 30 секунд
                print("💤 Ожидание 30 секунд перед новым запуском...")
                await asyncio.sleep(30)
                
                round_counter += 1

            except Exception as e:
                print(f"🔴 Ошибка в работе цикла: {e}")
                print("Перезапуск через 15 секунд...")
                await asyncio.sleep(15)

if __name__ == "__main__":
    asyncio.run(main())
EOF
