import re
from typing import Optional

from src.domain.enums import DocumentFamily, DocumentType
from src.domain.models import ExtractedPdfContent, ParsedDataset
from src.parsers.base import BasePdfParser
from src.services.normalizer import ValueNormalizer


class LegacyPdfParser(BasePdfParser):
    parser_name = "legacy_pdf_parser"
    family_id = DocumentFamily.LEGACY
    document_type = DocumentType.ANNUAL_RESULTS

    def can_handle(self, content: ExtractedPdfContent) -> bool:
        text = content.full_text.upper()
        return (
            "INFORME ANUAL DE RESULTADOS" in text
            and "CURSO 2009-2010" in text
        )

    def parse(self, content: ExtractedPdfContent) -> ParsedDataset:
        pages = [self._normalize_text(p) for p in content.pages_text if p]
        full_text = "\n".join(pages)

        academic_year = self.extract_academic_year(full_text, content.path.name)
        degree_name = self._extract_degree_name_20092010(pages[0] if pages else full_text)

        document = self.build_document_record(
            degree_name=degree_name,
            academic_year=academic_year,
            source_pdf=str(content.path),
        )

        dataset = ParsedDataset(document=document)

        if pages:
            self._parse_cutoff_grades(dataset, pages[0])
            self._parse_enrollment_metrics(dataset, pages[0])
            self._parse_entry_profile(dataset, pages[0])
            self._parse_subject_results(dataset, pages[0])

        if not dataset.subject_results:
            dataset.warnings.append(
                "No se pudieron extraer resultados por asignatura en 2009-2010."
            )

        return dataset

    def _normalize_text(self, text: str) -> str:
        text = text.replace("\r", "\n").replace("\xa0", " ")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{2,}", "\n", text)
        return text.strip()

    def _extract_degree_name_20092010(self, first_page_text: str) -> str:
        lines = [line.strip() for line in first_page_text.splitlines() if line.strip()]

        # Caso ideal: la línea entre "Última actualización..." y "RESUMEN"
        for i, line in enumerate(lines):
            if "ÚLTIMA ACTUALIZACIÓN" in line.upper():
                for j in range(i + 1, min(i + 5, len(lines))):
                    candidate = lines[j].strip()
                    upper = candidate.upper()

                    if upper in {"RESUMEN", "INFORME ANUAL DE RESULTADOS"}:
                        continue
                    if upper.startswith("CURSO "):
                        continue
                    if "INGRESO Y MATRICULACIÓN" in upper:
                        continue
                    if "VICERRECTORADO" in upper:
                        continue

                    # Este PDF tiene exactamente "INGENIERÍA DE SOFTWARE"
                    if "INGENIERÍA" in upper or "GRADO" in upper:
                        return candidate.title()

        # Fallback fuerte: línea previa a RESUMEN
        for i, line in enumerate(lines):
            if line.upper() == "RESUMEN" and i > 0:
                candidate = lines[i - 1].strip()
                if "VICERRECTORADO" not in candidate.upper():
                    return candidate.title()

        return "Desconocido"

    def _parse_cutoff_grades(self, dataset: ParsedDataset, page_text: str) -> None:
        match = re.search(
            r"NOTA DE CORTE\s+Junio\s+Septiembre\s+Campus Móstoles\s+"
            r"(?P<junio>\d+[.,]\d+)\s+(?P<septiembre>\d+[.,]\d+)",
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

    def _parse_enrollment_metrics(self, dataset: ParsedDataset, page_text: str) -> None:
        patterns = [
            ("offer_places", r"Oferta\s+(?P<campus>\d+)\s+(?P<total>\d+)"),
            ("demand", r"Demanda\s+(?P<campus>\d+)\s+(?P<total>\d+)"),
            ("enrollment", r"Matrícula\s+(?P<campus>\d+)\s+(?P<total>\d+)"),
            (
                "admitted_first_choice",
                r"Alumnos admitidos 1ª opción\s+(?P<campus>\d+)\s+(?P<total>\d+)",
            ),
            (
                "admitted_second_or_later_choice",
                r"Alumnos admitidos 2ª opción y sucesivas\s+(?P<campus>\d+)\s+(?P<total>\d+)",
            ),
            (
                "first_choice_share_percent",
                r"% alumnos 1ª opción sobre el total de matriculados\s+"
                r"(?P<campus>\d+[.,]\d+)\s+%\s+(?P<total>\d+[.,]\d+)\s+%",
            ),
            (
                "enrolled_vs_offer_percent",
                r"% alumnos matriculados en relación con la oferta\s+(?P<total>\d+[.,]?\d*)%",
            ),
        ]

        for metric_name, pattern in patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if not match:
                continue

            groups = match.groupdict()

            if "campus" in groups and groups["campus"] is not None:
                dataset.entry_profile_metrics.append(
                    self.build_entry_metric(
                        document_id=dataset.document.document_id,
                        degree_name=dataset.document.degree_name,
                        academic_year=dataset.document.academic_year,
                        campus="Móstoles",
                        metric_name_std=metric_name,
                        metric_name_raw=metric_name,
                        metric_value=ValueNormalizer.to_float(groups["campus"]),
                        unit="percent" if "percent" in metric_name else "count",
                        source_pdf=dataset.document.source_pdf,
                    )
                )

            if "total" in groups and groups["total"] is not None:
                dataset.entry_profile_metrics.append(
                    self.build_entry_metric(
                        document_id=dataset.document.document_id,
                        degree_name=dataset.document.degree_name,
                        academic_year=dataset.document.academic_year,
                        campus="Total",
                        metric_name_std=metric_name,
                        metric_name_raw=metric_name,
                        metric_value=ValueNormalizer.to_float(groups["total"]),
                        unit="percent" if "percent" in metric_name else "count",
                        source_pdf=dataset.document.source_pdf,
                    )
                )

    def _parse_entry_profile(self, dataset: ParsedDataset, page_text: str) -> None:
        profile_patterns = [
            ("male_percent", r"Hombres \(\*\)\s+(?P<campus>\d+[.,]\d+)\s+%\s+(?P<total>\d+[.,]\d+)\s+%"),
            ("female_percent", r"Mujeres \(\*\)\s+(?P<campus>\d+[.,]\d+)\s+%\s+(?P<total>\d+[.,]\d+)\s+%"),
            ("outside_cam_percent", r"Fuera de la CAM \(\*\)\s+(?P<campus>\d+[.,]\d+)\s+%\s+(?P<total>\d+[.,]\d+)\s+%"),
            ("foreign_students_percent", r"Alumnos extranjeros \(\*\)\s+(?P<campus>\d+[.,]\d+)\s+%\s+(?P<total>\d+[.,]\d+)\s+%"),
            ("full_time_students_percent", r"Estudiantes a tiempo completo\s+(?P<campus>\d+[.,]\d+)\s+%\s+(?P<total>\d+[.,]\d+)\s+%"),
            ("full_time_work_percent", r"Trabajo a tiempo completo\s+(?P<campus>\d+[.,]\d+)\s+%\s+(?P<total>\d+[.,]\d+)\s+%"),
            ("part_time_work_percent", r"Trabajo a tiempo parcial\s+(?P<campus>\d+[.,]\d+)\s+%\s+(?P<total>\d+[.,]\d+)\s+%"),
        ]

        for metric_name, pattern in profile_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if not match:
                continue

            dataset.entry_profile_metrics.append(
                self.build_entry_metric(
                    document_id=dataset.document.document_id,
                    degree_name=dataset.document.degree_name,
                    academic_year=dataset.document.academic_year,
                    campus="Móstoles",
                    metric_name_std=metric_name,
                    metric_name_raw=metric_name,
                    metric_value=ValueNormalizer.to_float(match.group("campus")),
                    unit="percent",
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
                    metric_value=ValueNormalizer.to_float(match.group("total")),
                    unit="percent",
                    source_pdf=dataset.document.source_pdf,
                )
            )

    def _parse_subject_results(self, dataset: ParsedDataset, page_text: str) -> None:
        if "Rendimiento académico" not in page_text:
            return

        section = page_text.split("Rendimiento académico", 1)[1]

        # Quitamos lo anterior al encabezado de tabla
        if "VALORACIÓN" in section:
            section = section.split("VALORACIÓN", 1)[1]

        lines = [line.strip() for line in section.splitlines() if line.strip()]

        merged_lines = []
        buffer = ""

        for line in lines:
            # Saltar encabezados residuales
            upper = line.upper()
            if upper in {"DOCENTE", "ASIGNATURA Nº", "ALUMNOS", "TASA DE", "RENDIMIENTO", "ÉXITO"}:
                continue

            # Línea final de página o basura
            if "ÚLTIMA ACTUALIZACIÓN" in upper:
                continue

            candidate = f"{buffer} {line}".strip() if buffer else line

            if re.search(r"\d+\s+\d+[.,]?\d*\s+%\s+\d+[.,]?\d*\s+%\s+\d+[.,]?\d*$", candidate):
                merged_lines.append(candidate)
                buffer = ""
            else:
                buffer = candidate

        row_pattern = re.compile(
            r"^(?P<subject>.+?)\s+"
            r"(?P<students>\d+)\s+"
            r"(?P<performance>\d+[.,]?\d*)\s+%\s+"
            r"(?P<success>\d+[.,]?\d*)\s+%\s+"
            r"(?P<teaching>\d+[.,]?\d*)$"
        )

        for row in merged_lines:
            match = row_pattern.match(row)
            if not match:
                continue

            dataset.subject_results.append(
                self.build_subject_result(
                    document_id=dataset.document.document_id,
                    degree_name=dataset.document.degree_name,
                    academic_year=dataset.document.academic_year,
                    campus="Móstoles",
                    year_of_study=1,
                    subject_name=match.group("subject").strip(),
                    subject_type_raw=None,
                    subject_type_std=None,
                    enrolled_total=ValueNormalizer.to_int(match.group("students")),
                    performance_rate=ValueNormalizer.to_float(match.group("performance")),
                    success_rate=ValueNormalizer.to_float(match.group("success")),
                    teaching_evaluation=ValueNormalizer.to_float(match.group("teaching")),
                    source_pdf=dataset.document.source_pdf,
                )
            )