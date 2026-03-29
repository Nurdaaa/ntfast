# 📧 Руководство по настройке отправки Email

## Текущий статус

✅ **Система email verification полностью реализована**:
- API endpoints для отправки и проверки кодов (`/api/email-verification/send-code`, `/api/email-verification/verify-code`)
- База данных с таблицей `email_verifications`
- Генерация 6-значных кодов
- HTML шаблоны писем
- Автоматическое истечение кодов через 10 минут

⚠️ **Сейчас работает в DEMO MODE** - коды выводятся в консоль сервера, но не отправляются на email.

---

## 🚀 Быстрая настройка (Gmail)

### Шаг 1: Создайте App Password в Gmail

1. **Откройте**: https://myaccount.google.com/
2. **Безопасность** → Включите **"Двухэтапную аутентификацию"** (если не включена)
3. **Вернитесь в "Безопасность"** → найдите **"Пароли приложений"** (App Passwords)
   - Прямая ссылка: https://myaccount.google.com/apppasswords
4. Выберите:
   - **Приложение**: Почта
   - **Устройство**: Другое (введите "ntFAST")
5. **Создать** → скопируйте 16-значный пароль (например: `abcd efgh ijkl mnop`)

### Шаг 2: Создайте файл .env

Скопируйте `.env.example` в `.env`:

```bash
cp .env.example .env
```

### Шаг 3: Настройте переменные в .env

Откройте `.env` и установите:

```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=ваша-почта@gmail.com
SMTP_PASSWORD=abcd efgh ijkl mnop
USE_REAL_EMAIL=true
```

⚠️ **Важно**:
- Используйте App Password, **НЕ** ваш обычный пароль от Gmail
- Удалите пробелы из App Password: `abcd efgh ijkl mnop` → `abcdefghijklmnop`
- Установите `USE_REAL_EMAIL=true` для отправки реальных писем

### Шаг 4: Перезапустите сервер

```bash
# Остановите текущий сервер (Ctrl+C)
# Затем запустите снова:
cd backend
uvicorn app.main:app --reload
```

### Шаг 5: Проверьте работу

Откройте консоль бэкенда - при отправке кода вы должны увидеть:

```
============================================================
✅ EMAIL SENT SUCCESSFULLY
============================================================
To: user@example.com
Subject: Подтвердите ваш Email - Код подтверждения
============================================================
```

---

## 📮 Альтернативные почтовые сервисы

### Yandex Mail

```env
SMTP_SERVER=smtp.yandex.ru
SMTP_PORT=587
SMTP_USERNAME=ваша-почта@yandex.ru
SMTP_PASSWORD=ваш-пароль
USE_REAL_EMAIL=true
```

**Примечание**: Для Yandex используйте обычный пароль от почты (или создайте пароль приложения в настройках безопасности).

### Mail.ru

```env
SMTP_SERVER=smtp.mail.ru
SMTP_PORT=587
SMTP_USERNAME=ваша-почта@mail.ru
SMTP_PASSWORD=ваш-пароль
USE_REAL_EMAIL=true
```

### Outlook/Hotmail

```env
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USERNAME=ваша-почта@outlook.com
SMTP_PASSWORD=ваш-пароль
USE_REAL_EMAIL=true
```

---

## 🧪 Тестирование

### Через API напрямую (curl):

```bash
# Отправить код
curl -X POST http://localhost:8000/api/email-verification/send-code \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'

# Проверить код
curl -X POST http://localhost:8000/api/email-verification/verify-code \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "code": "123456"}'
```

### Через frontend:

1. Откройте страницу регистрации
2. Заполните форму и нажмите "Отправить код"
3. Проверьте почту (и папку "Спам"!)
4. Введите 6-значный код

---

## ❌ Решение проблем

### Проблема: Ошибка аутентификации SMTP

```
SMTPAuthenticationError: (535, b'5.7.8 Username and Password not accepted')
```

**Решение**:
- Убедитесь, что используете App Password, а не обычный пароль
- Проверьте, что двухэтапная аутентификация включена в Gmail
- Удалите пробелы из App Password

