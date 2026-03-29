from __future__ import annotations

import argparse
from pathlib import Path

from openai_txt_to_excel import process_root_directory


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Procesa todos los TXT de todos los grados y genera un único Excel global."
    )
    parser.add_argument(
        "--root-dir",
        required=True,
        help="Ruta a la carpeta raíz que contiene subcarpetas de grados con archivos TXT"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root_dir = Path(args.root_dir)

    try:
        output_path = process_root_directory(root_dir)
        print(f"\n[OK] Excel global generado en: {output_path}")
    except Exception as e:
        print(f"[ERROR] {e}")


if __name__ == "__main__":
    main()