from pathlib import Path
import pdfplumber

PDF_PATH = Path("data/sample_pdf_text.pdf")  # <-- pon aquí un PDF real descargado

def main() -> None:
    if not PDF_PATH.exists():
        raise FileNotFoundError(f"No existe el archivo: {PDF_PATH.resolve()}")

    with pdfplumber.open(PDF_PATH) as pdf:
        first_page = pdf.pages[0]

        text = first_page.extract_text() or ""
        images = first_page.images or []

        print("PDF:", PDF_PATH.name)
        print("Nº páginas:", len(pdf.pages))
        print("Caracteres extraídos (pág.1):", len(text.strip()))
        print("Nº imágenes detectadas (pág.1):", len(images))

        if len(text.strip()) >= 50:
            print("Diagnóstico: PDF con TEXTO (extraíble)")
        elif len(images) > 0:
            print("Diagnóstico: PROBABLEMENTE ESCANEADO (requiere OCR)")
        else:
            print("Diagnóstico: texto muy bajo; revisar manualmente")

if __name__ == "__main__":
    main()