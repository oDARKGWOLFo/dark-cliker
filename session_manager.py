import os

SESSIONS_DIR = "sessions"

def ensure_sessions_dir():
    """Создает папку для хранения сессий, если ее нет"""
    if not os.path.exists(SESSIONS_DIR):
        os.makedirs(SESSIONS_DIR)

def get_session_path(user_id):
    """Возвращает путь к файлу сессии конкретного пользователя"""
    ensure_sessions_dir()
    return os.path.join(SESSIONS_DIR, f"session_{user_id}.json")

def is_session_exists(user_id):
    """Проверяет, авторизовался ли уже пользователь в системе"""
    path = get_session_path(user_id)
    # Проверяем, существует ли файл и не пустой ли он
    return os.path.exists(path) and os.path.getsize(path) > 0
