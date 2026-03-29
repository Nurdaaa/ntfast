"""
Ollama Client for Local AI Analysis
Zero-Trust: No external API calls, all processing local
"""
import json
import logging
import httpx
from typing import Dict, List, Any, Optional
from dataclasses import asdict

from .models import AnalysisReport, RiskAssessment, Transaction

logger = logging.getLogger(__name__)


class OllamaAnalyzer:
    """Local AI analyzer using Ollama"""

    def __init__(self, host: str = "http://localhost:11434", model: str = "llama3:8b"):
        self.host = host
        self.model = model
        self.timeout = 120.0

    async def check_connection(self) -> bool:
        """Check if Ollama is available"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.host}/api/tags", timeout=5.0)
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama connection failed: {e}")
            return False

    async def analyze_report(self, report: AnalysisReport) -> Dict[str, Any]:
        """Analyze full report with AI"""
        # Prepare anonymized data for AI
        prompt = self._build_analysis_prompt(report)

        try:
            response = await self._generate(prompt)
            return {
                "success": True,
                "summary": response,
                "recommendations": self._extract_recommendations(response)
            }
        except Exception as e:
            logger.error(f"Ollama analysis failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "summary": "AI analysis unavailable",
                "recommendations": []
            }

    def _build_analysis_prompt(self, report: AnalysisReport) -> str:
        """Build structured prompt for AI analysis"""
        risk = report.risk_assessment

        # Build transaction summary by category
        category_summary = {}
        for t in report.transactions:
            cat = t.category.value
            if cat not in category_summary:
                category_summary[cat] = {"count": 0, "total": 0}
            category_summary[cat]["count"] += 1
            category_summary[cat]["total"] += t.amount

        prompt = f"""You are a financial analyst reviewing a bank statement. Analyze the following anonymized data and provide insights.

IMPORTANT: All personal data has been anonymized. Use only the tags provided (e.g., [CUSTOMER_NAME], [COUNTERPARTY_1]).

=== ANALYSIS SUMMARY ===

Period: {report.account_period_start} to {report.account_period_end}
Total Transactions: {report.total_transactions}
Total Income: {report.total_income:,.0f} KZT
Total Expense: {report.total_expense:,.0f} KZT
Net Flow: {report.net_flow:,.0f} KZT

=== RISK ASSESSMENT ===

Overall Risk Score: {risk.total_score:.1f}/100 ({risk.risk_level.upper()})

1. Gaming/Gambling Risk: {risk.gaming_gambling.risk_score:.1f}/100 ({risk.gaming_gambling.risk_level})
   - Platforms: {', '.join(risk.gaming_gambling.platforms_detected) if risk.gaming_gambling.platforms_detected else 'None'}
   - Total spent: {risk.gaming_gambling.total_amount:,.0f} KZT
   - % of expenses: {risk.gaming_gambling.percentage_of_expenses:.1f}%

2. Money Laundering Risk: {risk.money_laundering.risk_score:.1f}/100 ({risk.money_laundering.risk_level})
   - Round amount transactions: {risk.money_laundering.round_amount_transactions}
   - Split transaction groups: {risk.money_laundering.split_transaction_groups}
   - Transit operations: {risk.money_laundering.transit_operations}
   - Cash intensity: {risk.money_laundering.cash_intensity:.1f}%

3. P2P Analysis Risk: {risk.p2p_analysis.risk_score:.1f}/100 ({risk.p2p_analysis.risk_level})
   - Unique counterparties: {risk.p2p_analysis.unique_counterparties}
   - Dependency on single source: {risk.p2p_analysis.dependency_on_single_source*100:.1f}%
   - Total P2P income: {risk.p2p_analysis.total_p2p_income:,.0f} KZT
   - Total P2P expense: {risk.p2p_analysis.total_p2p_expense:,.0f} KZT

=== SOCIAL PROFILE ===

