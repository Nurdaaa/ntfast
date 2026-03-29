"""
API endpoints for Kaspi Bank Statement Analysis
Comprehensive financial analysis with dashboard data
"""
import os
import tempfile
import logging
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse

from app.services.kaspi_analyzer import KaspiAnalyzer

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/analyze")
async def analyze_kaspi_statement(
    file: UploadFile = File(...),
):
    """
    Analyze uploaded Kaspi Bank PDF statement

    Returns comprehensive analysis including:
    - Account info and validation
    - Categorized transactions
    - Monthly breakdown
    - Category analysis
    - Top merchants and contacts
    - Recurring payments detection
    - Anomaly detection
    - Foreign currency analysis
    - Financial health indicators
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # Save uploaded file temporarily
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        logger.info(f"Analyzing Kaspi statement: {file.filename}")

        # Run analysis
        analyzer = KaspiAnalyzer(tmp_path)
        result = analyzer.analyze()

        # Add original filename
        result["meta"]["original_filename"] = file.filename

        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"Kaspi analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    finally:
        # Cleanup temp file
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.post("/analyze-local")
async def analyze_kaspi_local(
    pdf_path: str = Query(..., description="Path to PDF file")
):
    """
    Analyze Kaspi Bank PDF by local file path (for testing)

    WARNING: This endpoint accepts file paths and should be secured in production
    """
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="PDF file not found")

    if not pdf_path.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    try:
        logger.info(f"Analyzing local Kaspi statement: {pdf_path}")

        analyzer = KaspiAnalyzer(pdf_path)
        result = analyzer.analyze()

        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"Kaspi analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/categories")
async def get_categories():
    """Get all available transaction categories"""
    from app.services.kaspi_analyzer import TransactionCategorizer

    categorizer = TransactionCategorizer()

    return {
        "expense_categories": [
            {"id": cat_id, "name": cat_info["name"], "keywords_count": len(cat_info["keywords"])}
            for cat_id, cat_info in categorizer.EXPENSE_CATEGORIES.items()
        ],
        "transfer_categories": [
            {"id": cat_id, "name": cat_info["name"]}
            for cat_id, cat_info in categorizer.TRANSFER_CATEGORIES.items()
        ],
        "income_categories": [
            {"id": cat_id, "name": cat_info["name"]}
            for cat_id, cat_info in categorizer.INCOME_CATEGORIES.items()
        ]
    }
