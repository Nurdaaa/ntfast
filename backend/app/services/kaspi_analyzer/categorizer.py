"""
Transaction Categorizer
Smart categorization based on merchant names and patterns
"""
import re
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
from dataclasses import dataclass


@dataclass
class CategoryMatch:
    """Category match result"""
    category: str
    subcategory: str
    confidence: float
    matched_keyword: str


class TransactionCategorizer:
    """Categorizes transactions based on details field"""

    # Expense categories with keywords
    EXPENSE_CATEGORIES = {
        "transport": {
            "name": "Транспорт",
            "icon": "car",
            "keywords": [
                "YANDEX.GO", "ЯНДЕКС.GO", "YANDEX.DELIVERY", "ЯНДЕКС.ДОСТАВКА",
                "YANDEX ВПЕРЁД", "ЯНДЕКС ВПЕРЁД", "Автобыс", "Парковка",
                "BOLT", "UBER", "INDRIVER", "Такси", "АЗС", "БЕНЗИН"
            ]
        },
        "food_grocery": {
            "name": "Еда и продукты",
            "icon": "shopping-cart",
            "keywords": [
                "Salem Duken", "Family", "Асхана", "Durum", "овощной",
                "Рахмет магазин", "Береке", "ARCADA", "Hello food", "Рассвет",
                "Мама Маркет", "маг жайлау", "Континенталь", "Био", "ЭконоМаркет",
                "МЕЧТА МАРКЕТ", "Манас", "Бегемот", "Big Ben", "магазин Нур",
                "Рахат минимаркет", "A7 market", "Magnum", "SMALL", "Продукты",
                "Овощи", "Фрукты", "Супермаркет", "Минимаркет", "Бакалея"
            ]
        },
        "gaming": {
            "name": "Игры и развлечения",
            "icon": "gamepad-2",
            "keywords": [
                "SENET", "CODASHOP", "Steam", "TOP GAME", "Gold Game",
                "Underground", "Меркурий", "SUPERCELL", "FS *SUPERCELL",
                "Xsolla", "Арена", "Чаплин", "Soul Tennis", "PlayStation",
                "XBOX", "Nintendo", "Epic Games", "Riot", "Blizzard",
                "Кинотеатр", "Боулинг", "Бильярд"
            ]
        },
        "subscriptions": {
            "name": "Подписки и сервисы",
            "icon": "smartphone",
            "keywords": [
                "APPLE.COM", "APPLE COM", "Spotify", "CLAUDE", "CLAUDE.AI",
                "YANDEX.PLUS", "ЯНДЕКС.ПЛЮС", "Altel", "Netflix", "YouTube",
                "OpenAI", "ChatGPT", "Amazon Prime", "iCloud", "Подписка"
            ]
        },
        "shopping": {
            "name": "Шоппинг",
            "icon": "shopping-bag",
            "keywords": [
                "Intertop", "Интертоп", "Qazaq Republic", "URBAN OUTFIT",
                "INTERSPORT", "GOLDAPPLE", "NOMADICA", "Arba.kz", "Jakx.kz",
                "Tshopkz", "MNM FUTURE", "BEATRICE", "Bambino", "МҰСТАФА",
                "Керуен", "R77", "ZARA", "H&M", "LC Waikiki", "Bershka"
            ]
        },
        "food_delivery": {
            "name": "Доставка еды",
            "icon": "utensils",
            "keywords": [
                "YANDEX.EDA", "ЯНДЕКС.ЕДА", "WOLT", "Glovo", "Chocofood",
                "YANDEX.LAVKA", "ЯНДЕКС.ЛАВКА", "Delivery Club"
            ]
        },
        "postal": {
            "name": "Почта и доставка",
            "icon": "package",
            "keywords": [
                "Яна Пост", "Jana Post", "Казпочта", "СДЭК", "DHL", "FedEx"
            ]
        },
        "health": {
            "name": "Здоровье",
            "icon": "heart-pulse",
            "keywords": [
                "PHARMACY", "EUROPHARMA", "GalamatPharm", "Love Dent",
                "Nur Clinic", "Медицинский центр", "Аптека", "Стоматология",
                "Клиника", "Лаборатория", "Анализы"
            ]
        },
        "utilities": {
            "name": "Связь и коммуналка",
            "icon": "home",
            "keywords": [
                "Живая Вода", "Коммунальн", "Электричество", "Газ", "Вода",
                "Интернет", "Beeline", "Kcell", "Tele2", "Activ"
            ]
        },
        "online_shopping": {
            "name": "Онлайн-покупки",
            "icon": "globe",
            "keywords": [
                "PINDUODUO", "FFT*PINDUODUO", "TVLAND", "verytrendyus",
                "КАСПИ МАГАЗИН", "Kaspi Магазин", "AliExpress", "Wildberries",
                "OZON", "ШМУЛЬКО"
            ]
        },
        "restaurants": {
            "name": "Рестораны",
            "icon": "utensils-crossed",
            "keywords": [
                "Restaurant", "Ресторан", "Doner", "BEER GOOD", "REZEPT",
                "Ranch Social", "Shashlych", "Janzeto", "Sardar", "SMALL",
                "Durum K27", "Кафе", "Бар", "Паб", "Столовая", "I'm Restaurants"
            ]
        },
        "banking": {
            "name": "Банковские услуги",
            "icon": "credit-card",
            "keywords": [
                "Комиссия", "Обслуживание", "Перевыпуск", "Страховка карты"
            ]
        },
        "insurance": {
            "name": "Страхование",
            "icon": "shield",
            "keywords": [
                "ОСМС", "обязательное соц", "страхование", "ЕНПФ"
            ]
        },
        "charity": {
            "name": "Благотворительность",
            "icon": "heart-handshake",
            "keywords": [
                "Фонд", "Благотворител", "Человек в маске", "Пожертвование"
            ]
        }
    }

    # Transfer categories
    TRANSFER_CATEGORIES = {
        "deposit": {
            "name": "Депозит",
            "icon": "landmark",
            "keywords": ["Kaspi Депозит", "На Kaspi Депозит", "С Kaspi Депозит"]
        },
        "interbank": {
            "name": "Межбанк",
            "icon": "building-2",
            "keywords": ["другого банка", "другой банк"]
        }
    }

    # Income categories
    INCOME_CATEGORIES = {
        "pension": {
            "name": "Пенсия/пособие",
            "icon": "briefcase",
            "keywords": ["Пенсия", "пособие", "ГЦВП", "соцвыплат"]
        },
        "deposit": {
            "name": "С депозита",
            "icon": "landmark",
            "keywords": ["С Kaspi Депозит"]
        },
        "interbank": {
            "name": "Межбанк",
            "icon": "building-2",
            "keywords": ["С карты другого банка"]
        }
    }

    def __init__(self):
        self.contact_frequency: Dict[str, int] = defaultdict(int)
        self.frequent_contacts: set = set()

    def analyze_contacts(self, transactions: List) -> None:
        """Analyze transfer frequency to identify frequent contacts"""
        for tx in transactions:
            if tx.type in ['Перевод', 'Пополнение']:
                # Extract contact name from details
                contact = self._extract_contact_name(tx.details)
                if contact:
                    self.contact_frequency[contact] += 1

        # Contacts with 5+ transactions are "frequent"
        self.frequent_contacts = {
            name for name, count in self.contact_frequency.items()
            if count >= 5
        }

    def _extract_contact_name(self, details: str) -> Optional[str]:
        """Extract person name from transaction details"""
        # Skip non-person transfers
        skip_patterns = ['Kaspi Депозит', 'другого банка', 'Пенсия', 'пособие']
        for pattern in skip_patterns:
            if pattern.lower() in details.lower():
                return None

        # Kazakh/Russian name pattern: "Name S." or "Name Surname"
        name_match = re.search(r'([А-ЯЁа-яёӘәҒғҚқҢңӨөҰұҮүІіҺһəƏ]+\s+[А-ЯЁа-яёƏə]\.?)', details)
        if name_match:
            return name_match.group(1).strip()

        return None

    def categorize(self, tx) -> Tuple[str, str]:
        """Categorize a single transaction"""
        details_upper = tx.details.upper()
        details_lower = tx.details.lower()

        # Handle by transaction type
        if tx.type == 'Покупка':
            return self._categorize_purchase(details_upper, details_lower)
        elif tx.type == 'Перевод':
            return self._categorize_transfer(tx.details, tx.amount)
        elif tx.type == 'Пополнение':
            return self._categorize_income(tx.details)
        elif tx.type == 'Снятие':
            return "Снятие наличных", "Снятие"
        elif tx.type == 'Разное':
            return self._categorize_misc(details_lower)

        return "Прочее", "Неопределено"

    def _categorize_purchase(self, details_upper: str, details_lower: str) -> Tuple[str, str]:
        """Categorize purchase transaction"""
        for cat_id, cat_info in self.EXPENSE_CATEGORIES.items():
            for keyword in cat_info['keywords']:
                if keyword.upper() in details_upper:
                    return cat_info['name'], keyword
        return "Прочие покупки", "Другое"

    def _categorize_transfer(self, details: str, amount: float) -> Tuple[str, str]:
        """Categorize transfer transaction"""
        details_lower = details.lower()

        # Check special transfer types
        for cat_id, cat_info in self.TRANSFER_CATEGORIES.items():
            for keyword in cat_info['keywords']:
                if keyword.lower() in details_lower:
                    return cat_info['name'], keyword

        # Check if it's a person transfer
        contact = self._extract_contact_name(details)
        if contact:
            if contact in self.frequent_contacts:
                return "Частые контакты", contact
            else:
                return "Остальные контакты", contact

        return "Перевод", details[:30]

    def _categorize_income(self, details: str) -> Tuple[str, str]:
        """Categorize income/deposit transaction"""
        details_lower = details.lower()

        # Check income categories
        for cat_id, cat_info in self.INCOME_CATEGORIES.items():
            for keyword in cat_info['keywords']:
                if keyword.lower() in details_lower:
                    return cat_info['name'], keyword

        # Check if from person
        contact = self._extract_contact_name(details)
        if contact:
            if contact in self.frequent_contacts:
                return "От частых контактов", contact
            else:
                return "От остальных", contact

        return "Пополнение", details[:30]

    def _categorize_misc(self, details_lower: str) -> Tuple[str, str]:
        """Categorize miscellaneous transaction"""
        if 'комиссия' in details_lower:
            return "Банковские услуги", "Комиссия"
        if 'страхов' in details_lower:
            return "Страхование", "Страховка"
        return "Разное", "Другое"

    def get_contact_stats(self) -> Dict[str, Dict]:
        """Get statistics for all contacts"""
        return {
            name: {
                "count": count,
                "is_frequent": name in self.frequent_contacts
            }
            for name, count in sorted(
                self.contact_frequency.items(),
                key=lambda x: x[1],
                reverse=True
            )
        }
