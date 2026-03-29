# Email Verification System - Готово к использованию! ✅

## Статус системы

**Система email verification полностью реализована и протестирована!**

### Что работает:

✅ API endpoints для отправки и проверки кодов
✅ База данных с таблицей `email_verifications`
✅ Генерация 6-значных кодов
✅ HTML email шаблоны
✅ Автоматическое истечение кодов (10 минут)
✅ DEMO MODE - коды выводятся в консоль
✅ Поддержка реальной отправки email через SMTP
✅ Интеграция с settings через .env файл
✅ .gitignore для безопасности

---

## Текущий режим: DEMO MODE

Система работает в **demo mode** - коды НЕ отправляются на email, а выводятся в консоль сервера.

### Как использовать в demo mode:

1. Откройте консоль, где запущен backend (`uvicorn`)
2. На frontend нажмите "Отправить код" при регистрации
3. В консоли backend найдите:
   ```
   ============================================================
   EMAIL VERIFICATION CODE (DEMO MODE)
   ============================================================
   To: user@example.com
   Code: 123456
   Expires: 10 minutes
   ============================================================
   ```
4. Скопируйте код и введите его на frontend

---

## Включение реальной отправки email

### Вариант 1: Gmail (рекомендуется)

#### Шаг 1: Создайте App Password

1. Откройте https://myaccount.google.com/
2. **Безопасность** → Включите **"Двухэтапную аутентификацию"**
3. Вернитесь в "Безопасность" → **"Пароли приложений"**
   https://myaccount.google.com/apppasswords
4. Создайте пароль приложения (выберите "Почта" / "Другое")
5. Скопируйте 16-значный пароль (например: `abcd efgh ijkl mnop`)

#### Шаг 2: Создайте .env файл

```bash
cd backend
cp .env.example .env
```

#### Шаг 3: Настройте .env

Откройте `.env` и установите:

```env
# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=ваша-почта@gmail.com
SMTP_PASSWORD=abcdefghijklmnop
USE_REAL_EMAIL=true
```

**Важно:**
- Используйте App Password (16 символов), НЕ обычный пароль
- Удалите пробелы из App Password: `abcd efgh ijkl mnop` → `abcdefghijklmnop`
- Установите `USE_REAL_EMAIL=true`

#### Шаг 4: Перезапустите сервер

```bash
# Остановите сервер (Ctrl+C)
# Запустите снова:
uvicorn app.main:app --reload
```

---

### Вариант 2: Другие почтовые сервисы

#### Yandex

```env
SMTP_SERVER=smtp.yandex.ru
SMTP_PORT=587
SMTP_USERNAME=ваша-почта@yandex.ru
SMTP_PASSWORD=ваш-пароль
USE_REAL_EMAIL=true
```

#### Mail.ru

```env
SMTP_SERVER=smtp.mail.ru
SMTP_PORT=587
SMTP_USERNAME=ваша-почта@mail.ru
SMTP_PASSWORD=ваш-пароль
USE_REAL_EMAIL=true
```

#### Outlook/Hotmail

```env
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USERNAME=ваша-почта@outlook.com
SMTP_PASSWORD=ваш-пароль
USE_REAL_EMAIL=true
```

---

## Тестирование системы

### Быстрый тест (автоматический)

```bash
cd backend
python test_email_system.py --quick
```

Результат:
```
[QUICK TEST] Generating code for test@example.com...
[SUCCESS] Code generated: 893133
[SUCCESS] Verification successful!
```

### Полный тест (интерактивный)

```bash
cd backend
python test_email_system.py
```

Программа попросит ввести email и проверит весь цикл:
1. Генерация кода
2. Отправка email (или вывод в консоль)
3. Проверка кода

---

## API Endpoints

### 1. Отправить код верификации

```http
POST /api/email-verification/send-code
Content-Type: application/json

{
  "email": "user@example.com"
}
```

Ответ:
```json
{
  "message": "Verification code sent successfully",
  "success": true
}
```

### 2. Проверить код

```http
POST /api/email-verification/verify-code
Content-Type: application/json

{
  "email": "user@example.com",
  "code": "123456"
}
```

Ответ (успех):
```json
{
  "message": "Email verified successfully",
  "success": true
}
```

Ответ (ошибка):
```json
{
  "detail": "Invalid or expired verification code"
}
```

---

## Структура базы данных

Таблица `email_verifications`:

