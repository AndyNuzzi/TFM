from __future__ import annotations

import argparse
import csv
import re
import time
import unicodedata
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
import truststore
from bs4 import BeautifulSoup

truststore.inject_into_ssl()

HEADERS = {
    "User-Agent": "TFM-MUISD-scraper/0.1"
}

DATA_DIR = Path("data")
LOG_DIR = DATA_DIR / "logs"
ERROR_FILE = LOG_DIR / "errors.csv"
INVENTORY_FILE = LOG_DIR / "inventory.csv"
RAW_DIR = DATA_DIR / "raw"


def ensure_directories(pdf_dir: Path) -> None:
    pdf_dir.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def log_error(url: str, error_type: str, detail: str) -> None:
    file_exists = ERROR_FILE.exists()
    with open(ERROR_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "url", "error_type", "detail"])
        writer.writerow([datetime.now().isoformat(), url, error_type, detail])


def register_inventory(local_path: Path, url: str, grado: str) -> None:
    file_exists = INVENTORY_FILE.exists()
    with open(INVENTORY_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["grado", "local_path", "url_origen"])
        writer.writerow([grado, str(local_path), url])


def get_html(url: str, retries: int = 1, timeout: int = 20) -> str | None:
    for attempt in range(retries + 1):
        try:
            response = requests.get(url, headers=HEADERS, timeout=timeout)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            if attempt == retries:
                log_error(url, "html_request_failed", str(e))
                return None
            time.sleep(2)
    return None


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text).strip("-")
    return text


def normalize_filename(name: str) -> str:
    name = unicodedata.normalize("NFKD", name)
    name = name.encode("ascii", "ignore").decode("ascii")
    name = name.lower()
    name = re.sub(r"[^\w\s-]", "", name)
    name = re.sub(r"[-\s]+", "_", name).strip("_")
    if not name.endswith(".pdf"):
        name += ".pdf"
    return name


def filename_from_url(url: str) -> str:
    parsed = urlparse(url)
    raw_name = Path(parsed.path).name
    if raw_name:
        return normalize_filename(raw_name)
    return f"documento_{int(time.time())}.pdf"


def grade_slug_from_url(url: str) -> str:
    path = urlparse(url).path.strip("/")
    last_segment = path.split("/")[-1]
    return normalize_text(last_segment)


