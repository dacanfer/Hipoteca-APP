"""
pages/1_🏦_Amortización_Hipotecaria.py
--------------------------------------
Página de simulación de amortización anticipada y venta futura de la vivienda.
Trabaja siempre a nivel de mes y reutiliza los datos hipotecarios ya
introducidos en la página principal (st.session_state) cuando están disponibles.
"""

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from amortization import (
    calculate_early_amortization,
    compare_sale_scenarios,
    generate_equity_evolution,
)
from utils import exportar_excel

st.set_page_config(page_title="Amortización Hipotecaria", page_icon="🏦", layout="wide")

st.title("🏦 Amortización Hipotecaria")
st.caption(
    "Simula el efecto de aportaciones extra sobre tu hipoteca y compara la venta "
    "de la vivienda mes a mes, con y sin amortización anticipada."
)

# ─── Datos de la hipoteca (reutilizados de la página principal si existen) ───

with st.sidebar:
    st.header("🏠 Datos de la hipoteca")
    capital = st.number_input(
        "Capital pendiente (€)",
        min_value=1_000.0,
        max_value=10_000_000.0,
        value=float(st.session_state.get("capital", 200_000.0)),
        step=1_000.0,
        format="%.0f",
    )
    tipo_base = st.number_input(
        "Tipo de interés anual (%)",
        min_value=0.0,
        max_value=20.0,
        value=float(st.session_state.get("tipo_base", 3.5)),
        step=0.05,
        format="%.4f",
    )
    anios = st.number_input(
        "Plazo (años)",
        min_value=1,
        max_value=50,
        value=int(st.session_state.get("anios", 30)),
        step=1,
    )
    precio_inmueble = st.number_input(
        "Precio de compra original (€)",
        min_value=1_000.0,
        max_value=10_000_000.0,
        value=float(st.session_state.get("precio_inmueble", 300_000.0)),
        step=5_000.0,
        format="%.0f",
        help="Usado para calcular la plusvalía en el simulador de venta.",
    )

meses_totales = int(anios) * 12

st.divider()

# ═══════════════════════════════════════════════════════════════════════════
# FUNCIONALIDAD 1 — Amortización anticipada mediante aportación mensual extra
# ═══════════════════════════════════════════════════════════════════════════

st.header("1️⃣ Amortización anticipada con aportación extra")

col_input1, col_input2 = st.columns(2)
with col_input1:
    aportacion_extra = st.selectbox(
        "Aportación mensual extra (€)",
        options=[0, 50, 100, 200, 300, 500],
        index=2,
        help="Cantidad adicional destinada cada mes a amortizar capital.",
    )
    aportacion_extra = st.number_input(
        "Ajustar valor exacto (€)", min_value=0.0, value=float(aportacion_extra), step=10.0
    )
with col_input2:
    mes_inicio_extra = st.selectbox(
        "Mes de inicio de la aportación extra",
        options=[0, 12, 24, 36, 60, 120],
        index=0,
        help="0 = desde la primera cuota. Ej: 60 = empezar a partir de la cuota nº 60.",
    )
    mes_inicio_extra = st.number_input(
        "Ajustar mes exacto", min_value=0, max_value=meses_totales, value=int(mes_inicio_extra), step=1
    )

resultado = calculate_early_amortization(capital, tipo_base, int(anios), aportacion_extra, int(mes_inicio_extra))
df_normal = resultado["df_normal"]
df_extra = resultado["df_extra"]

# ── Resultados principales ────────────────────────────────────────────────

c1, c2, c3, c4 = st.columns(4)
c1.metric("Meses ahorrados", f"{resultado['meses_ahorrados']:,}")
c2.metric("Intereses ahorrados", f"{resultado['ahorro_intereses']:,.2f} €")
c3.metric("Intereses escenario normal", f"{resultado['intereses_normal']:,.2f} €")
c4.metric("Intereses con aportación extra", f"{resultado['intereses_extra']:,.2f} €")

c5, c6, c7 = st.columns(3)
c5.metric("Capital pendiente (hoy)", f"{capital:,.2f} €")
c6.metric("Fin hipoteca normal", resultado["fecha_fin_normal"].strftime("%B %Y"))
c7.metric("Fin con aportación extra", resultado["fecha_fin_extra"].strftime("%B %Y"))

