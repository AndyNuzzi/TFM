import re
from pathlib import Path
import pandas as pd


def extract_simple_indicators(raw_text: str, grado: str, pdf_file: str) -> list[dict]:
    """
    Extrae indicadores simples tipo:
    % DOCTORES 78.1%
    Nº DOCTORES 50
    """
    records = []

    lines = raw_text.split("\n")

    for line in lines:
        line = line.strip()

        # patrón: texto + número o porcentaje
        match = re.match(r"(.+?)\s+(\d+[.,]?\d*)%?$", line)

        if match:
            indicador = match.group(1).strip()
            valor = match.group(2).replace(",", ".")

            unidad = "%" if "%" in line else "numero"

            records.append({
                "grado": grado,
                "pdf_file": pdf_file,
                "indicador": indicador,
                "valor": float(valor),
                "unidad": unidad,
                "fuente_texto": line
            })

    return records

df = pd.read_excel("data/raw/excel/640-ingenieria-software/pdf_texts.xlsx")

raw_text = df.iloc[0]["raw_text_1"]

records = extract_simple_indicators(
    raw_text,
    grado="640-ingenieria-software",
    pdf_file="20212022.pdf"
)

print(records[:5])