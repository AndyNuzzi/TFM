from pathlib import Path
import pandas as pd

OUTPUT_PATH = Path("data/test_dataset.xlsx")

def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    dim_asignatura = pd.DataFrame([
        {"asignatura_id": 1, "asignatura": "Matemáticas I", "grado": "GITI"},
        {"asignatura_id": 2, "asignatura": "Programación", "grado": "GITI"},
        {"asignatura_id": 3, "asignatura": "Bases de Datos", "grado": "GITI"},
    ])

    dim_curso = pd.DataFrame([
        {"curso_id": 1, "curso_academico": "2023-2024"},
        {"curso_id": 2, "curso_academico": "2024-2025"},
    ])

    fact_resultados = pd.DataFrame([
        {"curso_id": 1, "asignatura_id": 1, "matriculados": 120, "aprobados": 85},
        {"curso_id": 1, "asignatura_id": 2, "matriculados": 95, "aprobados": 70},
        {"curso_id": 1, "asignatura_id": 3, "matriculados": 80, "aprobados": 65},
    ])

    with pd.ExcelWriter(OUTPUT_PATH, engine="openpyxl") as writer:
        dim_asignatura.to_excel(writer, sheet_name="dim_asignatura", index=False)
        dim_curso.to_excel(writer, sheet_name="dim_curso", index=False)
        fact_resultados.to_excel(writer, sheet_name="fact_resultados", index=False)

    print(f"Excel generado: {OUTPUT_PATH.resolve()}")

if __name__ == "__main__":
    main()