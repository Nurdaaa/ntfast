"""
ntFAST PDF Report Generator
Clean, professional B&W design with minimal accent colors.
"""
import io
import re
import math
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from xml.sax.saxutils import escape as xml_escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether,
)
from reportlab.graphics.shapes import Drawing, Circle, Rect, String, Line, Polygon, Group, Wedge
from reportlab.graphics import renderPDF
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus.flowables import Flowable

logger = logging.getLogger(__name__)

# ─── Register TTF font with Cyrillic support ───────────────
_FONT_REGISTERED = False


def _register_fonts():
    """Register Arial TTF font for Cyrillic support. Falls back to Helvetica."""
    global _FONT_REGISTERED
    if _FONT_REGISTERED:
        return
    _FONT_REGISTERED = True

    import os
    fonts_dir = "C:/Windows/Fonts"
    font_map = {
        "NtFont": "arial.ttf",
        "NtFont-Bold": "arialbd.ttf",
        "NtFont-Italic": "ariali.ttf",
        "NtFont-BoldItalic": "arialbi.ttf",
    }

    for font_name, font_file in font_map.items():
        font_path = os.path.join(fonts_dir, font_file)
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont(font_name, font_path))
            except Exception as e:
                logger.warning(f"Could not register font {font_name}: {e}")

    from reportlab.pdfbase.pdfmetrics import registerFontFamily
    try:
        registerFontFamily(
            "NtFont",
            normal="NtFont",
            bold="NtFont-Bold",
            italic="NtFont-Italic",
            boldItalic="NtFont-BoldItalic",
        )
        logger.info("ntFAST PDF fonts registered (Arial with Cyrillic support)")
    except Exception as e:
        logger.warning(f"Font family registration failed: {e}")


FONT_NORMAL = "NtFont"
FONT_BOLD = "NtFont-Bold"

# Regex to strip emoji and other non-printable/non-ASCII symbols
_EMOJI_RE = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF"
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "\U0001f926-\U0001f937"
    "\U00010000-\U0010ffff"
    "\u2600-\u26FF"
    "\u2700-\u27BF"
    "\u200d\ufe0f"
    "]+",
    flags=re.UNICODE,
)


def _sanitize(text: Any) -> str:
    """Sanitize text for safe use in ReportLab Paragraphs."""
    if text is None:
        return "N/A"
    s = str(text)
    s = s.replace("\u20b8", " KZT")
    s = s.replace("\u20bd", " RUB")
    s = s.replace("\u20ac", " EUR")
    s = s.replace("\u00a5", " JPY")
    s = s.replace("\u00a3", " GBP")
    s = _EMOJI_RE.sub("", s)
    s = "".join(c for c in s if ord(c) < 0x10000)
    s = xml_escape(s)
    s = " ".join(s.split())
    return s.strip() or "N/A"


# ─── B&W Color Palette ──────────────────────────────────────
BLACK = colors.HexColor("#000000")
DARK = colors.HexColor("#1a1a1a")
DARK_GRAY = colors.HexColor("#333333")
MID_GRAY = colors.HexColor("#666666")
GRAY = colors.HexColor("#999999")
LIGHT_GRAY = colors.HexColor("#E5E5E5")
PALE_GRAY = colors.HexColor("#F5F5F5")
WHITE = colors.HexColor("#FFFFFF")

# Accent colors — used ONLY for risk levels
RISK_LOW = colors.HexColor("#22C55E")       # Green — low risk
RISK_MEDIUM = colors.HexColor("#EAB308")    # Yellow — medium risk
RISK_HIGH = colors.HexColor("#EF4444")      # Red — high risk
RISK_CRITICAL = colors.HexColor("#DC2626")  # Dark red — critical risk

# Single accent for income/expense distinction
ACCENT_POSITIVE = colors.HexColor("#22C55E")
ACCENT_NEGATIVE = colors.HexColor("#EF4444")

MODULE_NAMES = {
    "velocity": "Velocity Analysis",
    "graph": "Graph / Network",
    "behavioral": "Behavioral",
    "structuring": "Structuring",
    "cross_reference": "Cross-Reference",
    "merchant_risk": "Merchant Risk",
    "night_transactions": "Night Transactions",
    "duplicate_payments": "Duplicate Payments",
    "round_amounts": "Round Amounts",
    "profile_mismatch": "Profile Mismatch",
}