### Проблема: Соединение отклонено

```
ConnectionRefusedError: [Errno 111] Connection refused
```

**Решение**:
- Проверьте SMTP_SERVER и SMTP_PORT
- Убедитесь, что ваш firewall не блокирует порт 587
- Попробуйте порт 465 с SSL:
  ```python
  # В email_service.py замените:
  with smtplib.SMTP(server, port) as smtp:
  # На:
  with smtplib.SMTP_SSL(server, 465) as smtp:
  ```

### Проблема: Email не приходит

**Решение**:
1. Проверьте папку "Спам"
2. Убедитесь, что `USE_REAL_EMAIL=true`
3. Проверьте консоль сервера на наличие ошибок
4. Попробуйте отправить тестовый email через веб-интерфейс Gmail с той же почты

### Проблема: В консоли всё ещё показывается DEMO MODE

```
📧 EMAIL VERIFICATION CODE (DEMO MODE)
```

**Решение**:
- Убедитесь, что файл `.env` находится в папке `backend/`
- Установите `USE_REAL_EMAIL=true` (без пробелов)
- Перезапустите сервер полностью (Ctrl+C, затем снова `uvicorn ...`)

---

## 🔒 Безопасность

### ⚠️ Никогда не коммитьте .env файл!

Убедитесь, что `.env` добавлен в `.gitignore`:

```bash
# В файле .gitignore должно быть:
.env
.env.local
*.env
```

### 🔐 Используйте переменные окружения в production

Для production окружения (например, на сервере или в Docker):

```bash
# Linux/Mac:
export SMTP_USERNAME=your-email@gmail.com
export SMTP_PASSWORD=your-app-password
export USE_REAL_EMAIL=true

# Windows:
set SMTP_USERNAME=your-email@gmail.com
set SMTP_PASSWORD=your-app-password
set USE_REAL_EMAIL=true
```

---

## 📊 Как это работает

### 1. Пользователь запрашивает код

```
Frontend → POST /api/email-verification/send-code
         → EmailService.create_verification_code()
         → Генерация 6-значного кода
         → Сохранение в БД с expires_at = now + 10 минут
         → EmailService.send_verification_code()
         → Отправка HTML email через SMTP
```

### 2. Пользователь вводит код

```
Frontend → POST /api/email-verification/verify-code
         → EmailService.verify_code()
         → Проверка: email + code + not_expired + not_used
         → Пометка кода как использованного
         → Возврат success/error
```

### 3. База данных

Таблица `email_verifications`:
```sql
id          | email              | code   | is_verified | created_at | expires_at
------------|-------------------|--------|-------------|------------|------------
1           | user@example.com  | 123456 | false       | 2024-...   | 2024-...
```

---

## 🎯 DEMO MODE (текущий режим)

В demo mode коды **НЕ отправляются на email**, а только выводятся в консоль сервера.

Это полезно для:
- Разработки без настройки SMTP
- Тестирования без реальной почты
- Демонстрации функционала

**Чтобы увидеть код в demo mode:**
1. Откройте консоль, где запущен `uvicorn`
2. Нажмите "Отправить код" на frontend
3. В консоли появится:
   ```
   ============================================================
   📧 EMAIL VERIFICATION CODE (DEMO MODE)
   ============================================================
   To: user@example.com
   Code: 123456
   Expires: 10 minutes

   ⚠️  DEMO MODE: Email не отправлен
   ============================================================
   ```
4. Скопируйте код и введите его на frontend

---

## ✅ Checklist настройки

- [ ] Создан App Password в Gmail (или пароль для другого сервиса)
- [ ] Скопирован `.env.example` в `.env`
- [ ] Установлены переменные: SMTP_USERNAME, SMTP_PASSWORD
- [ ] Установлено `USE_REAL_EMAIL=true`
- [ ] Перезапущен сервер
- [ ] Проверка: отправка кода работает
- [ ] Проверка: email приходит (проверен Спам)
- [ ] `.env` добавлен в `.gitignore`

---

Если возникнут проблемы, проверьте консоль бэкенда на наличие подробных сообщений об ошибках.
