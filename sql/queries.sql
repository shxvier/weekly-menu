-- ==========================================
-- Меню на неделю: SQL-запросы проекта
-- ==========================================
-- Значения в условиях (даты, лимиты, id) — примеры для проверки
-- в SQLite. В Django-представлениях вместо них стоят параметры ?.

-- -----------------------------------------
-- Выборка списков
-- -----------------------------------------

-- Запрос 1. Список всех блюд по алфавиту (страница «Блюда»)
SELECT
    id,
    name,
    calories,
    dish_type
FROM dishes
ORDER BY name;

-- Запрос 2. Список пользователей (выпадающий список на странице
-- «Меню на день»)
SELECT
    id,
    name,
    goal,
    daily_limit
FROM users
ORDER BY name;

-- -----------------------------------------
-- Фильтрация (WHERE)
-- -----------------------------------------

-- Запрос 3. Подбор блюд, укладывающихся в лимит калорий
-- (форма «Не больше … ккал» на странице «Блюда»)
SELECT
    id,
    name,
    calories,
    dish_type
FROM dishes
WHERE calories <= 300
ORDER BY calories;

-- Запрос 4. Блюдо по идентификатору (страница блюда)
SELECT
    id,
    name,
    calories,
    dish_type
FROM dishes
WHERE id = 1;

-- Запрос 5. Лёгкие блюда для завтрака или перекуса: несколько условий,
-- IN и BETWEEN
SELECT
    name,
    calories,
    dish_type
FROM dishes
WHERE dish_type IN ('завтрак', 'перекус')
    AND calories BETWEEN 150 AND 300
ORDER BY calories;

-- -----------------------------------------
-- Соединение таблиц (JOIN)
-- -----------------------------------------

-- Запрос 6. Активные записи меню с названием блюда и именем
-- пользователя (страница «Меню»)
SELECT
    menu_entries.id,
    menu_entries.menu_date,
    dishes.name AS dish_name,
    dishes.calories,
    users.name AS user_name,
    menu_entries.is_cancelled
FROM menu_entries
JOIN dishes
    ON menu_entries.dish_id = dishes.id
JOIN users
    ON menu_entries.user_id = users.id
WHERE menu_entries.is_cancelled = 0
ORDER BY menu_entries.menu_date, users.name;

-- Запрос 7. Полная информация о записи меню по id
-- (страница записи меню)
SELECT
    menu_entries.id,
    menu_entries.menu_date,
    menu_entries.is_cancelled,
    dishes.id AS dish_id,
    dishes.name AS dish_name,
    dishes.calories,
    dishes.dish_type,
    users.name AS user_name,
    users.daily_limit
FROM menu_entries
JOIN dishes
    ON menu_entries.dish_id = dishes.id
JOIN users
    ON menu_entries.user_id = users.id
WHERE menu_entries.id = 3;

-- Запрос 8. Меню пользователя на выбранный день
-- (страница «Меню на день»)
SELECT
    menu_entries.id,
    dishes.name AS dish_name,
    dishes.dish_type,
    dishes.calories
FROM menu_entries
JOIN dishes
    ON menu_entries.dish_id = dishes.id
WHERE menu_entries.user_id = 1
    AND menu_entries.menu_date = '2026-09-14'
    AND menu_entries.is_cancelled = 0
ORDER BY dishes.calories;

-- Запрос 9. Блюда, которые ещё можно добавить пользователю на день:
-- подзапрос NOT IN исключает блюда, уже стоящие в меню
SELECT
    id,
    name,
    calories,
    dish_type
FROM dishes
WHERE id NOT IN (
    SELECT dish_id
    FROM menu_entries
    WHERE user_id = 1
        AND menu_date = '2026-09-14'
        AND is_cancelled = 0
)
ORDER BY name;

-- -----------------------------------------
-- Агрегатные функции
-- -----------------------------------------

