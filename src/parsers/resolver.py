import re
from pathlib import Path

from src.domain.enums import DocumentFamily
from src.domain.models import ExtractedPdfContent
from src.parsers.base import BasePdfParser, ParserError
from src.parsers.legacy_parser import LegacyPdfParser
from src.parsers.modern_parser import ModernPdfParser
from src.parsers.narrative_parser import NarrativePdfParser


class ParserResolver:
    def __init__(self) -> None:
        self.legacy_parser = LegacyPdfParser()
        self.modern_parser = ModernPdfParser()
        self.narrative_parser = NarrativePdfParser()

    def resolve(self, content: ExtractedPdfContent) -> BasePdfParser:
        academic_year = self._extract_year_from_filename(content.path)

        if academic_year is None:
            raise ParserError(
                f"No se pudo determinar el curso académico a partir del nombre del archivo: {content.path.name}"
            )

        start_year = int(academic_year[:4])

        if 2009 <= start_year <= 2014:
            return self.legacy_parser

        if 2015 <= start_year <= 2023:
            return self.modern_parser

        if start_year == 2024:
            return self.narrative_parser

        raise ParserError(
            f"No hay parser asignado para el curso {academic_year} ({content.path.name})"
        )

    @staticmethod
    def _extract_year_from_filename(path: Path) -> str | None:
        name = path.stem

        # 20092010.pdf
        match = re.search(r"(20\d{2})(20\d{2})", name)
        if match:
            return f"{match.group(1)}-{match.group(2)}"

        # 2023-2024.pdf
        match = re.search(r"(20\d{2})[-_](20\d{2})", name)
        if match:
            return f"{match.group(1)}-{match.group(2)}"

        return None