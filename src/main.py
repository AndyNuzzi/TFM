import argparse
from pathlib import Path

from src.services.parsing_service import ParsingService
from src.services.excel_exporter import ExcelExporter


def collect_pdfs_from_dirs(directories: list[str]) -> list[Path]:
    pdf_paths = []

    for dir_path in directories:
        path = Path(dir_path)

        if not path.exists() or not path.is_dir():
            print(f"ERROR: Directorio no válido: {path}")
            continue

        pdfs = sorted(path.rglob("*.pdf"))
        pdf_paths.extend(pdfs)

    return pdf_paths


def collect_pdf_files(files: list[str]) -> list[Path]:
    pdf_paths = []

    for file_path in files:
        path = Path(file_path)

        if not path.exists():
            print(f"ERROR: No existe: {path}")
            continue

        if path.suffix.lower() != ".pdf":
            print(f"AVISO: No es PDF: {path}")
            continue

        pdf_paths.append(path)

    return pdf_paths


def process_pdf(service: ParsingService, pdf_path: Path):
    print(f"\nProcesando: {pdf_path}")

    dataset, parser_name = service.parse_pdf(pdf_path)

    print(f"Parser usado: {parser_name}")
    print(f"Familia detectada: {dataset.document.family_id}")
    print(f"Curso académico: {dataset.document.academic_year}")
    print(f"Grado: {dataset.document.degree_name}")
    print(f"Metricas de ingreso: {len(dataset.entry_profile_metrics)}")
    print(f"Resultados de asignaturas: {len(dataset.subject_results)}")

    return dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Parser de PDFs académicos")

    parser.add_argument(
        "--pdf",
        nargs="+",
        help="Uno o varios PDFs"
    )

    parser.add_argument(
        "--dir",
        nargs="+",
        help="Uno o varios directorios con PDFs"
    )

    parser.add_argument(
        "--output",
        default="output/resultados_parser.xlsx",
        help="Ruta del Excel de salida"
    )

    args = parser.parse_args()

    if not args.pdf and not args.dir:
        print("ERROR: Debes indicar --pdf o --dir")
        return

    pdf_paths = []

    if args.pdf:
        pdf_paths.extend(collect_pdf_files(args.pdf))

    if args.dir:
        pdf_paths.extend(collect_pdfs_from_dirs(args.dir))

    # eliminar duplicados
    pdf_paths = list(set(pdf_paths))

    if not pdf_paths:
        print("ERROR: No se encontraron PDFs")
        return

    print(f"\nTotal PDFs a procesar: {len(pdf_paths)}")

    service = ParsingService()
    exporter = ExcelExporter()

    datasets = []

    for pdf_path in pdf_paths:
        try:
            dataset = process_pdf(service, pdf_path)
            datasets.append(dataset)
        except Exception as exc:
            print(f"ERROR procesando {pdf_path}: {exc}")

    if not datasets:
        print("ERROR: No hay datos para exportar")
        return

    output_path = Path(args.output)
    exporter.export(datasets, output_path)

    print(f"\nExcel generado en: {output_path}")


if __name__ == "__main__":
    main()