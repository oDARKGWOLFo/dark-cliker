import sqlite3

DB_NAME = "mining_system.db"

def init_db():
    """Функция создает таблицы в базе данных при первом запуске"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Таблица пользователей: ID, баланс золота, статус майнинга (0 - выкл, 1 - вкл)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance REAL DEFAULT 0.0,
            is_mining INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def add_user(user_id):
    """Добавляет нового пользователя, если его еще нет в базе"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def get_user_data(user_id):
    """Получает баланс и статус майнинга пользователя"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT balance, is_mining FROM users WHERE user_id = ?", (user_id,))
    data = cursor.fetchone()
    conn.close()
    if data:
        return {"balance": data[0], "is_mining": data[1]}
    return {"balance": 0.0, "is_mining": 0}

def update_balance(user_id, amount):
    """Прибавляет золото к балансу пользователя за просмотр рекламы"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def set_mining_status(user_id, status):
    """Включает или выключает статус майнинга (1 или 0)"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_mining = ? WHERE user_id = ?", (status, user_id))
    conn.commit()
    conn.close()
