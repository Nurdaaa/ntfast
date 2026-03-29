# Установка и запуск Redis для Windows 11

## Текущий статус

✅ Python библиотеки установлены (celery, redis)
✅ Docker установлен
✅ docker-compose.yml создан
⏸️  Redis сервер нужно запустить

## Быстрый старт (через Docker)

### Шаг 1: Запустите Docker Desktop

1. Найдите **Docker Desktop** в меню Пуск
2. Запустите приложение
3. Дождитесь, пока Docker запустится (в трее появится значок)

### Шаг 2: Запустите Redis

Откройте терминал в папке проекта и выполните:

```bash
cd C:/Users/nurda/FinancialAnalysisSystem
docker-compose up -d
```

Эта команда:
- Скачает образ Redis (при первом запуске)
- Запустит контейнер в фоновом режиме
- Redis будет доступен на `localhost:6379`

### Шаг 3: Проверьте, что Redis работает

```bash
docker ps
```

Вы должны увидеть контейнер `financial_analysis_redis` со статусом `Up`.

Или проверьте подключение:

```bash
docker exec -it financial_analysis_redis redis-cli ping
```

Должен вернуть: `PONG`

## Управление Redis

### Остановить Redis:
```bash
docker-compose stop
```

### Запустить Redis (если остановлен):
```bash
docker-compose start
```

### Перезапустить Redis:
```bash
docker-compose restart
```

### Остановить и удалить контейнер:
```bash
docker-compose down
```

### Остановить и удалить контейнер + данные:
```bash
docker-compose down -v
```

### Посмотреть логи Redis:
```bash
docker-compose logs -f redis
```

## Запуск всей системы

После того как Redis запущен, запустите всю систему:

### Терминал 1: Backend API
```bash
cd C:/Users/nurda/FinancialAnalysisSystem/backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Терминал 2: Celery Worker
```bash
cd C:/Users/nurda/FinancialAnalysisSystem/backend
celery -A app.core.celery_app worker --loglevel=info --pool=solo
```

### Терминал 3: Frontend (опционально)
```bash
cd C:/Users/nurda/FinancialAnalysisSystem/frontend
npm run dev
```

## Альтернативные методы установки Redis

Если по какой-то причине Docker не работает, вы можете установить Redis напрямую:

### Вариант 1: Memurai (рекомендуется для Windows)

1. Перейдите на https://www.memurai.com/get-memurai
2. Скачайте **Memurai Developer Edition** (бесплатная)
3. Установите как обычное Windows приложение
4. Memurai автоматически запустится как служба Windows
5. Redis будет доступен на `localhost:6379`

### Вариант 2: WSL2 + Redis

```bash
# В WSL2 терминале
sudo apt update
sudo apt install redis-server
sudo service redis-server start
redis-cli ping
```

## Проверка подключения из Python

Создайте тестовый файл `test_redis.py`:

```python
import redis

try:
    r = redis.Redis(host='localhost', port=6379, db=0)
    r.ping()
    print("✅ Redis подключен успешно!")

    # Тест записи/чтения
    r.set('test_key', 'Hello Redis!')
    value = r.get('test_key')
    print(f"✅ Тест записи/чтения: {value.decode()}")

except redis.ConnectionError as e:
    print(f"❌ Ошибка подключения к Redis: {e}")
    print("\n🔧 Убедитесь, что Redis запущен:")
    print("   - Docker: docker-compose up -d")
    print("   - Memurai: проверьте Services (services.msc)")
```

Запустите:
```bash
python test_redis.py
```

## Мониторинг Redis

### Redis CLI (встроенный в контейнер)

```bash
# Подключиться к Redis CLI
docker exec -it financial_analysis_redis redis-cli

# Команды в Redis CLI:
127.0.0.1:6379> ping              # Проверка подключения
127.0.0.1:6379> keys *            # Показать все ключи
127.0.0.1:6379> info              # Информация о сервере
127.0.0.1:6379> dbsize            # Количество ключей
127.0.0.1:6379> flushall          # Очистить все данные
127.0.0.1:6379> exit              # Выход
```

### Flower (Web UI для Celery)

```bash
pip install flower
celery -A app.core.celery_app flower --port=5555
```

Откройте: http://localhost:5555

### RedisInsight (GUI для Redis)

1. Скачайте: https://redis.com/redis-enterprise/redis-insight/
2. Установите
3. Подключитесь к `localhost:6379`

## Troubleshooting

### Проблема: Docker Desktop не запускается

**Решение**:
1. Убедитесь, что включена виртуализация в BIOS
2. Включите WSL2: `wsl --install`
3. Перезагрузите компьютер

### Проблема: Порт 6379 уже занят

**Решение**:
```bash
# Найти процесс на порту 6379
netstat -ano | findstr :6379

# Завершить процесс (замените PID)
taskkill /PID <номер_процесса> /F
```

Или измените порт в `docker-compose.yml`:
```yaml
ports:
  - "6380:6379"  # Используем 6380 вместо 6379
```

И обновите настройки в `backend/app/core/config.py`:
```python
REDIS_PORT: int = 6380
```

### Проблема: "Connection refused" при подключении к Redis

**Проверьте**:
1. Redis запущен: `docker ps`
2. Firewall не блокирует порт 6379
3. В коде используется правильный хост: `localhost` или `127.0.0.1`

## Следующие шаги

После запуска Redis:

1. ✅ Проверьте подключение: `python test_redis.py`
2. ✅ Запустите Celery worker: `celery -A app.core.celery_app worker --pool=solo --loglevel=info`
3. ✅ Запустите backend: `uvicorn app.main:app --reload`
4. ✅ Протестируйте загрузку файла через API

Документация по Celery: `backend/CELERY_SETUP.md`
