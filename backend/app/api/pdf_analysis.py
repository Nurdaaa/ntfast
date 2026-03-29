"""
API endpoints for PDF Financial Analysis
"""
import os
import tempfile
import logging
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse

from app.services.pdf_analyzer import FinancialAnalyzer, analyze_pdf_file

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/analyze")
async def analyze_pdf(
    file: UploadFile = File(...),
    use_ai: bool = Query(True, description="Use Ollama AI for analysis summary"),
    anonymize: bool = Query(True, description="Anonymize personal data")
):
    """
    Analyze uploaded PDF bank statement

    - Extracts transactions from Kaspi Bank PDF
    - Anonymizes personal data (names, IINs, phone numbers)
    - Detects fraud patterns (gaming/gambling, money laundering, P2P anomalies)
    - Builds social profile
    - Generates AI summary (if Ollama is available)
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

        logger.info(f"Analyzing uploaded PDF: {file.filename}")

        # Run analysis
        analyzer = FinancialAnalyzer(use_ai=use_ai)
        result = analyzer.analyze_pdf(tmp_path, anonymize=anonymize)

        # Add original filename
        result["original_filename"] = file.filename

        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"PDF analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    finally:
        # Cleanup temp file
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.post("/analyze-path")
async def analyze_pdf_by_path(
    pdf_path: str,
    use_ai: bool = Query(True),
    anonymize: bool = Query(True)
):
    """
    Analyze PDF by file path (for local testing)

    WARNING: This endpoint accepts file paths and should be secured in production
    """
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="PDF file not found")

    if not pdf_path.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    try:
        analyzer = FinancialAnalyzer(use_ai=use_ai)
        result = analyzer.analyze_pdf(pdf_path, anonymize=anonymize)
        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"PDF analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/ollama-status")
async def check_ollama_status():
    """Check if Ollama is available for AI analysis"""
    from app.services.pdf_analyzer import OllamaAnalyzerSync

    ollama = OllamaAnalyzerSync()
    is_available = ollama.check_connection()

    return {
        "available": is_available,
        "host": ollama.host,
        "model": ollama.model
    }


@router.get("/supported-formats")
async def get_supported_formats():
    """Get information about supported PDF formats"""
    return {
        "supported_banks": [
            {
                "name": "Kaspi Bank",
                "country": "Kazakhstan",
                "format": "PDF statement export"
            }
        ],
        "detection_capabilities": [
            "Gaming/Gambling transactions",
            "Money laundering patterns",
            "P2P transfer analysis",
            "Social profiling"
        ],
        "anonymization": [
            "Customer names",
            "IIN (Individual Identification Number)",
            "Phone numbers",
            "Card numbers",
            "Account numbers"
        ]
    }