def _risk_color(score: float) -> colors.HexColor:
    if score >= 75:
        return RISK_CRITICAL
    elif score >= 50:
        return RISK_HIGH
    elif score >= 25:
        return RISK_MEDIUM
    return RISK_LOW


def _risk_label(level: str) -> str:
    return {
        "low": "LOW",
        "medium": "MEDIUM",
        "high": "HIGH",
        "critical": "CRITICAL",
    }.get(level, level.upper())


def _fmt_amount(val: Any, currency: str = "") -> str:
    try:
        num = float(val)
        if abs(num) >= 1_000_000:
            return f"{num:,.0f} {currency}".strip()
        return f"{num:,.2f} {currency}".strip()
    except (ValueError, TypeError):
        return str(val)


def _safe_get(d: dict, *keys, default=None):
    current = d
    for k in keys:
        if isinstance(current, dict):
            current = current.get(k, default)
        else:
            return default
    return current


# ─── Custom Flowables ───────────────────────────────────────

class RiskGaugeFlowable(Flowable):
    """Minimal B&W risk gauge with color only on the active segment."""

    def __init__(self, score: float, risk_level: str, width: float = 200, height: float = 110):
        Flowable.__init__(self)
        self.score = min(max(score, 0), 100)
        self.risk_level = risk_level
        self.width = width
        self.height = height

    def wrap(self, aW, aH):
        return self.width, self.height

    def draw(self):
        canvas = self.canv
        cx = self.width / 2
        cy = 28
        radius = 72

        # Background arc — light gray
        canvas.setStrokeColor(LIGHT_GRAY)
        canvas.setLineWidth(10)
        canvas.arc(
            cx - radius, cy - radius,
            cx + radius, cy + radius,
            startAng=0, extent=180,
        )

        # Active arc segment — colored by risk level
        active_color = _risk_color(self.score)
        extent = self.score / 100 * 180
        canvas.setStrokeColor(active_color)
        canvas.setLineWidth(10)
        canvas.arc(
            cx - radius, cy - radius,
            cx + radius, cy + radius,
            startAng=180, extent=-extent,
        )

        # Needle
        angle_deg = 180 - (self.score / 100 * 180)
        angle_rad = math.radians(angle_deg)
        needle_len = radius - 18
        nx = cx + needle_len * math.cos(angle_rad)
        ny = cy + needle_len * math.sin(angle_rad)

        canvas.setStrokeColor(DARK)
        canvas.setLineWidth(2)
        canvas.line(cx, cy, nx, ny)

        # Center dot
        canvas.setFillColor(DARK)
        canvas.circle(cx, cy, 4, fill=1, stroke=0)

        # Score text
        canvas.setFont(FONT_BOLD, 20)
        canvas.setFillColor(DARK)
        canvas.drawCentredString(cx, cy - 20, f"{self.score:.0f}")

        # Risk label
        canvas.setFont(FONT_BOLD, 9)
        canvas.setFillColor(active_color)
        canvas.drawCentredString(cx, cy - 32, _risk_label(self.risk_level))

        # Scale labels
        canvas.setFont(FONT_NORMAL, 6.5)
        canvas.setFillColor(GRAY)
        canvas.drawString(cx - radius - 3, cy - 6, "0")
        canvas.drawCentredString(cx, cy + radius + 3, "50")
        canvas.drawRightString(cx + radius + 3, cy - 6, "100")


