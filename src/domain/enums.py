from enum import Enum


class DocumentFamily(str, Enum):
    LEGACY = "legacy"        # 2009-2010 a 2014-2015
    MODERN = "modern"        # 2015-2016 a 2023-2024
    NARRATIVE = "narrative"  # 2024-2025


class DocumentType(str, Enum):
    ANNUAL_RESULTS = "annual_results"
    MONITORING_SUMMARY = "monitoring_summary"
    NARRATIVE_FOLLOWUP = "narrative_followup"
    UNKNOWN = "unknown"