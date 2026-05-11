"""
IngestService — SmartSupply
Recibe archivos de cualquier formato (imagen, Excel, PDF) y usa Claude
para extraer, interpretar y normalizar los datos de ventas al schema
de sales_history.
"""

import base64
import json
import os
from datetime import date
from pathlib import Path

import anthropic
import pandas as pd
from dotenv import load_dotenv

from app.models.schemas import IngestPreview, IngestRecord

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


class IngestService:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    def preview_from_image(self, image_bytes: bytes, media_type: str) -> IngestPreview:
        """Extrae datos de ventas desde una imagen (foto de cuaderno, captura, etc.)."""
        image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

        message = self.client.messages.create(
            model="claude-opus-4-7",
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
        """
        Para Excel/CSV: primero intenta parsear con pandas.
        Si las columnas son claras, mapea directamente.
        Si son ambiguas, manda una muestra a Claude para que interprete.
        """
        try:
            if filename.endswith(".csv"):
                df = pd.read_csv(pd.io.common.BytesIO(file_bytes))
            else:
                df = pd.read_excel(pd.io.common.BytesIO(file_bytes))
        except Exception as e:
            return IngestPreview(
                store_name="Desconocido",
                records_found=0,
                date_range_start=None,
                date_range_end=None,
                families_detected=[],
                records=[],
                warnings=[f"No se pudo leer el archivo: {str(e)}"],
            )

        direct = self._try_direct_mapping(df)
        if direct:
            return direct

        # Columnas ambiguas — mandar muestra a Claude como texto
        sample_text = df.head(20).to_string()
        message = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": f"Aqui tienes una muestra de un archivo Excel de ventas:\n\n{sample_text}\n\n{EXTRACTION_PROMPT}",
                }
            ],
        )
        return self._parse_claude_response(message.content[0].text)

    def preview_from_pdf(self, file_bytes: bytes) -> IngestPreview:
        """Extrae datos desde un PDF usando Claude con soporte de documentos."""
        pdf_b64 = base64.standard_b64encode(file_bytes).decode("utf-8")

        message = self.client.messages.create(
            model="claude-opus-4-7",
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
        """
        Intenta mapear columnas del Excel directamente si los nombres son reconocibles.
        Devuelve None si no puede mapear con certeza.
        """
        col_lower = {c.lower().strip(): c for c in df.columns}

        date_col = next((col_lower[k] for k in col_lower if k in ("date", "fecha", "dia", "day")), None)
        family_col = next((col_lower[k] for k in col_lower if k in ("family", "familia", "producto", "product", "categoria", "category", "item")), None)
        sales_col = next((col_lower[k] for k in col_lower if k in ("sales", "ventas", "cantidad", "quantity", "monto", "amount", "total")), None)
        promo_col = next((col_lower[k] for k in col_lower if k in ("onpromotion", "promocion", "promo", "oferta")), None)

        if not (date_col and family_col and sales_col):
            return None

        records = []
        warnings = []
        for _, row in df.iterrows():
            try:
                records.append(IngestRecord(
                    date=pd.to_datetime(row[date_col]).date(),
                    family=str(row[family_col]).upper().strip(),
                    sales=float(row[sales_col]),
                    onpromotion=int(row[promo_col]) if promo_col and pd.notna(row[promo_col]) else 0,
                ))
            except Exception:
                warnings.append(f"Fila ignorada por datos invalidos: {row.to_dict()}")

        return self._build_preview("Desconocido", records, warnings)

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

    def _build_preview(self, store_name: str, records: list[IngestRecord], warnings: list[str]) -> IngestPreview:
        dates = [r.date for r in records]
        return IngestPreview(
            store_name=store_name,
            records_found=len(records),
            date_range_start=min(dates) if dates else None,
            date_range_end=max(dates) if dates else None,
            families_detected=sorted(set(r.family for r in records)),
            records=records,
            warnings=warnings,
        )
