from pathlib import Path
import pandas as pd


CSV_ROOT = Path("out") / "csv"
EXCEL_ROOT = Path("out") / "excel"


def get_sheet_name(name: str) -> str:
    """
    Limpia y adapta el nombre de la hoja (máx 31 chars en Excel)
    """
    return name[:31]


def convert_grade_folder_to_excel(grade_dir: Path, output_dir: Path) -> None:
    csv_files = sorted(grade_dir.glob("*.csv"))

    if not csv_files:
        print(f"[WARN] No hay CSV en {grade_dir}")
        return

    output_file = output_dir / f"{grade_dir.name}.xlsx"

    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file, encoding="utf-8-sig")

                sheet_name = get_sheet_name(csv_file.stem)

                df.to_excel(writer, sheet_name=sheet_name, index=False)

                print(f"   ✔ Hoja creada: {sheet_name}")

            except Exception as e:
                print(f"   [ERROR] {csv_file.name}: {e}")

    print(f"[OK] Excel generado: {output_file}\n")


def convert_all_grades():
    if not CSV_ROOT.exists():
        raise FileNotFoundError(f"No existe la carpeta: {CSV_ROOT}")

    EXCEL_ROOT.mkdir(parents=True, exist_ok=True)

    grade_dirs = [p for p in CSV_ROOT.iterdir() if p.is_dir()]

    if not grade_dirs:
        print("[WARN] No hay carpetas de grados")
        return

    print(f"[INFO] Procesando {len(grade_dirs)} grados...\n")

    for grade_dir in sorted(grade_dirs):
        print(f"[INFO] Grado: {grade_dir.name}")
        convert_grade_folder_to_excel(grade_dir, EXCEL_ROOT)


if __name__ == "__main__":
    convert_all_grades()