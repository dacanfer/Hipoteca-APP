"""
optimizer.py
------------
Genera todas las combinaciones posibles de productos financieros (3^N escenarios)
y calcula el coste total para cada una, devolviendo un DataFrame ordenado.

Estados de producto:
  0 = No contratado
  1 = Contratado con el banco
  2 = Contratado externamente
"""

import itertools
import pandas as pd
from mortgage import calcular_cuota_mensual, calcular_coste_total

# Etiquetas legibles para cada estado
ESTADO_LABELS = {0: "No", 1: "Banco", 2: "Externo"}


def _formato_escenario(productos: list[dict], estados: tuple) -> str:
    """Construye la cadena legible de un escenario. Ej: 'Nómina Banco | Vida No'."""
    partes = []
    for producto, estado in zip(productos, estados):
        partes.append(f"{producto['nombre']} {ESTADO_LABELS[estado]}")
    return " | ".join(partes)


def optimizar(
    capital: float,
    anios: int,
    tipo_base: float,
    productos: list[dict],
) -> pd.DataFrame:
    """
    Genera todos los escenarios posibles y calcula el coste total de cada uno.

    Parámetros
    ----------
    capital    : Capital prestado (€).
    anios      : Plazo en años.
    tipo_base  : Tipo de interés base (%).
    productos  : Lista de dicts con claves:
                   - 'nombre'        : str
                   - 'bonificacion'  : float  (%)
                   - 'coste_banco'   : float  (€/mes)
                   - 'coste_externo' : float  (€/mes)
                   - 'obligatorio'   : bool   (si True, excluye el estado "No contratado")

    Retorna
    -------
    DataFrame ordenado por coste_mensual_total ascendente con columnas:
      Ranking, Escenario, Tipo final (%), Cuota hipotecaria (€),
      Coste productos (€), Coste mensual total (€),
      Coste anual total (€), Coste 5 años (€), Coste 30 años (€).
    """
    n = len(productos)
    filas = []

    # Estados posibles por producto: si es obligatorio, se descarta "No contratado" (0)
    estados_posibles = [
        (1, 2) if producto.get("obligatorio", False) else (0, 1, 2)
        for producto in productos
    ]

    # Genera todas las combinaciones válidas respetando la obligatoriedad
    for estados in itertools.product(*estados_posibles):

        # 1. Bonificación total (solo productos contratados con banco, estado==1)
        bonificacion_total = sum(
            productos[i]["bonificacion"]
            for i, estado in enumerate(estados)
            if estado == 1
        )

        # 2. Tipo final (nunca puede bajar de 0%)
        tipo_final = max(0.0, tipo_base - bonificacion_total)

        # 3. Cuota hipotecaria mensual
        cuota = calcular_cuota_mensual(capital, anios, tipo_final)

        # 4. Coste mensual de productos vinculados
        coste_productos = 0.0
        for i, estado in enumerate(estados):
            if estado == 1:
                coste_productos += productos[i]["coste_banco"]
            elif estado == 2:
                coste_productos += productos[i]["coste_externo"]

        # 5-8. Costes totales
        costes = calcular_coste_total(cuota, coste_productos)

        # Descripción legible del escenario
        escenario = _formato_escenario(productos, estados)

        filas.append(
            {
                "Escenario": escenario,
                "Tipo final (%)": round(tipo_final, 4),
                "Cuota hipotecaria (€)": cuota,
                "Coste productos (€)": round(coste_productos, 2),
                "Coste mensual total (€)": costes["coste_mensual_total"],
                "Coste anual total (€)": costes["coste_anual_total"],
                "Coste 5 años (€)": costes["coste_5_anios"],
                "Coste 30 años (€)": costes["coste_30_anios"],
            }
        )

    df = pd.DataFrame(filas)
    df.sort_values("Coste mensual total (€)", inplace=True, ignore_index=True)
    df.insert(0, "Ranking", range(1, len(df) + 1))
    return df
