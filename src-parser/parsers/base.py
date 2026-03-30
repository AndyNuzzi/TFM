from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
import re
import uuid
from typing import Optional

from src.domain.enums import DocumentFamily, DocumentType
from src.domain.models import (
    DocumentRecord,
    EntryProfileMetricRecord,
    ExtractedPdfContent,
    ParsedDataset,
    SubjectResultRecord,
)


class ParserError(Exception):
    pass


class BasePdfParser(ABC):
    parser_name: str = "base"
    family_id: DocumentFamily
    document_type: DocumentType

    @abstractmethod
    def can_handle(self, content: ExtractedPdfContent) -> bool:
        raise NotImplementedError

    @abstractmethod
    def parse(self, content: ExtractedPdfContent) -> ParsedDataset:
        raise NotImplementedError

    # -------- Helpers comunes --------

    def extract_academic_year(self, text: str, fallback_name: Optional[str] = None) -> str:
        match = re.search(r"(20\d{2})[-/](20\d{2}|\d{2})", text)
        if match:
            y1 = match.group(1)
            y2 = match.group(2)
            if len(y2) == 2:
                y2 = y1[:2] + y2
            return f"{y1}-{y2}"

        if fallback_name:
            name_match = re.search(r"(20\d{2})(20\d{2})", fallback_name)
            if name_match:
                return f"{name_match.group(1)}-{name_match.group(2)}"

        return "Desconocido"

    def extract_degree_name(self, text: str) -> str:
        patterns = [
            r"Grado en\s+([^\n]+)",
            r"Titulación\s*:\s*([^\n]+)",
            r"GRADO EN\s+([^\n]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip(" :.-")
        return "Desconocido"

    def build_document_record(
        self,
        *,
        degree_name: str,
        academic_year: str,
        source_pdf: str,
    ) -> DocumentRecord:
        return DocumentRecord(
            document_id=str(uuid.uuid4()),
            degree_name=degree_name,
            academic_year=academic_year,
            family_id=self.family_id,
            document_type=self.document_type,
            source_pdf=source_pdf,
        )

    def build_entry_metric(
        self,
        *,
        document_id: str,
        degree_name: str,
        academic_year: str,
        campus: Optional[str],
        metric_name_std: str,
        metric_name_raw: str,
        metric_value: Optional[float | str],
        unit: Optional[str],
        source_pdf: str,
    ) -> EntryProfileMetricRecord:
        return EntryProfileMetricRecord(
            document_id=document_id,
            degree_name=degree_name,
            academic_year=academic_year,
            campus=campus,
            metric_name_std=metric_name_std,
            metric_name_raw=metric_name_raw,
            metric_value=metric_value,
            unit=unit,
            source_pdf=source_pdf,
        )

    def build_subject_result(
        self,
        *,
        document_id: str,
        degree_name: str,
        academic_year: str,
        campus: Optional[str],
        year_of_study: Optional[int],
        subject_name: str,
        subject_type_raw: Optional[str],
        subject_type_std: Optional[str],
        source_pdf: str,
        **kwargs,
    ) -> SubjectResultRecord:
        return SubjectResultRecord(
            document_id=document_id,
            degree_name=degree_name,
            academic_year=academic_year,
            campus=campus,
            year_of_study=year_of_study,
            subject_name=subject_name,
            subject_type_raw=subject_type_raw,
            subject_type_std=subject_type_std,
            source_pdf=source_pdf,
            **kwargs,
        )