class RadarChartFlowable(Flowable):
    """B&W radar chart with single dark fill."""

    def __init__(self, module_scores: Dict[str, float], width: float = 240, height: float = 220):
        Flowable.__init__(self)
        self.module_scores = module_scores
        self.width = width
        self.height = height

    def wrap(self, aW, aH):
        return self.width, self.height

    def draw(self):
        canvas = self.canv
        cx = self.width / 2
        cy = self.height / 2 - 5
        radius = 80
        modules = list(self.module_scores.items())
        n = len(modules)
        if n == 0:
            return

        # Concentric circles
        for r_pct in [25, 50, 75, 100]:
            r = radius * r_pct / 100
            canvas.setStrokeColor(LIGHT_GRAY)
            canvas.setLineWidth(0.4)
            canvas.circle(cx, cy, r, fill=0)

        # Axes and labels
        for i, (name, score) in enumerate(modules):
            angle = math.pi / 2 + (2 * math.pi * i / n)
            x_end = cx + radius * math.cos(angle)
            y_end = cy + radius * math.sin(angle)

            canvas.setStrokeColor(LIGHT_GRAY)
            canvas.setLineWidth(0.4)
            canvas.line(cx, cy, x_end, y_end)

            lx = cx + (radius + 16) * math.cos(angle)
            ly = cy + (radius + 16) * math.sin(angle)
            canvas.setFont(FONT_NORMAL, 6)
            canvas.setFillColor(MID_GRAY)
            display_name = MODULE_NAMES.get(name, name)
            canvas.drawCentredString(lx, ly - 3, display_name)

        # Score polygon — dark fill with transparency
        points = []
        for i, (name, score) in enumerate(modules):
            angle = math.pi / 2 + (2 * math.pi * i / n)
            r = radius * min(score, 100) / 100
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            points.append((x, y))

        if points:
            path = canvas.beginPath()
            path.moveTo(points[0][0], points[0][1])
            for px, py in points[1:]:
                path.lineTo(px, py)
            path.close()
            canvas.setFillColor(colors.Color(0.15, 0.15, 0.15, 0.12))
            canvas.setStrokeColor(DARK_GRAY)
            canvas.setLineWidth(1.2)
            canvas.drawPath(path, fill=1, stroke=1)

            # Score dots
            for px, py in points:
                canvas.setFillColor(DARK)
                canvas.circle(px, py, 2.5, fill=1, stroke=0)


class ModuleScoreBar(Flowable):
    """Minimal horizontal bar — gray background, dark fill, color only on score number."""

    def __init__(self, name: str, score: float, width: float = 220, height: float = 22):
        Flowable.__init__(self)
        self.name = name
        self.score = min(max(score, 0), 100)
        self.width = width
        self.height = height

    def wrap(self, aW, aH):
        return self.width, self.height

    def draw(self):
        canvas = self.canv
        bar_h = 6
        bar_y = (self.height - bar_h) / 2

        # Label
        canvas.setFont(FONT_NORMAL, 7.5)
        canvas.setFillColor(DARK_GRAY)
        canvas.drawString(0, bar_y + bar_h + 3, self.name)

        # Background bar
        bar_x = 0
        bar_w = self.width - 35
        canvas.setFillColor(LIGHT_GRAY)
        canvas.roundRect(bar_x, bar_y, bar_w, bar_h, 2, fill=1, stroke=0)

        # Filled portion — dark gray
        fill_w = bar_w * self.score / 100
        if fill_w > 0:
            canvas.setFillColor(DARK_GRAY)
            canvas.roundRect(bar_x, bar_y, max(fill_w, 4), bar_h, 2, fill=1, stroke=0)

        # Score number — colored by risk level
        canvas.setFont(FONT_BOLD, 8)
        canvas.setFillColor(_risk_color(self.score))
        canvas.drawRightString(self.width, bar_y, f"{self.score:.0f}")


# ─── Main Report Generator ─────────────────────────────────

