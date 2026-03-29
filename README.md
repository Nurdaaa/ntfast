# ntFAST
### Financial Analysis System for Transactions

**Версия:** 1.0.0
**Дата обновления:** 22 ноября 2025
**Последняя актуальная версия с полным функционалом**

---

## 📋 СОДЕРЖАНИЕ

1. [О проекте](#о-проекте)
2. [Структура проекта](#структура-проекта)
3. [Требования](#требования)
4. [Быстрый старт](#быстрый-старт)
5. [Функциональность](#функциональность)
6. [Тестирование](#тестирование)
7. [Устранение проблем](#устранение-проблем)

---

## 🎯 О ПРОЕКТЕ

Корпоративная система для анализа финансовых транзакций с функциями:
- Мультиязычность (Русский, Казахский, Английский)
- WebSocket для обновлений в реальном времени
- Email верификация пользователей
- Управление пользователями и правами доступа
- Мониторинг активности пользователей
- Тёмная/светлая тема
- Время отображается в timezone Алматы (Asia/Almaty)

---

## 📁 СТРУКТУРА ПРОЕКТА

```
FinancialAnalysisSystem/
├── frontend/              # React + TypeScript + Vite
│   ├── src/
│   │   ├── components/    # Компоненты UI
│   │   ├── pages/         # Страницы приложения
│   │   ├── context/       # React Context (Auth, Theme, Language)
│   │   ├── services/      # API клиент
│   │   ├── hooks/         # Custom hooks (Activity Monitor)
│   │   └── i18n.ts        # Настройки локализации
│   ├── package.json
│   └── vite.config.ts
│
├── backend/               # FastAPI + SQLite
│   ├── app/
│   │   ├── api/           # API роутеры
│   │   │   ├── auth.py
│   │   │   ├── email_verification.py
│   │   │   ├── users.py
│   │   │   ├── websocket.py
│   │   │   ├── subjects.py
│   │   │   ├── analyses.py
│   │   │   └── transactions.py
│   │   ├── core/          # Конфигурация, БД, безопасность
│   │   ├── models/        # SQLAlchemy модели
│   │   ├── schemas/       # Pydantic схемы
│   │   ├── services/      # Бизнес-логика
│   │   │   ├── auth_service.py
│   │   │   ├── email_service.py
│   │   │   └── user_service.py
│   │   └── main.py        # Точка входа FastAPI
│   ├── financial_analysis.db  # SQLite база данных (77 KB)
│   ├── requirements.txt
│   └── .env               # Переменные окружения
│
├── backups/               # Бэкапы (создаются автоматически)
├── docs/                  # Документация
└── README.md              # Этот файл
```

---

## 🔧 ТРЕБОВАНИЯ

### Backend
- Python 3.8+
- pip

### Frontend
- Node.js 16+
- npm или yarn

### Операционная система
- Windows 10/11
- Linux
- macOS

---

## ⚡ БЫСТРЫЙ СТАРТ

### 1. Backend (Терминал 1)

```bash
# Перейти в папку backend
cd C:\Users\nurda\FinancialAnalysisSystem\backend

# Установить зависимости (если еще не установлены)
pip install -r requirements.txt

# Запустить сервер
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Проверка:** Откройте http://localhost:8000/docs - должна открыться документация API (Swagger)

### 2. Frontend (Терминал 2)

```bash
# Перейти в папку frontend
cd C:\Users\nurda\FinancialAnalysisSystem\frontend

# Установить зависимости (если еще не установлены)
npm install

# Запустить dev сервер
npm run dev
```

**Проверка:** Откройте http://localhost:5173 - должно открыться приложение

### 3. Тестовый пользователь

После запуска используйте:
- **Email:** admin@example.com
- **Пароль:** admin123

---

## 🚀 ФУНКЦИОНАЛЬНОСТЬ

### ✅ Реализованные фичи

#### Frontend
- **Мультиязычность:**
  - Русский (по умолчанию)
  - Казахский
  - Английский
  - Переключение через UI

- **Аутентификация:**
  - Регистрация новых пользователей
  - Вход/Выход
  - Токены JWT
  - Email верификация

- **Управление пользователями:**
  - Просмотр списка пользователей
  - Изменение ролей (admin)
  - Блокировка/разблокировка
  - Профиль пользователя

- **UI/UX:**
  - Тёмная/светлая тема
  - Адаптивный дизайн (Tailwind CSS)
  - Анимации (Framer Motion)
  - Иконки (Heroicons, Lucide, React Icons)

- **Мониторинг:**
  - Отслеживание активности пользователя
  - Автоматический выход при неактивности

#### Backend
- **API Эндпоинты:**
  - `/api/v1/auth/*` - Аутентификация
  - `/api/v1/email-verification/*` - Email верификация
  - `/api/v1/users/*` - Управление пользователями
  - `/api/v1/subjects/*` - Субъекты анализа
  - `/api/v1/analyses/*` - Анализы
  - `/api/v1/transactions/*` - Транзакции
  - `/ws` - WebSocket соединение

- **Безопасность:**
  - Хеширование паролей (bcrypt)
  - JWT токены
  - CORS настроен
  - Email верификация

- **База данных:**
  - SQLite (financial_analysis.db)
  - Размер: 77 KB (актуальная версия)
  - Миграции через Alembic

- **Email сервис:**
  - Отправка писем верификации
  - Настройка через .env файл

---

## 🧪 ТЕСТИРОВАНИЕ

### Проверка Backend

```bash
# В папке backend
cd C:\Users\nurda\FinancialAnalysisSystem\backend

# Проверка API
curl http://localhost:8000/health

# Должен вернуть: {"status": "healthy"}
```

### Проверка Frontend

```bash
# В папке frontend
cd C:\Users\nurda\FinancialAnalysisSystem\frontend

# Сборка production версии
npm run build

# Предпросмотр production версии
npm run preview
```

### Проверка WebSocket

1. Откройте приложение в браузере
2. Залогиньтесь
3. Откройте DevTools → Network → WS
4. Должно быть активное WebSocket соединение к `ws://localhost:8000/ws`

### Проверка локализации

1. В приложении найдите переключатель языка (обычно в хедере)
2. Переключите на Казахский (KZ) или Английский (EN)
3. Весь интерфейс должен перевестись

---

## 🐛 УСТРАНЕНИЕ ПРОБЛЕМ

### Backend не запускается

**Проблема:** `ModuleNotFoundError`
```bash
# Решение: Установить зависимости
cd C:\Users\nurda\FinancialAnalysisSystem\backend
pip install -r requirements.txt
```

**Проблема:** `Port 8000 already in use`
```bash
# Решение: Найти и убить процесс
netstat -ano | findstr :8000
taskkill /PID <номер_процесса> /F
```

**Проблема:** `Database is locked`
```bash
# Решение: Закрыть все процессы использующие БД
# Или удалить файл *.db-journal
```

### Frontend не запускается

**Проблема:** `npm ERR! code ENOENT`
```bash
# Решение: Установить node_modules
cd C:\Users\nurda\FinancialAnalysisSystem\frontend
npm install
```

**Проблема:** `Port 5173 already in use`
```bash
# Решение: Изменить порт в vite.config.ts
# Или убить процесс на порту 5173
```

### WebSocket не подключается

**Проверьте:**
1. Backend запущен на порту 8000
2. В консоли браузера нет ошибок CORS
3. Frontend использует правильный URL для WebSocket

**Решение:**
```javascript
// В файле frontend/src/services/api.ts
// Проверьте настройку WebSocket URL
const wsUrl = 'ws://localhost:8000/ws'
```

### Email не отправляются

**Проверьте файл `.env`:**
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=your-email@gmail.com
```

Для Gmail нужно создать App Password в настройках аккаунта.

---

## 📝 ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ

### Backend (.env)

```env
# База данных
DATABASE_URL=sqlite:///./financial_analysis.db

# Секретный ключ для JWT (ИЗМЕНИТЬ В PRODUCTION!)
SECRET_KEY=your-secret-key-change-in-production

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]

# Email (опционально)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=your-email@gmail.com

# Настройки приложения
PROJECT_NAME=ntFAST
VERSION=1.0.0
API_PREFIX=/api/v1
```

---

## 🔄 МИГРАЦИЯ ПОСЛЕ ПЕРЕНОСА

### После успешного тестирования новой версии:

1. **Убить старые процессы:**
```bash
# Найти и убить все uvicorn процессы
taskkill /F /IM python.exe

# Найти и убить npm процессы
taskkill /F /IM node.exe
```

2. **Обновить пути в скриптах запуска**

3. **Создать бэкап старых папок:**
```bash
# Архивировать старые версии
xcopy C:\Users\nurda\frontend C:\Users\nurda\backups\old_frontend /E /I
xcopy C:\Users\nurda\backend C:\Users\nurda\backups\old_backend /E /I
```

4. **Удалить старые папки (ТОЛЬКО ПОСЛЕ ПОДТВЕРЖДЕНИЯ):**
```bash
# ВНИМАНИЕ: Выполнять только после успешного теста!
rmdir /S /Q C:\Users\nurda\frontend
rmdir /S /Q C:\Users\nurda\backend
rmdir /S /Q "C:\Users\nurda\Desktop\FinancialAnalysisSystem"
```

---

## 📊 СРАВНЕНИЕ С DESKTOP ВЕРСИЕЙ

| Функция | Desktop версия (СТАРАЯ) | Эта версия (АКТУАЛЬНАЯ) |
|---------|------------------------|------------------------|
| Дата обновления | 12 ноября | 21 ноября |
| Размер БД | 65 KB | 77 KB |
| Мультиязычность | ❌ | ✅ |
| WebSocket | ❌ | ✅ |
| Email верификация | ❌ | ✅ |
| Управление пользователями | ❌ | ✅ |
| Мониторинг активности | ❌ | ✅ |
| i18n пакеты | ❌ | ✅ |

---

## 📞 ПОДДЕРЖКА

Если возникли проблемы:
1. Проверьте раздел [Устранение проблем](#устранение-проблем)
2. Посмотрите логи в консоли (backend) и DevTools (frontend)
3. Убедитесь что все зависимости установлены
4. Проверьте что порты 8000 и 5173 свободны

---

## 📜 ЛИЦЕНЗИЯ

ntFAST — Financial Analysis System for Transactions

---

**Актуальная версия от 21 ноября 2025**
**Все функции протестированы и работают**
