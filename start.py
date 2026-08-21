import os
import sys
import subprocess

def create_folders():
    """Автоматически создает структуру папок на сервере"""
    folders = ["sessions"]
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"📁 Создана папка: {folder}")

def run_bot():
    """Запускает главного бота"""
    print("🚀 Инициализация системы...")
    create_folders()
    
    # Проверяем, существует ли файл конфигурации
    if not os.path.exists("config.json"):
        print("❌ Ошибка: Файл config.json не найден! Сначала создайте его на GitHub.")
        sys.exit(1)
        
    print("🤖 Запуск главного скрипта main_bot.py...")
    try:
        # Запускаем основной процесс бота
        subprocess.run(["python3", "main_bot.py"], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Система остановлена пользователем.")
    except Exception as e:
        print(f"❌ Критическая ошибка при работе бота: {e}")

if __name__ == "__main__":
    run_bot()
