"""
mortgage.py
-----------
Lógica de cálculo hipotecario.
Usa el sistema de amortización francés (cuota constante) con numpy_financial.pmt.
"""

import numpy_financial as npf


def calcular_capital_hipotecario(
    precio: float,
    pct_financiacion: float,
    ahorros_disponibles: float,
    impuestos: float,
    gastos_compra: float,
) -> tuple[float, float]:
    """Return mortgage principal and minimum savings needed for the purchase."""
    capital_base = round(precio * pct_financiacion / 100, 2)
    entrada_minima = precio - capital_base
    ahorros_minimos = round(entrada_minima + impuestos + gastos_compra, 2)

    # Upfront costs are covered first; only savings beyond them pay down the loan.
    ahorro_extra = max(0.0, ahorros_disponibles - ahorros_minimos)
    capital = max(0.0, capital_base - ahorro_extra)
    return round(capital, 2), ahorros_minimos


def calcular_cuota_mensual(capital: float, anios: int, tipo_anual: float) -> float:
    """
    Calcula la cuota mensual de una hipoteca mediante el sistema francés.

    Parámetros
    ----------
    capital    : Capital prestado en euros.
    anios      : Plazo de amortización en años.
    tipo_anual : Tipo de interés anual en porcentaje (ej: 3.5 para 3,5 %).

    Retorna
    -------
    Cuota mensual (valor positivo, en euros).
    """
    if tipo_anual <= 0:
        # Si el tipo es 0 o negativo devolvemos división directa sin intereses
        return capital / (anios * 12)

    tipo_mensual = tipo_anual / 100 / 12
    n_pagos = anios * 12

    # npf.pmt devuelve valor negativo (pago de salida), lo invertimos
    cuota = -npf.pmt(tipo_mensual, n_pagos, capital)
    return round(cuota, 2)


def calcular_coste_total(cuota_mensual: float, coste_productos: float) -> dict:
    """
    Calcula el coste total mensual, anual, a 5 y a 30 años.

    Parámetros
    ----------
    cuota_mensual    : Cuota hipotecaria mensual en euros.
    coste_productos  : Coste mensual total de productos vinculados en euros.

    Retorna
    -------
    Diccionario con las métricas de coste.
    """
    mensual = cuota_mensual + coste_productos
    return {
        "coste_mensual_total": round(mensual, 2),
        "coste_anual_total": round(mensual * 12, 2),
        "coste_5_anios": round(mensual * 60, 2),
        "coste_30_anios": round(mensual * 360, 2),
    }
