-- ==========================================
-- Меню на неделю: структура базы данных
-- ==========================================

-- Блюда
CREATE TABLE IF NOT EXISTS dishes (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    calories INTEGER NOT NULL CHECK (calories > 0),
    dish_type TEXT NOT NULL
);

-- Пользователи; цель (goal) может отсутствовать — допускается NULL
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    goal TEXT,
    daily_limit INTEGER NOT NULL CHECK (daily_limit > 0)
);

-- Записи меню: какое блюдо, кому и на какую дату (ГГГГ-ММ-ДД)
CREATE TABLE IF NOT EXISTS menu_entries (
    id INTEGER PRIMARY KEY,
    dish_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    menu_date TEXT NOT NULL,
    is_cancelled INTEGER NOT NULL DEFAULT 0 CHECK (is_cancelled IN (0, 1)),
    FOREIGN KEY (dish_id) REFERENCES dishes(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
