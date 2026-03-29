# ИНСТРУКЦИЯ ПО ТЕСТИРОВАНИЮ НОВОЙ ВЕРСИИ

## ⚠️ ВАЖНО: НЕ УДАЛЯЙТЕ СТАРЫЕ ПАПКИ ДО ЗАВЕРШЕНИЯ ТЕСТОВ!

---

## ШАГ 1: ОСТАНОВИТЬ ТЕКУЩИЕ ПРОЦЕССЫ

### Проверить запущенные процессы:
```bash
# В PowerShell или CMD
netstat -ano | findstr :8000   # Backend
netstat -ano | findstr :5173   # Frontend
```

### Остановить процессы (если нужно):
```bash
# Убить процессы на порту 8000 (backend)
FOR /F "tokens=5" %P IN ('netstat -ano ^| findstr :8000') DO taskkill /PID %P /F

# Убить процессы на порту 5173 (frontend)
FOR /F "tokens=5" %P IN ('netstat -ano ^| findstr :5173') DO taskkill /PID %P /F
```

---

## ШАГ 2: ЗАПУСТИТЬ НОВУЮ ВЕРСИЮ BACKEND

### Терминал 1 (Backend):
```bash
cd C:\Users\nurda\FinancialAnalysisSystem\backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### ✅ Проверка успешного запуска:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 🧪 Тесты Backend:

#### Тест 1: Health Check
```bash
# Открыть новое окно терминала
curl http://localhost:8000/health
```
**Ожидаемый результат:** `{"status":"healthy"}`

#### Тест 2: API Docs
Откройте в браузере: http://localhost:8000/docs
**Ожидаемый результат:** Страница Swagger UI с документацией API

#### Тест 3: Root endpoint
```bash
curl http://localhost:8000/
```
**Ожидаемый результат:**
```json
{
  "message": "Financial Transaction Analysis System API",
  "version": "1.0.0",
  "docs": "/docs"
}
```

---

## ШАГ 3: ЗАПУСТИТЬ НОВУЮ ВЕРСИЮ FRONTEND

### Терминал 2 (Frontend):
```bash
cd C:\Users\nurda\FinancialAnalysisSystem\frontend
npm run dev
```

### ✅ Проверка успешного запуска:
```
VITE v5.0.11  ready in XXX ms

➜  Local:   http://localhost:5173/
➜  Network: http://192.168.X.X:5173/
➜  press h to show help
```

### 🧪 Тесты Frontend:

#### Тест 1: Открыть приложение
Откройте в браузере: http://localhost:5173

**Ожидаемый результат:**
- Страница логина загружается
- Нет ошибок в консоли (F12 → Console)
- CSS загружен корректно

#### Тест 2: Логин
```
Email: admin@example.com
Password: admin123
```

**Ожидаемый результат:**
- Успешный вход
- Редирект на дашборд
- В консоли (Network → WS) должно быть WebSocket соединение

#### Тест 3: Переключение языка
1. Найдите переключатель языка в хедере
2. Переключите на "Қазақша" (KZ)
3. Переключите на "English" (EN)
4. Вернитесь на "Русский" (RU)

**Ожидаемый результат:**
- Весь интерфейс переводится мгновенно
- Никаких ошибок в консоли

#### Тест 4: Переключение темы
1. Найдите кнопку переключения темы (moon/sun icon)
2. Переключите между светлой и темной темой

**Ожидаемый результат:**
- Плавное переключение анимации
- Цвета меняются корректно

#### Тест 5: Навигация по страницам
Проверьте каждую страницу:
- Dashboard
- Subjects (Субъекты)
- Analyses (Анализы)
- Settings (Настройки)
- User Management (Управление пользователями) - если admin

**Ожидаемый результат:**
- Все страницы загружаются без ошибок
- Данные отображаются корректно

---

## ШАГ 4: ТЕСТИРОВАНИЕ WEBSOCKET

### Проверка WebSocket соединения:

1. Откройте DevTools (F12)
2. Перейдите на вкладку **Network**
3. Включите фильтр **WS** (WebSocket)
4. Обновите страницу (F5)

**Ожидаемый результат:**
- Видно соединение к `ws://localhost:8000/ws`
- Статус: `101 Switching Protocols` (зеленый)
- Frames показывают обмен сообщениями

### Тест real-time updates:

1. Откройте 2 окна браузера
2. Залогиньтесь в обоих окнах
3. В одном окне сделайте изменение (например, создайте субъект)
4. Во втором окне должно появиться обновление

**Ожидаемый результат:**
- Изменения синхронизируются между окнами
- Нет задержек больше 1-2 секунд

---

## ШАГ 5: ТЕСТИРОВАНИЕ EMAIL ФУНКЦИЙ

### Если настроен SMTP в .env:

1. Зарегистрируйте нового пользователя
2. Проверьте email - должно прийти письмо верификации
3. Кликните на ссылку в письме

**Ожидаемый результат:**
- Email приходит в течение 1 минуты
- Ссылка верификации работает
- После верификации можно залогиниться

