import asyncio
import json
import random
import httpx
from database import set_mining_status, update_balance

def load_config():
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)

async def run_auto_mining(user_id):
    """Бесконечный серверный конвейер заработка через API Q32 без капчи и браузера"""
    set_mining_status(user_id, 1)
    print(f"[WORKER] Автономный API-конвейер Q32 успешно запущен для {user_id}")
    
    round_number = 1
    while True:
        print(f"\n=== СТАРТ КРУГА API №{round_number} ===")
        config = load_config()
        
        api_key = config.get("Q32_API_KEY", "")
        links = config.get("ARTICLE_LINKS", [])
        
        if not api_key or not links:
            print("[ERROR] Проверьте config.json! Отсутствует API ключ или ссылка на Blogger.")
            await asyncio.sleep(10)
            continue
            
        target_url = random.choice(links)
        
        # Собираем техническую служебную ссылку по инструкции Q32
        random_sub = random.randint(100000, 999999)
        
        # ВНИМАНИЕ: Проверьте формат по инструкции Q32. 
        # Если ключ передается как параметр, используйте вариант ниже:
        api_url = f"http://q32.ru{api_key}&url={target_url}&sub={random_sub}"
        
        # Если по инструкции ключ идет строго после слэша, раскомментируйте строку ниже, а строку выше удалите:
        # api_url = f"http://q32.ru{api_key}?url={target_url}&sub={random_sub}"

        try:
            print(f"[КРУГ {round_number}] Отправляем скрытый запрос на сервер Q32...")
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            
            async with httpx.AsyncClient(headers=headers) as client:
                # Сервер имитирует быстрый технический вызов
                response = await client.get(api_url, timeout=20)
                
                if response.status_code == 200:
                    result_text = response.text
                    print(f"[СЕРВЕР Q32] Ответ получен успешно!")
                    
                    # Начисляем 1 рубль на баланс внутри вашего бота
                    update_balance(user_id, 1.00)
                    print(f"[БАЛАНС БОТА] Круг №{round_number} засчитан. Начислено 1.00 ₽")
                else:
                    print(f"[ОШИБКА СЕТИ] Сервер Q32 вернул статус: {response.status_code}")
                    
        except Exception as e:
            # Исправлен вывод фактического текста ошибки в консоль
            print(f"[ERROR] Сбой во время запроса на круге {round_number}: {e}")
            
        # Пауза между кругами (от 20 до 40 секунд), чтобы система Q32 плавно фиксировала поток
        sleep_time = random.randint(20, 40)
        print(f"[ОТДЫХ] Ждем {sleep_time} сек. перед переходом на круг №{round_number + 1}...")
        await asyncio.sleep(sleep_time)
        round_number += 1
