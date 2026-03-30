from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List

from src.domain.enums import DocumentFamily, DocumentType


@dataclass
class DocumentRecord:
    document_id: str
    degree_name: str
    academic_year: str
    family_id: DocumentFamily
    document_type: DocumentType
    source_pdf: str


@dataclass
class EntryProfileMetricRecord:
    document_id: str
    degree_name: str
    academic_year: str
    campus: Optional[str]
    metric_name_std: str
    metric_name_raw: str
    metric_value: Optional[float | str]
    unit: Optional[str]
    source_pdf: str


@dataclass
class SubjectResultRecord:
    document_id: str
    degree_name: str
    academic_year: str
    campus: Optional[str]
    year_of_study: Optional[int]
    subject_name: str
    subject_type_raw: Optional[str]
    subject_type_std: Optional[str]
    enrolled_total: Optional[int] = None
    first_enrollment: Optional[int] = None
    repeat_enrollment: Optional[int] = None
    first_enrollment_performance: Optional[float] = None
    passed: Optional[int] = None
    failed: Optional[int] = None
    not_presented: Optional[int] = None
    performance_rate: Optional[float] = None
    presentation_rate: Optional[float] = None
    success_rate: Optional[float] = None
    teaching_evaluation: Optional[float] = None
    grade_ss: Optional[float] = None
    grade_ap: Optional[float] = None
    grade_nt: Optional[float] = None
    grade_sb: Optional[float] = None
    source_pdf: Optional[str] = None


@dataclass
class ParsedDataset:
    document: DocumentRecord
    entry_profile_metrics: List[EntryProfileMetricRecord] = field(default_factory=list)
    subject_results: List[SubjectResultRecord] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class ExtractedPdfContent:
    path: Path
    full_text: str
    pages_text: list[str]
    pages_words: list[list[dict]]
    pages_tables: list[list[list[list[str | None]]]]