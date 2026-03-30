from pathlib import Path

from src.domain.models import ParsedDataset
from src.extraction.pdf_extractor import PdfExtractor
from src.parsers.resolver import ParserResolver


class ParsingService:
    def __init__(self) -> None:
        self.extractor = PdfExtractor()
        self.resolver = ParserResolver()

    def parse_pdf(self, pdf_path):
        content = self.extractor.extract(pdf_path)
        parser = self.resolver.resolve(content)
        dataset = parser.parse(content)
        return dataset, parser.parser_name