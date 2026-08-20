"""
amortization.py
----------------
Funciones de cálculo para la página "Amortización Hipotecaria", trabajando
siempre a nivel de mes:
  - Cuadro de amortización mensual (sistema francés).
  - Amortización anticipada con aportación extra a partir de un mes concreto.
  - Resultado de venta en un mes determinado.
  - Comparativa de venta entre hipoteca normal y con amortización extra.
  - Evolución mensual del patrimonio neto (valor vivienda - capital pendiente).
"""

import pandas as pd
import numpy_financial as npf


def _simular_cuadro(
    capital: float,
    tipo_anual: float,
    anios: int,
    aportacion_extra: float = 0.0,
    mes_inicio_extra: int = 0,
    fecha_inicio: pd.Timestamp | None = None,
) -> pd.DataFrame:
    """Motor interno: simula mes a mes el cuadro de amortización francés."""
    if tipo_anual > 0:
        tipo_mensual = tipo_anual / 100 / 12
        cuota_base = -npf.pmt(tipo_mensual, anios * 12, capital)
    else:
        tipo_mensual = 0.0
        cuota_base = capital / (anios * 12)

    fecha_inicio = fecha_inicio or pd.Timestamp.today().normalize()
    # mes_inicio_extra=0 equivale a aplicar la aportación desde la primera cuota
    mes_activacion = max(mes_inicio_extra, 1)

    saldo = capital
    filas = []
    mes = 0
    tope_meses = anios * 12

    while saldo > 0.01 and mes < tope_meses:
        mes += 1
        interes_mes = saldo * tipo_mensual
        capital_cuota = min(cuota_base - interes_mes, saldo)

        extra_mes = 0.0
        if aportacion_extra > 0 and mes >= mes_activacion:
            extra_mes = min(aportacion_extra, max(saldo - capital_cuota, 0.0))

        capital_amortizado = capital_cuota + extra_mes
        saldo = round(saldo - capital_amortizado, 2)

        filas.append(
            {
                "Mes": mes,
                "Fecha": fecha_inicio + pd.DateOffset(months=mes - 1),
                "Año": (mes - 1) // 12 + 1,
                "Cuota (€)": round(capital_cuota + interes_mes + extra_mes, 2),
                "Intereses (€)": round(interes_mes, 2),
                "Capital amortizado (€)": round(capital_amortizado, 2),
                "Capital pendiente (€)": max(saldo, 0.0),
            }
        )

    return pd.DataFrame(filas)


def generate_monthly_schedule(
    capital: float,
    tipo_anual: float,
    anios: int,
    fecha_inicio: pd.Timestamp | None = None,
) -> pd.DataFrame:
    """
    Genera el cuadro de amortización mensual normal (sin aportaciones extra).

    Retorna
    -------
    DataFrame con columnas: Mes, Fecha, Año, Cuota (€), Intereses (€),
    Capital amortizado (€), Capital pendiente (€).
    """
    return _simular_cuadro(capital, tipo_anual, anios, aportacion_extra=0.0, fecha_inicio=fecha_inicio)


def generate_extra_payment_schedule(
    capital: float,
    tipo_anual: float,
    anios: int,
    aportacion_extra: float,
    mes_inicio_extra: int = 0,
    fecha_inicio: pd.Timestamp | None = None,
) -> pd.DataFrame:
    """
    Genera el cuadro de amortización mensual aplicando una aportación extra
    constante a partir de un mes concreto.

    Parámetros
    ----------
    mes_inicio_extra : Mes de la hipoteca a partir del cual se empieza a aportar
                        el extra (0 o 1 = desde la primera cuota).

    Retorna
    -------
    DataFrame con las mismas columnas que generate_monthly_schedule().
    """
    return _simular_cuadro(
        capital, tipo_anual, anios, aportacion_extra, mes_inicio_extra, fecha_inicio
    )


def calculate_early_amortization(
    capital: float,
    tipo_anual: float,
    anios: int,
    aportacion_extra: float = 0.0,
    mes_inicio_extra: int = 0,
) -> dict:
    """
    Compara la hipoteca con pago normal frente a la hipoteca con aportación
    extra a partir de un mes concreto.

    Retorna
    -------
    Diccionario con ambos cuadros de amortización (df_normal, df_extra) y las
    métricas de ahorro: meses/años ahorrados, intereses de cada escenario,
    ahorro total de intereses y fechas estimadas de finalización.
    """
    df_normal = generate_monthly_schedule(capital, tipo_anual, anios)
    df_extra = (
        generate_extra_payment_schedule(capital, tipo_anual, anios, aportacion_extra, mes_inicio_extra)
        if aportacion_extra > 0
        else df_normal.copy()
    )

    meses_normal = len(df_normal)
    meses_extra = len(df_extra)
    intereses_normal = round(df_normal["Intereses (€)"].sum(), 2)
    intereses_extra = round(df_extra["Intereses (€)"].sum(), 2)
    hoy = pd.Timestamp.today().normalize()

    return {
        "df_normal": df_normal,
        "df_extra": df_extra,
        "meses_normal": meses_normal,
        "meses_extra": meses_extra,
        "meses_ahorrados": meses_normal - meses_extra,
        "anios_ahorrados": round((meses_normal - meses_extra) / 12, 2),
        "intereses_normal": intereses_normal,
        "intereses_extra": intereses_extra,
        "ahorro_intereses": round(intereses_normal - intereses_extra, 2),
        "fecha_fin_normal": hoy + pd.DateOffset(months=meses_normal),
        "fecha_fin_extra": hoy + pd.DateOffset(months=meses_extra),
    }


