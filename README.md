# TFM - Pipeline de Web Scraping y Procesamiento con LLM

Este proyecto desarrolla un **pipeline completo de extracción, procesamiento y estructuración de información** a partir de documentos web, combinando técnicas de:
* Web scraping
* Procesamiento de PDFs
* Uso de modelos LLM (OpenAI)
* Generación de datos estructurados (CSV / Excel)
El objetivo es automatizar todo lo posible la obtención de información desde fuentes web y transformarla en datasets listos para análisis.

---

## Tecnologías utilizadas
* Python
* Web Scraping
* Procesamiento de PDFs
* OpenAI API (LLM)
* Pandas
* Git / GitHub

---

## Estructura del proyecto

```
TFM/
├── src_scraper/         # Descarga y parsing de PDFs
│   ├── downloader.py
│   ├── pdf_reader.py
│   ├── pdf_parser.py
│   └── pdf_text-txt.py
│
├── src_llm/            # Procesamiento con OpenAI
│   ├── main.py
│   ├── llm_client.py
│   └── openai_txt_to_excel.py
│
├── src/                # Transformaciones finales
│   ├── csv_to_excel.py
│   └── script2.py
│
├── data/               # Datos intermedios
├── output/             # Resultados finales
├── requirements.txt
└── README.md
```

---

## Instalación

### 1. Clonar repositorio

```bash
git clone https://github.com/AndyNuzzi/TFM.git
cd TFM
```

### 2. Crear entorno virtual

```bash
python -m venv venv
```

### 3. Activar entorno

* Windows:

```bash
venv\Scripts\activate
```

* Mac/Linux:

```bash
source venv/bin/activate
```

### 4. Instalar dependencias

```bash
pip install -r requirements.txt
```

---

## Configuración de OpenAI

Crea un archivo `.env` en la raíz del proyecto con:

```text
OPENAI_API_KEY=tu_api_key_aqui
```

---

# Uso del proyecto (pipeline completo)

El flujo del proyecto se divide en varias fases:

## Web Scraping (descarga de PDFs)

Ejecuta:

```bash
python src_scraper/downloader.py
```

Descarga los documentos PDF desde la fuente web.

## Lectura y parsing de PDFs

```bash
python src_scraper/pdf_reader.py
```

y/o:

```bash
python src_scraper/pdf_parser.py
```

Extrae el contenido de los PDFs.

## Conversión de PDF a TXT

```bash
python src_scraper/pdf_text-txt.py
```

Genera archivos `.txt` a partir de los PDFs.

## Procesamiento con LLM (OpenAI)

```bash
python src_llm/main.py
```
El modelo:
* analiza los textos
* extrae información relevante
* genera datos estructurados

## Generación de CSV

El procesamiento con LLM genera archivos en formato CSV automáticamente.

## Conversión de CSV a Excel

```bash
python src/csv_to_excel.py
```

Convierte los CSV en archivos Excel (`.xlsx`) listos para análisis.

---

# Resultados

Los resultados finales se almacenan en:

```
output/
```

Incluyen:
* archivos CSV
* archivos Excel
* datos estructurados listos para análisis

---

# Pipeline completo

```
Web → PDFs → TXT → LLM → CSV → Excel
```

---

# Licencia

Proyecto desarrollado con fines académicos.
