import time
import random
import requests

def ran_auto_mining():
    print("✅ Бот-воркер успешно запущен без использования Telegram API!")
    url = "https://githubusercontent.com"
    round_counter = 1
    
    while True:
        print(f"\n--- Круг №{round_counter} ---")
        try:
            # Скачиваем ваш конфиг с GitHub
            response = requests.get(url, timeout=10)
            config = response.json()
            
            # Извлекаем ссылку из MINI_APPS_DONORS
            donors = config.get("MINI_APPS_DONORS", [])
            if not donors:
                print("⚠️ Список MINI_APPS_DONORS пуст!")
                time.sleep(20)
                continue
                
            target_url = donors[0] if isinstance(donors, list) else donors
            print(f"🌐 Подключение к источнику: {target_url}")
            
            # Имитируем заход на сайт
            headers = {"User-Agent": "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36"}
            requests.get(target_url, headers=headers, timeout=15)
            print("鼠标 Виртуальный клик выполнен. Сессия просмотра активна.")
            
            # Таймер удержания от 120 до 180 секунд
            view_time = random.randint(120, 180)
            print(f"⏳ Удержание страницы... Ожидание {view_time} секунд.")
            time.sleep(view_time)
            
            print("❌ Круг просмотра успешно завершен.")
            print("💤 Ожидание 30 секунд перед переходом на следующий круг...")
            time.sleep(30)
            round_counter += 1
            
        except Exception as e:
            print(f"🔴 Ошибка во время выполнения круга: {e}")
            time.sleep(15)

if __name__ == "__main__":
    ran_auto_mining()
