"""
Структурированные промпты для AI-анализа финансовых транзакций
Оптимизированы для Claude API с structured output
"""

SYSTEM_PROMPT = """Ты — эксперт-аналитик по финансовым преступлениям и антифроду.
Ты анализируешь банковские выписки граждан Казахстана.
Валюта: тенге (KZT). Банки: Kaspi Bank, Halyk Bank, и другие.
Ответы давай на русском языке. Будь точным и конкретным."""

FRAUD_ANALYSIS_PROMPT = """Проанализируй следующие данные банковской выписки и выяви подозрительные паттерны:

## Сводка по счёту
- Владелец: {owner}
- Период: {period}
- Транзакций: {total_transactions}
- Доход: {total_income:,.0f} ₸
- Расход: {total_expense:,.0f} ₸
- Чистый поток: {net_flow:,.0f} ₸

## Результаты антифрод-анализа
{fraud_summary}

## Сетевой анализ контактов
{graph_summary}

## Velocity-аномалии
{velocity_summary}

## Топ контрагенты (по объёму)
{top_counterparties}

## Категории расходов
{category_breakdown}

Дай структурированную оценку рисков."""

RISK_ASSESSMENT_SCHEMA = {
    "type": "object",
    "properties": {
        "overall_risk_level": {
            "type": "string",
            "enum": ["low", "medium", "high", "critical"],
            "description": "Общий уровень риска"
        },
        "risk_score": {
            "type": "number",
            "minimum": 0,
            "maximum": 100,
            "description": "Числовой скор риска 0-100"
        },
        "key_findings": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Ключевые находки (3-7 пунктов)"
        },
        "fraud_indicators": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "indicator": {"type": "string", "description": "Название индикатора"},
                    "severity": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                    "evidence": {"type": "string", "description": "Доказательства"},
                    "recommendation": {"type": "string", "description": "Рекомендация"}
                },
                "required": ["indicator", "severity", "evidence", "recommendation"]
            },
            "description": "Индикаторы мошенничества"
        },
        "behavioral_profile": {
            "type": "string",
            "description": "Поведенческий профиль владельца счёта (2-3 предложения)"
        },
        "narrative_summary": {
            "type": "string",
            "description": "Полный нарративный отчёт (5-10 предложений)"
        },
        "recommendations": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Рекомендации для аналитика (3-5 пунктов)"
        }
    },
    "required": ["overall_risk_level", "risk_score", "key_findings",
                  "fraud_indicators", "narrative_summary", "recommendations"]
}
