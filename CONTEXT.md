# tg_date_walk_bot — контекст проекта

## Стек
- **Bot**: aiogram 3.x, Python 3.12
- **API**: FastAPI + SQLAlchemy 2 async + asyncpg
- **DB**: PostgreSQL + PostGIS
- **Infra**: Docker Compose
- **Path**: `C:\Users\Мустафа\tg_date_walk_bot\`
- **Запуск**: `docker compose down -v && docker compose up --build`

---

## Структура
```
api/
  main.py              ← auth, places, routes, ratings, history, groups
  schemas.py
  deps.py              ← get_current_user (X-Telegram-Id header)
  routers/
    auth.py            POST /auth/telegram
    places.py          POST/GET/DELETE /places
    routes.py          POST /routes/generate, POST /routes/{id}/reroll, GET /routes/{id}
    ratings.py         POST /ratings
    history.py         GET /history
    groups.py          POST /groups, POST /groups/invite,
                       POST /groups/{id}/accept, GET /groups/my

bot/
  main.py              ← Dispatcher + AutoAuthMiddleware
  api_client.py        ← все вызовы к API
  states.py            ← AddPlace, CreateGroup, InviteToGroup, CreateRoute, RateRoute
  keyboards/inline.py
  handlers/
    start.py           /start, back_to_menu, cancel
    places.py          add/list/delete/random
    routes.py          generate/reroll/history/notify_group
    ratings.py         rate route/place
    groups.py          create/invite/accept/detail

core/
  config.py
  database.py
  route_engine.py

db/
  models.py
  migrations/001_initial.sql
```

---

## Модели БД

```
User:         id, telegram_id, username, created_at
Place:        id, owner_id, title, address, lat, lon, geom, url,
              tags(JSONB), city, visibility(private|group),
              group_id(FK→groups), working_hours, rating_avg,
              rating_count, status(active|blacklisted), created_at, updated_at
Group:        id, title, created_by(FK→users), created_at
GroupMember:  group_id(PK), user_id(PK), role(owner|member), status(accepted|pending)
ScenarioTemplate: id, name, participant_min, participant_max, steps_json, active
GeneratedRoute: id, user_id, group_id, scenario_id, places_json(JSONB),
                distance_m, walk_minutes, total_minutes, rating_avg, created_at
Rating:       id, user_id, place_id, route_id, value(1-5), text, created_at
```

---

## Теги и сценарии

| Кнопка | Тег | Шаг |
|--------|-----|-----|
| ☕ Кафе | `cafe` | 1 |
| 🏞️ Парк | `park` | 2 |
| 🍴 Еда | `food` | 3 |

Сценарии (в БД):
- `date`: cafe(30м) → park(40м) → food(60м), 2 чел.
- `walk`: cafe(20м) → park(60м) → food(45м), 3+ чел.
- `light`: cafe(30м) → park(45м), любое кол-во

---

## Что полностью работает ✅

### Базовый бот
- `/start` → меню
- Добавление места: название → адрес → ссылка (опц.) → тег-кнопка → группа (если есть)
- Мои места: список с тегами и группой, удаление с подтверждением
- 🎲 Случайное место из бэклога

### Маршруты
- Генерация: выбор режима (solo/группа) → сценарий → маршрут
- Reroll: сначала без мест из предыдущего маршрута, fallback — полный пул
- История: последние 50 маршрутов
- Оценка маршрута (1–5 ⭐)

### Совместная БД (группы)
- Создание группы
- Приглашение по @username + push-уведомление приглашённому
- Принятие/отклонение приглашения
- При добавлении места — выбор группы (место привязывается к group_id)
- При генерации — выбор «свои места» или «пул группы»
- `🚨 Уведомить участников` — рассылает маршрут всем accepted-членам

---

## Авторизация
`AutoAuthMiddleware` вызывает `POST /auth/telegram` перед каждым апдейтом.
API читает `X-Telegram-Id` header → user из БД. Пользователь создаётся автоматически.

---

## Route engine (`core/route_engine.py`)
- Для каждого шага сценария ищет места с нужным тегом
- Исключает уже выбранные места
- Радиус 3000м — только если оба места имеют координаты (lat/lon)
- Места без координат допускаются (радиус и время не считаются)
- Лимит 120 мин — только если есть координаты
- До 10 попыток, `None` если не получилось

---

## Следующий приоритет: геокодинг

**Проблема:** места добавляются без координат (lat/lon), поэтому:
- Яндекс-ссылка в маршруте ведёт на поиск по адресу первого места, а не на настоящий маршрут
- Время ходьбы и дистанция не считаются
- Радиусная фильтрация не работает

**Решение:** при сохранении места автоматически запрашивать координаты через
Яндекс Geocoder API (`https://geocode-maps.yandex.ru/1.x/`) по адресу.

**Env:** `YANDEX_MAPS_API_KEY` уже есть в `.env.example` и `core/config.py`.

**Где добавить:** `api/routers/places.py::add_place` — после валидации, перед сохранением,
если `lat/lon` не переданы явно — геокодировать `address`.