st.divider()

# ── Gráficos comparativos (mes a mes) ─────────────────────────────────────

st.subheader("📉 Capital pendiente mes a mes")
fig_capital = go.Figure()
fig_capital.add_trace(go.Scatter(x=df_normal["Mes"], y=df_normal["Capital pendiente (€)"], name="Hipoteca normal"))
fig_capital.add_trace(go.Scatter(x=df_extra["Mes"], y=df_extra["Capital pendiente (€)"], name="Con aportación extra"))
fig_capital.update_layout(xaxis_title="Mes", yaxis_title="Capital pendiente (€)")
st.plotly_chart(fig_capital, use_container_width=True)

st.subheader("📈 Intereses acumulados mes a mes")
fig_intereses = go.Figure()
fig_intereses.add_trace(
    go.Scatter(x=df_normal["Mes"], y=df_normal["Intereses (€)"].cumsum(), name="Hipoteca normal")
)
fig_intereses.add_trace(
    go.Scatter(x=df_extra["Mes"], y=df_extra["Intereses (€)"].cumsum(), name="Con aportación extra")
)
fig_intereses.update_layout(xaxis_title="Mes", yaxis_title="Intereses acumulados (€)")
st.plotly_chart(fig_intereses, use_container_width=True)

st.subheader("💰 Patrimonio neto acumulado mes a mes")
equity_normal = generate_equity_evolution(df_normal, precio_inmueble)
equity_extra = generate_equity_evolution(df_extra, precio_inmueble)
fig_equity = go.Figure()
fig_equity.add_trace(
    go.Scatter(x=equity_normal["Mes"], y=equity_normal["Patrimonio neto (€)"], name="Hipoteca normal")
)
fig_equity.add_trace(
    go.Scatter(x=equity_extra["Mes"], y=equity_extra["Patrimonio neto (€)"], name="Con aportación extra")
)
fig_equity.update_layout(xaxis_title="Mes", yaxis_title="Patrimonio neto (€)")
st.plotly_chart(fig_equity, use_container_width=True)

with st.expander("📊 Agregación anual (opcional)"):
    desglose_anual = df_extra.groupby("Año").agg(
        **{
            "Intereses (€)": ("Intereses (€)", "sum"),
            "Capital amortizado (€)": ("Capital amortizado (€)", "sum"),
            "Capital pendiente (€)": ("Capital pendiente (€)", "last"),
        }
    ).reset_index()
    fig_desglose = px.bar(
        desglose_anual,
        x="Año",
        y=["Intereses (€)", "Capital amortizado (€)", "Capital pendiente (€)"],
        barmode="group",
    )
    fig_desglose.update_layout(yaxis_title="Importe (€)")
    st.plotly_chart(fig_desglose, use_container_width=True)

# ── Tablas mensuales completas y exportación ──────────────────────────────

