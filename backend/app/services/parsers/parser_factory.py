"""
Parser factory for bank statement files
Фабрика для создания подходящего парсера
"""
from pathlib import Path
from typing import Dict, Any, List
from .base_parser import BaseParser
from .csv_parser import CSVParser
from .excel_parser import ExcelParser
from .pdf_parser import PDFParser


class ParserFactory:
    """
    Factory for creating appropriate parser based on file type
    Создает нужный парсер в зависимости от типа файла
    """

    # Mapping of file extensions to parser classes
    PARSER_MAP = {
        ".csv": CSVParser,
        ".xlsx": ExcelParser,
        ".xls": ExcelParser,
        ".pdf": PDFParser,
    }

    @staticmethod
    def create_parser(file_path: str) -> BaseParser:
        """
        Create appropriate parser for the given file

        Args:
            file_path: Path to the file

        Returns:
            Parser instance

        Raises:
            ValueError: If file type is not supported
        """
        path = Path(file_path)
        extension = path.suffix.lower()

        if extension not in ParserFactory.PARSER_MAP:
            raise ValueError(
                f"Unsupported file type: {extension}. "
                f"Supported types: {', '.join(ParserFactory.PARSER_MAP.keys())}"
            )

        parser_class = ParserFactory.PARSER_MAP[extension]
        return parser_class(file_path)

    @staticmethod
    def parse_file(file_path: str) -> List[Dict[str, Any]]:
        """
        Parse file and return transactions

        Args:
            file_path: Path to the file

        Returns:
            List of transaction dictionaries

        Raises:
            ValueError: If file type is not supported or parsing fails
        """
        parser = ParserFactory.create_parser(file_path)
        return parser.parse()

    @staticmethod
    def is_supported(file_path: str) -> bool:
        """
        Check if file type is supported

        Args:
            file_path: Path to the file

        Returns:
            True if supported, False otherwise
        """
        path = Path(file_path)
        extension = path.suffix.lower()
        return extension in ParserFactory.PARSER_MAP