| Поле | Тип | Описание |
|------|-----|----------|
| id | INTEGER | Primary key |
| email | VARCHAR | Email получателя |
| code | VARCHAR(6) | 6-значный код |
| is_verified | BOOLEAN | Код использован? |
| created_at | DATETIME | Время создания |
| expires_at | DATETIME | Время истечения (+10 мин) |

### Проверка таблицы

```bash
cd backend
python check_email_table.py
```

---

## Утилиты

### check_email_table.py
Проверяет структуру таблицы и показывает последние записи:

```bash
python check_email_table.py
```

### test_email_system.py
Тестирует всю систему email verification:

```bash
# Быстрый тест
python test_email_system.py --quick

# Полный интерактивный тест
python test_email_system.py
```

### delete_other_users.py
Удаляет всех пользователей кроме указанного:

```bash
python delete_other_users.py
```

---

## Решение проблем

### Email не приходит

1. **Проверьте папку "Спам"**
2. **Убедитесь что `USE_REAL_EMAIL=true`**
3. **Проверьте консоль сервера** на наличие ошибок
4. **Проверьте настройки** `.env`:
   - App Password корректный
   - Нет пробелов в пароле
   - Email правильный

### Ошибка аутентификации SMTP

```
SMTPAuthenticationError: Username and Password not accepted
```

**Решение:**
- Используйте App Password, не обычный пароль Gmail
- Включите двухэтапную аутентификацию
- Проверьте что App Password скопирован без пробелов

### Всё ещё показывается DEMO MODE

**Решение:**
1. Убедитесь что файл `.env` находится в `backend/`
2. Установите `USE_REAL_EMAIL=true` (без лишних пробелов)
3. Полностью перезапустите сервер (Ctrl+C → uvicorn снова)

---

## Безопасность

### ⚠️ НИКОГДА не коммитьте .env!

Файл `.env` автоматически игнорируется через `.gitignore`.

Проверьте:
```bash
git status
# .env НЕ должен отображаться
```

### Production окружение

Для production используйте переменные окружения:

```bash
# Linux/Mac
export SMTP_USERNAME=your-email@gmail.com
export SMTP_PASSWORD=your-app-password
export USE_REAL_EMAIL=true

# Windows
set SMTP_USERNAME=your-email@gmail.com
set SMTP_PASSWORD=your-app-password
set USE_REAL_EMAIL=true
```

---

## Как это работает (flow)

### Регистрация с верификацией email:

```
1. Пользователь вводит email на frontend
   ↓
2. Frontend → POST /api/email-verification/send-code
   ↓
3. Backend генерирует 6-значный код
   ↓
4. Код сохраняется в БД (expires_at = +10 минут)
   ↓
5. Email отправляется через SMTP (или консоль в demo)
   ↓
6. Пользователь получает email с кодом
   ↓
7. Пользователь вводит код на frontend
   ↓
8. Frontend → POST /api/email-verification/verify-code
   ↓
9. Backend проверяет: email + code + not_expired + not_used
   ↓
10. Если OK → is_verified = true, регистрация продолжается
```

---

## Документация

- **EMAIL_SETUP_GUIDE.md** - Подробное руководство по настройке
- **README_EMAIL.md** (этот файл) - Краткая справка
- **.env.example** - Пример конфигурации

---

## Статус файлов

### Созданные файлы:

- ✅ `app/api/email_verification.py` - API endpoints
- ✅ `app/services/email_service.py` - Email логика
- ✅ `app/models/email_verification.py` - Database model
- ✅ `app/schemas/email_verification.py` - Pydantic schemas
- ✅ `check_email_table.py` - Утилита проверки БД
- ✅ `test_email_system.py` - Тесты системы
- ✅ `.env.example` - Пример конфигурации
- ✅ `.gitignore` - Безопасность
- ✅ `EMAIL_SETUP_GUIDE.md` - Подробная документация

### Обновленные файлы:

- ✅ `app/core/config.py` - Добавлены email настройки
- ✅ `app/main.py` - Подключен email router

---

## Следующие шаги

### Для разработки (demo mode):

1. ✅ Система уже работает!
2. ✅ Просто используйте коды из консоли

### Для production (реальные emails):

1. Создайте App Password в Gmail
2. Скопируйте `.env.example` → `.env`
3. Настройте SMTP_USERNAME и SMTP_PASSWORD
4. Установите `USE_REAL_EMAIL=true`
5. Перезапустите сервер

---

## Вопросы?

Проверьте:
- `EMAIL_SETUP_GUIDE.md` - детальное руководство
- Консоль backend - сообщения об ошибках
- `python test_email_system.py` - тест системы

**Система готова к использованию!** 🎉
