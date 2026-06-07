# Manual de usuario: replicación del pipeline de extracción de datos y elaboración del dashboard

Este anexo describe paso a paso cómo replicar el proceso completo de extracción de datos académicos y construcción del dashboard en Power BI para cualquier grado de la Universidad Rey Juan Carlos (URJC). El pipeline transforma los informes de calidad académica publicados en la web institucional en datos estructurados listos para su análisis visual.

---

## Requisitos previos

Antes de comenzar, es necesario disponer de los siguientes elementos:

- **Python 3.11** o superior, con `pip` disponible.
- **Visual Studio Code** u otro entorno de desarrollo.
- **Cuenta en OpenAI** con acceso a la API y una clave activa. El sistema utiliza el modelo `gpt-5.4` para el procesamiento semántico.
- **Power BI Desktop** (versión gratuita disponible en https://powerbi.microsoft.com), solo disponible para Windows.
- **Git** para clonar el repositorio.
- Conexión a internet para acceder a la web de la URJC y a la API de OpenAI.

---

## Instalación del entorno

Para poder ejecutar el pipeline es necesario configurar previamente el entorno de desarrollo. A continuación se describen los pasos necesarios para tener el proyecto operativo desde cero.

1. **Clonar el repositorio.** El código fuente está publicado en GitHub. Para obtener una copia local, ejecuta:
```bash
   git clone https://github.com/AndyNuzzi/TFM.git
   cd TFM
```

2. **Crear y activar el entorno virtual.** Para aislar las dependencias del proyecto y evitar conflictos con otras instalaciones de Python en el sistema, se recomienda trabajar dentro de un entorno virtual:
```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # Mac / Linux
   source venv/bin/activate
```
   Una vez activado, el nombre del entorno aparecerá entre paréntesis al inicio de la línea de comandos.

3. **Instalar las dependencias.** El repositorio incluye un fichero `requirements.txt` con todas las bibliotecas necesarias. Para instalarlas de una sola vez:
```bash
   pip install -r requirements.txt
```

4. **Configurar la clave de la API de OpenAI.** Crea un fichero `.env` en la raíz del proyecto con el siguiente contenido, sustituyendo el valor por tu clave personal:

```OPENAI_API_KEY=tu_api_key_aqui
```
Este fichero está incluido en el `.gitignore` y no debe subirse a GitHub bajo ningún concepto, ya que contiene credenciales de acceso privadas.

---

## Fase 1: Descarga de PDFs mediante web scraping

Para obtener los informes académicos de un grado, el primer paso consiste en identificar su página oficial en la web de la URJC y ejecutar el script de descarga.

1. **Identificar la URL del grado.** Accede a https://www.urjc.es/etsii y localiza la página del grado que se desea procesar.
   La URL debe seguir el patrón:
```https://www.urjc.es/estudios/XXXX-nombre-del-grado```
   Por ejemplo, para el Grado en Ingeniería del Software:
```https://www.urjc.es/estudios/640-ingenieria-software```
2. **Ejecutar el script de descarga.** Desde el directorio raíz del proyecto, ejecuta:
```bash
   python src_scraper/downloader.py \
       --url https://www.urjc.es/estudios/640-ingenieria-software
```
   El script realiza automáticamente las siguientes acciones: valida que la URL pertenece al dominio oficial de la URJC, navega hasta la sección de Garantía de Calidad del grado, localiza todos los enlaces a documentos PDF de informes de resultados, descarga cada PDF y lo almacena en `data/raw/pdfs/<nombre-del-grado>/`, y registra tanto un inventario de las descargas en `data/logs/inventory.csv` como los errores producidos, si los hubiera, en `data/logs/errors.csv`. Si un PDF ya existe en la carpeta de destino, el script lo omite sin volver a descargarlo, lo que permite relanzar el proceso sin generar duplicados.

---

## Fase 2: Conversión de PDFs a TXT

Una vez descargados los PDFs, el siguiente paso consiste en extraer su contenido textual y almacenarlo en ficheros `.txt`, uno por cada PDF. El script admite dos modos de ejecución dependiendo de si se quiere procesar un grado completo o un único documento.

1. **Procesar todos los PDFs de un grado.** Desde el directorio raíz del proyecto, indica la carpeta del grado con el argumento `--dir`:
```bash
   python src_scraper/pdf_text-txt.py \
       --dir data/raw/pdfs/640-ingenieria-software
```

2. **Procesar un único PDF.** Si solo se quiere convertir un documento concreto, usa el argumento `--pdf`:
```bash
   python src_scraper/pdf_text-txt.py \
       --pdf data/raw/pdfs/640-ingenieria-software/20232024.pdf
```

Los ficheros TXT resultantes se almacenan en `src_pruebas/txt/<nombre-del-grado>/`. Cada fichero incluye el texto extraído página a página con separadores explícitos (`--- PAGINA N ---`) y metadatos básicos del PDF de origen. Si la carpeta del grado ya existe, el script la omite para evitar sobreescrituras; para forzar la regeneración, es necesario eliminar previamente la carpeta correspondiente.

---

## Fase 3: Revisión manual de los TXT

Esta es la única fase manual del pipeline y resulta fundamental para garantizar la calidad de los datos. Los PDFs de informes académicos presentan con frecuencia problemas de extracción debidos a su formato tabular y a la fragmentación del contenido entre páginas. Antes de enviar los TXT al modelo de lenguaje, se deben revisar y corregir los problemas más habituales:

- **Nombres de asignaturas partidos:** reconstruir manualmente los nombres fragmentados por saltos de línea o espacios erróneos (por ejemplo, `PROGRAMA CION` → `PROGRAMACION`).
- **Números con espacios intermedios:** corregir valores como `6 5` que deben leerse como `65`.
- **Tablas fragmentadas entre páginas:** verificar que el encabezado de columnas y sus filas de datos estén en el mismo bloque de texto.
- **Encabezados de campus:** comprobar que los encabezados `MADRID`, `MÓSTOLES` y `SEMIPRESENCIAL` estén presentes y claramente diferenciados cuando el grado tiene varios campus.
- **Contenido redundante:** eliminar páginas de portada, índices u otros elementos que no contengan datos académicos y puedan interferir con la extracción.

La revisión de cada TXT suele requerir entre 5 y 15 minutos dependiendo de la complejidad del documento.

---

## Fase 4: Procesamiento con LLM y generación de CSV

En esta fase, cada TXT revisado se envía a la API de OpenAI. El modelo de lenguaje analiza el contenido semánticamente y genera una salida en formato JSON estructurado, que se transforma automáticamente en ficheros CSV.

1. **Ejecutar el procesamiento.** Desde el directorio `src_llm/`, ejecuta el siguiente comando. El script procesará de forma secuencial todos los grados que encuentre bajo la ruta indicada:
```bash
   python main.py --root-dir ../src_pruebas/txt
```

2. **Ficheros generados.** Por cada grado, se crean los siguientes ficheros CSV en `out/csv/<nombre-del-grado>/`:

   | Fichero | Contenido |
   |---|---|
   | `origen_datos.csv` | Metadatos del fichero de origen |
   | `resumen_documento.csv` | Grado, campus y curso académico |
   | `nota_corte.csv` | Nota de corte por curso y campus |
   | `perfil_ingreso.csv` | Métricas de acceso y demanda |
   | `resultados_asignaturas.csv` | Resultados académicos por asignatura |
   | `profesorado_distribucion_porcentual.csv` | Distribución porcentual del profesorado |
   | `profesorado_distribucion_absoluta.csv` | Distribución absoluta del profesorado |
   | `profesorado_indicadores.csv` | Indicadores del profesorado |
   | `notas_documento.csv` | Notas y advertencias metodológicas |

---

## Fase 5: Conversión de CSV a Excel

El último paso del pipeline en Python convierte los CSV en ficheros Excel, uno por grado, con una hoja por cada tipo de datos. Para ejecutarlo:

```bash
python src/csv_to_excel.py
```

Los ficheros resultantes se almacenan en `out/excel/<nombre-del-grado>.xlsx` y constituyen el punto de entrada para Power BI.

---

## Fase 6: Construcción del dashboard en Power BI

1. **Importar los datos.** Abre Power BI Desktop y, en la pestaña *Inicio*, selecciona *Obtener datos* → *Excel*. Selecciona el fichero `out/excel/<nombre-del-grado>.xlsx`, marca todas las hojas en el navegador y haz clic en *Cargar*.

2. **Corregir el orden temporal.** El campo `curso_academico` se almacena como texto (por ejemplo, `"2016-17"`), lo que provoca que Power BI lo ordene alfabéticamente en lugar de cronológicamente. Para corregirlo, crea una columna calculada en la vista *Datos*:
```Año Inicio = VALUE(LEFT([curso_academico], 4))```
A continuación, selecciona la columna `curso_academico`, ve a *Herramientas de columna* y usa *Ordenar por columna* → *Año Inicio*.

3. **Definir las medidas DAX.** En la pestaña *Modelado*, crea las siguientes medidas como base del análisis:
```Presentados =
SUM(resultados_asignaturas[aprobados])
+ SUM(resultados_asignaturas[suspensos])

Tasa Rendimiento =
DIVIDE( SUM(resultados_asignaturas[aprobados]),
SUM(resultados_asignaturas[matriculados])) * 100

Tasa Abandono =
DIVIDE( SUM(resultados_asignaturas[no_presentados]),
SUM(resultados_asignaturas[matriculados])) * 100

Tasa Superacion =
DIVIDE( SUM(resultados_asignaturas[aprobados]),
[Presentados] ) * 100

Asignatura Critica =
IF( [Tasa Rendimiento] < 60 && [Tasa Abandono] > 30,
"Crítica", "Normal" )

Demanda Total = SUM(perfil_ingreso[demanda])
```
4. **Organizar los paneles.** El dashboard se estructura en cuatro paneles principales:
   - **Panel 1 — Acceso, demanda y matrícula inicial:** nota de corte por curso, plazas ofertadas y demandadas, ratio demanda/oferta y matriculados de nuevo ingreso. Se recomienda un gráfico de líneas para la evolución temporal de la nota de corte.
   - **Panel 2 — Perfil del estudiantado y matrícula:** distribución por género, porcentaje de primera opción, tasa de anulaciones, tasa de cobertura, dedicación y procedencia geográfica. Se recomienda el uso de gráficos de dona y barras apiladas.
   - **Panel 3 — Rendimiento académico por asignatura:** tasa de rendimiento, tasa de abandono, tasa de superación y clasificación de asignaturas críticas. Se recomienda una tabla con formato condicional y un diagrama de dispersión abandono frente a rendimiento.
   - **Panel 4 — Profesorado:** distribución por categoría profesional, tasa de doctores, sexenios, quinquenios y tramos DOCENTIA. Se recomienda el uso de gráficos de barras y tarjetas de KPI.

   En todos los paneles se deben añadir segmentadores de datos para los campos `curso_academico`, `campus` (cuando el grado tiene varios) y `tipo` de asignatura.

5. **Extender el dashboard a un segundo grado.** Para incorporar un segundo grado al mismo fichero de Power BI, importa el Excel correspondiente siguiendo el paso anterior, renombra las tablas añadiendo un sufijo identificativo y duplica las páginas del dashboard actualizando las referencias a las nuevas tablas en cada visual.

---

## Estructura de carpetas del proyecto

El repositorio está organizado de forma modular, separando claramente cada fase del pipeline en su propio directorio:
TFM/
+-- src_scraper/         # Modulo de descarga y extraccion de PDFs
|   +-- downloader.py
|   +-- pdf_reader.py
|   +-- pdf_parser.py
|   -- pdf_text-txt.py
|
+-- src_llm/             # Modulo de procesamiento con LLM
|   +-- main.py
|   +-- llm_client.py
|   -- openai_txt_to_excel.py
|
+-- src/                 # Utilidades finales
|   +-- csv_to_excel.py
|   -- script2.py
|
+-- data/
|   +-- raw/pdfs/        # PDFs descargados, por grado
|   -- logs/            # Inventario y registro de errores
|
+-- src_pruebas/txt/     # TXT generados, por grado
+-- out/csv/             # CSV generados por el LLM
+-- out/excel/           # Excel finales para Power BI
+-- .env                 # API Key de OpenAI
-- requirements.txt     # Dependencias del proyecto

Los directorios `src_scraper/`, `src_llm/` y `src/` contienen el código fuente del pipeline y corresponden respectivamente a las fases de descarga, procesamiento con LLM y generación del Excel final. Las carpetas `data/`, `src_pruebas/txt/` y `out/` almacenan los datos intermedios y finales generados durante la ejecución y no se suben al repositorio, tal como indica el `.gitignore`. El fichero `requirements.txt` recoge todas las dependencias necesarias para reproducir el entorno de ejecución.

---

## Solución de problemas frecuentes

- **El script de descarga rechaza la URL del grado.** Verifica que la URL pertenece al dominio `www.urjc.es` y que la página contiene el apartado de Garantía de Calidad. Asegúrate de no incluir una barra `/` al final de la URL.

- **No se encuentran PDFs de resultados en la página del grado.** Accede manualmente a la sección de Garantía de Calidad y comprueba si los documentos están etiquetados con el término *resultado* o *resultados* en el texto del enlace. Si no es así, ajusta el filtro en la función `filter_result_reports_pdf_links` del fichero `downloader.py`.

- **El TXT generado está vacío o tiene muy poco contenido.** El PDF puede estar basado en imágenes escaneadas sin capa de texto. En ese caso, la extracción automática no funcionará y será necesario aplicar OCR manualmente antes de continuar.

- **La API de OpenAI devuelve un error de límite de tokens.** El documento TXT es demasiado largo. Divide el fichero en dos partes y procésalos por separado.

- **En Power BI los cursos académicos no se ordenan cronológicamente.** Sigue el procedimiento del paso 2 de la Fase 6 para crear la columna auxiliar *Año Inicio* y configurar la ordenación por columna.

- **Algunos campos aparecen como `null` en los CSV tras el procesamiento LLM.** El modelo de lenguaje no ha encontrado ese dato en el TXT. Revisa el fichero correspondiente para comprobar si la información está presente y si fue correctamente revisada en la fase manual.
