from pathlib import Path

import pdfplumber

from src.domain.models import ExtractedPdfContent


class PdfExtractionError(Exception):
    pass


class PdfExtractor:
    def extract(self, pdf_path: Path) -> ExtractedPdfContent:
        if not pdf_path.exists():
            raise PdfExtractionError(f"No existe el archivo: {pdf_path}")

        if pdf_path.suffix.lower() != ".pdf":
            raise PdfExtractionError(f"El archivo no es un PDF: {pdf_path}")

        try:
            pages_text = []
            full_text_parts = []
            pages_words = []
            pages_tables = []

            table_settings = {
                "vertical_strategy": "lines",
                "horizontal_strategy": "lines",
                "intersection_tolerance": 5,
                "snap_tolerance": 3,
                "join_tolerance": 3,
            }

            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text() or ""
                    words = page.extract_words(
                        use_text_flow=False,
                        keep_blank_chars=False
                    ) or []

                    tables = page.extract_tables(table_settings=table_settings) or []

                    pages_text.append(text)
                    full_text_parts.append(text)
                    pages_words.append(words)
                    pages_tables.append(tables)

            full_text = "\n".join(full_text_parts)

            return ExtractedPdfContent(
                path=pdf_path,
                full_text=full_text,
                pages_text=pages_text,
                pages_words=pages_words,
                pages_tables=pages_tables,
            )

        except Exception as exc:
            raise PdfExtractionError(
                f"No se pudo extraer texto de {pdf_path}: {exc}"
            ) from exc