from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

OUTPUT_PATH = Path("src") / "excel" / "resultados_globales.xlsx"


def get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("No se ha encontrado OPENAI_API_KEY en el archivo .env")
    return OpenAI(api_key=api_key)


def build_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "resumen_documento": {
                "type": "object",
                "properties": {
                    "archivo_origen": {"type": ["string", "null"]},
                    "pdf_file": {"type": ["string", "null"]},
                    "curso_academico": {"type": ["string", "null"]},
                    "grado": {"type": ["string", "null"]},
                    "campus": {"type": ["string", "null"]},
                    "num_pages": {"type": ["integer", "null"]},
                    "has_text": {"type": ["boolean", "null"]},
                    "tipo_documento": {"type": ["string", "null"]},
                },
                "required": [
                    "archivo_origen",
                    "pdf_file",
                    "curso_academico",
                    "grado",
                    "campus",
                    "num_pages",
                    "has_text",
                    "tipo_documento",
                ],
                "additionalProperties": False,
            },
            "nota_corte": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "archivo_origen": {"type": ["string", "null"]},
                        "curso_academico": {"type": ["string", "null"]},
                        "grado": {"type": ["string", "null"]},
                        "campus": {"type": ["string", "null"]},
                        "convocatoria": {"type": ["string", "null"]},
                        "nota_corte": {"type": ["number", "null"]},
                    },
                    "required": [
                        "archivo_origen",
                        "curso_academico",
                        "grado",
                        "campus",
                        "convocatoria",
                        "nota_corte",
                    ],
                    "additionalProperties": False,
                },
            },
            "resultados_asignaturas": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "archivo_origen": {"type": ["string", "null"]},
                        "curso_academico": {"type": ["string", "null"]},
                        "grado": {"type": ["string", "null"]},
                        "campus": {"type": ["string", "null"]},
                        "curso": {"type": ["integer", "null"]},
                        "asignatura": {"type": ["string", "null"]},
                        "caracter": {"type": ["string", "null"]},
                        "num_alumnos": {"type": ["integer", "null"]},
                        "matriculados": {"type": ["integer", "null"]},
                        "matriculados_1_matricula": {"type": ["integer", "null"]},
                        "matriculados_posteriores": {"type": ["integer", "null"]},
                        "aprobados": {"type": ["integer", "null"]},
                        "suspensos": {"type": ["integer", "null"]},
                        "no_presentados": {"type": ["integer", "null"]},
                        "rendimiento": {"type": ["number", "null"]},
                        "presentacion": {"type": ["number", "null"]},
                        "superacion": {"type": ["number", "null"]},
                        "exito": {"type": ["number", "null"]},
                        "valoracion_docente": {"type": ["number", "null"]},
                        "rend_en_1_matricula": {"type": ["number", "null"]},
                        "pct_aprobados": {"type": ["number", "null"]},
                        "pct_suspensos": {"type": ["number", "null"]},
                        "pct_no_presentados": {"type": ["number", "null"]},
                        "observaciones": {"type": ["string", "null"]},
                    },
                    "required": [
                        "archivo_origen",
                        "curso_academico",
                        "grado",
                        "campus",
                        "curso",
                        "asignatura",
                        "caracter",
                        "num_alumnos",
                        "matriculados",
                        "matriculados_1_matricula",
                        "matriculados_posteriores",
                        "aprobados",
                        "suspensos",
                        "no_presentados",
                        "rendimiento",
                        "presentacion",
                        "superacion",
                        "exito",
                        "valoracion_docente",
                        "rend_en_1_matricula",
                        "pct_aprobados",
                        "pct_suspensos",
                        "pct_no_presentados",
                        "observaciones",
                    ],
                    "additionalProperties": False,
                },
            },
        },
        "required": [
            "resumen_documento",
            "nota_corte",
            "resultados_asignaturas",
        ],
        "additionalProperties": False,
    }


def build_prompt(txt_content: str, filename: str, grade_folder: str) -> str:
    return f"""
Eres un extractor de datos académicos universitarios.

Debes analizar un archivo TXT procedente de informes académicos de la URJC
y devolver SOLO datos estructurados siguiendo exactamente el esquema JSON solicitado.

Reglas:
1. No inventes datos.
2. Si un valor no aparece claramente, devuelve null.
3. Los porcentajes deben devolverse como números sin el símbolo %, por ejemplo 66.67
4. Reconstruye correctamente nombres de asignaturas aunque estén partidos en varias líneas.
5. Devuelve tres bloques:
   - resumen_documento
   - nota_corte
   - resultados_asignaturas
6. En resultados_asignaturas:
   - una fila por asignatura
   - usa el curso numérico: 1, 2, 3 o 4 cuando se pueda identificar
   - si una columna no existe en ese año, deja null
7. Mantén archivo_origen como "{filename}"
8. El valor de "grado" debe salir del documento si aparece claramente; si no, usa null.
9. No metas texto fuera del JSON.

Información adicional:
- carpeta_del_grado = "{grade_folder}"

Contenido del TXT:
--------------------
{txt_content}
--------------------
"""


