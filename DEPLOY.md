# Деплой на Railway через GitHub

## 1. Локально: инициализация Git и пуш на GitHub

```bash
cd C:\Users\Мустафа\tg_date_walk_bot

git init
git add .
git commit -m "Initial commit: tg_date_walk_bot MVP"

# Подключаем GitHub репо (URL подставь свой)
git branch -M main
git remote add origin https://github.com/USERNAME/REPO.git
git push -u origin main
```

⚠️ Перед пушем убедись, что `.env` НЕ попадает в коммит (он в `.gitignore`).
Проверка: `git status` — `.env` не должен показываться.

---

## 2. Railway: создание проекта

1. Заходишь на https://railway.app → **New Project**
2. **Deploy from GitHub repo** → выбираешь свой репо
3. Railway автоматически найдёт `docker-compose.yml` и создаст сервисы

---

## 3. Railway: PostgreSQL

В проекте на Railway:
1. **+ New** → **Database** → **Add PostgreSQL**
2. После создания скопируй из вкладки **Variables** значение `DATABASE_URL`
3. Сразу же добавь расширение PostGIS:
   - Открой БД → **Data** → **Query** → выполни:
     ```sql
     CREATE EXTENSION IF NOT EXISTS postgis;
     ```
4. Затем загрузи миграцию из `db/migrations/001_initial.sql` (скопируй содержимое и выполни через Query)

---

## 4. Railway: переменные окружения

Для сервиса **api** и **bot** добавь в **Variables**:

```
BOT_TOKEN=твой_токен_от_BotFather
API_BASE_URL=http://${{api.RAILWAY_PRIVATE_DOMAIN}}:8000
DATABASE_URL=postgresql+asyncpg://...    # из Railway PostgreSQL, замени postgresql:// на postgresql+asyncpg://
DATABASE_SYNC_URL=postgresql://...        # тот же URL без +asyncpg
YANDEX_MAPS_API_KEY=твой_ключ
SECRET_KEY=любая_длинная_строка_для_продакшна
```

---

## 5. Проверка

- В Railway: **Deployments** → должны быть зелёные галочки у api и bot
- В Telegram: пиши `/start` боту → должен ответить

---

## Полезные команды

```bash
# Посмотреть, что попадёт в коммит
git status

# Обновить код на проде (после изменений)
git add .
git commit -m "fix: описание"
git push
# Railway автоматически передеплоит
```
