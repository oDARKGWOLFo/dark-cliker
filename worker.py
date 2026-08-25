import asyncio
import json
import random
import httpx
from playwright.async_api import async_playwright
from database import update_balance, set_mining_status, get_user_data

# Жесткий лимит на 1 одновременный скрипт браузера для стабильности сервера
MAX_CONCURRENT_BROWSERS = asyncio.Semaphore(1)

def load_config():
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)

async def fetch_socks_proxy_url(proxy_url):
    """Автоматически вытягивает свежий мобильный IP по твоей ссылке ротации"""
    if not proxy_url or "your-proxy-provider" in proxy_url:
        return None
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(proxy_url, timeout=15)
            if response.status_code == 200:
                data = response.json()
                # Корректно берем первый элемент из списка прокси
                if isinstance(data, list) and len(data) > 0:
                    data = data[0]
                return {
                    "server": f"socks5://{data.get('host')}:{data.get('port')}",
                    "username": data.get("user"),
                    "password": data.get("pass")
                }
    except Exception as e:
        print(f"[ERROR] Ошибка загрузки SOCKS5: {e}")
        return None

async def run_auto_mining(user_id):
    """Главная функция запуска закрытого браузера под статьи"""
    async with MAX_CONCURRENT_BROWSERS:
        config = load_config()
        set_mining_status(user_id, 1)
        print(f"[WORKER] Запуск безопасной сессии для пользователя {user_id}")
        
        async with async_playwright() as p:
            # Скачиваем свежий мобильный IP перед стартом
            proxy_config = await fetch_socks_proxy_url(config['PROXY']['ROTATE_URL'])
            
            # Настройки оптимизации: отключаем картинки
            browser_args = ["--blink-settings=imagesEnabled=false"]
            
            if proxy_config:
                browser = await p.chromium.launch(headless=True, proxy=proxy_config, args=browser_args)
            else:
                browser = await p.chromium.launch(headless=True, args=browser_args)
                print("[WARNING] Работа напрямую через IP сервера без прокси.")
                
            context = await browser.new_context(viewport={"width": 375, "height": 812})
            page = await context.new_page()
            
            # Рандомная статья из конфига config.json
            links = config.get("ARTICLE_LINKS", [])
            if not links:
                print("[ERROR] Список ARTICLE_LINKS пуст!")
                await context.close()
                await browser.close()
                return
                
            target_url = random.choice(links)
            
            try:
                print(f"[BOT] Скрытый браузер открывает статью: {target_url}")
                await page.goto(target_url, timeout=45000)
                await page.wait_for_timeout(3000)
                
                print("[BOT] Имитирую чтение статьи человеком...")
                
                # Временное окно удержания трафика
                watch_time = random.randint(110, 390)
                elapsed_time = 0
                
                # Плавный скроллинг статьи на протяжении всего watch_time
                while elapsed_time < watch_time:
                    user_status = get_user_data(user_id)
                    
                    # Ваша проверка статуса перенесена сюда (внутрь try-блока)
                    if user_status.get("status") in ["stopped", "none", None] or user_status.get("status") != "is_mining":
                        print(f"[WORKER] Заработок для {user_id} не запущен в боте. Выходим.")
                        break
                        
                    # Крутим страницу вниз на случайное расстояние
                    scroll_step = random.randint(120, 280)
                    await page.mouse.wheel(0, scroll_step)
                    
                    # Делаем паузу между скроллами
                    sleep_step = random.uniform(4.0, 9.0)
                    await asyncio.sleep(sleep_step)
                    elapsed_time += sleep_step
                    
                # Проверяем статус перед начислением денег
                user_status = get_user_data(user_id)
                if user_status.get("status") == "is_mining":
                    reward_amount = 1.00
                    update_balance(user_id, reward_amount)
                    print(f"[БАЛАНС] Просмотр успешно засчитан! Начислено {reward_amount:.2f} Р")
                    
            except Exception as e:
                print(f"[ERROR] Критическая ошибка в потоке браузера: {e}")
                
            finally:
                # Чистим за собой память на сервере и закрываем вкладки
                await context.close()
                await browser.close()
                set_mining_status(user_id, 0)
                print(f"[WORKER] Безопасный поток для пользователя {user_id} полностью завершен!")
