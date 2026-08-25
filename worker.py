import asyncio
import json
import random
import httpx
from playwright.async_api import async_playwright
from database import update_balance, set_mining_status, get_user_data

# Лимит на 1 одновременный браузер
MAX_CONCURRENT_BROWSERS = asyncio.Semaphore(1)

def load_config():
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)

async def fetch_socks_proxy_url(proxy_url):
    """Сбор свежего IP из списка ASocks перед каждым кругом"""
    if not proxy_url or "your-proxy-provider" in proxy_url:
        return None
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(proxy_url, timeout=15)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    proxy_data = data[0]
                else:
                    proxy_data = data
                return {
                    "server": f"http://{proxy_data.get('host')}:{proxy_data.get('port')}",
                    "username": proxy_data.get("login"),
                    "password": proxy_data.get("password")
                }
    except Exception as e:
        print(f"[ERROR] Ошибка загрузки SOCKS5: {e}")
        return None

async def run_auto_mining(user_id):
    """Бесконечный конвейер: крутит статьи, меняет IP и уходит на новый круг"""
    async with MAX_CONCURRENT_BROWSERS:
        set_mining_status(user_id, 1)
        print(f"[WORKER] Запуск бесконечного конвейера для пользователя {user_id}")
        
        # НАЧАЛО БЕСКОНЕЧНОГО ЦИКЛА (КРУГИ НАКРУТКИ)
        round_number = 1
        while True:
            print(f"\n🚀 === НАЧАЛО КРУГА №{round_number} ===")
            config = load_config()
            
            async with async_playwright() as p:
                # 1. Обновляем IP через ASocks для нового круга
                print("[PROXY] Запрос свежего мобильного IP-адреса...")
                proxy_config = await fetch_socks_proxy_url(config['PROXY']['ROTATE_URL'])
                browser_args = ["--blink-settings=imagesEnabled=false"]
                
                if proxy_config:
                    browser = await p.chromium.launch(headless=True, proxy=proxy_config, args=browser_args)
                    print(f"[PROXY] Успешно подключен новый IP: {proxy_config['server']}")
                else:
                    browser = await p.chromium.launch(headless=True, args=browser_args)
                    print("[WARNING] Работа напрямую без прокси (не удалось получить IP).")
                    
                context = await browser.new_context(viewport={"width": 375, "height": 812})
                page = await context.new_page()
                
                links = config.get("ARTICLE_LINKS", [])
                if not links:
                    print("[ERROR] Список ARTICLE_LINKS пуст! Ждем 10 секунд и проверяем снова...")
                    await context.close()
                    await browser.close()
                    await asyncio.sleep(10)
                    continue
                    
                target_url = random.choice(links)
                
                try:
                    # 2. Заходим на страницу
                    print(f"[BOT] Открываем статью: {target_url}")
                    await page.goto(target_url, timeout=60000, wait_until="domcontentloaded")
                    await page.wait_for_timeout(5000)
                except Exception as e:
                    print(f"[⚠️ СЕТЬ] Ошибка загрузки страницы ({e}), но продолжаем удержание ради маскировки.")
                    
                try:
                    # 3. Имитируем чтение человеком (скроллинг)
                    watch_time = random.randint(120, 240)  # Удержание от 2 до 4 минут на статью
                    elapsed_time = 0
                    print(f"[BOT] Начинаем плавное чтение на {watch_time} секунд...")
                    
                    while elapsed_time < watch_time:
                        scroll_step = random.randint(100, 250)
                        await page.mouse.wheel(0, scroll_step)
                        
                        sleep_step = random.uniform(5.0, 10.0)
                        await asyncio.sleep(sleep_step)
                        elapsed_time += sleep_step
                        print(f"[КРУГ {round_number}] Прокрутка... Прошло: {int(elapsed_time)}/{watch_time} сек.")
                        
                    # 4. Начисляем баланс за успешно пройденный круг
                    reward_amount = 1.00
                    update_balance(user_id, reward_amount)
                    print(f"[БАЛАНС] Круг №{round_number} завершен! Начислено {reward_amount:.2f} Р")
                        
                except Exception as e:
                    print(f"[ERROR] Ошибка внутри цикла чтения на круге {round_number}: {e}")
                    
                finally:
                    # 5. Закрываем браузер, чтобы полностью сбросить сессию и куки перед сменой IP
                    print(f"[WORKER] Закрываем браузер круга №{round_number} для очистки кэша.")
                    await context.close()
                    await browser.close()
            
            # Пауза перед тем, как запросить новый IP и пойти на следующий круг
            rest_time = random.randint(15, 30)
            print(f"[ОТДЫХ] Ждем {rest_time} сек. перед переходом на круг №{round_number + 1}...")
            await asyncio.sleep(rest_time)
            round_number += 1
            
