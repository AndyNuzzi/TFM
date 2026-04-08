import pdfplumber
import os
import sys
from pathlib import Path


def extract_text(root, filename):
    file_path = os.path.join(root, filename)
    output_lines = []

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:

            # ---- 1. Detectar tablas ----
            tables = page.find_tables()
            table_bboxes = [t.bbox for t in tables]

            # ---- 2. Texto fuera de tablas ----
            words = page.extract_words()
            texto_fuera = []

            for w in words:
                x0, top, x1, bottom = w["x0"], w["top"], w["x1"], w["bottom"]

                dentro_tabla = any(
                    (x0 >= bx0 and x1 <= bx1 and top >= by0 and bottom <= by1)
                    for (bx0, by0, bx1, by1) in table_bboxes
                )

                if not dentro_tabla:
                    texto_fuera.append(w["text"])

            if texto_fuera:
                output_lines.append("[TEXTO]")
                output_lines.append(" ".join(texto_fuera))

            # ---- 3. Procesar tablas ----
            for table in page.extract_tables():
                output_lines.append("[TABLA]")
                for row in table:
                    row_clean = [
                        (cell or "").replace("\n", " ").strip()
                        for cell in row
                    ]
                    output_lines.append(" | ".join(row_clean))

    # ---- 4. Unir todo en un único string ----
    texto_final = "\n".join(output_lines)

    # ---- 5. Guardar ----
    carpeta_origen = Path(root).name
    output_dir = Path("output") / carpeta_origen
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"{Path(filename).stem}.txt"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(texto_final)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python script.py <ruta_pdf_o_directorio>")
        sys.exit(1)

    ruta = Path(sys.argv[1])

    if ruta.is_file() and ruta.suffix.lower() == ".pdf":
        extract_text(str(ruta.parent), ruta.name)

    elif ruta.is_dir():
        for root, dirs, files in os.walk(ruta):
            for f in files:
                if f.lower().endswith(".pdf"):
                    extract_text(root, f)

    else:
        print("La ruta indicada no es un PDF ni un directorio válido")
        sys.exit(1)