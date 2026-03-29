# ntFAST — Deploy to Railway.app

## Шаг 1: GitHub

Залить проект на GitHub (приватный репозиторий):

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/ntfast.git
git branch -M main
git push -u origin main
```

---

## Шаг 2: Railway.app

1. Зайди на https://railway.app и войди через GitHub
2. Нажми **"New Project"**

---

## Шаг 3: PostgreSQL

1. В проекте нажми **"+ New"** → **"Database"** → **"PostgreSQL"**
2. Готово — Railway автоматически создаст базу данных
3. Скопируй `DATABASE_URL` из вкладки **Variables** (понадобится для backend)

---

## Шаг 4: Redis

1. Нажми **"+ New"** → **"Database"** → **"Redis"**
2. Скопируй `REDIS_URL` из вкладки **Variables**

---

## Шаг 5: Backend

1. Нажми **"+ New"** → **"GitHub Repo"** → выбери свой ntfast репозиторий
2. Railway автоматически найдет `railway.json` и задеплоит backend
3. Перейди в **Settings** сервиса:
   - **Root Directory**: `/` (корень)
   - **Builder**: Dockerfile
   - **Dockerfile Path**: `backend/Dockerfile`
4. Перейди во вкладку **Variables** и добавь:

```
DATABASE_URL=<скопируй из PostgreSQL сервиса — кнопка Reference>
SECRET_KEY=<сгенерируй: python -c "import secrets; print(secrets.token_hex(32))">
REDIS_HOST=<хост Redis из Railway>
REDIS_PORT=<порт Redis>
CELERY_BROKER_URL=<REDIS_URL из Redis сервиса>
CELERY_RESULT_BACKEND=<REDIS_URL из Redis сервиса>
BACKEND_CORS_ORIGINS=["http://localhost:5173"]
DEBUG=false
```

> Совет: используй кнопку **"Add Reference"** чтобы Railway автоматически подставил переменные из PostgreSQL и Redis сервисов.

5. Перейди в **Settings** → **Networking** → **Generate Domain**
6. Скопируй домен бэкенда (например: `ntfast-backend-production-abc123.up.railway.app`)

---

## Шаг 6: Frontend

1. Нажми **"+ New"** → **"GitHub Repo"** → тот же репозиторий
2. Перейди в **Settings**:
   - **Root Directory**: `frontend`
   - **Builder**: Dockerfile
   - **Dockerfile Path**: `Dockerfile.railway`
3. Во вкладке **Variables** добавь:

```
VITE_API_URL=https://ntfast-backend-production-abc123.up.railway.app
```

> Замени на реальный домен бэкенда из Шага 5!

4. **Settings** → **Networking** → **Generate Domain**
5. Это будет ссылка для доступа к ntFAST!

---

## Шаг 7: Обновить CORS

После создания frontend домена, вернись в **Backend** → **Variables** и обнови:

```
BACKEND_CORS_ORIGINS=["http://localhost:5173","https://ntfast-frontend-production-xyz.up.railway.app"]
```

Или просто добавь переменную — Railway подхватит автоматически через `RAILWAY_ENVIRONMENT`.

---

## Шаг 8: Проверка

1. Открой домен фронтенда в браузере
2. Зарегистрируйся / войди
3. Загрузи банк выписку
4. Проверь что анализ работает

---

## Бесплатный лимит

- Railway дает **$5 бесплатных кредитов** при привязке карты (Trial)
- Этого хватит примерно на **2-3 недели** работы всех 4 сервисов
- Без карты — **500 часов/месяц** (хватит на 1 сервис)

---

## Приватность

- Домен рандомный — никто не найдет через поиск
- `<meta name="robots" content="noindex, nofollow">` — Google не индексирует
- `X-Robots-Tag: noindex, nofollow` в nginx — дополнительная защита
- Репозиторий на GitHub — приватный
