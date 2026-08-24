cat << 'EOF' > worker.py
import asyncio
import json
import random
import httpx
from playwright.async_api import async_playwright
from database import update_balance, set_mining_status, get_user_data

# Жесткий лимит на 3 одновременных скрытых браузера для стабильности сервера
MAX_CONCURRENT_BROWSERS = asyncio.Semaphore(3)

def load_config():
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)

async def fetch_asocks_proxy(url):
    """Автоматически вытягивает свежий сотовый IP по твоей ссылке Asocks"""
    if not url or "proxy-provider.com" in url:
        return None
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    proxy_info = data
                    return {
                        "server": f"http://{proxy_info.get('host')}:{proxy_info.get('port')}",
                        "username": proxy_info.get("user"),
                        "password": proxy_info.get("pass")
                    }
    except Exception as e:
        print(f"❌ [ПРОКСИ] Ошибка загрузки Asocks: {e}")
    return None

async def run_auto_mining(user_id):
    """Главная функция запуска закрытого браузера под Матрешку ТВ"""
    # Если 3 места уже заняты другими, новые пользователи встанут в безопасную очередь
    async with MAX_CONCURRENT_BROWSERS:
        config = load_config()
        set_mining_status(user_id, 1)
        print(f"🚀 [ВИДЕО-КОНВЕЙЕР] Запущен безопасный поток для пользователя {user_id}")
EOF
cat << 'EOF' >> worker.py

        async with async_playwright() as p:
            try:
                # Скачиваем свежий мобильный IP перед стартом
                proxy_config = await fetch_asocks_proxy(config["PROXY"]["ROTATE_URL"])
                
                # Настройки оптимизации: отключаем картинки, чтобы не тратить мегабайты прокси
                browser_args = ["--blink-settings=imagesEnabled=false"]
                
                # Запускаем настоящий СКРЫТЫЙ браузер
                if proxy_config:
                    browser = await p.chromium.launch(headless=True, proxy=proxy_config, args=browser_args)
                    print(f"🛡️ [ЗАЩИТА] Скрытый браузер запущен под мобильным IP вышки РФ.")
                else:
                    browser = await p.chromium.launch(headless=True, args=browser_args)
                    print("⚠️ [ВНИМАНИЕ] Работа напрямую через IP сервера без прокси.")

                context = await browser.new_context(viewport={"width": 375, "height": 812})
                page = await context.new_page()

                # Обходим ссылки на видео из нашего config.json
                for video_url in config["VIDEO_LINKS"]:
                    # Проверяем, не нажал ли юзер кнопку 'Стоп' во время просмотра
                    user_status = get_user_data(user_id)
                    if user_status["is_mining"] == 0:
                        break

                    print(f"🤖 Скрытый браузер открывает видео: {video_url}")
                    
                    try:
                        # Переходим на сайт Матрешки ТВ
                        await page.goto(video_url, timeout=45000)
                        await page.wait_for_timeout(5000)

                        # Имитируем клик по центру экрана, чтобы включить плеер без автоплея
                        print("▶️ Кликаю по плееру для запуска трансляции...")
                        await page.mouse.click(187, 300)
                        await page.wait_for_timeout(3000)

                        # ТВОЯ НАСТРОЙКА: Рандомное время удержания от 120 до 180 секунд
                        watch_time = random.randint(120, 180)
                        print(f"⏳ Видео пошло. Удерживаю вкладку ровно {watch_time} сек для беспалевной накрутки...")
                        await asyncio.sleep(watch_time)

                        # Проверяем статус 'Стоп' перед начислением денег
                        user_status = get_user_data(user_id)
                        if user_status["is_mining"] == 0:
                            break

                        # Начисляем пользователю в боте 1.00 рубль за длинный просмотр
                        reward_amount = 1.00
                        update_balance(user_id, reward_amount)
                        print(f"🪙 [БАЛАНС] Просмотр успешно засчитан! Начислено +{reward_amount:.2f} ₽")

                    except Exception as e:
                        print(f"❌ Ошибка на странице видео: {e}")

                # Чистим за собой память сервера и закрываем вкладки
                await context.close()
                await browser.close()

            except Exception as e:
                print(f"❌ Критическая ошибка в потоке браузера: {e}")
            finally:
                # Гарантированно выключаем статус майнинга для юзера
                set_mining_status(user_id, 0)
                print(f"🎉 [ФИНИШ] Безопасный поток для пользователя {user_id} полностью завершен!")
EOF
