from __future__ import annotations

import argparse
from pathlib import Path

import pdfplumber
import pandas as pd

EXCEL_CELL_LIMIT = 32767


def split_text_for_excel(text: str, chunk_size: int = EXCEL_CELL_LIMIT) -> dict[str, str]:
    """
    Divide el texto en múltiples columnas raw_text_1, raw_text_2, ...
    """
    if not text:
        return {"raw_text_1": ""}

    chunks = [
        text[i:i + chunk_size]
        for i in range(0, len(text), chunk_size)
    ]

    return {f"raw_text_{idx + 1}": chunk for idx, chunk in enumerate(chunks)}


def get_grade_from_pdf_path(pdf_path: Path) -> str:
    """
    Extrae el grado desde una ruta tipo:
    data/raw/pdfs/<grado>/<archivo>.pdf
    """
    return pdf_path.parent.name


def get_grade_from_dir(directory: Path) -> str:
    """
    Extrae el grado desde una ruta tipo:
    data/raw/pdfs/<grado>
    """
    return directory.name


def get_excel_output_path(grado: str) -> Path:
    """
    Devuelve la ruta del Excel final para ese grado:
    data/excels/<grado>/pdf_texts.xlsx
    """
    return Path("data/raw") / "excel" / grado / "pdf_texts.xlsx"


def excel_grade_folder_exists(grado: str) -> bool:
    """
    Comprueba si ya existe la carpeta del grado en data/excels/.
    """
    return (Path("data/raw") / "excel" / grado).exists()


def save_to_excel(pdf_path: Path, num_pages: int, has_text: bool, raw_text: str) -> Path:
    """
    Guarda la salida intermedia en un Excel por grado.
    """
    grado = get_grade_from_pdf_path(pdf_path)
    excel_output = get_excel_output_path(grado)
    excel_output.parent.mkdir(parents=True, exist_ok=True)

    text_columns = split_text_for_excel(raw_text)

    new_row_dict = {
        "pdf_file": pdf_path.name,
        "num_pages": num_pages,
        "has_text": has_text,
        **text_columns,
    }
    new_row = pd.DataFrame([new_row_dict])

    if excel_output.exists():
        existing_df = pd.read_excel(excel_output, sheet_name="raw_texts")
        all_columns = list(dict.fromkeys(existing_df.columns.tolist() + new_row.columns.tolist()))
        existing_df = existing_df.reindex(columns=all_columns)
        new_row = new_row.reindex(columns=all_columns)
        updated_df = pd.concat([existing_df, new_row], ignore_index=True)
    else:
        updated_df = new_row

    with pd.ExcelWriter(excel_output, engine="openpyxl", mode="w") as writer:
        updated_df.to_excel(writer, sheet_name="raw_texts", index=False)

    return excel_output


def load_pdf(pdf_path: Path) -> pdfplumber.pdf.PDF:
    if not pdf_path.exists():
        raise FileNotFoundError(f"No existe el archivo: {pdf_path}")

    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(f"El archivo no es un PDF: {pdf_path}")

    return pdfplumber.open(pdf_path)


def detect_text_pdf(pdf_path: Path, min_chars: int = 30) -> bool:
    with load_pdf(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            if len(text.strip()) >= min_chars:
                return True
    return False


def extract_raw_text(pdf_path: Path) -> str:
    parts: list[str] = []

    with load_pdf(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            parts.append(f"\n--- PAGINA {i} ---\n")
            parts.append(text)

    return "".join(parts).strip()


def process_pdf(pdf_path: Path) -> None:
    print(f"\nProcesando: {pdf_path.name}")

    try:
        with load_pdf(pdf_path) as pdf:
            num_pages = len(pdf.pages)
            print(f"[OK] PDF cargado ({num_pages} páginas)")
    except Exception as e:
        print(f"[ERROR] No se ha podido abrir el PDF: {e}")
        return

    try:
        has_text = detect_text_pdf(pdf_path)
        print(f"[INFO] Tiene texto: {has_text}")
    except Exception as e:
        print(f"[ERROR] Error detectando texto: {e}")
        return

    try:
        raw_text = extract_raw_text(pdf_path)
        print(f"[OK] Texto extraído ({len(raw_text)} caracteres)")
    except Exception as e:
        print(f"[ERROR] Error extrayendo texto: {e}")
        return

    try:
        excel_output = save_to_excel(pdf_path, num_pages, has_text, raw_text)
        print(f"[OK] Guardado en Excel: {excel_output}")
    except Exception as e:
        print(f"[ERROR] Error guardando Excel: {e}")
        return


def process_directory(directory: Path) -> None:
    if not directory.exists():
        raise FileNotFoundError(f"No existe la carpeta: {directory}")

    grado = get_grade_from_dir(directory)

    # ✅ comprobación correcta pedida: revisar si ya existe la carpeta del grado en excels
    if excel_grade_folder_exists(grado):
        print(f"[SKIP] Ya existe la carpeta del grado en data/excels/{grado}. No se genera un nuevo Excel.")
        return

    pdf_files = list(directory.glob("*.pdf"))

    if not pdf_files:
        print("No se han encontrado PDFs en la carpeta.")
        return

    print(f"Se han encontrado {len(pdf_files)} PDFs para el grado {grado}.\n")

    for pdf in pdf_files:
        process_pdf(pdf)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Procesar PDFs y guardar resultados en Excel por grado."
    )

    parser.add_argument("--pdf", help="Ruta a un único PDF")
    parser.add_argument("--dir", help="Ruta a carpeta con PDFs de un grado")

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.pdf:
        process_pdf(Path(args.pdf))
    elif args.dir:
        process_directory(Path(args.dir))
    else:
        print("Debes indicar --pdf o --dir")


if __name__ == "__main__":
    main()