import re

from src.domain.enums import DocumentFamily, DocumentType
from src.domain.models import ExtractedPdfContent, ParsedDataset
from src.parsers.base import BasePdfParser
from src.services.normalizer import ValueNormalizer


class Legacy20112012PdfParser(BasePdfParser):
    parser_name = "legacy_20112012_pdf_parser"
    family_id = DocumentFamily.LEGACY
    document_type = DocumentType.ANNUAL_RESULTS

    def can_handle(self, content: ExtractedPdfContent) -> bool:
        text = content.full_text.upper()
        return (
            "CURSO 2011-2012" in text
            and "GRADO EN INGENIERÍA DE SOFTWARE" in text
        )

    def parse(self, content: ExtractedPdfContent) -> ParsedDataset:
        pages_text = [self._normalize_text(page) for page in content.pages_text if page]
        full_text = "\n".join(pages_text)

        academic_year = self.extract_academic_year(full_text, content.path.name)
        degree_name = self._extract_degree_name(pages_text[0] if pages_text else full_text)

        document = self.build_document_record(
            degree_name=degree_name,
            academic_year=academic_year,
            source_pdf=str(content.path),
        )

        dataset = ParsedDataset(document=document)

        if len(pages_text) >= 1:
            self._parse_cutoff_grades(dataset, pages_text[0])
            self._parse_entry_profile(dataset, pages_text[0])

        subject_results_before = len(dataset.subject_results)

        # 1) Intento principal: tablas
        if hasattr(content, "pages_tables") and len(content.pages_tables) >= 2:
            self._parse_subject_results_from_tables(dataset, content.pages_tables[1])

        # 2) Fallback: palabras/coordenadas
        if (
            len(dataset.subject_results) == subject_results_before
            and hasattr(content, "pages_words")
            and len(content.pages_words) >= 2
        ):
            self._parse_subject_results_from_words(dataset, content.pages_words[1])

        if not dataset.subject_results:
            dataset.warnings.append(
                "No se pudieron extraer resultados por asignatura en 2011-2012."
            )

        return dataset

    def _normalize_text(self, text: str) -> str:
        text = text.replace("\r", "\n").replace("\xa0", " ")
        text = text.replace("\ufffe", "-")
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
        match = re.search(
            r"NOTA DE CORTE\s+Junio\s+Septiembre\s+M[ÓO]STOLES\s+(?P<june>\d+[.,]\d+)",
            page_text,
            re.IGNORECASE | re.DOTALL,
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
                metric_value=ValueNormalizer.to_float(match.group("june")),
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
                r"Total alumnos matriculados de nuevo ingreso 1ª\s+opción\s+(?P<campus>\d+)\s+(?P<total>\d+)",
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
                r"Alumnos matriculados de nuevo ingreso de fuera\s+de la cam\s+(?P<campus>\d+)\s+(?P<total>\d+)",
                "count",
            ),
            (
                "foreign_students",
                r"Alumnos matriculados de nuevo ingreso\s+extranjeros\s+(?P<campus>\d+)\s+(?P<total>\d+)",
                "count",
            ),
            (
                "full_time_students",
                r"Alumnos matriculados de nuevo ingreso a tiempo\s+completo\s+(?P<campus>\d+)\s+(?P<total>\d+)",
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
                "first_choice_share_percent",
                r"% Alumnos de 1ª opción sobre el total de\s+matriculados\s+(?P<campus>\d+[.,]\d+)%\s+(?P<total>\d+[.,]\d+)%",
                "percent",
            ),
            (
                "disabled_students",
                r"Discapacitados\s+(?P<campus>\d+)\s+(?P<total>\d+)",
                "count",
            ),
        ]

        for metric_name, pattern, unit in patterns:
            match = re.search(pattern, page_text, re.IGNORECASE | re.DOTALL)
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

    def _parse_subject_results_from_tables(self, dataset: ParsedDataset, page_tables: list) -> None:
        if not page_tables:
            return

        seen = set()

        for table in page_tables:
            if not table:
                continue

            for row in table:
                normalized = self._normalize_table_row(row)
                if not normalized:
                    continue

                course = normalized[0]
                subject = normalized[1]
                students = normalized[2]
                performance = normalized[3]
                presentation = normalized[4]
                success = normalized[5]
                teaching = normalized[6]

                if not self._looks_like_subject_row(
                    course=course,
                    subject=subject,
                    students=students,
                    performance=performance,
                    presentation=presentation,
                    success=success,
                    teaching=teaching,
                ):
                    continue

                row_key = (
                    course,
                    subject.upper(),
                    students,
                    performance,
                    presentation,
                    success,
                )
                if row_key in seen:
                    continue
                seen.add(row_key)

                teaching_value = None if teaching == "-" else ValueNormalizer.to_float(teaching)

                dataset.subject_results.append(
                    self.build_subject_result(
                        document_id=dataset.document.document_id,
                        degree_name=dataset.document.degree_name,
                        academic_year=dataset.document.academic_year,
                        campus="Vicálvaro",
                        year_of_study=ValueNormalizer.to_int(course),
                        subject_name=subject,
                        subject_type_raw=None,
                        subject_type_std=None,
                        enrolled_total=ValueNormalizer.to_int(students),
                        performance_rate=ValueNormalizer.to_float(performance),
                        presentation_rate=ValueNormalizer.to_float(presentation),
                        success_rate=ValueNormalizer.to_float(success),
                        teaching_evaluation=teaching_value,
                        source_pdf=dataset.document.source_pdf,
                    )
                )

    def _normalize_table_row(self, row: list) -> list[str] | None:
        if not row:
            return None

        cells = []
        for cell in row:
            value = "" if cell is None else str(cell)
            value = value.replace("\n", " ")
            value = re.sub(r"\s+", " ", value).strip()
            cells.append(value)

        cells = [c for c in cells if c != ""]

        if len(cells) < 7:
            return None

        # Nos quedamos con las 7 columnas esperadas.
        # Si viniera alguna columna extra, la absorbemos en subject.
        if len(cells) > 7:
            course = cells[0]
            subject = " ".join(cells[1:-5]).strip()
            tail = cells[-5:]
            cells = [course, subject] + tail

        if len(cells) != 7:
            return None

        cells[1] = re.sub(r"\s+", " ", cells[1]).strip().upper()

        return cells

    def _looks_like_subject_row(
        self,
        course: str,
        subject: str,
        students: str,
        performance: str,
        presentation: str,
        success: str,
        teaching: str,
    ) -> bool:
        ignored_subjects = {
            "ASIGNATURA",
            "VICÁLVARO",
            "CURSO",
            "ALUMNOS",
            "DOCENTE",
        }

        return (
            bool(re.fullmatch(r"[123]", course))
            and bool(subject)
            and subject not in ignored_subjects
            and bool(re.fullmatch(r"\d+", students))
            and bool(re.fullmatch(r"\d+[.,]\d+%", performance))
            and bool(re.fullmatch(r"\d+[.,]\d+%", presentation))
            and bool(re.fullmatch(r"\d+[.,]\d+%", success))
            and bool(re.fullmatch(r"\d+[.,]\d+|-", teaching))
        )

    def _parse_subject_results_from_words(self, dataset: ParsedDataset, page_words: list[dict]) -> None:
        if not page_words:
            return

        words = page_words
        rows = self._group_words_by_row(words, tolerance=4.5)

        candidates = []
        current = None

        for row_words in rows:
            row_words = sorted(row_words, key=lambda x: x["x0"])
            texts = [w["text"].strip() for w in row_words if w["text"].strip()]
            if not texts:
                continue

            joined = " ".join(texts)
            joined_upper = joined.upper()

            if any(
                marker in joined_upper
                for marker in [
                    "VICÁLVARO",
                    "CURSO ASIGNATURA",
                    "VALORACIÓN DOCENTE",
                    "PROFESORADO QUE IMPARTE EN EL GRADO",
                    "ÚLTIMA ACTUALIZACIÓN",
                ]
            ):
                continue

            row_data = self._extract_row_from_tokens(texts)

            if row_data is not None:
                if current and self._is_complete_subject_row(current):
                    candidates.append(current)
                current = row_data
            else:
                if current:
                    extra_subject = joined.strip().upper()
                    if extra_subject and not self._looks_numeric_tail(extra_subject):
                        current["subject"] = f'{current["subject"]} {extra_subject}'.strip()

        if current and self._is_complete_subject_row(current):
            candidates.append(current)

        seen = set()
        for row in candidates:
            subject_name = re.sub(r"\s+", " ", row["subject"]).strip()

            row_key = (
                row["course"],
                subject_name.upper(),
                row["students"],
                row["performance"],
                row["presentation"],
                row["success"],
            )
            if row_key in seen:
                continue
            seen.add(row_key)

            teaching_raw = row["teaching"].strip()
            teaching_value = None if teaching_raw == "-" else ValueNormalizer.to_float(teaching_raw)

            dataset.subject_results.append(
                self.build_subject_result(
                    document_id=dataset.document.document_id,
                    degree_name=dataset.document.degree_name,
                    academic_year=dataset.document.academic_year,
                    campus="Vicálvaro",
                    year_of_study=ValueNormalizer.to_int(row["course"]),
                    subject_name=subject_name,
                    subject_type_raw=None,
                    subject_type_std=None,
                    enrolled_total=ValueNormalizer.to_int(row["students"]),
                    performance_rate=ValueNormalizer.to_float(row["performance"]),
                    presentation_rate=ValueNormalizer.to_float(row["presentation"]),
                    success_rate=ValueNormalizer.to_float(row["success"]),
                    teaching_evaluation=teaching_value,
                    source_pdf=dataset.document.source_pdf,
                )
            )

    def _group_words_by_row(self, words: list[dict], tolerance: float = 4.5) -> list[list[dict]]:
        useful_words = []
        for w in words:
            text = str(w.get("text", "")).strip()
            if not text:
                continue
            useful_words.append(w)

        sorted_words = sorted(useful_words, key=lambda w: (w["top"], w["x0"]))

        rows = []
        current_row = []
        current_y = None

        for word in sorted_words:
            y = word["top"]

            if current_y is None:
                current_y = y
                current_row = [word]
                continue

            if abs(y - current_y) <= tolerance:
                current_row.append(word)
            else:
                rows.append(current_row)
                current_row = [word]
                current_y = y

        if current_row:
            rows.append(current_row)

        return rows

    def _extract_row_from_tokens(self, tokens: list[str]) -> dict | None:
        if not tokens:
            return None

        if not re.fullmatch(r"[123]", tokens[0]):
            return None

        if len(tokens) < 6:
            return None

        course = tokens[0]
        rest = tokens[1:]

        if len(rest) < 6:
            return None

        teaching = rest[-1]
        success = rest[-2]
        presentation = rest[-3]
        performance = rest[-4]
        students = rest[-5]
        subject_tokens = rest[:-5]

        subject = " ".join(subject_tokens).strip().upper()

        row = {
            "course": course,
            "subject": subject,
            "students": students,
            "performance": performance,
            "presentation": presentation,
            "success": success,
            "teaching": teaching,
        }

        if not self._is_complete_subject_row(row):
            return None

        return row

    def _looks_numeric_tail(self, text: str) -> bool:
        return bool(
            re.fullmatch(
                r"\d+\s+\d+[.,]\d+%\s+\d+[.,]\d+%\s+\d+[.,]\d+%\s+(\d+[.,]\d+|-)",
                text
            )
        )

    def _is_complete_subject_row(self, row: dict) -> bool:
        return self._looks_like_subject_row(
            course=row["course"],
            subject=row["subject"],
            students=row["students"],
            performance=row["performance"],
            presentation=row["presentation"],
            success=row["success"],
            teaching=row["teaching"],
        )