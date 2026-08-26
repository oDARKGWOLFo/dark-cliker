import os
import time
import random
import asyncio
import requests

# ПРЯМАЯ ССЫЛКА НА ВАШ CONFIG.JSON НА GITHUB
RAW_CONFIG_URL = "https://githubusercontent.com"

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
    print("✅ Бот-воркер успешно запущен без использования Telegram API!")
    round_counter = 1
    
    while True:
        print(f"\n--- Круг №{round_counter} ---")
        
        # Обновляем конфиг перед каждым кругом, чтобы подхватывать новые ссылки на лету
        config = get_github_config()
        if not config:
            print("❌ Ошибка загрузки конфигурации с GitHub. Повтор через 20 секунд...")
            await asyncio.sleep(20)
            continue

        try:
            # Извлекаем список доноров (MINI_APPS_DONORS)
            donors = config.get("MINI_APPS_DONORS", [])
            if not donors:
                print("⚠️ Список MINI_APPS_DONORS пуст! Нечего открывать.")
                await asyncio.sleep(20)
                continue
            
            # Если в списке несколько ссылок, берем первую (или можно random.choice(donors))
            target_url = donors[0] if isinstance(donors, list) else donors

            # Имитируем заголовки реального мобильного браузера Android
            headers = {
                "User-Agent": "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
                "Connection": "keep-alive"
            }
            
            # 1. Отправляем запрос к сайту донора (имитируем заход в Mini App / открытие плеера)
            print(f"🌐 Подключение к источнику: {target_url}")
            response = requests.get(target_url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                print("🖱 Виртуальный клик выполнен. Сессия просмотра активна.")
            else:
                print(f"⚠️ Сайт-донор ответил с кодом: {response.status_code}")
            
            # 2. Ожидание от 120 до 180 секунд (имитация реального просмотра видео пользователем)
            view_time = random.randint(120, 180)
            print(f"⏳ Удержание страницы... Ожидание {view_time} секунд.")
            await asyncio.sleep(view_time)

            # 3. Закрываем текущий круг
            print("❌ Круг просмотра успешно завершен.")

            # 4. Пауза перед новым кругом — ровно 30 секунд
            print("💤 Ожидание 30 секунд перед переходом на следующий круг...")
            await asyncio.sleep(30)
            
            round_counter += 1

        except Exception as e:
            print(f"🔴 Ошибка во время выполнения круга: {e}")
            print("Перезапуск цикла через 15 секунд...")
            await asyncio.sleep(15)

# --- ЭТА ФУНКЦИЯ КРИТИЧЕСКИ ВАЖНА ДЛЯ ВАШЕГО MAIN_BOT.PY ---
def ran_auto_mining():
    print("🚀 Вызов функции ran_auto_mining из главного бота...")
    # Запуск асинхронного движка для бесконечного цикла
    asyncio.run(main())

if __name__ == "__main__":
    ran_auto_mining()
