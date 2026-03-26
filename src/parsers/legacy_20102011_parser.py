import re

from src.domain.enums import DocumentFamily, DocumentType
from src.domain.models import ExtractedPdfContent, ParsedDataset
from src.parsers.base import BasePdfParser
from src.services.normalizer import ValueNormalizer


class Legacy20102011PdfParser(BasePdfParser):
    parser_name = "legacy_20102011_pdf_parser"
    family_id = DocumentFamily.LEGACY
    document_type = DocumentType.ANNUAL_RESULTS

    def can_handle(self, content: ExtractedPdfContent) -> bool:
        text = content.full_text.upper()
        return (
            "CURSO 2010-2011" in text
            and "GRADO EN INGENIERÍA DE SOFTWARE" in text
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
                "No se pudieron extraer resultados por asignatura en 2010-2011."
            )

        return dataset

    def _normalize_text(self, text: str) -> str:
        text = text.replace("\r", "\n").replace("\xa0", " ")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{2,}", "\n", text)
        return text.strip()

    def _extract_degree_name(self, first_page_text: str) -> str:
        match = re.search(
            r"GRADO EN\s+([A-ZÁÉÍÓÚÑ ]+)",
            first_page_text,
            re.IGNORECASE
        )
        if match:
            return f"Grado en {match.group(1).strip().title()}"
        return "Desconocido"

    def _parse_cutoff_grades(self, dataset: ParsedDataset, page_text: str) -> None:
        match = re.search(
            r"NOTA DE CORTE\s+Junio\s+Septiembre\s+MÓSTOLES\s+"
            r"(?P<junio>\d+[.,]\d+)\s+(?P<septiembre>\d+[.,]?\d*)",
            page_text,
            re.IGNORECASE,
        )
        if not match:
            return

        dataset.entry_profile_metrics.append(
            self.build_entry_metric(
                document_id=dataset.document.document_id,
                degree_name=dataset.document.degree_name,
                academic_year=dataset.document.academic_year,
                campus="Móstoles",
                metric_name_std="cutoff_grade_june",
                metric_name_raw="NOTA DE CORTE Junio",
                metric_value=ValueNormalizer.to_float(match.group("junio")),
                unit="grade",
                source_pdf=dataset.document.source_pdf,
            )
        )

        dataset.entry_profile_metrics.append(
            self.build_entry_metric(
                document_id=dataset.document.document_id,
                degree_name=dataset.document.degree_name,
                academic_year=dataset.document.academic_year,
                campus="Móstoles",
                metric_name_std="cutoff_grade_september",
                metric_name_raw="NOTA DE CORTE Septiembre",
                metric_value=ValueNormalizer.to_float(match.group("septiembre")),
                unit="grade",
                source_pdf=dataset.document.source_pdf,
            )
        )

    def _parse_entry_profile(self, dataset: ParsedDataset, page_text: str) -> None:
        patterns = [
            (
                "average_entry_grade",
                r"Nota media de acceso al plan de estudios\s+(?P<campus>\d+[.,]\d+)\s+(?P<total>\d+[.,]\d+)",
                "grade",
            ),
            (
                "demand",
                r"Demanda del plan de estudios\s+(?P<campus>\d+)\s+(?P<total>\d+)",
                "count",
            ),
            (
                "new_enrolled_first_choice",
                r"Total alumnos matriculados de nuevo ingreso 1ª opción\s+(?P<campus>\d+)\s+(?P<total>\d+)",
                "count",
            ),
            (
                "new_enrolled_total",
                r"Total alumnos matriculados de nuevo ingreso\s+(?P<campus>\d+)\s+(?P<total>\d+)",
                "count",
            ),
            (
                "new_enrolled_men",
                r"Alumnos matriculados de nuevo ingreso \(hombres\)\s+(?P<campus>\d+)\s+(?P<total>\d+)",
                "count",
            ),
            (
                "new_enrolled_women",
                r"Alumnos matriculados de nuevo ingreso \(mujeres\)\s+(?P<campus>\d+)\s+(?P<total>\d+)",
                "count",
            ),
            (
                "outside_cam",
                r"Alumnos matriculados de nuevo ingreso de fuera de la cam\s+(?P<campus>\d+)\s+(?P<total>\d+)",
                "count",
            ),
            (
                "foreign_students",
                r"Alumnos matriculados de nuevo ingreso extranjeros\s+(?P<campus>\d+)\s+(?P<total>\d+)",
                "count",
            ),
            (
                "full_time_students",
                r"Alumnos matriculados de nuevo ingreso a tiempo completo\s+(?P<campus>\d+)\s+(?P<total>\d+)",
                "count",
            ),
            (
                "offer_places",
                r"Oferta\s+(?P<campus>\d+)\s+(?P<total>\d+)",
                "count",
            ),
            (
                "coverage_rate",
                r"Tasa de cobertura .*?\)\s+(?P<campus>\d+[.,]\d+)%\s+(?P<total>\d+[.,]\d+)%",
                "percent",
            ),
            (
                "first_choice_share",
                r"% Alumnos de 1ª opción sobre el total de matriculados\s+(?P<campus>\d+[.,]\d+)%\s+(?P<total>\d+[.,]\d+)%",
                "percent",
            ),
            (
                "disabled_students",
                r"Discapacitados\s+(?P<campus>\d+)\s+(?P<total>\d+)",
                "count",
            ),
        ]

        for metric_name, pattern, unit in patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if not match:
                continue

            campus_raw = match.group("campus")
            total_raw = match.group("total")

            campus_value = (
                ValueNormalizer.to_float(campus_raw)
                if unit in {"grade", "percent"}
                else ValueNormalizer.to_int(campus_raw)
            )
            total_value = (
                ValueNormalizer.to_float(total_raw)
                if unit in {"grade", "percent"}
                else ValueNormalizer.to_int(total_raw)
            )

            dataset.entry_profile_metrics.append(
                self.build_entry_metric(
                    document_id=dataset.document.document_id,
                    degree_name=dataset.document.degree_name,
                    academic_year=dataset.document.academic_year,
                    campus="Móstoles",
                    metric_name_std=metric_name,
                    metric_name_raw=metric_name,
                    metric_value=campus_value,
                    unit=unit,
                    source_pdf=dataset.document.source_pdf,
                )
            )

            dataset.entry_profile_metrics.append(
                self.build_entry_metric(
                    document_id=dataset.document.document_id,
                    degree_name=dataset.document.degree_name,
                    academic_year=dataset.document.academic_year,
                    campus="Total",
                    metric_name_std=metric_name,
                    metric_name_raw=metric_name,
                    metric_value=total_value,
                    unit=unit,
                    source_pdf=dataset.document.source_pdf,
                )
            )

    def _parse_subject_results(self, dataset: ParsedDataset, page_text: str) -> None:
        if "Rendimiento académico" not in page_text:
            return

        section = page_text.split("Rendimiento académico", 1)[1]

        if "PROFESORADO QUE IMPARTE EN EL GRADO" in section:
            section = section.split("PROFESORADO QUE IMPARTE EN EL GRADO", 1)[0]

        lines = [line.strip() for line in section.splitlines() if line.strip()]

        cleaned_lines = []
        for line in lines:
            upper = line.upper()
            if upper in {
                "VICÁLVARO",
                "CURSO ASIGNATURA Nº",
                "ALUMNOS",
                "TASA DE",
                "RENDIMIENTO",
                "PRESENTACIÓN",
                "ÉXITO",
                "VALORACIÓN",
                "DOCENTE",
            }:
                continue
            if "ÚLTIMA ACTUALIZACIÓN" in upper:
                continue
            cleaned_lines.append(line)

        merged_rows = []
        buffer = ""

        for line in cleaned_lines:
            candidate = f"{buffer} {line}".strip() if buffer else line

            if re.search(
                r"\d+\s+\d+[.,]\d+%\s+\d+[.,]\d+%\s+\d+[.,]\d+%(?:\s+\d+[.,]\d+)?$",
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
            r"(?P<success>\d+[.,]\d+)%"
            r"(?:\s+(?P<teaching>\d+[.,]\d+))?$"
        )

        for row in merged_rows:
            match = row_pattern.match(row)
            if not match:
                continue

            teaching_raw = match.group("teaching")

            dataset.subject_results.append(
                self.build_subject_result(
                    document_id=dataset.document.document_id,
                    degree_name=dataset.document.degree_name,
                    academic_year=dataset.document.academic_year,
                    campus="Vicálvaro",
                    year_of_study=ValueNormalizer.to_int(match.group("course")),
                    subject_name=match.group("subject").strip().title(),
                    subject_type_raw=None,
                    subject_type_std=None,
                    enrolled_total=ValueNormalizer.to_int(match.group("students")),
                    performance_rate=ValueNormalizer.to_float(match.group("performance")),
                    presentation_rate=ValueNormalizer.to_float(match.group("presentation")),
                    success_rate=ValueNormalizer.to_float(match.group("success")),
                    teaching_evaluation=ValueNormalizer.to_float(teaching_raw) if teaching_raw else None,
                    source_pdf=dataset.document.source_pdf,
                )
            )