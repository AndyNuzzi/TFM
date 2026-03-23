import argparse
from pathlib import Path

from src.services.parsing_service import ParsingService


def collect_pdf_paths(inputs: list[str]) -> list[Path]:
    pdf_paths: list[Path] = []

    for input_path in inputs:
        path = Path(input_path)

        if not path.exists():
            print(f" No existe: {path}")
            continue

        if path.is_dir():
            found_pdfs = sorted(path.rglob("*.pdf"))
            pdf_paths.extend(found_pdfs)
        elif path.is_file():
            if path.suffix.lower() == ".pdf":
                pdf_paths.append(path)
            else:
                print(f"⚠ Se ignora porque no es PDF: {path}")

    # Eliminar duplicados conservando orden
    unique_paths: list[Path] = []
    seen: set[Path] = set()

    for pdf_path in pdf_paths:
        resolved = pdf_path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique_paths.append(pdf_path)

    return unique_paths


def process_pdf(service: ParsingService, pdf_path: Path) -> None:
    print(f"\n📄 Procesando: {pdf_path}")

    try:
        dataset, parser_name = service.parse_pdf(pdf_path)

        print(f"✔ Parser usado: {parser_name}")
        print(f"✔ Familia detectada: {dataset.document.family_id}")
        print(f"✔ Curso académico: {dataset.document.academic_year}")
        print(f"✔ Grado: {dataset.document.degree_name}")
        print(f"➡ Métricas de ingreso: {len(dataset.entry_profile_metrics)}")
        print(f"➡ Resultados de asignaturas: {len(dataset.subject_results)}")

        if dataset.subject_results:
            print(" Asignaturas extraídas:")
            for row in dataset.subject_results:
                print(
                    f"   - curso = {row.year_of_study} | "
                    f"asignatura = {row.subject_name} | "
                    f"matriculados = {row.enrolled_total} | "
                    f"rendimiento = {row.performance_rate} | "
                    f"éxito = {row.success_rate} | "
                    f"valoración_docente = {row.teaching_evaluation}"
                )

        if dataset.warnings:
            print("Warnings:")
            for warning in dataset.warnings:
                print(f"   - {warning}")

    except Exception as exc:
        print(f" Error procesando {pdf_path}: {exc}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Parser de PDFs académicos"
    )

    parser.add_argument(
        "--pdf",
        nargs="+",
        required=True,
        help="Ruta(s) a PDF(s) o carpeta(s) que contengan PDFs"
    )

    args = parser.parse_args()

    pdf_paths = collect_pdf_paths(args.pdf)

    if not pdf_paths:
        print("No se encontraron PDFs válidos")
        return

    print(f"\n Total PDFs a procesar: {len(pdf_paths)}")

    service = ParsingService()

    for pdf_path in pdf_paths:
        process_pdf(service, pdf_path)


if __name__ == "__main__":
    main()