# Celery + Redis Setup Guide

## Обзор

Система использует Celery для асинхронной обработки задач:
- **Парсинг загруженных файлов** (PDF, CSV, Excel)
- **ML анализ транзакций** (будет добавлено позже)
- **Периодическая очистка старых файлов**

## Установка Redis

### Windows

1. **Скачать Redis для Windows**:
   - Перейдите на https://github.com/microsoftarchive/redis/releases
   - Скачайте `Redis-x64-3.0.504.msi` или новее
   - Установите Redis как сервис Windows

2. **Или используйте Memurai** (рекомендуется для Windows):
   - Перейдите на https://www.memurai.com/get-memurai
   - Скачайте и установите Memurai Developer Edition (бесплатная)
   - Автоматически запустится как сервис Windows

3. **Проверка установки**:
   ```bash
   redis-cli ping
   # Должен ответить: PONG
   ```

### Linux/macOS

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install redis-server

# macOS
brew install redis

# Запуск Redis
redis-server

# Проверка
redis-cli ping
```

## Установка зависимостей Python

```bash
cd backend
pip install -r requirements.txt
```

## Запуск системы

### 1. Запуск Redis

**Windows** (если установлен как сервис):
- Redis/Memurai запустится автоматически
- Или запустите вручную через Services (services.msc)

**Linux/macOS**:
```bash
redis-server
```

### 2. Запуск Celery Worker

Откройте **новое окно терминала**:

```bash
cd backend

# Windows
celery -A app.core.celery_app worker --loglevel=info --pool=solo

# Linux/macOS
celery -A app.core.celery_app worker --loglevel=info
```

**Опции:**
- `--loglevel=info` - уровень логирования (debug, info, warning, error)
- `--pool=solo` - для Windows (обязательно!)
- `--concurrency=4` - количество параллельных воркеров (по умолчанию = кол-во CPU)

### 3. Запуск FastAPI Backend

Откройте **еще одно окно терминала**:

```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Мониторинг задач

### Flower - Web UI для Celery

```bash
pip install flower

# Запуск Flower
celery -A app.core.celery_app flower --port=5555
```

Откройте браузер: http://localhost:5555

### Redis Commander - Web UI для Redis

```bash
npm install -g redis-commander

# Запуск
redis-commander
```

Откройте браузер: http://localhost:8081

## Очереди задач

Система использует 2 очереди:

1. **file_processing** - обработка загруженных файлов
2. **ml_analysis** - ML анализ (будет добавлено позже)

### Запуск воркера для конкретной очереди

```bash
# Только для обработки файлов
celery -A app.core.celery_app worker -Q file_processing --loglevel=info --pool=solo

# Только для ML анализа
celery -A app.core.celery_app worker -Q ml_analysis --loglevel=info --pool=solo
```

## Проверка работы

### 1. Проверка подключения к Redis

```bash
redis-cli
127.0.0.1:6379> ping
PONG
127.0.0.1:6379> keys *
(empty array)
127.0.0.1:6379> exit
```

### 2. Загрузка файла через API

```bash
curl -X POST "http://localhost:8000/api/analyses/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test_statement.pdf"
```

Ответ:
```json
{
  "id": 1,
  "file_name": "test_statement.pdf",
  "file_type": "pdf",
  "file_size": 102400,
  "status": "pending",
  "message": "File uploaded successfully. Processing started. Task ID: abc-123-def"
}
```

### 3. Проверка статуса задачи

```bash
curl "http://localhost:8000/api/analyses/task/abc-123-def/status" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Ответ:
```json
{
  "task_id": "abc-123-def",
  "status": "SUCCESS",
  "result": {
    "success": true,
    "analysis_id": 1,
    "total_transactions": 50,
    "total_amount": 1500000.0,
    "message": "Successfully parsed 50 transactions"
  },
  "info": null
}
```

### 4. Проверка анализа

```bash
curl "http://localhost:8000/api/analyses/1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Возможные проблемы

### Celery worker не запускается на Windows

**Проблема**: `ValueError: not enough values to unpack`

**Решение**: Используйте `--pool=solo`:
```bash
celery -A app.core.celery_app worker --pool=solo --loglevel=info
```

### Redis connection refused

**Проблема**: `Error 111 connecting to localhost:6379. Connection refused.`

**Решение**:
1. Проверьте, что Redis запущен: `redis-cli ping`
2. Проверьте настройки в `.env`:
   ```
   REDIS_HOST=localhost
   REDIS_PORT=6379
   ```

### Задачи не выполняются

**Проблема**: Файлы загружаются, но статус остается "pending"

**Решение**:
1. Проверьте логи Celery worker
2. Убедитесь, что воркер запущен
3. Проверьте подключение к Redis: `redis-cli keys *`

### ImportError при запуске воркера

**Проблема**: `ImportError: cannot import name 'celery_app'`

**Решение**:
1. Убедитесь, что вы в директории `backend`
2. Проверьте PYTHONPATH:
   ```bash
   # Windows
   set PYTHONPATH=%CD%

   # Linux/macOS
   export PYTHONPATH=$(pwd)
   ```

## Конфигурация для Production

### Supervisor (Linux)

Создайте `/etc/supervisor/conf.d/celery.conf`:

```ini
[program:celery_worker]
command=/path/to/venv/bin/celery -A app.core.celery_app worker --loglevel=info
directory=/path/to/backend
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/celery/worker.err.log
stdout_logfile=/var/log/celery/worker.out.log
```

### systemd (Linux)

Создайте `/etc/systemd/system/celery.service`:

```ini
[Unit]
Description=Celery Worker
After=network.target

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/path/to/backend
ExecStart=/path/to/venv/bin/celery -A app.core.celery_app worker --loglevel=info --detach
Restart=always

[Install]
WantedBy=multi-user.target
```

## Дополнительные команды

```bash
# Остановить все задачи
celery -A app.core.celery_app control shutdown

# Проверить активные задачи
celery -A app.core.celery_app inspect active

# Проверить зарегистрированные задачи
celery -A app.core.celery_app inspect registered

# Очистить очередь
celery -A app.core.celery_app purge

# Статистика воркеров
celery -A app.core.celery_app inspect stats
```

## Логи

Celery выводит логи в консоль. Для продакшена настройте логирование в файлы:

```python
# app/core/celery_app.py
celery_app.conf.update(
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s',
)
```

## Производительность

- **1 воркер** = 1 процесс Python
- **Concurrency** = количество параллельных задач в воркере
- Для файловой обработки рекомендуется: 2-4 воркера, concurrency = 1-2
- Для ML анализа рекомендуется: 1-2 воркера (из-за использования GPU/CPU)

```bash
# Запуск нескольких воркеров
celery -A app.core.celery_app worker -Q file_processing --concurrency=2 --pool=solo
celery -A app.core.celery_app worker -Q ml_analysis --concurrency=1 --pool=solo
```
