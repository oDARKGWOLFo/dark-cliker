import time, random, requests

def ran_auto_mining():
    print("✅ Бот-воркер успешно запущен!")
    url = "https://raw.githubusercontent.com/oDARKGWoLFo/dark-cliker/main/config.json"
    rc = 1
    while True:
        print(f"\n--- Круг {rc} ---")
        try:
            cfg = requests.get(url, timeout=10).json()
            lnk = cfg.get("MINI_APPS_DONORS", [])
            if not lnk:
                print("⚠️ Список доноров пуст!")
                time.sleep(20)
                continue
            target = lnk[0] if isinstance(lnk, list) else lnk
            print(f"🌐 Подключение: {target}")
            requests.get(target, timeout=15)
            print("鼠标 Клик выполнен.")
            vt = random.randint(120, 180)
            print(f"⏳ Ожидание {vt} секунд.")
            time.sleep(vt)
            print("❌ Круг завершен. Пауза 30 секунд...")
            time.sleep(30)
            rc += 1
        except Exception as e:
            print(f"🔴 Ошибка: {e}")
            time.sleep(15)
