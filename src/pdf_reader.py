from __future__ import annotations

import argparse
import csv
from pathlib import Path

import pdfplumber


def save_to_csv(pdf_path: Path, num_pages: int, has_text: bool, raw_text: str) -> Path:
    """
    HU-D-10.5: Guardar salida de prueba en CSV por grado.
    """

    # Extraer el grado desde la carpeta que contiene el PDF
    grado = pdf_path.parent.name

    # Guardar CSV en data/raw/<grado>/pdf_texts.csv
    csv_output = Path("data/raw") / "csv" / grado / "pdf_texts.csv"
    csv_output.parent.mkdir(parents=True, exist_ok=True)

    file_exists = csv_output.exists()

    with open(csv_output, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow(["pdf_file", "num_pages", "has_text", "raw_text"])

        writer.writerow([
            pdf_path.name,
            num_pages,
            has_text,
            raw_text
        ])

    return csv_output


def load_pdf(pdf_path: Path) -> pdfplumber.pdf.PDF:
    """
    HU-D-10.1: Leer un PDF desde ruta local.
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"No existe el archivo: {pdf_path}")

    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(f"El archivo no es un PDF: {pdf_path}")

    return pdfplumber.open(pdf_path)


def detect_text_pdf(pdf_path: Path, min_chars: int = 30) -> bool:
    """
    HU-D-10.2: Detectar si el PDF contiene texto extraíble.
    Devuelve True si encuentra suficiente texto en alguna página.
    """
    with load_pdf(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            if len(text.strip()) >= min_chars:
                return True
    return False


def extract_raw_text(pdf_path: Path) -> str:
    """
    HU-D-10.3: Extraer texto bruto del PDF.
    Concatena el texto de todas las páginas.
    """
    parts: list[str] = []

    with load_pdf(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            parts.append(f"\n--- PAGINA {i} ---\n")
            parts.append(text)

    return "".join(parts).strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Leer un PDF local, detectar si contiene texto y extraer su texto bruto."
    )
    parser.add_argument(
        "--pdf",
        required=True,
        help="Ruta local al archivo PDF"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pdf_path = Path(args.pdf)

    print(f"PDF de entrada: {pdf_path}")

    # HU-D-10.1
    try:
        with load_pdf(pdf_path) as pdf:
            num_pages = len(pdf.pages)
            print("[OK] PDF cargado correctamente.")
            print(f"[INFO] Número de páginas: {num_pages}")
    except Exception as e:
        print(f"[ERROR] No se ha podido abrir el PDF: {e}")
        return

    # HU-D-10.2
    try:
        has_text = detect_text_pdf(pdf_path)
        if has_text:
            print("[OK] El PDF contiene texto extraíble.")
        else:
            print("[WARN] El PDF no parece contener texto extraíble (podría ser escaneado).")
    except Exception as e:
        print(f"[ERROR] No se ha podido analizar el PDF: {e}")
        return

    # HU-D-10.3
    try:
        raw_text = extract_raw_text(pdf_path)
        print("[OK] Texto bruto extraído correctamente.")
        print(f"[INFO] Número total de caracteres extraídos: {len(raw_text)}")
        print("\nPrimeros 100 caracteres:\n")
        print(raw_text[:100])
    except Exception as e:
        print(f"[ERROR] No se ha podido extraer texto del PDF: {e}")
        return

    # HU-D-10.5
    try:
        csv_output = save_to_csv(pdf_path, num_pages, has_text, raw_text)
        print(f"[OK] Datos guardados en CSV: {csv_output}")
    except Exception as e:
        print(f"[ERROR] No se ha podido guardar en CSV: {e}")
        return


if __name__ == "__main__":
    main()