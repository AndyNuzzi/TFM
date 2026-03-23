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

            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text() or ""
                    pages_text.append(text)
                    full_text_parts.append(text)

            full_text = "\n".join(full_text_parts)

            return ExtractedPdfContent(
                path=pdf_path,
                full_text=full_text,
                pages_text=pages_text,
            )

        except Exception as exc:
            raise PdfExtractionError(
                f"No se pudo extraer texto de {pdf_path}: {exc}"
            ) from exc