class NtFastPDFReport:
    """Generates ntFAST B&W professional PDF reports."""

    PAGE_W, PAGE_H = A4
    MARGIN = 20 * mm
    CONTENT_W = PAGE_W - 2 * (20 * mm)

    def __init__(self, data: Dict[str, Any]):
        _register_fonts()
        self.data = data
        self.meta = data.get("meta", {})
        self.account = data.get("account", {})
        self.summary = data.get("summary", {})
        self.analytics = data.get("analytics", {})
        self.fraud = data.get("fraud_report", {})
        self.transactions = data.get("transactions", [])
        self.styles = self._build_styles()

    def _build_styles(self) -> Dict[str, ParagraphStyle]:
        base = getSampleStyleSheet()
        return {
            "title": ParagraphStyle(
                "ntfast_title", parent=base["Title"],
                fontSize=24, leading=28,
                textColor=BLACK, fontName=FONT_BOLD,
                spaceAfter=0,
            ),
            "subtitle": ParagraphStyle(
                "ntfast_subtitle", parent=base["Normal"],
                fontSize=8.5, leading=11,
                textColor=GRAY, fontName=FONT_NORMAL,
            ),
            "h2": ParagraphStyle(
                "ntfast_h2", parent=base["Heading2"],
                fontSize=13, leading=17,
                textColor=BLACK, fontName=FONT_BOLD,
                spaceBefore=6 * mm, spaceAfter=3 * mm,
                borderPadding=0,
            ),
            "h3": ParagraphStyle(
                "ntfast_h3", parent=base["Heading3"],
                fontSize=10.5, leading=14,
                textColor=DARK, fontName=FONT_BOLD,
                spaceBefore=4 * mm, spaceAfter=2 * mm,
            ),
            "body": ParagraphStyle(
                "ntfast_body", parent=base["Normal"],
                fontSize=9, leading=13,
                textColor=DARK_GRAY, fontName=FONT_NORMAL,
            ),
            "body_small": ParagraphStyle(
                "ntfast_body_small", parent=base["Normal"],
                fontSize=7.5, leading=10,
                textColor=MID_GRAY, fontName=FONT_NORMAL,
            ),
            "kpi_value": ParagraphStyle(
                "ntfast_kpi_value", parent=base["Normal"],
                fontSize=15, leading=18,
                textColor=BLACK, fontName=FONT_BOLD,
                alignment=TA_CENTER,
            ),
            "kpi_label": ParagraphStyle(
                "ntfast_kpi_label", parent=base["Normal"],
                fontSize=7, leading=9,
                textColor=GRAY, fontName=FONT_NORMAL,
                alignment=TA_CENTER,
            ),
            "red_flag": ParagraphStyle(
                "ntfast_red_flag", parent=base["Normal"],
                fontSize=8.5, leading=12,
                textColor=DARK_GRAY, fontName=FONT_NORMAL,
                leftIndent=4 * mm,
            ),
            "recommendation": ParagraphStyle(
                "ntfast_recommendation", parent=base["Normal"],
                fontSize=8.5, leading=12,
                textColor=DARK_GRAY, fontName=FONT_NORMAL,
                leftIndent=4 * mm,
            ),
            "footer": ParagraphStyle(
                "ntfast_footer", parent=base["Normal"],
                fontSize=7, leading=9,
                textColor=GRAY, fontName=FONT_NORMAL,
                alignment=TA_CENTER,
            ),
        }

    # ─── Common table style helper ───────────────────────────

    def _table_style(self, n_rows: int, has_header: bool = True) -> TableStyle:
        """Standard B&W table style."""
        cmds = [
            ("FONTNAME", (0, 0), (-1, -1), FONT_NORMAL),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GRAY),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]
        if has_header:
            cmds += [
                ("FONTNAME", (0, 0), (-1, 0), FONT_BOLD),
                ("TEXTCOLOR", (0, 0), (-1, 0), BLACK),
                ("LINEBELOW", (0, 0), (-1, 0), 1, BLACK),
            ]
        # Subtle alternating rows
        for i in range(2, n_rows, 2):
            cmds.append(("BACKGROUND", (0, i), (-1, i), PALE_GRAY))
        # Bottom border on last row
        cmds.append(("LINEBELOW", (0, -1), (-1, -1), 0.5, LIGHT_GRAY))
        return TableStyle(cmds)

    # ─── Section divider ─────────────────────────────────────

    def _section_line(self, story: list):
        story.append(Spacer(1, 2 * mm))
        story.append(HRFlowable(
            width="100%", thickness=0.5,
            color=LIGHT_GRAY, spaceAfter=1 * mm,
        ))

    # ─── Generate ────────────────────────────────────────────

    def generate(self) -> bytes:
        buffer = io.BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=self.MARGIN,
            rightMargin=self.MARGIN,
            topMargin=15 * mm,
            bottomMargin=20 * mm,
            title="ntFAST Analysis Report",
            author="ntFAST AI v2.0",
        )

        story = []

        sections = [
            ("header", self._add_header),
            ("account_info", self._add_account_info),
            ("financial_kpis", self._add_financial_kpis),
            ("risk_overview", self._add_risk_overview),
            ("module_scores", self._add_module_scores),
            ("radar_chart", self._add_radar_chart),
            ("red_flags", self._add_red_flags),
            ("recommendations", self._add_recommendations),
            ("monthly_breakdown", self._add_monthly_breakdown),
            ("category_breakdown", self._add_category_breakdown),
            ("top_counterparties", self._add_top_counterparties),
            ("flagged_transactions", self._add_flagged_transactions),
            ("footer", self._add_footer_section),
        ]

        for name, builder in sections:
            try:
                builder(story)
            except Exception as e:
                logger.warning(f"PDF section '{name}' failed: {e}", exc_info=True)
                story.append(Paragraph(
                    f"[Section '{name}' could not be rendered]",
                    self.styles["body_small"]
                ))

        doc.build(story, onFirstPage=self._page_footer, onLaterPages=self._page_footer)

        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    # ─── Header ──────────────────────────────────────────────

    def _add_header(self, story: list):
        generated_at = self.meta.get("generated_at", datetime.now().isoformat())
        try:
            dt = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
            date_str = dt.strftime("%d.%m.%Y %H:%M")
        except Exception:
            date_str = str(generated_at)[:16]

        original_file = self.meta.get("original_filename", "")

        # Title row: brand name left, date right
        title_p = Paragraph("ntFAST", self.styles["title"])
        sub_parts = [f"Financial Analysis Report"]
        if original_file:
            sub_parts.append(_sanitize(original_file))
        sub_parts.append(date_str)
        sub_p = Paragraph(
            " &nbsp;|&nbsp; ".join(sub_parts),
            self.styles["subtitle"],
        )

        header_data = [
            [title_p],
            [sub_p],
        ]
        header_table = Table(header_data, colWidths=[self.CONTENT_W])
        header_table.setStyle(TableStyle([
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (0, 0), 2),
            ("BOTTOMPADDING", (0, 1), (0, 1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(header_table)

        # Thick black line under header
        story.append(HRFlowable(
            width="100%", thickness=2,
            color=BLACK, spaceAfter=4 * mm,
        ))

    # ─── Account Info ────────────────────────────────────────

    def _add_account_info(self, story: list):
        story.append(Paragraph("Account Information", self.styles["h2"]))

        owner = _sanitize(self.account.get("owner", "N/A"))
        card = _sanitize(self.account.get("card", ""))
        account_num = _sanitize(self.account.get("account_number", ""))
        currency = _sanitize(self.account.get("currency", "KZT"))
        period = self.account.get("period", {})
        period_str = f'{_sanitize(period.get("from", ""))} - {_sanitize(period.get("to", ""))}'

        bank_info = self.meta.get("detected_bank", {})
        bank_name = _sanitize(bank_info.get("name", "Unknown"))
        confidence = bank_info.get("confidence", 0)

        lbl_style = ParagraphStyle("lbl", parent=self.styles["body_small"], textColor=GRAY, fontSize=7.5)
        val_style = ParagraphStyle("val", parent=self.styles["body"], textColor=DARK, fontSize=9)

        def _field(label, value):
            return [
                Paragraph(label, lbl_style),
                Paragraph(str(value), val_style),
            ]

        info_data = [
            _field("Owner", owner) + _field("Bank", f"{bank_name} ({confidence * 100:.0f}%)"),
            _field("Card", card) + _field("Account", account_num),
            _field("Period", period_str) + _field("Currency", currency),
        ]

        if self.account.get("balance_start") is not None:
            info_data.append(
                _field("Opening Balance", _fmt_amount(self.account.get("balance_start", 0), currency))
                + _field("Closing Balance", _fmt_amount(self.account.get("balance_end", 0), currency))
            )

        col_w = self.CONTENT_W / 4
        info_table = Table(info_data, colWidths=[col_w * 0.55, col_w * 1.45, col_w * 0.55, col_w * 1.45])
        info_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), FONT_NORMAL),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LINEBELOW", (0, -1), (-1, -1), 0.5, LIGHT_GRAY),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 3 * mm))

    # ─── Financial KPIs ──────────────────────────────────────

    def _add_financial_kpis(self, story: list):
        story.append(Paragraph("Financial Overview", self.styles["h2"]))

        currency = self.account.get("currency", "KZT")
        total_tx = self.summary.get("total_transactions", 0)
        total_in = self.summary.get("total_income", 0)
        total_out = self.summary.get("total_expense", 0)
        net_flow = self.summary.get("net_flow", 0)

        # Build KPI cells — black values, color only for +/-
        kpi_items = [
            ("Total Income", _fmt_amount(total_in, currency), ACCENT_POSITIVE),
            ("Total Expense", _fmt_amount(total_out, currency), ACCENT_NEGATIVE),
            ("Net Flow", _fmt_amount(net_flow, currency),
             ACCENT_POSITIVE if net_flow >= 0 else ACCENT_NEGATIVE),
            ("Transactions", str(total_tx), BLACK),
        ]

        val_cells = []
        lbl_cells = []
        for label, value, color in kpi_items:
            val_style = ParagraphStyle(
                f"kpi_{label}", parent=self.styles["kpi_value"],
                textColor=color, fontSize=14,
            )
            val_cells.append(Paragraph(value, val_style))
            lbl_cells.append(Paragraph(label, self.styles["kpi_label"]))

        col_w = self.CONTENT_W / 4
        kpi_data = [val_cells, lbl_cells]

        kpi_table = Table(kpi_data, colWidths=[col_w] * 4)
        kpi_table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BACKGROUND", (0, 0), (-1, -1), PALE_GRAY),
            ("TOPPADDING", (0, 0), (-1, 0), 8),
            ("BOTTOMPADDING", (0, -1), (-1, -1), 8),
            ("LINEABOVE", (0, 0), (-1, 0), 0.5, LIGHT_GRAY),
            ("LINEBELOW", (0, -1), (-1, -1), 0.5, LIGHT_GRAY),
        ]))
        story.append(kpi_table)
        story.append(Spacer(1, 3 * mm))

    # ─── Risk Overview ───────────────────────────────────────

    def _add_risk_overview(self, story: list):
        story.append(Paragraph("Risk Assessment", self.styles["h2"]))

        score = self.fraud.get("composite_score", 0)
        risk_level = self.fraud.get("risk_level", "low")

        gauge = RiskGaugeFlowable(score, risk_level, width=190, height=110)

        risk_desc_lines = [
            f"<b>Composite Risk Score: {score:.1f} / 100</b>",
            f"<b>Risk Level: {_risk_label(risk_level)}</b>",
            "",
            "This score aggregates results from 11 independent",
            "anti-fraud analysis modules using AI-powered",
            "pattern recognition and statistical analysis.",
        ]
        risk_desc = Paragraph("<br/>".join(risk_desc_lines), self.styles["body"])

        risk_table = Table(
            [[gauge, risk_desc]],
            colWidths=[200, self.CONTENT_W - 210],
        )
        risk_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (1, 0), (1, 0), 12),
            ("LEFTPADDING", (0, 0), (0, 0), 0),
        ]))
        story.append(risk_table)
        story.append(Spacer(1, 3 * mm))

    # ─── Module Scores ───────────────────────────────────────

    def _add_module_scores(self, story: list):
        story.append(Paragraph("Module Analysis Scores", self.styles["h3"]))

        modules = self._get_module_scores()
        if not modules:
            story.append(Paragraph("No module data available.", self.styles["body"]))
            return

        left_items = []
        right_items = []

        for i, (key, score) in enumerate(modules.items()):
            name = MODULE_NAMES.get(key, key)
            bar = ModuleScoreBar(name, score, width=230, height=22)
            if i % 2 == 0:
                left_items.append(bar)
            else:
                right_items.append(bar)

        while len(right_items) < len(left_items):
            right_items.append(Spacer(1, 22))

        rows = [[l, r] for l, r in zip(left_items, right_items)]
        col_w = self.CONTENT_W / 2
        mod_table = Table(rows, colWidths=[col_w, col_w])
        mod_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        story.append(mod_table)
        story.append(Spacer(1, 3 * mm))

    # ─── Radar Chart ─────────────────────────────────────────

    def _add_radar_chart(self, story: list):
        modules = self._get_module_scores()
        if len(modules) < 3:
            return

        story.append(Paragraph("Module Score Distribution", self.styles["h3"]))

        radar = RadarChartFlowable(modules, width=260, height=220)
        radar_table = Table([[radar]], colWidths=[self.CONTENT_W])
        radar_table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ]))
        story.append(radar_table)
        story.append(Spacer(1, 3 * mm))

    # ─── Red Flags ───────────────────────────────────────────

    def _add_red_flags(self, story: list):
        flags = self.fraud.get("red_flags", [])
        if not flags:
            return

        story.append(PageBreak())
        story.append(Paragraph("Red Flags", self.styles["h2"]))

        for flag in flags:
            clean_flag = _sanitize(flag)
            # Bullet with red marker, text in dark gray
            story.append(Paragraph(
                f'<font color="#EF4444">&bull;</font> {clean_flag}',
                self.styles["red_flag"],
            ))
            story.append(Spacer(1, 1 * mm))

        story.append(Spacer(1, 3 * mm))

    # ─── Recommendations ─────────────────────────────────────

    def _add_recommendations(self, story: list):
        recs = self.fraud.get("recommendations", [])
        if not recs:
            return

        story.append(Paragraph("Recommendations", self.styles["h2"]))

        for i, rec in enumerate(recs, 1):
            clean_rec = _sanitize(rec)
            story.append(Paragraph(f"{i}. {clean_rec}", self.styles["recommendation"]))
            story.append(Spacer(1, 1 * mm))

        story.append(Spacer(1, 3 * mm))

    # ─── Monthly Breakdown ───────────────────────────────────

    def _add_monthly_breakdown(self, story: list):
        monthly = self.analytics.get("monthly_breakdown", [])
        if not monthly:
            return

        story.append(Paragraph("Monthly Breakdown", self.styles["h2"]))

        currency = self.account.get("currency", "KZT")

        header = ["Month", f"Income ({currency})", f"Expense ({currency})", f"Balance ({currency})", "Txns"]
        rows = [header]

        for m in monthly[:12]:
            rows.append([
                _sanitize(m.get("month_name", m.get("month", ""))),
                _fmt_amount(m.get("income", 0)),
                _fmt_amount(m.get("expense", 0)),
                _fmt_amount(m.get("balance", 0)),
                _sanitize(m.get("transaction_count", 0)),
            ])

        col_w = self.CONTENT_W / 5
        table = Table(rows, colWidths=[col_w * 1.2, col_w * 1.1, col_w * 1.1, col_w * 1.1, col_w * 0.5])
        table.setStyle(self._table_style(len(rows)))
        table.setStyle(TableStyle([
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ]))
        story.append(table)
        story.append(Spacer(1, 3 * mm))

    # ─── Category Breakdown ──────────────────────────────────

    def _add_category_breakdown(self, story: list):
        cat_data = self.analytics.get("category_breakdown", {})
        expenses = cat_data.get("expense", [])
        if not expenses:
            return

        story.append(Paragraph("Expense Categories", self.styles["h3"]))

        header = ["Category", "Amount", "Count", "Share"]
        rows = [header]

        for cat in expenses[:10]:
            rows.append([
                _sanitize(cat.get("category", "")),
                _fmt_amount(cat.get("amount", 0)),
                _sanitize(cat.get("count", 0)),
                f'{cat.get("percentage", 0):.1f}%',
            ])

        col_w = self.CONTENT_W / 4
        table = Table(rows, colWidths=[col_w * 1.5, col_w * 1.0, col_w * 0.7, col_w * 0.8])
        table.setStyle(self._table_style(len(rows)))
        table.setStyle(TableStyle([
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ]))
        story.append(table)
        story.append(Spacer(1, 3 * mm))

    # ─── Top Counterparties ──────────────────────────────────

    def _add_top_counterparties(self, story: list):
        merchants = self.analytics.get("top_merchants", [])
        contacts = self.analytics.get("top_contacts", [])
        top = merchants or contacts
        if not top:
            return

        story.append(Paragraph("Top Counterparties", self.styles["h3"]))

        header = ["Counterparty", "Amount", "Transactions"]
        rows = [header]

        for item in top[:10]:
            name = item.get("merchant", item.get("contact", item.get("name", "Unknown")))
            rows.append([
                _sanitize(name)[:40],
                _fmt_amount(item.get("amount", 0)),
                _sanitize(item.get("count", 0)),
            ])

        col_w = self.CONTENT_W / 3
        table = Table(rows, colWidths=[col_w * 1.5, col_w * 0.9, col_w * 0.6])
        table.setStyle(self._table_style(len(rows)))
        table.setStyle(TableStyle([
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ]))
        story.append(table)
        story.append(Spacer(1, 3 * mm))

    # ─── Flagged Transactions ────────────────────────────────

    def _add_flagged_transactions(self, story: list):
        patterns = self.fraud.get("flagged_patterns", [])
        explained = self.fraud.get("explained_flags", [])

        if not patterns and not explained:
            return

        story.append(PageBreak())
        story.append(Paragraph("Flagged Patterns &amp; Evidence", self.styles["h2"]))

        if patterns:
            for p in patterns[:8]:
                name = _sanitize(p.get("display_name", p.get("pattern_name", "Unknown")))
                conf = p.get("confidence", 0)
                reason = _sanitize(p.get("reason", ""))
                contrib = p.get("risk_contribution", 0)

                story.append(Paragraph(
                    f"<b>{name}</b> &nbsp; (confidence: {conf * 100:.0f}%, risk +{contrib:.0f})",
                    self.styles["h3"]
                ))
                if reason and reason != "N/A":
                    story.append(Paragraph(reason, self.styles["body"]))

                evidence = p.get("evidence", [])[:3]
                if evidence:
                    for ev in evidence:
                        ev_text = ", ".join(f"{_sanitize(k)}: {_sanitize(v)}" for k, v in ev.items() if k != "id")
                        story.append(Paragraph(f"  - {ev_text[:120]}", self.styles["body_small"]))

                story.append(Spacer(1, 2 * mm))

        if explained:
            story.append(Paragraph("Detailed Flag Explanations", self.styles["h3"]))
            for ef in explained[:10]:
                severity = _sanitize(ef.get("severity", "warning"))
                module = _sanitize(ef.get("module", ""))
                reason = _sanitize(ef.get("reason", ""))
                counter = _sanitize(ef.get("counter_evidence", ""))

                # Severity markers: only color on the severity badge
                sev_color = {
                    "info": "#999999",
                    "warning": "#EAB308",
                    "critical": "#EF4444",
                }.get(ef.get("severity", "warning"), "#999999")

                story.append(Paragraph(
                    f'<font color="{sev_color}"><b>[{severity.upper()}]</b></font> '
                    f'<b>{module}</b>: {reason}',
                    self.styles["body"]
                ))
                if counter and counter != "N/A":
                    story.append(Paragraph(
                        f'<i>Counter-evidence: {counter}</i>',
                        self.styles["body_small"]
                    ))
                story.append(Spacer(1, 1.5 * mm))

    # ─── Footer Section ──────────────────────────────────────

    def _add_footer_section(self, story: list):
        story.append(Spacer(1, 8 * mm))
        story.append(HRFlowable(
            width="100%", thickness=1,
            color=BLACK, spaceAfter=3 * mm,
        ))

        story.append(Paragraph(
            "This report was generated automatically by ntFAST AI v2.0 — "
            "Financial Analysis System for Transactions. "
            "Results are advisory and should be verified by qualified analysts.",
            self.styles["footer"]
        ))
        story.append(Spacer(1, 2 * mm))
        story.append(Paragraph(
            f"Generated: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')} &nbsp;|&nbsp; "
            f"ntFAST &nbsp;|&nbsp; Confidential",
            self.styles["footer"]
        ))

    # ─── Page Footer ─────────────────────────────────────────

    def _page_footer(self, canvas, doc):
        canvas.saveState()

        # Bottom line
        canvas.setStrokeColor(LIGHT_GRAY)
        canvas.setLineWidth(0.5)
        canvas.line(self.MARGIN, 14 * mm, self.PAGE_W - self.MARGIN, 14 * mm)

        canvas.setFont(FONT_NORMAL, 6.5)
        canvas.setFillColor(GRAY)

        # Left: branding
        canvas.drawString(self.MARGIN, 10 * mm, "ntFAST AI v2.0")

        # Right: page number
        canvas.drawRightString(
            self.PAGE_W - self.MARGIN, 10 * mm,
            f"Page {canvas.getPageNumber()}"
        )

        # Top line on non-first pages
        if canvas.getPageNumber() > 1:
            canvas.setStrokeColor(LIGHT_GRAY)
            canvas.setLineWidth(0.5)
            canvas.line(self.MARGIN, self.PAGE_H - 12 * mm, self.PAGE_W - self.MARGIN, self.PAGE_H - 12 * mm)

        canvas.restoreState()

    # ─── Helpers ─────────────────────────────────────────────

    def _get_module_scores(self) -> Dict[str, float]:
        modules = {}
        for key in [
            "velocity", "graph", "behavioral", "structuring",
            "cross_reference", "merchant_risk",
            "night_transactions", "duplicate_payments", "round_amounts", "profile_mismatch",
        ]:
            module_data = self.fraud.get(key, {})
            if isinstance(module_data, dict):
                score = module_data.get("risk_score", 0)
                modules[key] = float(score)
        return modules