def normalize_url_for_comparison(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    return f"{parsed.scheme}://{parsed.netloc}{path}"


def validate_degree_url(url: str) -> None:
    parsed = urlparse(url)

    if parsed.scheme != "https":
        raise ValueError("La URL debe usar HTTPS.")

    if parsed.netloc not in {"www.urjc.es", "urjc.es"}:
        raise ValueError("La URL debe pertenecer al dominio oficial de la URJC.")

    path = parsed.path.rstrip("/")

    valid_patterns = [
        r"^/estudios/\d+-[a-zA-Z0-9\-]+$",
        r"^/estudios/grado/\d+-[a-zA-Z0-9\-]+$",
        r"^/universidad/facultades/escuela-tecnica-superior-de-ingenieria-informatica/\d+-[a-zA-Z0-9\-]+$",
    ]

    if not any(re.match(pattern, path) for pattern in valid_patterns):
        raise ValueError(
            "La URL no tiene un formato válido de página de grado URJC."
        )


def validate_degree_page(url: str) -> str:
    validate_degree_url(url)

    try:
        response = requests.get(url, headers=HEADERS, timeout=20, allow_redirects=True)
        response.raise_for_status()
    except requests.RequestException as e:
        raise ValueError(f"No se ha podido acceder a la página del grado: {e}")

    input_url = normalize_url_for_comparison(url)
    final_url = normalize_url_for_comparison(response.url)

    # Si la URL final no coincide exactamente con la introducida, no se acepta
    if final_url != input_url:
        raise ValueError(
            f"La URL introducida no coincide exactamente con una página válida del grado. "
            f"URL solicitada: {input_url} | URL final resuelta: {final_url}"
        )

    html = response.text

    # Comprobación adicional opcional: asegurarse de que parece una ficha académica
    indicators = [
        "guías docentes",
        "garantía de calidad",
        "plan de estudios",
        "admisión"
    ]

    html_lower = html.lower()
    if not any(indicator in html_lower for indicator in indicators):
        raise ValueError(
            "La página no parece corresponder a una ficha válida de titulación de la URJC."
        )

    return html


def download_file(url: str, filename: str, pdf_dir: Path, grado: str,
                  retries: int = 1, timeout: int = 20) -> bool:
    ensure_directories(pdf_dir)
    destination = pdf_dir / filename

    if destination.exists():
        print(f"[SKIP] Ya existe: {destination}")
        return True

    last_error = ""

    for attempt in range(retries + 1):
        try:
            response = requests.get(url, headers=HEADERS, timeout=timeout)
            response.raise_for_status()

            destination.write_bytes(response.content)
            register_inventory(destination, url, grado)
            print(f"[OK] Descargado: {destination}")
            return True

        except requests.RequestException as e:
            last_error = str(e)
            print(f"[WARN] Intento {attempt + 1} fallido para {url}: {last_error}")
            if attempt < retries:
                time.sleep(2)

    log_error(url, "download_failed", last_error)
    return False


def extract_links_from_html(page_url: str, html: str) -> list[tuple[str, str]]:
    soup = BeautifulSoup(html, "lxml")
    results: list[tuple[str, str]] = []

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        text = a.get_text(" ", strip=True)
        full_url = urljoin(page_url, href)
        results.append((text, full_url))

    return results


def extract_links(page_url: str) -> list[tuple[str, str]]:
    html = get_html(page_url)
    if html is None:
        return []
    return extract_links_from_html(page_url, html)


def find_quality_page_url(links: list[tuple[str, str]]) -> str | None:
    for text, url in links:
        combined = f"{text} {url}".lower()
        if "garantia" in combined and "calidad" in combined:
            return url
    return None


def filter_result_reports_pdf_links(links: list[tuple[str, str]]) -> list[tuple[str, str]]:
    pdf_links: list[tuple[str, str]] = []

    for text, url in links:
        text_low = text.lower()
        url_low = url.lower()

        is_pdf = url_low.endswith(".pdf") or ".pdf?" in url_low
        looks_like_results = (
            "resultado" in text_low
            or "resultados" in text_low
            or "resultado" in url_low
            or "resultados" in url_low
        )

        if is_pdf and looks_like_results:
            pdf_links.append((text, url))

    return pdf_links


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Descarga informes de resultados desde la sección de Garantía de Calidad de un grado URJC."
    )
    parser.add_argument(
        "--url",
        required=True,
        help="URL exacta de la página del grado, por ejemplo: https://www.urjc.es/estudios/640-ingenieria-software"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base_url = args.url

    # Validación estricta de la página de entrada
    try:
        base_html = validate_degree_page(base_url)
    except ValueError as e:
        print(f"[ERROR] {e}")
        return

    grado = grade_slug_from_url(base_url)
    pdf_dir = RAW_DIR / "pdfs" / grado

    print(f"Página base validada: {base_url}")
    print(f"Grado detectado: {grado}")
    print(f"Directorio de descarga: {pdf_dir}")

    base_links = extract_links_from_html(base_url, base_html)

    if not base_links:
        print("[ERROR] No se han podido extraer enlaces de la página base.")
        return

    quality_url = find_quality_page_url(base_links)

    if quality_url is None:
        print("[ERROR] No se ha encontrado el enlace de Garantía de Calidad en la página base.")
        return

    print(f"Página de Garantía de Calidad encontrada: {quality_url}")

    quality_links = extract_links(quality_url)

    if not quality_links:
        print("[ERROR] No se han podido extraer enlaces de la página de Garantía de Calidad.")
        return

    pdf_links = filter_result_reports_pdf_links(quality_links)

    if not pdf_links:
        print("[ERROR] No se han encontrado PDFs de informes de resultados.")
        print("Revisa manualmente la página para ajustar el filtro.")
        return

    print(f"PDFs de informes de resultados encontrados: {len(pdf_links)}")

    for text, pdf_url in pdf_links:
        suggested_name = normalize_filename(text) if text else filename_from_url(pdf_url)
        if suggested_name == ".pdf":
            suggested_name = filename_from_url(pdf_url)

        download_file(pdf_url, suggested_name, pdf_dir, grado)


if __name__ == "__main__":
    main()