with st.expander("📋 Ver cuadro de amortización mensual completo"):
    tab_normal, tab_extra = st.tabs(["Hipoteca normal", "Con aportación extra"])
    columnas_mostrar = ["Mes", "Fecha", "Cuota (€)", "Intereses (€)", "Capital amortizado (€)", "Capital pendiente (€)"]
    with tab_normal:
        st.dataframe(df_normal[columnas_mostrar], use_container_width=True, height=400)
        st.download_button(
            "Descargar Excel (hipoteca normal)",
            data=exportar_excel(df_normal[columnas_mostrar], "Amortización normal"),
            file_name="amortizacion_normal.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    with tab_extra:
        st.dataframe(df_extra[columnas_mostrar], use_container_width=True, height=400)
        st.download_button(
            "Descargar Excel (con aportación extra)",
            data=exportar_excel(df_extra[columnas_mostrar], "Amortización con extra"),
            file_name="amortizacion_extra.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

st.divider()

# ═══════════════════════════════════════════════════════════════════════════
# FUNCIONALIDAD 2 — Simulador de venta futura de la vivienda (por mes)
# ═══════════════════════════════════════════════════════════════════════════

st.header("2️⃣ Simulador de venta futura de la vivienda")

col_a, col_b, col_c = st.columns(3)
with col_a:
    mes_venta = st.slider(
        "Mes de venta", min_value=1, max_value=max(len(df_normal), 1), value=min(64, len(df_normal))
    )
    st.caption(f"Equivale a {mes_venta // 12} años y {mes_venta % 12} meses.")
    precio_venta = st.number_input(
        "Precio estimado de venta (€)", min_value=0.0, value=float(precio_inmueble), step=5_000.0, format="%.0f"
    )
with col_b:
    pct_cancelacion = st.number_input(
        "Coste de cancelación de hipoteca (%)", min_value=0.0, max_value=5.0, value=0.25, step=0.05, format="%.2f"
    )
with col_c:
    coste_agencia = st.number_input("Agencia inmobiliaria (€)", min_value=0.0, value=0.0, step=500.0)
    coste_legal = st.number_input("Gastos legales (€)", min_value=0.0, value=0.0, step=100.0)
    coste_otros = st.number_input("Otros costes (€)", min_value=0.0, value=0.0, step=100.0)

costes_venta_total = coste_agencia + coste_legal + coste_otros

comparativa_venta = compare_sale_scenarios(
    df_normal=df_normal,
    df_extra=df_extra,
    mes_venta=mes_venta,
    precio_venta=precio_venta,
    pct_cancelacion=pct_cancelacion,
    costes_venta=costes_venta_total,
    precio_compra_original=precio_inmueble,
)
venta_normal = comparativa_venta["normal"]
venta_extra = comparativa_venta["extra"]

st.subheader("💶 Resultado de la venta — comparativa")
st.dataframe(
    comparativa_venta["tabla"].style.format(
        {"Sin amortización extra": "{:,.2f} €", "Con amortización extra": "{:,.2f} €"}
    ),
    use_container_width=True,
    hide_index=True,
)
st.success(
    f"✅ Gracias a la amortización extra obtienes **{comparativa_venta['diferencia_patrimonio']:,.2f} €** "
    "adicionales de patrimonio neto al vender en el mes seleccionado."
)

# ── Gráficos de venta mes a mes ───────────────────────────────────────────

df_venta_normal = generate_equity_evolution(df_normal, precio_venta)
df_venta_extra = generate_equity_evolution(df_extra, precio_venta)

st.subheader("📈 Dinero neto recuperado si vendo en cada mes")
fig_venta_mensual = go.Figure()
fig_venta_mensual.add_trace(
    go.Scatter(x=df_venta_normal["Mes"], y=df_venta_normal["Patrimonio neto (€)"], name="Sin amortización extra")
)
fig_venta_mensual.add_trace(
    go.Scatter(x=df_venta_extra["Mes"], y=df_venta_extra["Patrimonio neto (€)"], name="Con amortización extra")
)
fig_venta_mensual.add_vline(x=mes_venta, line_dash="dash", annotation_text="Mes seleccionado")
fig_venta_mensual.update_layout(xaxis_title="Mes", yaxis_title="Dinero neto recuperado (€)")
st.plotly_chart(fig_venta_mensual, use_container_width=True)

st.divider()

# ═══════════════════════════════════════════════════════════════════════════
# PANEL RESUMEN
# ═══════════════════════════════════════════════════════════════════════════

st.header("📊 Panel resumen")

r1, r2, r3, r4 = st.columns(4)
r1.metric("Meses ahorrados", f"{resultado['meses_ahorrados']:,}")
r2.metric("Intereses ahorrados", f"{resultado['ahorro_intereses']:,.2f} €")
r3.metric("Capital pendiente (hoy)", f"{capital:,.2f} €")
r4.metric("Capital pendiente en venta", f"{venta_extra['capital_pendiente']:,.2f} €")

r5, r6, r7 = st.columns(3)
r5.metric("Patrimonio neto sin amortización", f"{venta_normal['dinero_neto']:,.2f} €")
r6.metric("Patrimonio neto con amortización", f"{venta_extra['dinero_neto']:,.2f} €")
r7.metric("Diferencia de patrimonio", f"{comparativa_venta['diferencia_patrimonio']:,.2f} €")

