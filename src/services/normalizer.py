from __future__ import annotations

from typing import Optional


class ValueNormalizer:
    CAMPUS_MAP = {
        "campus móstoles": "Móstoles",
        "móstoles": "Móstoles",
        "mostoles": "Móstoles",
        "madrid": "Madrid",
        "vicálvaro": "Vicálvaro",
        "vicalvaro": "Vicálvaro",
        "on-line": "Online",
        "online": "Online",
        "semipresencial": "Semipresencial",
    }

    SUBJECT_TYPE_MAP = {
        "troncal": "Troncal",
        "troncales": "Troncal",
        "obligatoria": "Obligatoria",
        "obligatorias": "Obligatoria",
        "optativa": "Optativa",
        "optativas": "Optativa",
        "f.b.": "Formación básica",
        "formación básica": "Formación básica",
        "basica": "Formación básica",
        "básica": "Formación básica",
    }

    METRIC_MAP = {
        "oferta": ("offer_places", "count"),
        "demanda del plan de estudios": ("demand", "count"),
        "nota media de acceso": ("average_entry_grade", "grade"),
        "nota de corte": ("cutoff_grade", "grade"),
        "estudiantes matriculados de nuevo ingreso": ("new_enrolled", "count"),
        "1ª opcion": ("first_choice_enrolled", "count"),
        "1ª opción": ("first_choice_enrolled", "count"),
        "sin anulaciones": ("new_enrolled_without_cancellations", "count"),
        "que anularon": ("cancelled_enrollment", "count"),
        "tasa de cobertura": ("coverage_rate", "percent"),
        "de fuera de la cam": ("outside_cam", "count"),
        "extranjeros": ("foreign_students", "count"),
    }

    @classmethod
    def normalize_campus(cls, value: Optional[str]) -> Optional[str]:
        if not value:
            return None
        key = value.strip().lower()
        return cls.CAMPUS_MAP.get(key, value.strip())

    @classmethod
    def normalize_subject_type(cls, value: Optional[str]) -> Optional[str]:
        if not value:
            return None
        key = value.strip().lower()
        return cls.SUBJECT_TYPE_MAP.get(key, value.strip())

    @classmethod
    def normalize_metric_name(cls, value: str) -> tuple[str, Optional[str]]:
        key = value.strip().lower()
        if key in cls.METRIC_MAP:
            return cls.METRIC_MAP[key]
        return value.strip().lower().replace(" ", "_"), None

    @staticmethod
    def to_float(value: str | None) -> Optional[float]:
        if value is None:
            return None
        clean = value.strip().replace("%", "").replace(",", ".")
        if clean == "":
            return None
        try:
            return float(clean)
        except ValueError:
            return None

    @staticmethod
    def to_int(value: str | None) -> Optional[int]:
        if value is None:
            return None
        clean = value.strip().replace(".", "").replace(",", "")
        if clean == "":
            return None
        try:
            return int(clean)
        except ValueError:
            return None