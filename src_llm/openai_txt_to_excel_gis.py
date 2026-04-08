from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

OUTPUT_DIR = Path("out") / "csv"


def get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("No se ha encontrado OPENAI_API_KEY en el archivo .env")
    return OpenAI(api_key=api_key)


def build_schema() -> dict:
    nullable_string = {"type": ["string", "null"]}
    nullable_number = {"type": ["number", "null"]}
    nullable_integer = {"type": ["integer", "null"]}

    resultado_asignatura = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "asignatura": {"type": "string"},
            "curso": nullable_integer,
            "tipo": nullable_string,
            "matriculados": nullable_integer,
            "matriculados_primera_matricula": nullable_integer,
            "matriculados_segundas_o_posteriores": nullable_integer,
            "rendimiento_previo": nullable_number,
            "superados_previo": nullable_integer,
            "no_superados_previo": nullable_integer,
            "no_presentados": nullable_integer,
            "aprobados": nullable_integer,
            "suspensos": nullable_integer,
            "tasa_rendimiento": nullable_number,
            "tasa_presentacion": nullable_number,
            "tasa_superacion": nullable_number,
            "ss": nullable_number,
            "ap": nullable_number,
            "nt": nullable_number,
            "sb": nullable_number,
        },
        "required": [
            "asignatura",
            "curso",
            "tipo",
            "matriculados",
            "matriculados_primera_matricula",
            "matriculados_segundas_o_posteriores",
            "rendimiento_previo",
            "superados_previo",
            "no_superados_previo",
            "no_presentados",
            "aprobados",
            "suspensos",
            "tasa_rendimiento",
            "tasa_presentacion",
            "tasa_superacion",
            "ss",
            "ap",
            "nt",
            "sb",
        ],
    }

    categoria_porcentaje = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "categoria": {"type": "string"},
            "porcentaje": nullable_number,
        },
        "required": ["categoria", "porcentaje"],
    }

    categoria_cantidad = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "categoria": {"type": "string"},
            "cantidad": nullable_integer,
        },
        "required": ["categoria", "cantidad"],
    }

    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "resumen_documento": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "grado": nullable_string,
                    "campus": nullable_string,
                    "curso_academico": nullable_string,
                    "archivo_origen": {"type": "string"},
                },
                "required": [
                    "grado",
                    "campus",
                    "curso_academico",
                    "archivo_origen",
                ],
            },
            "nota_corte": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "convocatoria": nullable_string,
                    "nota": nullable_number,
                },
                "required": ["convocatoria", "nota"],
            },
            "perfil_ingreso": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "oferta": nullable_integer,
                    "demanda": nullable_integer,
                    "nota_media_acceso": nullable_number,
                    "matriculados_nuevo_ingreso": nullable_integer,
                    "matriculados_via_traslado": nullable_integer,
                    "matriculados_via_traslado_anularon": nullable_integer,
                    "matriculados_primera_opcion": nullable_integer,
                    "matriculados_tiempo_completo": nullable_integer,
                    "matriculados_tiempo_parcial": nullable_integer,
                    "matriculados_sin_anulaciones": nullable_integer,
                    "matriculados_anularon": nullable_integer,
                    "porcentaje_anularon": nullable_number,
                    "matriculados_hombres": nullable_integer,
                    "matriculados_mujeres": nullable_integer,
                    "matriculados_fuera_cam": nullable_integer,
                    "matriculados_extranjeros": nullable_integer,
                    "porcentaje_hombres": nullable_number,
                    "porcentaje_mujeres": nullable_number,
                    "porcentaje_fuera_cam": nullable_number,
                    "porcentaje_extranjeros": nullable_number,
                    "tasa_cobertura_sin_traslados": nullable_number,
                    "tasa_cobertura_global": nullable_number,
                    "porcentaje_primera_opcion": nullable_number,
                },
                "required": [
                    "oferta",
                    "demanda",
                    "nota_media_acceso",
                    "matriculados_nuevo_ingreso",
                    "matriculados_via_traslado",
                    "matriculados_via_traslado_anularon",
                    "matriculados_primera_opcion",
                    "matriculados_tiempo_completo",
                    "matriculados_tiempo_parcial",
                    "matriculados_sin_anulaciones",
                    "matriculados_anularon",
                    "porcentaje_anularon",
                    "matriculados_hombres",
                    "matriculados_mujeres",
                    "matriculados_fuera_cam",
                    "matriculados_extranjeros",
                    "porcentaje_hombres",
                    "porcentaje_mujeres",
                    "porcentaje_fuera_cam",
                    "porcentaje_extranjeros",
                    "tasa_cobertura_sin_traslados",
                    "tasa_cobertura_global",
                    "porcentaje_primera_opcion",
                ],
            },
            "resultados_asignaturas": {
                "type": "array",
                "items": resultado_asignatura,
            },
            "profesorado": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "distribucion_porcentual": {
                        "type": "array",
                        "items": categoria_porcentaje,
                    },
                    "distribucion_absoluta": {
                        "type": "array",
                        "items": categoria_cantidad,
                    },
                    "indicadores": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "porcentaje_doctores": nullable_number,
                            "numero_doctores": nullable_integer,
                            "numero_tiempo_completo": nullable_integer,
                            "numero_tiempo_parcial": nullable_integer,
                            "quinquenios": nullable_integer,
                            "sexenios": nullable_integer,
                            "tramos_docentia": nullable_integer,
                        },
                        "required": [
                            "porcentaje_doctores",
                            "numero_doctores",
                            "numero_tiempo_completo",
                            "numero_tiempo_parcial",
                            "quinquenios",
                            "sexenios",
                            "tramos_docentia",
                        ],
                    },
                },
                "required": [
                    "distribucion_porcentual",
                    "distribucion_absoluta",
                    "indicadores",
                ],
            },
            "notas_documento": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
        "required": [
            "resumen_documento",
            "nota_corte",
            "perfil_ingreso",
            "resultados_asignaturas",
            "profesorado",
            "notas_documento",
        ],
    }


