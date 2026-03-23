from src.domain.enums import DocumentFamily, DocumentType
from src.domain.models import ExtractedPdfContent, ParsedDataset
from src.parsers.base import BasePdfParser


class LegacyPdfParser(BasePdfParser):
    parser_name = "legacy_pdf_parser"
    family_id = DocumentFamily.LEGACY
    document_type = DocumentType.ANNUAL_RESULTS

    def can_handle(self, content: ExtractedPdfContent) -> bool:
        return True

    def parse(self, content: ExtractedPdfContent) -> ParsedDataset:
        academic_year = self.extract_academic_year(content.full_text, content.path.name)
        degree_name = self.extract_degree_name(content.full_text)

        document = self.build_document_record(
            degree_name=degree_name,
            academic_year=academic_year,
            source_pdf=str(content.path),
        )

        dataset = ParsedDataset(document=document)
        dataset.warnings.append(
            "Parser LEGACY seleccionado: pendiente implementar parseo real de notas de corte, perfil y rendimiento."
        )
        return dataset