def call_openai_for_txt(txt_path: Path, grade_folder: str) -> dict:
    client = get_client()
    txt_content = txt_path.read_text(encoding="utf-8")
    schema = build_schema()
    prompt = build_prompt(txt_content, txt_path.name, grade_folder)

    response = client.responses.create(
        model="gpt-5.4",
        input=prompt,
        text={
            "format": {
                "type": "json_schema",
                "name": "urjc_academic_report",
                "schema": schema,
                "strict": True,
            }
        },
    )

    return json.loads(response.output_text)


def ensure_dataframe(columns: list[str], rows: list[dict]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(columns=columns)

    df = pd.DataFrame(rows)

    for col in columns:
        if col not in df.columns:
            df[col] = None

    return df[columns]


def list_grade_directories(root_dir: Path) -> list[Path]:
    return sorted([p for p in root_dir.iterdir() if p.is_dir()])


def list_txt_files(directory: Path) -> list[Path]:
    return sorted(directory.glob("*.txt"))


def process_root_directory(root_dir: Path) -> Path:
    if not root_dir.exists():
        raise FileNotFoundError(f"No existe la carpeta raíz: {root_dir}")

    if not root_dir.is_dir():
        raise ValueError(f"La ruta no es un directorio: {root_dir}")

    grade_dirs = list_grade_directories(root_dir)
    if not grade_dirs:
        raise FileNotFoundError(f"No se han encontrado subcarpetas de grados en: {root_dir}")

    print(f"[INFO] Se han encontrado {len(grade_dirs)} carpetas de grados")

    resumen_rows: list[dict] = []
    nota_corte_rows: list[dict] = []
    resultados_rows: list[dict] = []

    for grade_dir in grade_dirs:
        grade_folder = grade_dir.name
        txt_files = list_txt_files(grade_dir)

        if not txt_files:
            print(f"[WARN] La carpeta {grade_folder} no contiene TXT")
            continue

        print(f"\n[INFO] Procesando grado: {grade_folder} ({len(txt_files)} TXT)")

        for txt_file in txt_files:
            print(f"  -> {txt_file.name}")

            data = call_openai_for_txt(txt_file, grade_folder)

            resumen = data.get("resumen_documento", {})
            if resumen:
                resumen["grado_carpeta"] = grade_folder
                resumen_rows.append(resumen)

            notas = data.get("nota_corte", [])
            for row in notas:
                row["grado_carpeta"] = grade_folder
            nota_corte_rows.extend(notas)

            resultados = data.get("resultados_asignaturas", [])
            for row in resultados:
                row["grado_carpeta"] = grade_folder
            resultados_rows.extend(resultados)

            print(
                f"     [OK] resumen={1 if resumen else 0}, "
                f"nota_corte={len(notas)}, "
                f"resultados={len(resultados)}"
            )

    resumen_columns = [
        "grado_carpeta",
        "archivo_origen",
        "pdf_file",
        "curso_academico",
        "grado",
        "campus",
        "num_pages",
        "has_text",
        "tipo_documento",
    ]

    nota_corte_columns = [
        "grado_carpeta",
        "archivo_origen",
        "curso_academico",
        "grado",
        "campus",
        "convocatoria",
        "nota_corte",
    ]

    resultados_columns = [
        "grado_carpeta",
        "archivo_origen",
        "curso_academico",
        "grado",
        "campus",
        "curso",
        "asignatura",
        "caracter",
        "num_alumnos",
        "matriculados",
        "matriculados_1_matricula",
        "matriculados_posteriores",
        "aprobados",
        "suspensos",
        "no_presentados",
        "rendimiento",
        "presentacion",
        "superacion",
        "exito",
        "valoracion_docente",
        "rend_en_1_matricula",
        "pct_aprobados",
        "pct_suspensos",
        "pct_no_presentados",
        "observaciones",
    ]

    df_resumen = ensure_dataframe(resumen_columns, resumen_rows)
    df_nota_corte = ensure_dataframe(nota_corte_columns, nota_corte_rows)
    df_resultados = ensure_dataframe(resultados_columns, resultados_rows)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(OUTPUT_PATH, engine="openpyxl") as writer:
        df_resumen.to_excel(writer, sheet_name="resumen_documentos", index=False)
        df_nota_corte.to_excel(writer, sheet_name="nota_corte", index=False)
        df_resultados.to_excel(writer, sheet_name="resultados_asignaturas", index=False)

    return OUTPUT_PATH