-- Запрос 10. Количество активных и отменённых записей меню
SELECT
    COUNT(*) AS total_entries,
    SUM(is_cancelled = 0) AS active_entries,
    SUM(is_cancelled = 1) AS cancelled_entries
FROM menu_entries;

-- Запрос 11. Минимальная, максимальная и средняя калорийность блюд
SELECT
    COUNT(*) AS dishes_count,
    MIN(calories) AS min_calories,
    MAX(calories) AS max_calories,
    ROUND(AVG(calories), 1) AS avg_calories
FROM dishes;

-- Запрос 12. Сколько раз блюдо стоит в активном меню (страница блюда)
SELECT
    COUNT(*) AS times_planned
FROM menu_entries
WHERE dish_id = 1
    AND is_cancelled = 0;

-- Запрос 13. Суммарная калорийность меню пользователя на день
SELECT
    COALESCE(SUM(dishes.calories), 0) AS day_calories
FROM menu_entries
JOIN dishes
    ON menu_entries.dish_id = dishes.id
WHERE menu_entries.user_id = 1
    AND menu_entries.menu_date = '2026-09-14'
    AND menu_entries.is_cancelled = 0;

-- -----------------------------------------
-- Группировка (GROUP BY) и фильтрация групп (HAVING)
-- -----------------------------------------

-- Запрос 14. Количество блюд и средняя калорийность по типам
SELECT
    dish_type,
    COUNT(*) AS dishes_count,
    ROUND(AVG(calories)) AS avg_calories
FROM dishes
GROUP BY dish_type
ORDER BY dishes_count DESC, dish_type;

-- Запрос 15. Популярность блюд: сколько раз каждое блюдо в активном
-- меню. LEFT JOIN сохраняет блюда, которых в меню нет (0)
SELECT
    dishes.name AS dish_name,
    COUNT(menu_entries.id) AS times_planned
FROM dishes
LEFT JOIN menu_entries
    ON dishes.id = menu_entries.dish_id
    AND menu_entries.is_cancelled = 0
GROUP BY dishes.id, dishes.name
ORDER BY times_planned DESC, dishes.name;

-- Запрос 16. Калорийность по дням для каждого пользователя
-- и сравнение с его дневным лимитом
SELECT
    users.name AS user_name,
    menu_entries.menu_date,
    COUNT(*) AS dishes_count,
    SUM(dishes.calories) AS day_calories,
    users.daily_limit
FROM menu_entries
JOIN dishes
    ON menu_entries.dish_id = dishes.id
JOIN users
    ON menu_entries.user_id = users.id
WHERE menu_entries.is_cancelled = 0
GROUP BY users.id, users.name, menu_entries.menu_date, users.daily_limit
ORDER BY menu_entries.menu_date, users.name;

-- Запрос 17. Дни, где калорийность превышает лимит пользователя:
-- WHERE отбирает строки до группировки, HAVING — группы после неё
SELECT
    users.name AS user_name,
    menu_entries.menu_date,
    SUM(dishes.calories) AS day_calories,
    users.daily_limit,
    SUM(dishes.calories) - users.daily_limit AS excess
FROM menu_entries
JOIN dishes
    ON menu_entries.dish_id = dishes.id
JOIN users
    ON menu_entries.user_id = users.id
WHERE menu_entries.is_cancelled = 0
GROUP BY users.id, users.name, menu_entries.menu_date, users.daily_limit
HAVING SUM(dishes.calories) > users.daily_limit
ORDER BY excess DESC;

-- Запрос 18. Блюда, запланированные больше заданного числа раз
-- (порог вводит пользователь на странице «Статистика»)
SELECT
    dishes.name AS dish_name,
    COUNT(menu_entries.id) AS times_planned
FROM dishes
JOIN menu_entries
    ON dishes.id = menu_entries.dish_id
WHERE menu_entries.is_cancelled = 0
GROUP BY dishes.id, dishes.name
HAVING COUNT(menu_entries.id) > 2
ORDER BY times_planned DESC;
