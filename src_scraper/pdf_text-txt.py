from __future__ import annotations

import argparse
from pathlib import Path

import pdfplumber


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


def get_txt_output_path(pdf_path: Path) -> Path:
    """
    Devuelve la ruta del TXT final para ese PDF:
    src_pruebas/txt/<grado>/<mismo_nombre_que_pdf>.txt
    """
    grado = get_grade_from_pdf_path(pdf_path)
    return Path("src_pruebas") / "txt" / grado / f"{pdf_path.stem}.txt"


def txt_grade_folder_exists(grado: str) -> bool:
    """
    Comprueba si ya existe la carpeta del grado en src_pruebas/txt/.
    """
    return (Path("src_pruebas") / "txt" / grado).exists()


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


def save_to_txt(pdf_path: Path, num_pages: int, has_text: bool, raw_text: str) -> Path:
    """
    Guarda la salida intermedia en un TXT por PDF/curso,
    usando el mismo nombre que el PDF.
    """
    txt_output = get_txt_output_path(pdf_path)
    txt_output.parent.mkdir(parents=True, exist_ok=True)

    content = [
        "===== PDF START =====",
        f"pdf_file: {pdf_path.name}",
        f"num_pages: {num_pages}",
        f"has_text: {has_text}",
        "",
        "===== RAW TEXT =====",
        raw_text,
        "",
        "===== PDF END =====",
    ]

    txt_output.write_text("\n".join(content), encoding="utf-8")
    return txt_output


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
        txt_output = save_to_txt(pdf_path, num_pages, has_text, raw_text)
        print(f"[OK] Guardado en TXT: {txt_output}")
    except Exception as e:
        print(f"[ERROR] Error guardando TXT: {e}")
        return


def process_directory(directory: Path) -> None:
    if not directory.exists():
        raise FileNotFoundError(f"No existe la carpeta: {directory}")

    grado = get_grade_from_dir(directory)

    if txt_grade_folder_exists(grado):
        print(f"[SKIP] Ya existe la carpeta del grado en src_pruebas/txt/{grado}. No se generan nuevos TXT.")
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
        description="Procesar PDFs y guardar resultados en TXT por curso."
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