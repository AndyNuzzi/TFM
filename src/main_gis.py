from __future__ import annotations

import argparse
from pathlib import Path

from openai_gis_txt_root_to_excel import process_root_directory


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Procesa todos los grados dentro de una carpeta raíz y genera un único Excel."
    )
    parser.add_argument(
        "--root-dir",
        required=True,
        help="Ruta a la carpeta raíz que contiene las subcarpetas de los grados"
    )
    parser.add_argument(
        "--model",
        default="gpt-5.4-mini",
        help="Modelo de OpenAI a utilizar"
    )
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Ignora la caché y vuelve a llamar a OpenAI"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    output_path = process_root_directory(
        root_dir=Path(args.root_dir),
        model=args.model,
        force_refresh=args.force_refresh,
    )

    print(f"\n[OK] Excel generado en: {output_path}")


if __name__ == "__main__":
    main()