def calculate_sale_result(
    df_amortizacion: pd.DataFrame,
    mes_venta: int,
    precio_venta: float,
    pct_cancelacion: float = 0.0,
    costes_venta: float = 0.0,
    precio_compra_original: float | None = None,
) -> dict:
    """
    Calcula el resultado económico de vender la vivienda en un mes concreto,
    a partir de un único cuadro de amortización.

    Parámetros
    ----------
    df_amortizacion       : Cuadro de amortización (normal o con extra).
    mes_venta             : Mes de la hipoteca en el que se vende (1, 2, 3…).
    precio_venta          : Precio estimado de venta (€).
    pct_cancelacion       : % de comisión de cancelación sobre el capital pendiente.
    costes_venta          : Otros gastos de venta (agencia, legales, etc.) en €.
    precio_compra_original: Precio de compra original, para calcular plusvalía (opcional).

    Retorna
    -------
    Diccionario con capital pendiente, intereses y capital amortizado
    acumulados hasta ese mes, coste de cancelación, dinero neto recibido
    y (si se indica precio de compra) plusvalía y rentabilidad.
    """
    if df_amortizacion.empty:
        capital_pendiente = intereses_acumulados = capital_amortizado_acumulado = 0.0
    else:
        idx = min(mes_venta, len(df_amortizacion)) - 1
        if idx < 0:
            capital_pendiente = df_amortizacion["Capital pendiente (€)"].iloc[0]
            intereses_acumulados = 0.0
            capital_amortizado_acumulado = 0.0
        else:
            fila = df_amortizacion.iloc[: idx + 1]
            capital_pendiente = fila["Capital pendiente (€)"].iloc[-1]
            intereses_acumulados = fila["Intereses (€)"].sum()
            capital_amortizado_acumulado = fila["Capital amortizado (€)"].sum()

    coste_cancelacion = round(capital_pendiente * pct_cancelacion / 100, 2)
    dinero_neto = round(precio_venta - capital_pendiente - coste_cancelacion - costes_venta, 2)

    resultado = {
        "mes_venta": mes_venta,
        "precio_venta": round(precio_venta, 2),
        "capital_pendiente": round(capital_pendiente, 2),
        "intereses_acumulados": round(intereses_acumulados, 2),
        "capital_amortizado_acumulado": round(capital_amortizado_acumulado, 2),
        "coste_cancelacion": coste_cancelacion,
        "costes_venta": round(costes_venta, 2),
        "dinero_neto": dinero_neto,
    }

    if precio_compra_original:
        plusvalia = round(precio_venta - precio_compra_original, 2)
        resultado["plusvalia"] = plusvalia
        resultado["rentabilidad_pct"] = round(plusvalia / precio_compra_original * 100, 2)

    return resultado


def compare_sale_scenarios(
    df_normal: pd.DataFrame,
    df_extra: pd.DataFrame,
    mes_venta: int,
    precio_venta: float,
    pct_cancelacion: float = 0.0,
    costes_venta: float = 0.0,
    precio_compra_original: float | None = None,
) -> dict:
    """
    Compara el resultado de venta en un mes concreto entre la hipoteca normal
    y la hipoteca con amortización extra.

    Retorna
    -------
    Diccionario con:
      - 'normal'  : resultado de calculate_sale_result() para la hipoteca normal.
      - 'extra'   : resultado de calculate_sale_result() para la hipoteca con extra.
      - 'tabla'   : DataFrame comparativo con fila "Diferencia obtenida".
    """
    resultado_normal = calculate_sale_result(
        df_normal, mes_venta, precio_venta, pct_cancelacion, costes_venta, precio_compra_original
    )
    resultado_extra = calculate_sale_result(
        df_extra, mes_venta, precio_venta, pct_cancelacion, costes_venta, precio_compra_original
    )

    conceptos = [
        ("Capital pendiente", "capital_pendiente"),
        ("Intereses pagados", "intereses_acumulados"),
        ("Capital amortizado", "capital_amortizado_acumulado"),
        ("Dinero neto tras venta", "dinero_neto"),
    ]

    filas = []
    for etiqueta, clave in conceptos:
        filas.append(
            {
                "Concepto": etiqueta,
                "Sin amortización extra": resultado_normal[clave],
                "Con amortización extra": resultado_extra[clave],
            }
        )

    diferencia_patrimonio = round(resultado_extra["dinero_neto"] - resultado_normal["dinero_neto"], 2)
    filas.append(
        {
            "Concepto": "Diferencia obtenida",
            "Sin amortización extra": 0.0,
            "Con amortización extra": diferencia_patrimonio,
        }
    )

    return {
        "normal": resultado_normal,
        "extra": resultado_extra,
        "tabla": pd.DataFrame(filas),
        "diferencia_patrimonio": diferencia_patrimonio,
    }


def generate_equity_evolution(df_amortizacion: pd.DataFrame, precio_venta: float) -> pd.DataFrame:
    """
    Genera la evolución MES A MES del valor de la vivienda, el capital
    pendiente y el patrimonio neto (valor vivienda - capital pendiente),
    a lo largo de toda la vida del préstamo.

    Retorna
    -------
    DataFrame con columnas: Mes, Fecha, Valor vivienda (€),
    Capital pendiente (€), Patrimonio neto (€).
    """
    if df_amortizacion.empty:
        return pd.DataFrame(
            columns=["Mes", "Fecha", "Valor vivienda (€)", "Capital pendiente (€)", "Patrimonio neto (€)"]
        )

    df = df_amortizacion[["Mes", "Fecha", "Capital pendiente (€)"]].copy()
    df["Valor vivienda (€)"] = precio_venta
    df["Patrimonio neto (€)"] = round(precio_venta - df["Capital pendiente (€)"], 2)
    return df[["Mes", "Fecha", "Valor vivienda (€)", "Capital pendiente (€)", "Patrimonio neto (€)"]]
