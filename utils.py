"""
utils.py
--------
Funciones auxiliares:
  - Guardar y cargar configuraciones en JSON.
  - Exportar resultados a Excel (en memoria, para Streamlit).
"""

import json
import io
from pathlib import Path

import pandas as pd


# ─── Guardar / cargar configuración ──────────────────────────────────────────

def guardar_config(config: dict, ruta: str) -> None:
    """
    Guarda la configuración en un archivo JSON.

    Parámetros
    ----------
    config : Diccionario con los datos de la hipoteca y los productos.
    ruta   : Ruta al archivo de destino.
    """
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def cargar_config(ruta: str) -> dict:
    """
    Carga una configuración desde un archivo JSON.

    Parámetros
    ----------
    ruta : Ruta al archivo JSON.

    Retorna
    -------
    Diccionario con la configuración.

    Lanza
    -----
    FileNotFoundError si el archivo no existe.
    ValueError si el JSON no es válido.
    """
    path = Path(ruta)
    if not path.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {ruta}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def config_desde_bytes(data: bytes) -> dict:
    """
    Parsea una configuración desde bytes (útil con st.file_uploader).

    Parámetros
    ----------
    data : Contenido del archivo en bytes.

    Retorna
    -------
    Diccionario con la configuración.
    """
    return json.loads(data.decode("utf-8"))


# ─── Exportar a Excel ─────────────────────────────────────────────────────────

def exportar_excel(df: pd.DataFrame, nombre_hoja: str = "Comparativa hipotecas") -> bytes:
    """
    Serializa un DataFrame a bytes de Excel (.xlsx) para su descarga en Streamlit.

    Parámetros
    ----------
    df          : DataFrame con los resultados a exportar.
    nombre_hoja : Nombre de la hoja de Excel.

    Retorna
    -------
    Bytes del archivo Excel.
    """
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=nombre_hoja)

        # Ajustar ancho de columnas automáticamente
        worksheet = writer.sheets[nombre_hoja]
        for col_idx, col in enumerate(df.columns, start=1):
            max_len = max(
                len(str(col)),
                df[col].astype(str).map(len).max() if len(df) > 0 else 0,
            )
            # openpyxl usa letras de columna
            col_letter = worksheet.cell(row=1, column=col_idx).column_letter
            worksheet.column_dimensions[col_letter].width = min(max_len + 4, 50)

    return buffer.getvalue()


# ─── Configuración por defecto ────────────────────────────────────────────────

PRODUCTOS_DEFAULT = [
    {"nombre": "Nómina",  "bonificacion": 0.40, "coste_banco": 0.0,  "coste_externo": 0.0,  "obligatorio": True},
    {"nombre": "Hogar",   "bonificacion": 0.10, "coste_banco": 13.0, "coste_externo": 10.0, "obligatorio": True},
    {"nombre": "Vida",    "bonificacion": 0.40, "coste_banco": 21.0, "coste_externo": 15.0, "obligatorio": False},
    {"nombre": "Pagos",   "bonificacion": 0.10, "coste_banco": 28.0, "coste_externo": 0.0,  "obligatorio": False},
]

CONFIG_DEFAULT = {
    "capital": 200_000.0,
    "anios": 30,
    "tipo_base": 3.5,
    "productos": PRODUCTOS_DEFAULT,
}
