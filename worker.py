import asyncio
import json
import random
import httpx
from playwright.async_api import async_playwright
# Импортируем функции из Части 2
from database import update_balance, set_mining_status, get_user_data
from session_manager import get_session_path

def load_config():
    """Загружает настройки из файла config.json"""
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)

async def rotate_ip(rotate_url):
    """Отправляет запрос провайдеру на автоматическую смену IP-адреса"""
    if not rotate_url or "proxy-provider.com" in rotate_url:
        print("⚠️ Ссылка для смены IP не настроена в config.json. Пропускаю.")
        return
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(rotate_url, timeout=10)
            print(f"🔄 Запрос на смену IP отправлен. Ответ сервера: {response.status_code}")
            # Даем мобильному оператору 4 секунды, чтобы переключить вышку
            await asyncio.sleep(4)
    except Exception as e:
        print(f"❌ Не удалось обновить IP: {e}")

async def run_auto_mining(user_id):
    """Основной цикл обхода твоих Mini Apps и просмотра видеорекламы"""
    config = load_config()
    session_path = get_session_path(user_id)
    
    # Ставим статус в базе данных: майнинг запущен
    set_mining_status(user_id, 1)
    
    # Настраиваем прокси для браузера
    proxy_config = None
    if config["PROXY"]["SERVER"] and "proxy_ip" not in config["PROXY"]["SERVER"]:
        proxy_config = {
            "server": config["PROXY"]["SERVER"],
            "username": config["PROXY"]["USERNAME"],
            "password": config["PROXY"]["PASSWORD"]
        }

    async with async_playwright() as p:
        # Запускаем скрытый браузер Chromium на сервере
        browser = await p.chromium.launch(headless=True, proxy=proxy_config)
        
        try:
            # Загружаем сохраненные куки авторизации пользователя в Telegram
            context = await browser.new_context(storage_state=session_path)
            page = await context.new_page()
        except Exception as e:
            print(f"❌ Ошибка загрузки сессии для пользователя {user_id}: {e}")
            set_mining_status(user_id, 0)
            await browser.close()
            return

        # Обходим каждого созданного тобой бота по очереди
        for bot_username in config["MINI_APPS_DONORS"]:
            # Проверяем, не нажал ли пользователь кнопку 'Остановить' в Главном боте
            user_status = get_user_data(user_id)
            if user_status["is_mining"] == 0:
                print(f"🛑 Пользователь {user_id} принудительно остановил майнинг.")
                break

            print(f"🤖 Перехожу в Mini App бота: @{bot_username}")
            
            # Принудительно меняем IP перед входом в новое приложение
            await rotate_ip(config["PROXY"]["ROTATE_URL"])

            # Прямая ссылка на открытие Mini App внутри Telegram Web
            app_url = f"https://telegram.org{bot_username}"
            
            try:
                await page.goto(app_url, timeout=30000)
                await page.wait_for_timeout(6000) # Ждем загрузки интерфейса Telegram Web
                
                # Автоматически нажимаем кнопку запуска WebApp (Launch / Ок), если Telegram просит подтверждение
                confirm_button = page.locator("button:has-text('Launch'), button:has-text('Start'), button:has-text('Ок'), button:has-text('Proceed')")
                if await confirm_button.is_visible():
                    await confirm_button.click()
                    await page.wait_for_timeout(4000)

                print("📺 Ищу кнопку запуска видеорекламы Adsgram внутри Mini App...")
                
                # Робот ищет кнопку просмотра видео на экране Mini App.
                # Текст на кнопке в твоих Mini App-донорах должен быть одним из этих вариантов.
                watch_button = page.locator("button:has-text('Смотреть видео'), button:has-text('Watch Video'), button:has-text('Claim Reward'), .mining-btn")
                
                if await watch_button.is_visible():
                    await watch_button.click()
                    print("▶️ Кнопка видео нажата. Видео плеер Adsgram запущен.")
                    
                    # Видео в Adsgram длится от 15 до 30 секунд. 
                    # Даем ему доиграть до конца + делаем случайную паузу для имитации человека
                    watch_time = random.randint(32, 38)
                    await asyncio.sleep(watch_time)
                    
                    # Реклама просмотрена! Начисляем награду (например, 0.0.5 ₽) в базу данных
                    reward_amount = 0.0.5
                    update_balance(user_id, reward_amount)
                    print(f"🪙 Начислено {reward_amount} Рублей пользователю {user_id} за просмотр.")
                else:
                    print("⚠️ Кнопка просмотра видео не найдена на экране приложения. Возможно, интерфейс не загрузился.")
                
            except Exception as e:
                print(f"❌ Ошибка при обработке Mini App @{bot_username}: {e}")
            
            # Делаем паузу между переключениями приложений (от 4 до 8 секунд)
            await asyncio.sleep(random.randint(4, 8))

        # После обхода всех ботов закрываем браузер и выключаем статус майнинга
        await context.close()
        await browser.close()
        set_mining_status(user_id, 0)
        print(f"🎉 Майнинг-сессия для пользователя {user_id} полностью завершена.")
