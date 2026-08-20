"""
Optimizador_Hipotecario.py
---------------------------
Aplicación Streamlit para comparar hipotecas y optimizar bonificaciones bancarias.

Ejecución:
    streamlit run Optimizador_Hipotecario.py
"""

import copy
import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# Asegurar que los módulos del proyecto son localizables
sys.path.insert(0, str(Path(__file__).parent))

from optimizer import optimizar
from utils import (
    CONFIG_DEFAULT,
    PRODUCTOS_DEFAULT,
    cargar_config,
    config_desde_bytes,
    exportar_excel,
    guardar_config,
)

# ─── Configuración de página ──────────────────────────────────────────────────

st.set_page_config(
    page_title="Optimizador Hipotecario",
    page_icon="🏠",
    layout="wide",
)

# ─── CSS personalizado ────────────────────────────────────────────────────────

st.markdown(
    """
    <style>
    /* Tarjetas KPI */
    .kpi-card {
        background: #f0f4ff;
        border-radius: 12px;
        padding: 18px 22px;
        text-align: center;
        border: 1px solid #c5d3f5;
    }
    .kpi-label { font-size: 0.80rem; color: #555; margin-bottom: 4px; }
    .kpi-value { font-size: 1.55rem; font-weight: 700; color: #1a3c8f; }

    /* Resaltar fila óptima */
    .highlight-green { background-color: #d4edda !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─── Estado de sesión ─────────────────────────────────────────────────────────

def _init_session():
    """Inicializa el estado de sesión con los valores por defecto."""
    defaults = {
        "precio_inmueble": 300_000.0,
        "pct_financiacion": 80.0,
        "pct_impuestos": 7.0,
        "gastos_hipoteca": 3_000.0,
        "ahorros_banco": 90_000.0,
        "anios": CONFIG_DEFAULT["anios"],
        "tipo_base": CONFIG_DEFAULT["tipo_base"],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
    if "productos_df" not in st.session_state:
        st.session_state["productos_df"] = pd.DataFrame(PRODUCTOS_DEFAULT)
    # Garantizar que la columna obligatorio existe aunque venga de una sesión antigua
    if "obligatorio" not in st.session_state["productos_df"].columns:
        st.session_state["productos_df"]["obligatorio"] = False


_init_session()

# ─── Sidebar: datos hipoteca ──────────────────────────────────────────────────

with st.sidebar:
    st.header("🏠 Datos de la hipoteca")

    # ── Precio e importe a financiar ──────────────────────────────────────────
    precio_inmueble = st.number_input(
        "Precio del inmueble (€)",
        min_value=10_000.0,
        max_value=10_000_000.0,
        value=float(st.session_state["precio_inmueble"]),
        step=5_000.0,
        format="%.0f",
        help="Precio de compraventa del inmueble.",
    )

    pct_financiacion = st.number_input(
        "% del precio a financiar",
        min_value=1.0,
        max_value=100.0,
        value=float(st.session_state["pct_financiacion"]),
        step=1.0,
        format="%.1f",
        help="Porcentaje del precio que financiará el banco. El resto sale de tus ahorros.",
    )

    # Capital prestado calculado automáticamente
    capital = round(precio_inmueble * pct_financiacion / 100, 2)
    st.info(f"**Capital hipotecario:** {capital:,.0f} €")

    st.divider()

    # ── Gastos e impuestos ────────────────────────────────────────────────────
    pct_impuestos = st.number_input(
        "Impuestos previstos (% del precio)",
        min_value=0.0,
        max_value=100.0,
        value=float(st.session_state["pct_impuestos"]),
        step=0.5,
        format="%.2f",
        help="En España suele expresarse como % del precio (ITP, AJD, etc.).",
    )

    # Impuestos en euros calculados automáticamente
    impuestos = round(precio_inmueble * pct_impuestos / 100, 2)
    st.info(f"**Impuestos previstos:** {impuestos:,.0f} €")

    gastos_hipoteca = st.number_input(
        "Gastos de hipoteca previstos (€)",
        min_value=0.0,
        max_value=500_000.0,
        value=float(st.session_state["gastos_hipoteca"]),
        step=100.0,
        format="%.0f",
        help="Tasación, notaría, registro, gestoría, etc.",
    )

    st.divider()

    # ── Ahorros disponibles ───────────────────────────────────────────────────
    ahorros_banco = st.number_input(
        "Ahorros disponibles en banco (€)",
        min_value=0.0,
        max_value=10_000_000.0,
        value=float(st.session_state["ahorros_banco"]),
        step=1_000.0,
        format="%.0f",
        help="Dinero en cuenta que destinarás a la entrada, impuestos y gastos.",
    )

    st.divider()

    # ── Condiciones del préstamo ──────────────────────────────────────────────
    anios = st.number_input(
        "Plazo (años)",
        min_value=1,
        max_value=50,
        value=int(st.session_state["anios"]),
        step=1,
    )

    tipo_base = st.number_input(
        "Tipo de interés base (%)",
        min_value=0.0,
        max_value=20.0,
        value=float(st.session_state["tipo_base"]),
        step=0.05,
        format="%.4f",
    )

    # Se guarda en sesión para que otras páginas (p.ej. Amortización) lo reutilicen
    st.session_state["capital"] = capital
    st.session_state["precio_inmueble"] = precio_inmueble
    st.session_state["anios"] = int(anios)
    st.session_state["tipo_base"] = tipo_base

    st.divider()

    # ── Guardar configuración ─────────────────────────────────────────────────
    st.subheader("💾 Guardar configuración")
    nombre_config = st.text_input("Nombre del archivo", value="mi_hipoteca")
    if st.button("Guardar en JSON"):
        config_actual = {
            "precio_inmueble": precio_inmueble,
            "pct_financiacion": pct_financiacion,
            "pct_impuestos": pct_impuestos,
            "gastos_hipoteca": gastos_hipoteca,
            "ahorros_banco": ahorros_banco,
            "capital": capital,
            "anios": anios,
            "tipo_base": tipo_base,
            "productos": st.session_state["productos_df"].to_dict(orient="records"),
        }
        ruta = Path(__file__).parent / f"{nombre_config}.json"
        try:
            guardar_config(config_actual, str(ruta))
            st.success(f"Guardado en {ruta.name}")
        except Exception as e:
            st.error(f"Error al guardar: {e}")

    st.divider()

    # ── Cargar configuración ──────────────────────────────────────────────────
    st.subheader("📂 Cargar configuración")
    archivo_cargado = st.file_uploader("Sube un archivo JSON", type=["json"])
    if archivo_cargado is not None:
        try:
            cfg = config_desde_bytes(archivo_cargado.read())
            st.session_state["precio_inmueble"] = cfg.get("precio_inmueble", 300_000.0)
            st.session_state["pct_financiacion"] = cfg.get("pct_financiacion", 80.0)
            # Compatibilidad con configs antiguas que guardaban impuestos en euros
            if "pct_impuestos" in cfg:
                st.session_state["pct_impuestos"] = cfg["pct_impuestos"]
            elif "impuestos" in cfg and cfg.get("precio_inmueble"):
                st.session_state["pct_impuestos"] = round(
                    cfg["impuestos"] / cfg["precio_inmueble"] * 100, 2
                )
            st.session_state["gastos_hipoteca"] = cfg.get("gastos_hipoteca", 0.0)
            st.session_state["ahorros_banco"] = cfg.get("ahorros_banco", 0.0)
            st.session_state["anios"] = cfg.get("anios", 30)
            st.session_state["tipo_base"] = cfg.get("tipo_base", 3.5)
            st.session_state["productos_df"] = pd.DataFrame(cfg["productos"])
            st.success("Configuración cargada.")
        except Exception as e:
            st.error(f"Error al cargar: {e}")

# ─── Cuerpo principal ─────────────────────────────────────────────────────────

st.title("🏠 Optimizador Hipotecario — Bonificaciones y Productos Vinculados")
st.caption(
    "Encuentra automáticamente la combinación de productos financieros que minimiza "
    "tu coste total hipotecario."
)

# ── Resumen financiero de la operación ───────────────────────────────────────

aportacion_necesaria = precio_inmueble - capital          # lo que pones tú del precio
total_ahorros_necesarios = aportacion_necesaria + impuestos + gastos_hipoteca
saldo_restante = ahorros_banco - total_ahorros_necesarios

with st.expander("💰 Resumen financiero de la operación", expanded=True):
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Precio del inmueble", f"{precio_inmueble:,.0f} €")
        st.metric("Capital hipotecario", f"{capital:,.0f} €",
                  help=f"{pct_financiacion:.1f}% del precio")
        st.metric("Aportación propia (entrada)", f"{aportacion_necesaria:,.0f} €",
                  help=f"{100 - pct_financiacion:.1f}% del precio")
    with c2:
        st.metric("Impuestos previstos", f"{impuestos:,.0f} €")
        st.metric("Gastos de hipoteca", f"{gastos_hipoteca:,.0f} €")
        st.metric("Total ahorros necesarios", f"{total_ahorros_necesarios:,.0f} €",
                  help="Entrada + Impuestos + Gastos")
    with c3:
        st.metric("Ahorros disponibles", f"{ahorros_banco:,.0f} €")
        delta_label = f"{abs(saldo_restante):,.0f} € {'sobrantes' if saldo_restante >= 0 else 'faltan'}"
        st.metric(
            "Saldo tras la operación",
            f"{saldo_restante:,.0f} €",
            delta=delta_label,
            delta_color="normal" if saldo_restante >= 0 else "inverse",
        )
    if saldo_restante < 0:
        st.error(
            f"⚠️ Te faltan **{abs(saldo_restante):,.0f} €** de ahorros para cubrir "
            "la entrada, impuestos y gastos con el porcentaje de financiación actual."
        )
    else:
        st.success(
            f"✅ Tus ahorros son suficientes. Te sobrarán **{saldo_restante:,.0f} €** "
            "tras la operación."
        )

st.divider()

# ── Tabla editable de productos ───────────────────────────────────────────────

st.subheader("📋 Productos vinculados")
st.markdown(
    "Edita la tabla con los productos ofrecidos por el banco. "
    "Puedes añadir o eliminar filas con los botones de la parte inferior de la tabla."
)

productos_df = st.data_editor(
    st.session_state["productos_df"],
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "nombre": st.column_config.TextColumn(
            "Producto", help="Nombre del producto financiero", required=True
        ),
        "bonificacion": st.column_config.NumberColumn(
            "Bonificación (%)", help="Reducción sobre el tipo base si se contrata con banco",
            min_value=0.0, max_value=5.0, step=0.05, format="%.2f", required=True
        ),
        "coste_banco": st.column_config.NumberColumn(
            "Coste banco (€/mes)", help="Coste mensual si se contrata con el banco",
            min_value=0.0, step=1.0, format="%.2f", required=True
        ),
        "coste_externo": st.column_config.NumberColumn(
            "Coste externo (€/mes)", help="Coste mensual si se contrata fuera del banco",
            min_value=0.0, step=1.0, format="%.2f", required=True
        ),
        "obligatorio": st.column_config.CheckboxColumn(
            "Obligatorio banco",
            help="El banco exige contratar este producto para conceder la hipoteca "
                 "(aunque no obliga a hacerlo con ellos).",
            default=False,
        ),
    },
    key="tabla_productos",
)

# Guardar en sesión los cambios
st.session_state["productos_df"] = productos_df

st.divider()

# ── Botón de cálculo ──────────────────────────────────────────────────────────

calcular = st.button("🔍 Calcular todos los escenarios", type="primary", use_container_width=True)

# Firma de los inputs actuales, para detectar si el resultado guardado quedó desactualizado
firma_actual = json.dumps(
    {
        "capital": capital,
        "anios": anios,
        "tipo_base": tipo_base,
        "productos": productos_df.to_dict(orient="records") if productos_df is not None else [],
    },
    sort_keys=True,
    default=str,
)

if calcular:
    # Validaciones básicas
    if productos_df is None or len(productos_df) == 0:
        st.warning("Añade al menos un producto para poder calcular.")
        st.stop()

    productos_lista = productos_df.to_dict(orient="records")
    n = len(productos_lista)
    # Los productos obligatorios solo tienen 2 estados posibles (Banco/Externo)
    total_escenarios = 1
    for p in productos_lista:
        total_escenarios *= 2 if p.get("obligatorio", False) else 3

    with st.spinner(f"Calculando {total_escenarios:,} escenarios para {n} productos…"):
        df_resultado = optimizar(
            capital=capital,
            anios=int(anios),
            tipo_base=tipo_base,
            productos=productos_lista,
        )

    # Guardar resultado y la firma de los inputs usados para generarlo
    st.session_state["resultado"] = df_resultado
    st.session_state["resultado_firma"] = firma_actual

# ── Mostrar resultados si existen ─────────────────────────────────────────────

if "resultado" in st.session_state:
    if st.session_state.get("resultado_firma") != firma_actual:
        st.warning(
            "⚠️ Has cambiado datos de la hipoteca o de los productos. "
            "Pulsa **Calcular todos los escenarios** para actualizar los resultados."
        )

    productos_lista_actual = productos_df.to_dict(orient="records")

    df = st.session_state["resultado"]
    mejor = df.iloc[0]

    # ── KPI Cards ─────────────────────────────────────────────────────────────
    st.subheader("📊 Mejor escenario — Indicadores clave")

    col1, col2, col3, col4 = st.columns(4)

    def _kpi(col, label: str, valor: float, prefijo: str = "€"):
        col.markdown(
            f"""
            <div class="kpi-card">
              <div class="kpi-label">{label}</div>
              <div class="kpi-value">{valor:,.2f} {prefijo}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    _kpi(col1, "Tipo interés final",    mejor["Tipo final (%)"], prefijo="%")
    _kpi(col2, "Cuota hipotecaria",       mejor["Cuota hipotecaria (€)"])
    _kpi(col3, "Coste de productos",      mejor["Coste productos (€)"])
    _kpi(col4, "Mejor coste mensual",     mejor["Coste mensual total (€)"])

    # Parsear el string de escenario → dict {producto: estado}
    def _parsear_escenario(escenario_str: str) -> dict:
        resultado = {}
        for parte in escenario_str.split(" | "):
            tokens = parte.rsplit(" ", 1)          # separa por el último espacio
            nombre, estado = tokens[0], tokens[1]
            resultado[nombre] = estado
        return resultado

    escenario_dict = _parsear_escenario(mejor["Escenario"])
    df_mejor_tabla = pd.DataFrame(
        [escenario_dict],
        index=["Contratación"],
    )

    # Colores por estado de contratación
    _COLORES = {
        "Banco":   "background-color: #d4edda; color: #155724; font-weight: 700; text-align: center",
        "Externo": "background-color: #fff3cd; color: #856404; font-weight: 700; text-align: center",
        "No":      "background-color: #f8d7da; color: #721c24; font-weight: 700; text-align: center",
    }

    def _colorear(val):
        return _COLORES.get(val, "text-align: center")

    st.dataframe(
        df_mejor_tabla.style.map(_colorear),
        use_container_width=True,
    )

    st.divider()

    # ── Gráfico de barras — Top 10 ────────────────────────────────────────────
    st.subheader("📈 Top 10 escenarios más baratos (coste mensual total)")

    vista_grafico = st.radio(
        "Desglose del gráfico",
        options=["Hipoteca vs. productos", "Coste por producto contratado"],
        horizontal=True,
        key="vista_grafico_top10",
    )

    top10 = df.head(10).copy()

    # Acortar etiquetas del eje X para legibilidad
    top10["Etiqueta"] = top10["Escenario"].str.replace(" | ", "\n", regex=False)

    if vista_grafico == "Hipoteca vs. productos":
        chart_data = top10.set_index("Etiqueta")[["Cuota hipotecaria (€)", "Coste productos (€)"]]
    else:
        # Coste en euros de cada producto según su estado en cada escenario
        costes_por_producto = {}
        for _, fila in top10.iterrows():
            estado_por_nombre = _parsear_escenario(fila["Escenario"])
            costes_fila = {}
            for producto in productos_lista_actual:
                nombre = producto["nombre"]
                estado = estado_por_nombre.get(nombre, "No")
                if estado == "Banco":
                    costes_fila[nombre] = producto["coste_banco"]
                elif estado == "Externo":
                    costes_fila[nombre] = producto["coste_externo"]
                else:
                    costes_fila[nombre] = 0.0
            costes_por_producto[fila["Etiqueta"]] = costes_fila

        chart_data = pd.DataFrame.from_dict(costes_por_producto, orient="index")

    st.bar_chart(chart_data, use_container_width=True)

    st.divider()

    # ── Tabla de resultados completa ──────────────────────────────────────────
    st.subheader("📋 Todos los escenarios ordenados por coste mensual")

    # Función de resaltado: fila 0 (mejor) en verde
    def _resaltar_mejor(row):
        if row.name == 0:
            return ["background-color: #d4edda"] * len(row)
        return [""] * len(row)

    df_mostrar = df.copy()
    cols_euro = [
        "Cuota hipotecaria (€)", "Coste productos (€)",
        "Coste mensual total (€)", "Coste anual total (€)",
        "Coste 5 años (€)", "Coste 30 años (€)",
    ]

    # Formatear columnas numéricas
    df_styled = (
        df_mostrar.style
        .apply(_resaltar_mejor, axis=1)
        .format({col: "{:,.2f} €" for col in cols_euro})
        .format({"Tipo final (%)": "{:.4f}%"})
    )

    st.dataframe(df_styled, use_container_width=True, height=500)

    st.caption(f"Total de escenarios evaluados: **{len(df):,}** | La fila verde corresponde al escenario óptimo.")

    st.divider()

    # ── Exportar a Excel ──────────────────────────────────────────────────────
    st.subheader("⬇️ Exportar resultados")

    excel_bytes = exportar_excel(df)
    st.download_button(
        label="Descargar Excel (.xlsx)",
        data=excel_bytes,
        file_name="comparativa_hipotecas.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

else:
    st.info(
        "Configura los datos de la hipoteca y los productos en el panel lateral, "
        "luego pulsa **Calcular todos los escenarios**."
    )