def build_prompt(txt_content: str, filename: str, grade_folder: str) -> str:
    return f"""
Eres un extractor de datos académicos universitarios altamente preciso.

Debes analizar un archivo TXT procedente de informes académicos de la URJC
y devolver EXCLUSIVAMENTE un JSON válido siguiendo exactamente la estructura esperada por el sistema.

Tu prioridad es la exactitud, la consistencia y la limpieza de datos.
No incluyas ningún texto fuera del JSON.

REGLAS GENERALES
1. No inventes datos.
2. Si un valor no aparece claramente, devuelve null.
3. Mantén archivo_origen como "{filename}".
4. El valor de "grado" debe salir del documento si aparece claramente; si no, usa null.
5. Hay un único curso académico por archivo TXT.
6. Conserva la información de todos los bloques relevantes del documento:
   - resumen_documento
   - nota_corte
   - perfil_ingreso
   - resultados_asignaturas
   - profesorado
   - notas_documento

NORMALIZACIÓN GENERAL
7. Corrige errores típicos de extracción:
   - Si encuentras números con espacios intermedios, por ejemplo "6 5", interprétalo como "65".
   - Si encuentras porcentajes con espacios, por ejemplo "75 %", interprétalo como "75%".
   - Si encuentras porcentajes partidos, por ejemplo "36.3 6%", interprétalo como "36.36%".
   - Elimina espacios innecesarios dentro de valores numéricos.
   - Si encuentras "Na", "NaN", "NAN", sustitúyelo por 0.
8. Todos los porcentajes deben devolverse como números sin el símbolo %, por ejemplo 66.67.
9. Los números deben devolverse como números, no como texto.

REGLAS DE EXTRACCIÓN DE TEXTO
10. Reconstruye correctamente nombres partidos en varias líneas o con espacios erróneos.
11. Une palabras separadas artificialmente por el OCR o extracción, por ejemplo:
   - "METODOLO GIA" -> "METODOLOGIA"
   - "PROGRAMA CION" -> "PROGRAMACION"
   - "COMPUTAD ORES" -> "COMPUTADORES"
12. Normaliza mayúsculas/minúsculas sin alterar el significado.
13. No confundas filas de datos con líneas descriptivas del tipo:
   - "MÓSTOLES. Resultados por asignatura..."
   - "MÓSTOLES. Métricas del perfil de ingreso..."
   - "MÓSTOLES. Composición porcentual del profesorado..."
   Estas líneas NO son registros de datos.

REGLAS PARA RESUMEN_DOCUMENTO
14. Extrae:
   - grado
   - campus
   - curso_academico
   - archivo_origen
15. El campus debe extraerse del encabezado del bloque de datos y propagarse a todos los registros contenidos en ese bloque.

REGLAS PARA NOTA_CORTE
16. Extrae la convocatoria tal como aparezca, por ejemplo "JUN.", "Jun." o equivalente.
17. Extrae la nota de corte como número.

REGLAS PARA PERFIL_INGRESO
18. Mapea las métricas del perfil de ingreso a los nombres normalizados del sistema.
19. Si una métrica no existe en ese curso, déjala en null.
20. No crees campos nuevos fuera de la estructura esperada.
21. Normaliza equivalencias como:
   - oferta
   - demanda del plan de estudios
   - nota media de acceso
   - estudiantes de nuevo ingreso
   - vía traslado
   - primera opción
   - tiempo completo
   - tiempo parcial
   - sin anulaciones
   - anularon
   - hombres
   - mujeres
   - fuera de la CAM / fuera de la C.M.
   - extranjeros
   - tasas de cobertura
   - porcentaje primera opción sobre total

REGLAS PARA RESULTADOS_ASIGNATURAS
22. Debe haber una fila por asignatura.
23. El campo "curso" debe ser numérico: 1, 2, 3 o 4 cuando se pueda identificar.
24. Usa el tipo de asignatura normalizado:
   - "TRO.", "TRONCAL", "TRONCALES", "F.B", "F.B.", "F.b." -> "troncal"
   - "OPT.", "OPTATIVA", "OPTATIVAS", "Opt." -> "optativa"
   - "OBL.", "OBLIGATORIA", "OBLIGATORIAS", "Obl." -> "obligatoria"
25. Normaliza encabezados equivalentes:
   - "Nº MAT." y "MATRICULADOS" -> matriculados
   - "1ª MATRÍCULA" -> matriculados_primera_matricula
   - "2ª Y POSTERIORES" -> matriculados_segundas_o_posteriores
   - "APROBADOS" -> aprobados
   - "SUSPENSOS" -> suspensos
26. Si aparece el formato nuevo con columnas "REND.", "SUP.", "NO SUP.", "NO-PRES." además de tasas finales:
   - "REND." -> rendimiento_previo
   - "SUP." -> superados_previo
   - "NO SUP." -> no_superados_previo
   - "NO-PRES." -> no_presentados
   - "RENDIMIENTO" -> tasa_rendimiento
   - "PRESENTACION" -> tasa_presentacion
   - "SUPERACION" -> tasa_superacion
27. Si aparece el formato antiguo:
   - usa aprobados, suspensos y no_presentados
   - deja en null los campos no existentes del formato nuevo
28. En cursos nuevos:
   - rellena matriculados_primera_matricula, matriculados_segundas_o_posteriores, ss, ap, nt, sb cuando existan
29. No mezcles métricas previas con métricas finales.
30. Si aparece algún dato explícito de "nota" asociado a una asignatura, guárdalo en "nota" o "nota_media" según corresponda.
31. Si no aparece claramente, deja "nota" y "nota_media" en null.
32. Minimiza nulls, pero no inventes datos.

REGLAS PARA PROFESORADO
33. Extrae tres partes:
   - distribucion_porcentual
   - distribucion_absoluta
   - indicadores
34. En distribucion_porcentual:
   - una fila por categoría con nombre normalizado y porcentaje
35. En distribucion_absoluta:
   - una fila por categoría con nombre normalizado y cantidad
36. Excluye la fila "TOTAL" o "Total" de las listas de distribución.
37. En indicadores normaliza:
   - "% DOCTORES" o "% Doctores" -> porcentaje_doctores
   - "Nº DOCTORES" o "Nº doctores" -> numero_doctores
   - "Nº TIEMPO COMPLETO" -> numero_tiempo_completo
   - "Nº TIEMPO PARCIAL" -> numero_tiempo_parcial
   - "QUINQUENIOS" -> quinquenios
   - "SEXENIOS" -> sexenios
   - "TRAMOS DOCENTIA" -> tramos_docentia
38. Si la tabla de indicadores aparece partida en dos bloques, combínalos en un único objeto.

REGLAS PARA CATEGORÍAS DE PROFESORADO
39. Normaliza variaciones de escritura manteniendo una única forma coherente, por ejemplo:
   - "Catedrático/a de Universidad", "Catedrático /a de universidad"
   - "Profesor/a Contratado/a Doctor/a", "Profesor Contratado Doctor"
   - "Profesor/a Asociado/a", "Profesor Asociado"
   - "Titular de Universidad"
   - "Titular Escuela Universitaria"
   - "Investigador"

REGLAS PARA NOTAS_DOCUMENTO
40. Incluye en "notas_documento" cualquier nota textual relevante del documento que no pertenezca a una tabla, por ejemplo advertencias metodológicas o aclaraciones sobre interpretación de porcentajes o calificaciones.
41. No incluyas títulos de secciones ni líneas decorativas.

VALIDACIÓN FINAL
42. Devuelve solo JSON válido.
43. No añadas comentarios.
44. No añadas markdown.
45. No omitas bloques aunque estén vacíos.
46. Si un bloque no tiene contenido, devuélvelo vacío o con null según corresponda.
47. No incluyas columnas de nota media y nota

REGLAS CRÍTICAS PARA CAMPUS

48. El documento puede contener bloques independientes identificados por los encabezados:
   - MADRID
   - MÓSTOLES
   - SEMIPRESENCIAL

49. Debes interpretar esos encabezados como el valor del campo "campus".

50. Normaliza el campo "campus" con estos únicos valores:
   - "madrid"
   - "mostoles"
   - "semipresencial"

51. El campo "campus" es OBLIGATORIO en todos los registros de:
   - resumen_documento
   - nota_corte
   - perfil_ingreso
   - resultados_asignaturas
   - profesorado

52. Ningún registro puede devolverse con "campus": null si pertenece a un bloque bajo un encabezado de campus identificable.

53. Cuando aparezca un encabezado de campus, debes actualizar el contexto actual de campus y mantenerlo para todas las filas siguientes hasta que aparezca otro encabezado de campus.

54. Todas las filas extraídas dentro de un bloque deben heredar explícitamente ese valor de "campus", aunque el nombre del campus no se repita en cada línea de la tabla.

55. No dejes el campus vacío por el hecho de que la fila individual no lo mencione: debes propagar el campus del bloque activo.

56. Si una tabla aparece debajo de un encabezado "MADRID", todas sus filas deben llevar "campus": "madrid".
57. Si una tabla aparece debajo de un encabezado "MÓSTOLES", todas sus filas deben llevar "campus": "mostoles".
58. Si una tabla aparece debajo de un encabezado "SEMIPRESENCIAL", todas sus filas deben llevar "campus": "semipresencial".

59. Antes de generar el JSON final, verifica que cada elemento de:
   - nota_corte
   - perfil_ingreso
   - resultados_asignaturas
   - profesorado.distribucion_porcentual
   - profesorado.distribucion_absoluta
tenga el campo "campus" correctamente rellenado cuando el bloque de origen sea identificable.

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


def write_csv(df: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")


def process_root_directory(root_dir: Path) -> Path:
    if not root_dir.exists():
        raise FileNotFoundError(f"No existe la carpeta raíz: {root_dir}")

    if not root_dir.is_dir():
        raise ValueError(f"La ruta no es un directorio: {root_dir}")

    grade_dirs = list_grade_directories(root_dir)
    if not grade_dirs:
        raise FileNotFoundError(f"No se han encontrado subcarpetas de grados en: {root_dir}")

    print(f"[INFO] Se han encontrado {len(grade_dirs)} carpetas de grados")

    for grade_dir in grade_dirs:
        grade_folder = grade_dir.name
        txt_files = list_txt_files(grade_dir)

        if not txt_files:
            print(f"[WARN] La carpeta {grade_folder} no contiene TXT")
            continue

        print(f"\n[INFO] Procesando grado: {grade_folder} ({len(txt_files)} TXT)")

        origen_rows: list[dict] = []
        resumen_rows: list[dict] = []
        nota_corte_rows: list[dict] = []
        perfil_ingreso_rows: list[dict] = []
        resultados_rows: list[dict] = []
        profesorado_pct_rows: list[dict] = []
        profesorado_abs_rows: list[dict] = []
        profesorado_indicadores_rows: list[dict] = []
        notas_documento_rows: list[dict] = []

        for txt_file in txt_files:
            print(f"  -> {txt_file.name}")
            data = call_openai_for_txt(txt_file, grade_folder)

            resumen = data.get("resumen_documento", {}) or {}
            base_info = {
                "curso_academico": resumen.get("curso_academico"),
                "grado": resumen.get("grado"),
                "campus": resumen.get("campus"),
            }

            origen_rows.append({
                "grado_carpeta": grade_folder,
                "archivo_origen": resumen.get("archivo_origen"),
                "curso_academico": resumen.get("curso_academico"),
                "grado": resumen.get("grado"),
                "campus": resumen.get("campus"),
            })

            resumen_rows.append({
                **base_info,
            })

            nota_corte = data.get("nota_corte", {}) or {}
            nota_corte_rows.append({
                **base_info,
                "convocatoria": nota_corte.get("convocatoria"),
                "nota": nota_corte.get("nota"),
            })

            perfil_ingreso = data.get("perfil_ingreso", {}) or {}
            perfil_ingreso_rows.append({
                **base_info,
                **perfil_ingreso,
            })

            resultados = data.get("resultados_asignaturas", []) or []
            for row in resultados:
                resultados_rows.append({
                    **base_info,
                    **row,
                })

            profesorado = data.get("profesorado", {}) or {}

            distribucion_porcentual = profesorado.get("distribucion_porcentual", []) or []
            for row in distribucion_porcentual:
                profesorado_pct_rows.append({
                    **base_info,
                    **row,
                })

            distribucion_absoluta = profesorado.get("distribucion_absoluta", []) or []
            for row in distribucion_absoluta:
                profesorado_abs_rows.append({
                    **base_info,
                    **row,
                })

            indicadores = profesorado.get("indicadores", {}) or {}
            profesorado_indicadores_rows.append({
                **base_info,
                **indicadores,
            })

            notas_documento = data.get("notas_documento", []) or []
            for nota in notas_documento:
                notas_documento_rows.append({
                    **base_info,
                    "nota_documento": nota,
                })

            print(
                f"     [OK] origen=1, "
                f"resumen=1, "
                f"nota_corte=1, "
                f"perfil_ingreso=1, "
                f"resultados={len(resultados)}, "
                f"prof_pct={len(distribucion_porcentual)}, "
                f"prof_abs={len(distribucion_absoluta)}, "
                f"notas={len(notas_documento)}"
            )

        grade_output_dir = OUTPUT_DIR / grade_folder

        origen_columns = [
            "grado_carpeta",
            "archivo_origen",
            "curso_academico",
            "grado",
            "campus",
        ]

        resumen_columns = [
            "curso_academico",
            "grado",
            "campus",
        ]

        nota_corte_columns = [
            "curso_academico",
            "grado",
            "campus",
            "convocatoria",
            "nota",
        ]

        perfil_ingreso_columns = [
            "curso_academico",
            "grado",
            "campus",
            "oferta",
            "demanda",
            "nota_media_acceso",
            "matriculados_nuevo_ingreso",
            "matriculados_via_traslado",
            "matriculados_via_traslado_anularon",
            "matriculados_primera_opcion",
            "matriculados_tiempo_completo",
            "matriculados_tiempo_parcial",
            "matriculados_sin_anulaciones",
            "matriculados_anularon",
            "porcentaje_anularon",
            "matriculados_hombres",
            "matriculados_mujeres",
            "matriculados_fuera_cam",
            "matriculados_extranjeros",
            "porcentaje_hombres",
            "porcentaje_mujeres",
            "porcentaje_fuera_cam",
            "porcentaje_extranjeros",
            "tasa_cobertura_sin_traslados",
            "tasa_cobertura_global",
            "porcentaje_primera_opcion",
        ]

        resultados_columns = [
            "curso_academico",
            "grado",
            "campus",
            "curso",
            "asignatura",
            "tipo",
            "matriculados",
            "matriculados_primera_matricula",
            "matriculados_segundas_o_posteriores",
            "rendimiento_previo",
            "superados_previo",
            "no_superados_previo",
            "no_presentados",
            "aprobados",
            "suspensos",
            "tasa_rendimiento",
            "tasa_presentacion",
            "tasa_superacion",
            "ss",
            "ap",
            "nt",
            "sb",
            "nota_media",
            "nota",
        ]

        profesorado_pct_columns = [
            "curso_academico",
            "grado",
            "campus",
            "categoria",
            "porcentaje",
        ]

        profesorado_abs_columns = [
            "curso_academico",
            "grado",
            "campus",
            "categoria",
            "cantidad",
        ]

        profesorado_indicadores_columns = [
            "curso_academico",
            "grado",
            "campus",
            "porcentaje_doctores",
            "numero_doctores",
            "numero_tiempo_completo",
            "numero_tiempo_parcial",
            "quinquenios",
            "sexenios",
            "tramos_docentia",
        ]

        notas_documento_columns = [
            "curso_academico",
            "grado",
            "campus",
            "nota_documento",
        ]

        df_origen = ensure_dataframe(origen_columns, origen_rows)
        df_resumen = ensure_dataframe(resumen_columns, resumen_rows)
        df_nota_corte = ensure_dataframe(nota_corte_columns, nota_corte_rows)
        df_perfil_ingreso = ensure_dataframe(perfil_ingreso_columns, perfil_ingreso_rows)
        df_resultados = ensure_dataframe(resultados_columns, resultados_rows)
        df_prof_pct = ensure_dataframe(profesorado_pct_columns, profesorado_pct_rows)
        df_prof_abs = ensure_dataframe(profesorado_abs_columns, profesorado_abs_rows)
        df_prof_ind = ensure_dataframe(profesorado_indicadores_columns, profesorado_indicadores_rows)
        df_notas = ensure_dataframe(notas_documento_columns, notas_documento_rows)

        write_csv(df_origen, grade_output_dir / "origen_datos.csv")
        write_csv(df_resumen, grade_output_dir / "resumen_documento.csv")
        write_csv(df_nota_corte, grade_output_dir / "nota_corte.csv")
        write_csv(df_perfil_ingreso, grade_output_dir / "perfil_ingreso.csv")
        write_csv(df_resultados, grade_output_dir / "resultados_asignaturas.csv")
        write_csv(df_prof_pct, grade_output_dir / "profesorado_distribucion_porcentual.csv")
        write_csv(df_prof_abs, grade_output_dir / "profesorado_distribucion_absoluta.csv")
        write_csv(df_prof_ind, grade_output_dir / "profesorado_indicadores.csv")
        write_csv(df_notas, grade_output_dir / "notas_documento.csv")

        print(f"[OK] CSV generados en: {grade_output_dir}")

    return OUTPUT_DIR