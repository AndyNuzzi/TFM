import re

from src.domain.enums import DocumentFamily, DocumentType
from src.domain.models import ExtractedPdfContent, ParsedDataset
from src.parsers.base import BasePdfParser
from src.services.normalizer import ValueNormalizer


class ModernPdfParser(BasePdfParser):
    parser_name = "modern_pdf_parser"
    family_id = DocumentFamily.MODERN
    document_type = DocumentType.MONITORING_SUMMARY

    def can_handle(self, content: ExtractedPdfContent) -> bool:
        text = content.full_text.upper()
        return (
            "RESUMEN MEMORIA ANUAL DE SEGUIMIENTO" in text
            or "SEGUIMIENTO INTERNO" in text
            or "RENDIMIENTO ACADÉMICO" in text
        )

    def parse(self, content: ExtractedPdfContent) -> ParsedDataset:
        pages = [self._normalize_text(p) for p in content.pages_text if p]
        full_text = "\n".join(pages)

        academic_year = self.extract_academic_year(full_text, content.path.name)
        degree_name = self._extract_degree_name(pages[0] if pages else full_text)

        document = self.build_document_record(
            degree_name=degree_name,
            academic_year=academic_year,
            source_pdf=str(content.path),
        )

        dataset = ParsedDataset(document=document)

        if len(pages) >= 1:
            self._parse_cutoff_grades(dataset, pages[0])
            self._parse_entry_profile(dataset, pages[0])

        if len(pages) >= 2:
            self._parse_subject_results(dataset, pages[1])

        if not dataset.subject_results:
            dataset.warnings.append(
                "No se pudieron extraer resultados por asignatura en formato modern."
            )

        return dataset

    def _normalize_text(self, text: str) -> str:
        text = text.replace("\r", "\n").replace("\xa0", " ")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{2,}", "\n", text)
        return text.strip()

    def _extract_degree_name(self, first_page_text: str) -> str:
        match = re.search(
            r"GRADO EN\s+([A-ZÁÉÍÓÚÜÑ ]+)",
            first_page_text,
            re.IGNORECASE
        )
        if match:
            return f"Grado en {match.group(1).strip().title()}"

        return "Desconocido"

    def _parse_cutoff_grades(self, dataset: ParsedDataset, page_text: str) -> None:
        #
        # Caso 2014-2015:
        # NOTA DE CORTE 2014-15
        # JUNIO
        # MÓSTOLES
        # 5.93
        #
        # En años posteriores puede haber ligeras variantes, por eso usamos
        # varios patrones posibles.
        #
        patterns = [
            (
                "cutoff_grade_june",
                r"NOTA DE CORTE.*?JUNIO\s+M[ÓO]STOLES\s+(?P<value>\d+[.,]\d+)",
                "Móstoles",
            ),
            (
                "cutoff_grade_september",
                r"NOTA DE CORTE.*?SEPTIEMBRE\s+M[ÓO]STOLES\s+(?P<value>\d+[.,]\d+)",
                "Móstoles",
            ),
        ]

        for metric_name, pattern, campus in patterns:
            match = re.search(pattern, page_text, re.IGNORECASE | re.DOTALL)
            if not match:
                continue

            dataset.entry_profile_metrics.append(
                self.build_entry_metric(
                    document_id=dataset.document.document_id,
                    degree_name=dataset.document.degree_name,
                    academic_year=dataset.document.academic_year,
                    campus=campus,
                    metric_name_std=metric_name,
                    metric_name_raw=metric_name,
                    metric_value=ValueNormalizer.to_float(match.group("value")),
                    unit="grade",
                    source_pdf=dataset.document.source_pdf,
                )
            )

    def _parse_entry_profile(self, dataset: ParsedDataset, page_text: str) -> None:
        #
        # Caso 2014-2015:
        # a. NOTA MEDIA DE ACCESO AL PLAN DE ESTUDIOS 7.12
        # b. DEMANDA DEL PLAN DE ESTUDIOS 482.00
        # ...
        #
        profile_patterns = [
            (
                "average_entry_grade",
                r"a\.\s+NOTA MEDIA DE ACCESO AL PLAN DE ESTUDIOS\s+(?P<value>\d+[.,]\d+)",
                "grade",
            ),
            (
                "demand",
                r"b\.\s+DEMANDA DEL PLAN DE ESTUDIOS\s+(?P<value>\d+[.,]\d+)",
                "count",
            ),
            (
                "new_enrolled_first_choice",
                r"c\.\s+TOTAL ESTUDIANTES MATRICULADOS DE NUEVO INGRESO 1ª\s+OPCI[ÓO]N\s+(?P<value>\d+[.,]\d+)",
                "count",
            ),
            (
                "new_enrolled_total",
                r"d\.\s+TOTAL ESTUDIANTES MATRICULADOS DE NUEVO INGRESO\s+(?P<value>\d+[.,]\d+)",
                "count",
            ),
            (
                "new_enrolled_men",
                r"e\.\s+ESTUDIANTES MATRICULADOS DE NUEVO INGRESO \(HOMBRES\)\s+(?P<value>\d+[.,]\d+)",
                "count",
            ),
            (
                "new_enrolled_women",
                r"f\.\s+ESTUDIANTES MATRICULADOS DE NUEVO INGRESO \(MUJERES\)\s+(?P<value>\d+[.,]\d+)",
                "count",
            ),
            (
                "new_enrolled_men_percent",
                r"g\.\s+ESTUDIANTES MATRICULADOS DE NUEVO INGRESO \(HOMBRES\)\s+%\s+(?P<value>\d+[.,]\d+)",
                "percent",
            ),
            (
                "new_enrolled_women_percent",
                r"h\.\s+ESTUDIANTES MATRICULADOS DE NUEVO INGRESO \(MUJERES\)\s+%\s+(?P<value>\d+[.,]\d+)",
                "percent",
            ),
            (
                "outside_cam",
                r"i\.\s+ESTUDIANTES MATRICULADOS DE NUEVO INGRESO DE FUERA\s+DE LA CAM\s+(?P<value>\d+[.,]\d+)",
                "count",
            ),
            (
                "outside_cam_percent",
                r"j\.\s+ESTUDIANTES MATRICULADOS DE NUEVO INGRESO DE FUERA\s+DE LA CAM\s+%\s+(?P<value>\d+[.,]\d+)",
                "percent",
            ),
            (
                "foreign_students",
                r"k\.\s+ESTUDIANTES MATRICULADOS DE NUEVO INGRESO\s+EXTRANJEROS\s+(?P<value>\d+[.,]\d+)",
                "count",
            ),
            (
                "foreign_students_percent",
                r"l\.\s+ESTUDIANTES MATRICULADOS DE NUEVO INGRESO\s+EXTRANJEROS\s+%\s+(?P<value>\d+[.,]\d+)",
                "percent",
            ),
            (
                "full_time_students",
                r"m\.\s+ESTUDIANTES MATRICULADOS DE NUEVO INGRESO A TIEMPO\s+COMPLETO\s+(?P<value>\d+[.,]\d+)",
                "count",
            ),
            (
                "offer_places",
                r"n\.\s+OFERTA\s+(?P<value>\d+[.,]\d+)",
                "count",
            ),
            (
                "coverage_rate",
                r"o\.\s+TASA DE COBERTURA.*?\s+(?P<value>\d+[.,]\d+)",
                "percent",
            ),
            (
                "first_choice_share_percent",
                r"p\.\s+% ESTUDIANTES DE 1ª OPCI[ÓO]N SOBRE EL TOTAL DE\s+MATRICULADOS\s+(?P<value>\d+[.,]\d+)",
                "percent",
            ),
            (
                "disabled_students",
                r"q\.\s+ESTUDIANTES MATRICULADOS DE NUEVO INGRESO\s+DISCAPACITADOS\s+(?P<value>\d+[.,]\d+)",
                "count",
            ),
        ]

        for metric_name, pattern, unit in profile_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE | re.DOTALL)
            if not match:
                continue

            raw_value = match.group("value")
            value = (
                ValueNormalizer.to_float(raw_value)
                if unit in {"grade", "percent"}
                else ValueNormalizer.to_int(raw_value)
            )

            dataset.entry_profile_metrics.append(
                self.build_entry_metric(
                    document_id=dataset.document.document_id,
                    degree_name=dataset.document.degree_name,
                    academic_year=dataset.document.academic_year,
                    campus="Móstoles",
                    metric_name_std=metric_name,
                    metric_name_raw=metric_name,
                    metric_value=value,
                    unit=unit,
                    source_pdf=dataset.document.source_pdf,
                )
            )

    def _parse_subject_results(self, dataset: ParsedDataset, page_text: str) -> None:
        if "RENDIMIENTO ACADÉMICO" not in page_text.upper():
            return

        section = page_text

        # Cortamos si aparecen páginas siguientes o secciones nuevas
        stop_markers = [
            "PROFESORADO QUE IMPARTE EN EL PLAN DE ESTUDIO",
            "OTROS INDICADORES DEL PROFESORADO",
        ]
        for marker in stop_markers:
            if marker in section.upper():
                section = re.split(marker, section, flags=re.IGNORECASE)[0]

        lines = [line.strip() for line in section.splitlines() if line.strip()]

        cleaned_lines = []
        for line in lines:
            upper = line.upper()

            if upper in {
                "RENDIMIENTO ACADÉMICO",
                "MÓSTOLES",
                "CURSO ASIGNATURA Nº",
                "ALUMNOS",
                "T",
                "RENDIMIENTO",
                "PRESENTACIÓN",
                "T ÉXITO",
                "T EXITO",
            }:
                continue

            cleaned_lines.append(line)

        merged_rows = []
        buffer = ""

        for line in cleaned_lines:
            candidate = f"{buffer} {line}".strip() if buffer else line

            if re.search(
                r"\d+\s+\d+[.,]\d+%\s+\d+[.,]\d+%\s+\d+[.,]\d+%$",
                candidate
            ):
                merged_rows.append(candidate)
                buffer = ""
            else:
                buffer = candidate

        row_pattern = re.compile(
            r"^(?P<course>\d)\s+"
            r"(?P<subject>.+?)\s+"
            r"(?P<students>\d+)\s+"
            r"(?P<performance>\d+[.,]\d+)%\s+"
            r"(?P<presentation>\d+[.,]\d+)%\s+"
            r"(?P<success>\d+[.,]\d+)%$"
        )

        for row in merged_rows:
            match = row_pattern.match(row)
            if not match:
                continue

            dataset.subject_results.append(
                self.build_subject_result(
                    document_id=dataset.document.document_id,
                    degree_name=dataset.document.degree_name,
                    academic_year=dataset.document.academic_year,
                    campus="Móstoles",
                    year_of_study=ValueNormalizer.to_int(match.group("course")),
                    subject_name=match.group("subject").strip().title(),
                    subject_type_raw=None,
                    subject_type_std=None,
                    enrolled_total=ValueNormalizer.to_int(match.group("students")),
                    performance_rate=ValueNormalizer.to_float(match.group("performance")),
                    presentation_rate=ValueNormalizer.to_float(match.group("presentation")),
                    success_rate=ValueNormalizer.to_float(match.group("success")),
                    source_pdf=dataset.document.source_pdf,
                )
            )