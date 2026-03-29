import re
from pathlib import Path

from src.domain.models import ExtractedPdfContent
from src.parsers.base import ParserError
from src.parsers.legacy_parser import LegacyPdfParser
from src.parsers.legacy_20102011_parser import Legacy20102011PdfParser
from src.parsers.legacy_20112012_parser import Legacy20112012PdfParser
from src.parsers.modern_2014_parser import Modern20142015PdfParser
from src.parsers.modern_parser import ModernPdfParser
from src.parsers.narrative_parser import NarrativePdfParser


class ParserResolver:
    def __init__(self) -> None:
        self.legacy_20092010_parser = LegacyPdfParser()
        self.legacy_20102011_parser = Legacy20102011PdfParser()
        self.legacy_20112012_parser = Legacy20112012PdfParser()
        self.modern_parser = ModernPdfParser()
        self.modern_20142015_parser = Modern20142015PdfParser()
        self.narrative_parser = NarrativePdfParser()

    def resolve(self, content: ExtractedPdfContent):
        academic_year = self._extract_year_from_filename(content.path)
        if academic_year is None:
            raise ParserError(
                f"No se pudo determinar el curso académico a partir del nombre del archivo: {content.path.name}"
            )

        start_year = int(academic_year[:4])

        if start_year == 2009:
            return self.legacy_20092010_parser

        if start_year == 2010:
            return self.legacy_20102011_parser

        if 2011 == start_year:
            return self.legacy_20102011_parser
        
        if 2012 == start_year:
            return self.legacy_20102011_parser

        if 2015 <= start_year <= 2024:
            return self.modern_parser

        if start_year == 2025:
            return self.narrative_parser

        raise ParserError(f"No hay parser para {academic_year}")

    @staticmethod
    def _extract_year_from_filename(path: Path) -> str | None:
        name = path.stem

        match = re.search(r"(20\d{2})(20\d{2})", name)
        if match:
            return f"{match.group(1)}-{match.group(2)}"

        match = re.search(r"(20\d{2})[-_](20\d{2})", name)
        if match:
            return f"{match.group(1)}-{match.group(2)}"

        return None