### Если SMTP не настроен:

Можно пропустить этот тест. Email функции опциональны.

---

## ШАГ 6: ТЕСТИРОВАНИЕ УПРАВЛЕНИЯ ПОЛЬЗОВАТЕЛЯМИ

### Для admin пользователя:

1. Перейдите в "User Management"
2. Посмотрите список пользователей
3. Попробуйте:
   - Изменить роль пользователя
   - Заблокировать/разблокировать пользователя

**Ожидаемый результат:**
- Список пользователей загружается
- Изменения сохраняются
- Нет ошибок в консоли

---

## ШАГ 7: ПРОВЕРКА БАЗЫ ДАННЫХ

### Проверить что БД скопирована:
```bash
dir C:\Users\nurda\FinancialAnalysisSystem\backend\financial_analysis.db
```

**Ожидаемый размер:** ~77 KB

### Проверить что данные на месте:
```bash
# Установить sqlite3 если нужно
sqlite3 C:\Users\nurda\FinancialAnalysisSystem\backend\financial_analysis.db

# В sqlite3 консоли:
.tables
SELECT COUNT(*) FROM users;
.exit
```

**Ожидаемый результат:**
- Таблицы: users, subjects, analyses, transactions, email_verifications
- Минимум 1 пользователь (admin)

---

## ШАГ 8: ФИНАЛЬНАЯ ПРОВЕРКА

### Чек-лист всех фич:

- [ ] Backend запускается на порту 8000
- [ ] Frontend запускается на порту 5173
- [ ] Логин работает (admin@example.com / admin123)
- [ ] WebSocket соединение активно
- [ ] Мультиязычность работает (RU/KZ/EN)
- [ ] Переключение темы работает
- [ ] Все страницы загружаются
- [ ] Навигация работает
- [ ] База данных содержит данные
- [ ] Нет ошибок в консоли браузера
- [ ] Нет ошибок в логах backend

---

## ✅ ЕСЛИ ВСЕ ТЕСТЫ ПРОЙДЕНЫ

### Поздравляем! Новая версия работает!

### Следующие шаги:

1. **Создать бэкап старых версий:**
```bash
mkdir C:\Backup
xcopy C:\Users\nurda\frontend C:\Backup\old_frontend /E /I /H
xcopy C:\Users\nurda\backend C:\Backup\old_backend /E /I /H
xcopy "C:\Users\nurda\Desktop\FinancialAnalysisSystem" "C:\Backup\Desktop_FinancialAnalysisSystem" /E /I /H
```

2. **Проверить что бэкап создан:**
```bash
dir C:\Backup
```

3. **Только после проверки бэкапа удалить старые версии:**
```bash
# ВНИМАНИЕ: ВЫПОЛНЯТЬ ТОЛЬКО ПОСЛЕ ПРОВЕРКИ БЭКАПА!
rmdir /S /Q C:\Users\nurda\frontend
rmdir /S /Q C:\Users\nurda\backend
rmdir /S /Q "C:\Users\nurda\Desktop\FinancialAnalysisSystem"
```

4. **Обновить рабочий каталог:**
Теперь ваш основной проект находится в:
```
C:\Users\nurda\FinancialAnalysisSystem\
```

---

## ❌ ЕСЛИ ТЕСТЫ НЕ ПРОЙДЕНЫ

### Проблемы и решения:

#### Backend не запускается:
```bash
# Проверить зависимости
cd C:\Users\nurda\FinancialAnalysisSystem\backend
pip install -r requirements.txt

# Проверить .env файл
type .env
```

#### Frontend не запускается:
```bash
# Переустановить зависимости
cd C:\Users\nurda\FinancialAnalysisSystem\frontend
rm -rf node_modules package-lock.json
npm install
```

#### Ошибки в консоли:
1. Откройте DevTools (F12)
2. Скопируйте ошибку
3. Проверьте настройки CORS в backend
4. Проверьте API URL в frontend

#### WebSocket не работает:
1. Проверьте что backend запущен
2. Проверьте URL WebSocket в коде
3. Проверьте настройки CORS

---

## 📝 ОТЧЕТ О ТЕСТИРОВАНИИ

После завершения тестирования заполните:

**Дата теста:** _________________

**Backend:**
- [ ] Запустился успешно
- [ ] Health check работает
- [ ] API docs доступны
- [ ] Проблемы: _________________

**Frontend:**
- [ ] Запустился успешно
- [ ] Логин работает
- [ ] Навигация работает
- [ ] Проблемы: _________________

**Фичи:**
- [ ] Мультиязычность (RU/KZ/EN)
- [ ] Переключение темы
- [ ] WebSocket
- [ ] Управление пользователями
- [ ] Проблемы: _________________

**Общая оценка:**
- [ ] ВСЕ РАБОТАЕТ - можно удалять старые версии
- [ ] ЕСТЬ ПРОБЛЕМЫ - нужно исправить перед удалением

---

**Удачного тестирования!**
