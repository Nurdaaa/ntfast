"""
Subject Identification Helpers
Утилиты для идентификации субъектов БЕЗ ИИН/БИН
"""
import re
from typing import Optional, Tuple
import unicodedata


def normalize_name(name: str) -> str:
    """
    Нормализация имени для создания идентификатора

    Args:
        name: Исходное имя

    Returns:
        Нормализованное имя (латиница, lowercase, underscores)

    Examples:
        "Ержан О." -> "erzhan_o"
        "YANDEX.GO" -> "yandex_go"
        "ТОО Астана Моторс" -> "too_astana_motors"
    """
    if not name:
        return "unknown"

    # Убираем лишние пробелы
    name = ' '.join(name.split())

    # Транслитерация кириллицы в латиницу
    translit_map = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
        'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'E',
        'Ж': 'Zh', 'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M',
        'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U',
        'Ф': 'F', 'Х': 'H', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Shch',
        'Ъ': '', 'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya',
        'Ә': 'A', 'Ғ': 'G', 'Қ': 'Q', 'Ң': 'N', 'Ө': 'O', 'Ұ': 'U', 'Ү': 'U', 'Һ': 'H', 'І': 'I',
        'ә': 'a', 'ғ': 'g', 'қ': 'q', 'ң': 'n', 'ө': 'o', 'ұ': 'u', 'ү': 'u', 'һ': 'h', 'і': 'i'
    }

    # Транслитерация
    result = []
    for char in name:
        if char in translit_map:
            result.append(translit_map[char])
        else:
            result.append(char)

    normalized = ''.join(result)

    # Удаление акцентов из других языков
    normalized = unicodedata.normalize('NFKD', normalized)
    normalized = ''.join([c for c in normalized if not unicodedata.combining(c)])

    # Оставляем только буквы, цифры и пробелы
    normalized = re.sub(r'[^a-zA-Z0-9\s]', '', normalized)

    # Приводим к lowercase и заменяем пробелы на underscores
    normalized = normalized.lower().strip()
    normalized = re.sub(r'\s+', '_', normalized)

    # Убираем повторяющиеся underscores
    normalized = re.sub(r'_+', '_', normalized)

    # Убираем underscores в начале и конце
    normalized = normalized.strip('_')

    return normalized if normalized else "unknown"


def is_organization(name: str) -> bool:
    """
    Определение, является ли субъект организацией

    Args:
        name: Имя субъекта

    Returns:
        True если организация, False если физическое лицо

    Examples:
        "ТОО Астана Моторс" -> True
        "YANDEX.GO" -> True
        "Ержан О." -> False
        "Иванов Иван Иванович" -> False
    """
    if not name:
        return False

    name_upper = name.upper()

    # Маркеры организаций (русский и английский)
    org_markers = [
        # Русские
        'ТОО', 'АО', 'ООО', 'ЗАО', 'ПАО', 'НАО', 'ОАО',
        'ИП', 'ЧП', 'КХ', 'ГП', 'МП', 'УП',
        # Английские
        'LLC', 'LTD', 'INC', 'CORP', 'CO', 'CORPORATION',
        'LIMITED', 'COMPANY', 'JSC', 'OJSC', 'CJSC',
        # Международные
        'GMBH', 'AG', 'SA', 'BV', 'NV', 'SPA', 'SRL',
        # Казахстанские
        'ЖШС', 'АҚ', 'ҚҚ',
    ]

    # Проверка наличия маркеров организации
    for marker in org_markers:
        # Проверяем как отдельное слово или в начале
        if re.search(r'\b' + re.escape(marker) + r'\b', name_upper):
            return True

    # Специальные паттерны для популярных компаний
    company_patterns = [
        r'YANDEX',
        r'KASPI',
        r'HALYK',
        r'FORTE',
        r'EURASIAN',
        r'BANK',
        r'БАНК',
        r'МАРКЕТ',
        r'MARKET',
        r'SERVICE',
        r'СЕРВИС',
        r'GROUP',
        r'ГРУППА',
    ]

    for pattern in company_patterns:
        if re.search(pattern, name_upper):
            return True

    # Если содержит точку в середине (например "O." или "А.") - скорее всего физлицо
    if re.search(r'\b[А-ЯA-Z]\.\s*$', name):
        return False

    # Если имя состоит из 2-3 слов с большой буквы и без маркеров - вероятно физлицо
    words = name.split()
    if 2 <= len(words) <= 4:
        # Проверяем, все ли слова с большой буквы (как в ФИО)
        capitalized_words = [w for w in words if w and w[0].isupper()]
        if len(capitalized_words) == len(words) and not any(marker in name_upper for marker in org_markers):
            # Если нет цифр и специальных символов - скорее всего физлицо
            if not re.search(r'[0-9]', name):
                return False

    # По умолчанию считаем организацией (безопаснее)
    return True


