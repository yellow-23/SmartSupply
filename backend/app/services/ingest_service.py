"""
IngestService — SmartSupply
Recibe archivos de cualquier formato (imagen, Excel, PDF) y usa Claude
para extraer, interpretar y normalizar los datos de ventas al schema
de sales_history.
"""

import base64
import json
import os
import warnings
from datetime import date, datetime
from pathlib import Path

import anthropic
import pandas as pd
from dotenv import load_dotenv

from app.models.schemas import IngestPreview, IngestRecord
from app.services.ingest_validator import validate_ingest_records

load_dotenv(Path(__file__).parents[3] / "backend" / ".env")

SUPPORTED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
SUPPORTED_EXCEL_TYPES = {
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "text/csv",
}

EXTRACTION_PROMPT = """Eres un asistente de datos para una plataforma de inventario de distribuidoras chilenas.

Se te entrega un documento (imagen de cuaderno, Excel exportado o PDF) con registros de ventas de una tienda.

Tu tarea:
1. Identificar las columnas que corresponden a: fecha, producto/categoria, cantidad vendida, y si hubo promocion.
2. Extraer TODOS los registros de ventas que puedas encontrar.
3. Normalizar las fechas al formato YYYY-MM-DD.
4. Normalizar los nombres de producto/categoria a texto limpio en mayusculas (ej: "LACTEOS", "BEBIDAS", "ABARROTES").
5. Si la cantidad es en pesos, unidades u otro, intentar interpretarla como numero decimal de ventas.

Responde UNICAMENTE con un JSON valido con esta estructura exacta:
{
  "store_name": "nombre de la tienda si aparece, si no 'Tienda sin nombre'",
  "records": [
    {
      "date": "YYYY-MM-DD",
      "family": "NOMBRE_CATEGORIA",
      "sales": 123.45,
      "onpromotion": 0
    }
  ],
  "warnings": ["lista de advertencias si hay datos ambiguos o ilegibles"]
}

Si no puedes extraer ningun registro valido, devuelve records como lista vacia y explica en warnings.
No incluyas texto fuera del JSON."""

COLUMN_MAPPING_PROMPT = """Eres un experto en análisis de archivos de ventas para distribuidoras.

Se te entrega una muestra de un archivo tabular (Excel o CSV) leída SIN encabezado forzado — las primeras filas pueden ser títulos, metadatos, filas en blanco o sub-encabezados antes de los datos reales.

Tu tarea es detectar la estructura y devolver ÚNICAMENTE un JSON válido con esta forma:
{
  "header_row": 2,
  "date_col": "Fecha",
  "family_col": "Familia",
  "sales_col": "Monto Neto ($)",
  "promo_col": "Con Oferta",
  "store_name": "Distribuidora XYZ - Sucursal Norte",
  "number_format": "european",
  "warnings": []
}

Definiciones de cada campo:
- header_row: índice 0-based de la fila que contiene los NOMBRES de las columnas (no datos). Si los datos empiezan en la fila 0 sin encabezado, devuelve -1.
- date_col: nombre EXACTO (mismo case y caracteres) de la columna de fecha.
- family_col: nombre EXACTO de la columna de producto, familia, categoría, SKU, ítem o descripción.
- sales_col: nombre EXACTO de la columna de ventas, monto, cantidad, unidades o ingresos. Si hay varias opciones elige la más representativa (preferir monto total sobre unidades).
- promo_col: nombre EXACTO de la columna de promoción/oferta, o null si no existe.
- store_name: nombre de tienda o distribuidora si aparece en los metadatos. Si no, "Tienda sin nombre".
- number_format: "european" si usa punto como separador de miles y coma como decimal (ej: 1.234,56), "american" si es al revés (ej: 1,234.56), "plain" si no hay separadores de miles.
- warnings: lista de advertencias sobre datos ambiguos, columnas con doble significado, etc.

Reglas importantes:
- Los nombres de columna en date_col/family_col/sales_col/promo_col deben ser EXACTAMENTE como aparecen en la fila header_row, sin modificar.
- Si hay filas de totales, subtotales o resumen al final, anótalas en warnings.
- No incluyas texto fuera del JSON."""


