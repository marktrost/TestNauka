# init_db.py
import sqlite3

conn = sqlite3.connect("ent.db")
cur = conn.cursor()

# ВКЛЮЧАЕМ поддержку внешних ключей
cur.execute("PRAGMA foreign_keys = ON")

# --- Блоки (например, Физика-Математика, Химия-Биология)
cur.execute("""
CREATE TABLE IF NOT EXISTS blocks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
)
""")

# --- Варианты внутри блока
cur.execute("""
CREATE TABLE IF NOT EXISTS variants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    block_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    FOREIGN KEY (block_id) REFERENCES blocks(id) ON DELETE CASCADE
)
""")

# --- Предметы внутри варианта
cur.execute("""
CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    variant_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    FOREIGN KEY (variant_id) REFERENCES variants(id) ON DELETE CASCADE
)
""")

# --- Вопросы внутри предмета
cur.execute("""
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER NOT NULL,
    text TEXT NOT NULL,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
)
""")

# --- Варианты ответов для вопроса
cur.execute("""
CREATE TABLE IF NOT EXISTS answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER NOT NULL,
    text TEXT NOT NULL,
    is_correct BOOLEAN NOT NULL DEFAULT 0,
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
)
""")

# --- Пользователи ---
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

# --- Результаты тестов ---
cur.execute("""
CREATE TABLE IF NOT EXISTS test_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    variant_id INTEGER NOT NULL,
    score INTEGER NOT NULL,
    total_questions INTEGER NOT NULL,
    percentage REAL NOT NULL,
    time_spent INTEGER NOT NULL,
    completed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (variant_id) REFERENCES variants(id)
)
""")

# --- Прогресс по предметам ---
cur.execute("""
CREATE TABLE IF NOT EXISTS subject_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    subject_name TEXT NOT NULL,
    total_answered INTEGER DEFAULT 0,
    correct_answered INTEGER DEFAULT 0,
    last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(user_id, subject_name)
)
""")

# Добавляем несколько примеров для тестирования
# Пример блока
cur.execute("INSERT OR IGNORE INTO blocks (name) VALUES (?)", ("Физика-Математика",))
cur.execute("INSERT OR IGNORE INTO blocks (name) VALUES (?)", ("Химия-Биология",))

conn.commit()
conn.close()

print("База создана и проинициализирована: ent.db")
print("Все таблицы созданы: blocks, variants, subjects, questions, answers, users, test_results, subject_progress")