def generate_subject_identifier(
    name: str,
    account: Optional[str] = None,
    is_account_owner: bool = False
) -> str:
    """
    Генерация уникального идентификатора субъекта

    Args:
        name: Имя субъекта
        account: Номер счета (IBAN)
        is_account_owner: True если это владелец счета

    Returns:
        Уникальный идентификатор

    Examples:
        generate_subject_identifier("Ержан О.", is_account_owner=False)
            -> "erzhan_o_individual"
        generate_subject_identifier("YANDEX.GO", is_account_owner=False)
            -> "yandex_go_organization"
        generate_subject_identifier("Владелец", "KZ00722C000000000000", is_account_owner=True)
            -> "KZ00722C000000000000"
    """
    # Для владельца счета используем IBAN
    if is_account_owner and account:
        # Очищаем IBAN от пробелов
        clean_account = re.sub(r'\s+', '', account.upper())
        return clean_account

    # Для получателей используем нормализованное имя + тип
    normalized = normalize_name(name)
    subject_type = "organization" if is_organization(name) else "individual"

    return f"{normalized}_{subject_type}"


def parse_subject_identifier(identifier: str) -> Tuple[str, str]:
    """
    Парсинг идентификатора субъекта

    Args:
        identifier: Идентификатор субъекта

    Returns:
        Tuple (type, normalized_name)
        type: "account_owner", "individual", or "organization"
        normalized_name: Нормализованное имя или IBAN

    Examples:
        parse_subject_identifier("KZ00722C000000000000")
            -> ("account_owner", "KZ00722C000000000000")
        parse_subject_identifier("erzhan_o_individual")
            -> ("individual", "erzhan_o")
        parse_subject_identifier("yandex_go_organization")
            -> ("organization", "yandex_go")
    """
    # Проверка на IBAN (начинается с KZ и состоит из букв и цифр)
    if re.match(r'^[A-Z]{2}[0-9A-Z]+$', identifier):
        return ("account_owner", identifier)

    # Парсинг идентификатора формата "name_type"
    if identifier.endswith("_individual"):
        name = identifier[:-11]  # убираем "_individual"
        return ("individual", name)
    elif identifier.endswith("_organization"):
        name = identifier[:-13]  # убираем "_organization"
        return ("organization", name)
    else:
        # Неизвестный формат - считаем организацией по умолчанию
        return ("organization", identifier)


def get_subject_display_name(identifier: str, original_name: Optional[str] = None) -> str:
    """
    Получение отображаемого имени субъекта

    Args:
        identifier: Идентификатор субъекта
        original_name: Оригинальное имя (если есть)

    Returns:
        Имя для отображения
    """
    if original_name:
        return original_name

    subject_type, normalized = parse_subject_identifier(identifier)

    if subject_type == "account_owner":
        return f"Владелец счета {normalized}"

    # Преобразуем обратно из normalized формата
    display = normalized.replace('_', ' ').title()

    if subject_type == "individual":
        return f"{display} (физ. лицо)"
    else:
        return f"{display} (организация)"
