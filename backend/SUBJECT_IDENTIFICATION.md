# Система идентификации субъектов БЕЗ ИИН/БИН

## Обзор

Реализована новая система идентификации субъектов, которая НЕ требует наличия ИИН/БИН. Система использует комбинацию имени и типа субъекта для генерации уникальных идентификаторов.

## Ключевые изменения

### 1. Модель Subject (`app/models/subject.py`)

```python
class Subject(Base):
    unique_identifier = Column(String(200), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False, index=True)
    iin_bin = Column(String(12), index=True, nullable=True)  # Теперь опциональный
    type = Column(String(20), nullable=False)  # individual, legal_entity, account_owner
```

**Изменения:**
- Добавлено поле `unique_identifier` - главный ключ идентификации
- `iin_bin` теперь опциональный (nullable=True)
- Добавлен новый тип `account_owner` для владельцев счетов

### 2. Утилиты идентификации (`app/utils/helpers.py`)

Созданы функции для работы с новой системой идентификации:

#### `generate_subject_identifier(name, account, is_account_owner)`

Генерирует уникальный идентификатор субъекта.

**Примеры:**
```python
# Для получателя - физ. лицо
generate_subject_identifier("Ержан О.", None, False)
# → "erzhan_o_individual"

# Для получателя - организация
generate_subject_identifier("YANDEX.GO", None, False)
# → "yandex_go_organization"

# Для владельца счета (используется IBAN)
generate_subject_identifier("Владелец", "KZ00722C000000000000", True)
# → "KZ00722C000000000000"
```

#### `is_organization(name)`

Определяет, является ли субъект организацией или физическим лицом.

**Логика определения:**
- Проверяет наличие маркеров организаций (ТОО, АО, ООО, LLC, LTD, и т.д.)
- Проверяет наличие ключевых слов компаний (YANDEX, KASPI, BANK, и т.д.)
- Анализирует формат имени (ФИО vs название компании)

**Примеры:**
```python
is_organization("ТОО Астана Моторс")  # → True
is_organization("YANDEX.GO")  # → True
is_organization("Ержан О.")  # → False
is_organization("Иванов Иван Иванович")  # → False
```

#### `normalize_name(name)`

Нормализует имя для создания идентификатора.

**Преобразования:**
- Транслитерация кириллицы → латиница
- Удаление специальных символов
- Приведение к lowercase
- Замена пробелов на underscores

**Примеры:**
```python
normalize_name("Ержан О.")  # → "erzhan_o"
normalize_name("YANDEX.GO")  # → "yandex_go"
normalize_name("ТОО Астана Моторс")  # → "too_astana_motors"
```

### 3. FileProcessingService (`app/services/file_processing_service.py`)

Обновлен для использования новой системы идентификации:

```python
# Создание субъектов
unique_identifier = generate_subject_identifier(
    name=counterparty_name,
    account=None,
    is_account_owner=False
)

# Проверка существования
existing_subject = db.query(Subject).filter(
    Subject.unique_identifier == unique_identifier
).first()

# Создание нового субъекта
new_subject = Subject(
    unique_identifier=unique_identifier,
    name=name,
    type='legal_entity' if is_organization(name) else 'individual',
    iin_bin=None  # Может быть None
)
```

## Миграция базы данных

SQL скрипт миграции: `backend/migrations/add_unique_identifier_to_subjects.sql`

### Шаги миграции:

1. Добавление поля `unique_identifier`
2. Изменение `iin_bin` на nullable
3. Генерация `unique_identifier` для существующих записей
4. Удаление дубликатов
5. Добавление constraints и индексов

### Запуск миграции:

```bash
psql -U your_user -d your_database -f backend/migrations/add_unique_identifier_to_subjects.sql
```

## Примеры использования

### Создание субъекта из транзакции

```python
from app.utils.helpers import generate_subject_identifier, is_organization

# Данные контрагента
counterparty_name = "YANDEX.GO"
counterparty_account = "KZ123456789012345678"

# Генерация идентификатора
unique_identifier = generate_subject_identifier(
    name=counterparty_name,
    account=None,
    is_account_owner=False
)
# → "yandex_go_organization"

# Определение типа
subject_type = 'legal_entity' if is_organization(counterparty_name) else 'individual'
# → 'legal_entity'

# Создание субъекта
subject = Subject(
    unique_identifier=unique_identifier,
    name=counterparty_name,
    type=subject_type,
    iin_bin=None  # Нет ИИН/БИН
)
```

### Поиск субъекта

```python
# Поиск по unique_identifier
subject = db.query(Subject).filter(
    Subject.unique_identifier == "yandex_go_organization"
).first()

# Поиск по имени
subjects = db.query(Subject).filter(
    Subject.name.ilike("%yandex%")
).all()
```

## Преимущества новой системы

1. **Не требует ИИН/БИН**: Работает с любыми контрагентами
2. **Автоматическое определение типа**: ML определяет физ/юр лицо
3. **Уникальность**: Гарантируется через `unique_identifier`
4. **Гибкость**: Поддерживает владельцев счетов (IBAN) и получателей (name+type)
5. **Транслитерация**: Корректно обрабатывает кириллицу и латиницу

## Обратная совместимость

- Поле `iin_bin` сохранено для старых данных
- Можно использовать оба способа идентификации
- Миграция автоматически генерирует `unique_identifier` для existing записей

## Тестирование

### Примеры тестовых данных:

```python
# Физическое лицо
{
    "name": "Ержан О.",
    "unique_identifier": "erzhan_o_individual",
    "type": "individual",
    "iin_bin": None
}

# Юридическое лицо
{
    "name": "YANDEX.GO",
    "unique_identifier": "yandex_go_organization",
    "type": "legal_entity",
    "iin_bin": None
}

# Владелец счета
{
    "name": "Владелец счета",
    "unique_identifier": "KZ00722C000000000000",
    "type": "account_owner",
    "iin_bin": None
}
```

## Технические детали

### Транслитерация

Поддерживаются:
- Русская кириллица (А-Я, а-я)
- Казахские символы (Ә, Ғ, Қ, Ң, Ө, Ұ, Ү, Һ, І)
- Латиница (A-Z, a-z)

### Маркеры организаций

Русские: ТОО, АО, ООО, ЗАО, ПАО, ИП, ЧП, и др.
Английские: LLC, LTD, INC, CORP, CO, и др.
Международные: GMBH, AG, SA, BV, NV, и др.
Казахстанские: ЖШС, АҚ, ҚҚ

### Ключевые слова компаний

YANDEX, KASPI, HALYK, FORTE, BANK, MARKET, SERVICE, GROUP, и др.

## Roadmap

- [ ] Добавить API endpoints для работы с unique_identifier
- [ ] Обновить frontend для отображения новых идентификаторов
- [ ] Добавить тесты для функций идентификации
- [ ] Расширить список маркеров организаций
- [ ] Добавить поддержку других языков (английский, казахский)