class IngestService:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        self._last_mapping_error: str | None = None

    def preview_from_image(self, image_bytes: bytes, media_type: str) -> IngestPreview:
        """Extrae datos de ventas desde una imagen (foto de cuaderno, captura, etc.)."""
        image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

        message = self.client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_b64,
                            },
                        },
                        {"type": "text", "text": EXTRACTION_PROMPT},
                    ],
                }
            ],
        )

        return self._parse_claude_response(message.content[0].text)

    def preview_from_excel(self, file_bytes: bytes, filename: str) -> IngestPreview:
        is_csv = filename.lower().endswith(".csv")

        # Step 1: pick best sheet and read raw (no header assumption)
        df_raw, sheet_name = self._read_best_sheet(file_bytes, filename, is_csv)
        if df_raw is None:
            return IngestPreview(
                store_name="Desconocido", records_found=0,
                date_range_start=None, date_range_end=None,
                families_detected=[], records=[],
                warnings=["No se pudo leer el archivo."],
            )

        # Step 2: fast path — if columns are already clean, skip Claude
        try:
            df_direct = (
                pd.read_csv(pd.io.common.BytesIO(file_bytes))
                if is_csv
                else pd.read_excel(pd.io.common.BytesIO(file_bytes), sheet_name=sheet_name)
            )
            direct = self._try_direct_mapping(df_direct)
            if direct:
                return direct
        except Exception:
            pass

        # Step 3: Claude analyzes raw rows to detect structure
        self._last_mapping_error = None
        mapping = self._get_column_mapping(df_raw)
        if mapping is None:
            friendly = self._last_mapping_error or (
                "No se pudo procesar el archivo. Verifica que tenga columnas "
                "claras de fecha, producto y ventas, e intentalo de nuevo."
            )
            return IngestPreview(
                store_name="Desconocido", records_found=0,
                date_range_start=None, date_range_end=None,
                families_detected=[], records=[],
                warnings=[friendly],
            )

        date_col = mapping.get("date_col")
        family_col = mapping.get("family_col")
        sales_col = mapping.get("sales_col")
        promo_col = mapping.get("promo_col")
        store_name = mapping.get("store_name", "Tienda sin nombre")
        number_format = mapping.get("number_format", "plain")
        header_row = int(mapping.get("header_row", 0))
        warnings = list(mapping.get("warnings", []))

        if not (date_col and family_col and sales_col):
            return IngestPreview(
                store_name="Desconocido", records_found=0,
                date_range_start=None, date_range_end=None,
                families_detected=[], records=[],
                warnings=["No se encontraron columnas de fecha, familia o ventas en el archivo."],
            )

        # Step 4: re-read with correct header row — dtype=str to avoid pandas mangling values
        try:
            skiprows = list(range(header_row)) if header_row > 0 else None
            if is_csv:
                df = pd.read_csv(
                    pd.io.common.BytesIO(file_bytes),
                    header=0, skiprows=skiprows, dtype=str,
                )
            else:
                df = pd.read_excel(
                    pd.io.common.BytesIO(file_bytes),
                    sheet_name=sheet_name,
                    header=header_row, dtype=str,
                )
        except Exception as e:
            return IngestPreview(
                store_name="Desconocido", records_found=0,
                date_range_start=None, date_range_end=None,
                families_detected=[], records=[],
                warnings=[f"Error al releer el archivo con el header detectado: {e}"],
            )

        # Step 5: iterate all rows with robust parsing
        records = []
        for _, row in df.iterrows():
            try:
                date_val = self._parse_date(row.get(date_col))
                if date_val is None:
                    continue
                family_val = str(row.get(family_col, "")).upper().strip()
                if not family_val or family_val in ("NAN", "NONE", ""):
                    continue
                sales_val = self._parse_number(row.get(sales_col), number_format)
                if sales_val is None:
                    continue
                promo_val = self._parse_promo(row.get(promo_col) if promo_col else None)
                records.append(IngestRecord(
                    date=date_val,
                    family=family_val,
                    sales=sales_val,
                    onpromotion=promo_val,
                ))
            except Exception:
                pass

        return self._build_preview(store_name, records, warnings)

    def _read_best_sheet(self, file_bytes: bytes, filename: str, is_csv: bool):
        """Returns (df_raw_no_header, sheet_name). Picks the sheet with the most data rows."""
        try:
            if is_csv:
                df = pd.read_csv(pd.io.common.BytesIO(file_bytes), header=None, dtype=str)
                return df, None
            xl = pd.ExcelFile(pd.io.common.BytesIO(file_bytes))
            best_sheet, best_count = xl.sheet_names[0], 0
            for name in xl.sheet_names:
                try:
                    tmp = xl.parse(name, header=None, dtype=str)
                    # count non-empty cells to find most data-rich sheet
                    count = tmp.notna().sum().sum()
                    if count > best_count:
                        best_count = count
                        best_sheet = name
                except Exception:
                    pass
            df = xl.parse(best_sheet, header=None, dtype=str)
            return df, best_sheet
        except Exception:
            return None, None

    def _get_column_mapping(self, df_raw: pd.DataFrame) -> dict | None:
        """
        Pide a Claude que detecte la estructura del archivo. Intenta Sonnet
        primero (mas preciso) y cae a Haiku si Sonnet esta sobrecargado.
        """
        sample_text = df_raw.head(30).to_string()
        content = f"Muestra del archivo (sin header forzado):\n\n{sample_text}\n\n{COLUMN_MAPPING_PROMPT}"

        for model_name in ("claude-sonnet-4-6", "claude-haiku-4-5-20251001"):
            try:
                message = self.client.messages.create(
                    model=model_name,
                    max_tokens=1500,
                    messages=[{"role": "user", "content": content}],
                )
                text = message.content[0].text
                if "```" in text:
                    text = text.split("```")[1]
                    if text.startswith("json"):
                        text = text[4:]
                return json.loads(text.strip())
            except anthropic.InternalServerError as e:
                # Sonnet sobrecargado → log y prueba Haiku
                print(f"[ingest_service] {model_name} no disponible ({e.status_code}), probando fallback...")
                continue
            except Exception as e:
                import traceback
                print(f"[ingest_service] _get_column_mapping FAILED ({model_name}): {type(e).__name__}: {e}")
                traceback.print_exc()
                continue

        # Mensaje friendly para el usuario (sin detalles tecnicos)
        self._last_mapping_error = (
            "Servicio de IA temporalmente saturado. Intentalo en unos segundos."
        )
        return None

    def _parse_number(self, val, number_format: str) -> float | None:
        """Parses a numeric value in european, american, or plain format."""
        if val is None:
            return None
        if isinstance(val, (int, float)):
            return float(val) if not pd.isna(val) else None
        s = str(val).strip()
        # strip currency symbols and whitespace
        for ch in ("$", "CLP", "USD", "€", "\xa0", " "):
            s = s.replace(ch, "")
        s = s.strip()
        if not s or s.lower() in ("nan", "none", "-", "—"):
            return None
        try:
            if number_format == "european":
                # 1.234,56 -> 1234.56
                s = s.replace(".", "").replace(",", ".")
            elif number_format == "american":
                # 1,234.56 -> 1234.56
                s = s.replace(",", "")
            else:
                # plain or unknown: try as-is, then try both
                pass
            return float(s)
        except ValueError:
            pass
        # fallback: try stripping all separators
        try:
            return float(s.replace(",", "").replace(".", ""))
        except ValueError:
            return None

    def _parse_date(self, val) -> date | None:
        """Parses a date value tolerantly. Asume convencion chilena (dd/mm/yyyy)."""
        if val is None:
            return None
        if isinstance(val, datetime):
            return val.date()
        if isinstance(val, date):
            return val
        # Silenciamos warnings de pandas: intentamos varios formatos a proposito.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            # 1. ISO y dd/mm/yyyy (CL/EU). dayfirst=True parsea YYYY-MM-DD correctamente.
            result = pd.to_datetime(val, dayfirst=True, errors="coerce")
            # 2. Fallback US (mm/dd/yyyy) si dayfirst=True fallo (ej: dia=21 invalido).
            if pd.isna(result):
                result = pd.to_datetime(val, dayfirst=False, errors="coerce")
        return result.date() if not pd.isna(result) else None

    def _parse_promo(self, val) -> int:
        """Returns 1 if the value indicates a promotion, 0 otherwise."""
        if val is None:
            return 0
        s = str(val).strip().upper()
        return 0 if s in ("", "0", "NO", "N", "FALSE", "NAN", "NONE", "—", "-") else 1

    def preview_from_pdf(self, file_bytes: bytes) -> IngestPreview:
        """Extrae datos desde un PDF usando Claude con soporte de documentos."""
        pdf_b64 = base64.standard_b64encode(file_bytes).decode("utf-8")

        message = self.client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "document",
                            "source": {
                                "type": "base64",
                                "media_type": "application/pdf",
                                "data": pdf_b64,
                            },
                        },
                        {"type": "text", "text": EXTRACTION_PROMPT},
                    ],
                }
            ],
        )
        return self._parse_claude_response(message.content[0].text)

    def _try_direct_mapping(self, df: pd.DataFrame) -> IngestPreview | None:
        """Fast path: maps columns directly if names are unambiguous. Returns None otherwise."""
        col_lower = {c.lower().strip(): c for c in df.columns}

        date_col = next((col_lower[k] for k in col_lower if k in ("date", "fecha", "dia", "day")), None)
        family_col = next((col_lower[k] for k in col_lower if k in ("family", "familia", "producto", "product", "categoria", "category", "item")), None)
        sales_col = next((col_lower[k] for k in col_lower if k in ("sales", "ventas", "cantidad", "quantity", "monto", "amount", "total")), None)
        promo_col = next((col_lower[k] for k in col_lower if k in ("onpromotion", "promocion", "promo", "oferta")), None)

        if not (date_col and family_col and sales_col):
            return None

        records = []
        for _, row in df.iterrows():
            try:
                date_val = self._parse_date(row[date_col])
                if date_val is None:
                    continue
                family_val = str(row[family_col]).upper().strip()
                if not family_val or family_val in ("NAN", "NONE", ""):
                    continue
                sales_val = self._parse_number(row[sales_col], "plain")
                if sales_val is None:
                    continue
                records.append(IngestRecord(
                    date=date_val,
                    family=family_val,
                    sales=sales_val,
                    onpromotion=self._parse_promo(row.get(promo_col) if promo_col else None),
                ))
            except Exception:
                pass

        if not records:
            return None
        return self._build_preview("Tienda sin nombre", records, [])

    def _parse_claude_response(self, text: str) -> IngestPreview:
        """Parsea el JSON que devuelve Claude y construye el IngestPreview."""
        try:
            # Claude a veces envuelve el JSON en ```json ... ```
            if "```" in text:
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]

            data = json.loads(text.strip())
            records = [
                IngestRecord(
                    date=r["date"],
                    family=str(r["family"]).upper().strip(),
                    sales=float(r["sales"]),
                    onpromotion=int(r.get("onpromotion", 0)),
                )
                for r in data.get("records", [])
            ]
            return self._build_preview(
                store_name=data.get("store_name", "Tienda sin nombre"),
                records=records,
                warnings=data.get("warnings", []),
            )
        except Exception as e:
            return IngestPreview(
                store_name="Desconocido",
                records_found=0,
                date_range_start=None,
                date_range_end=None,
                families_detected=[],
                records=[],
                warnings=[f"Error al interpretar respuesta de Claude: {str(e)}", text[:500]],
            )

    def chat(self, messages: list, preview_summary: str, business_name: str = "") -> str:
        """Stocky responde preguntas sobre los datos extraídos en el preview."""
        negocio = f"Estás asistiendo a **{business_name}**." if business_name else ""
        system = f"""Eres Stocky, asistente de ingesta de SmartSupply — plataforma de forecasting e inventario para distribuidoras chilenas.
{negocio}

DATOS EXTRAÍDOS DEL ARCHIVO (ya los tienes, no los pidas):
{preview_summary}

PERSONALIDAD:
- Presentas los datos directamente, sin pedir que el usuario te explique qué subió.
- Eres breve y concreto. Máximo 3 oraciones por respuesta, salvo que el usuario pida más detalle.
- Hablas en español natural, sin frases de relleno ni saludos.
- Cuando hay advertencias, las explicas en términos simples de negocio.
- Haces UNA sola pregunta a la vez si necesitas aclarar algo.
- No usas listas con guiones ni asteriscos para negritas. Escribes en prosa simple.
- Si todo parece correcto, lo dices claramente y preguntas si el usuario quiere agregar contexto adicional (nombre de tienda, período, notas) antes de confirmar la carga.

PRIMERA RESPUESTA: resume en 1-2 frases lo que encontraste y pregunta si quieren agregar contexto o confirmar directo.

AUTO-CONFIRMAR: Cuando el usuario indique que quiere proceder (ejemplos: "carga nomas", "confirma", "dale", "listo", "sí carga", "cárgalo", "no hay más", "todo bien"), termina tu respuesta con la etiqueta exacta [CONFIRMAR] en una línea separada al final. No la uses si el usuario solo está respondiendo preguntas o dando contexto."""

        response = self.client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            system=system,
            messages=[{"role": m.role, "content": m.content} for m in messages],
        )
        raw = response.content[0].text
        trigger = "[CONFIRMAR]" in raw
        reply = raw.replace("[CONFIRMAR]", "").strip()
        return reply, trigger

    def _build_preview(self, store_name: str, records: list[IngestRecord], warnings: list[str]) -> IngestPreview:
        dates = [r.date for r in records]
        quality_issues = validate_ingest_records(records)
        sales_unit_detected = (
            "CLP" if any(i.code == "LIKELY_CURRENCY" for i in quality_issues) else "units"
        )
        return IngestPreview(
            store_name=store_name,
            records_found=len(records),
            date_range_start=min(dates) if dates else None,
            date_range_end=max(dates) if dates else None,
            families_detected=sorted(set(r.family for r in records)),
            records=records,
            warnings=warnings,
            quality_issues=quality_issues,
            sales_unit_detected=sales_unit_detected,
        )
