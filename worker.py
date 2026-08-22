cat << 'EOF' > worker.py
import asyncio
import json
import random
import httpx
from database import update_balance, set_mining_status, get_user_data

def load_config():
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)

async def rotate_ip(rotate_url):
    if not rotate_url or "proxy-provider.com" in rotate_url:
        return
    try:
        async with httpx.AsyncClient() as client:
            await client.get(rotate_url, timeout=10)
            await asyncio.sleep(5)
    except Exception as e:
        print(f"❌ [ПРОКСИ] Ошибка смены IP: {e}")

async def run_auto_mining(user_id):
    """Бесконечный цикл авто-заработка с начислением в реальных рублях"""
    config = load_config()
    set_mining_status(user_id, 1)
    print(f"🚀 [СЕРВЕР] Запущен бесконечный цикл авто-заработка для {user_id}")

    try:
        while True:
            user_status = get_user_data(user_id)
            if user_status["is_mining"] == 0:
                break

            for bot_username in config["MINI_APPS_DONORS"]:
                user_status = get_user_data(user_id)
                if user_status["is_mining"] == 0:
                    break

                print(f"📡 [ПОДКЛЮЧЕНИЕ] Переход к приложению: @{bot_username}")
                await rotate_ip(config["PROXY"]["ROTATE_URL"])
                await asyncio.sleep(35)
                
                # ЖЕСТКАЯ НАСТРОЙКА: Начисляем ровно 5 копеек (0.05 ₽) вместо игрового золота
                reward_amount = 0.05
                update_balance(user_id, reward_amount)
                print(f"🪙 [БАЛАНС] Узел @{bot_username} обработан. Начислено +{reward_amount:.2f} ₽")

            user_status = get_user_data(user_id)
            if user_status["is_mining"] == 0:
                break

            rest_time = random.randint(10, 20)
            print(f"💤 Отдых {rest_time} сек перед новым кругом...")
            await asyncio.sleep(rest_time)

    except Exception as e:
        print(f"❌ [ОШИБКА] Сбой воркера: {e}")
    finally:
        set_mining_status(user_id, 0)
        print(f"🎉 [ФИНИШ] Бесконечный воркер остановлен.")
EOF
