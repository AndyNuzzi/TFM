from src.domain.enums import DocumentFamily, DocumentType
from src.domain.models import ExtractedPdfContent, ParsedDataset
from src.parsers.base import BasePdfParser


class ModernPdfParser(BasePdfParser):
    parser_name = "modern_pdf_parser"
    family_id = DocumentFamily.MODERN
    document_type = DocumentType.MONITORING_SUMMARY

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
            "Parser MODERN seleccionado: pendiente implementar parseo real de perfil de ingreso y resultados por asignatura."
        )
        return dataset