Estimated Status: {risk.social_profile.estimated_status} (confidence: {risk.social_profile.confidence*100:.0f}%)
Income Sources: {', '.join(risk.social_profile.income_sources) if risk.social_profile.income_sources else 'Unknown'}
Avg Monthly Income: {risk.social_profile.avg_monthly_income:,.0f} KZT
Avg Monthly Expense: {risk.social_profile.avg_monthly_expense:,.0f} KZT
Financial Stability: {risk.social_profile.financial_stability}
Subscriptions: {', '.join(risk.social_profile.subscriptions) if risk.social_profile.subscriptions else 'None'}

=== EXPENSE BREAKDOWN ===
"""
        for cat, data in sorted(category_summary.items(), key=lambda x: x[1]["total"], reverse=True):
            prompt += f"- {cat}: {data['count']} transactions, {data['total']:,.0f} KZT\n"

        prompt += """
=== RED FLAGS ===
"""
        for flag in risk.red_flags:
            prompt += f"- {flag}\n"

        prompt += """

=== TASK ===

Based on this data, provide:
1. A brief summary of the customer's financial behavior (2-3 sentences)
2. Key risk concerns (if any)
3. Recommendations for further investigation or action
4. Assessment of financial stability

Keep your response concise and focused on actionable insights. Use bullet points where appropriate.
Response in Russian language.
"""
        return prompt

    async def _generate(self, prompt: str) -> str:
        """Generate response from Ollama"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_predict": 1024
                    }
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json().get("response", "")

    def _extract_recommendations(self, response: str) -> List[str]:
        """Extract recommendations from AI response"""
        recommendations = []
        lines = response.split('\n')

        in_recommendations = False
        for line in lines:
            line = line.strip()
            if 'рекоменд' in line.lower() or 'recommendation' in line.lower():
                in_recommendations = True
                continue
            if in_recommendations and line.startswith(('-', '•', '*', '1', '2', '3')):
                # Clean bullet point
                clean = line.lstrip('-•*0123456789. ')
                if clean:
                    recommendations.append(clean)

        return recommendations[:5]  # Limit to 5 recommendations

    async def analyze_transactions_batch(
        self,
        transactions: List[Transaction],
        batch_size: int = 50
    ) -> List[Dict[str, Any]]:
        """Analyze transactions in batches"""
        results = []

        for i in range(0, len(transactions), batch_size):
            batch = transactions[i:i + batch_size]
            prompt = self._build_transaction_batch_prompt(batch)

            try:
                response = await self._generate(prompt)
                results.append({
                    "batch_index": i // batch_size,
                    "transaction_count": len(batch),
                    "analysis": response
                })
            except Exception as e:
                logger.error(f"Batch analysis failed: {e}")
                results.append({
                    "batch_index": i // batch_size,
                    "error": str(e)
                })

        return results

    def _build_transaction_batch_prompt(self, transactions: List[Transaction]) -> str:
        """Build prompt for transaction batch analysis"""
        prompt = "Analyze these anonymized transactions for suspicious patterns:\n\n"

        for t in transactions:
            prompt += f"- {t.date.strftime('%Y-%m-%d')}: {t.anonymized_description or t.description} | "
            prompt += f"{'+' if t.transaction_type.value.endswith('in') else '-'}{t.amount:,.0f} KZT\n"

        prompt += "\nIdentify any suspicious patterns, unusual activity, or risk indicators. Response in Russian."
        return prompt


class OllamaAnalyzerSync:
    """Synchronous wrapper for OllamaAnalyzer"""

    def __init__(self, host: str = "http://localhost:11434", model: str = "llama3:8b"):
        self.host = host
        self.model = model
        self.timeout = 120.0

    def check_connection(self) -> bool:
        """Check if Ollama is available"""
        try:
            response = httpx.get(f"{self.host}/api/tags", timeout=5.0)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama connection failed: {e}")
            return False

    def generate(self, prompt: str) -> str:
        """Generate response from Ollama synchronously"""
        response = httpx.post(
            f"{self.host}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": 1024
                }
            },
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json().get("response", "")
