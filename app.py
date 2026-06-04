import streamlit as st
import pandas as pd
from simulation import SimulationEngine
from events import Evento
from utils import format_rnd, format_time

st.set_page_config(page_title="Simulación Aduana - Grupo 7", layout="wide")

st.markdown("""
<style>
/* --- Celdas del dataframe: texto negro --- */
[data-testid="stDataFrame"] iframe {
    color-scheme: light;
}
[data-testid="stDataFrame"] div[class*="dvn-scroller"] *,
[data-testid="stDataFrame"] .cell-text,
[data-testid="stDataFrame"] span {
    color: #000000 !important;
}

/* --- Encabezados de columna: fondo naranja, texto negro y en negrita --- */
[data-testid="stDataFrame"] .ag-header-cell-label,
[data-testid="stDataFrame"] .ag-header-cell-text,
[data-testid="stDataFrame"] .col_heading,
[data-testid="stDataFrame"] th {
    background-color: #F5A623 !important;
    color: #000000 !important;
    font-weight: 700 !important;
}
</style>
""", unsafe_allow_html=True)

st.title("⚓ Simulación de Aduana de Camiones - Grupo 7 (Distribución Propia)")
st.write("Trabajo Práctico 4 - Cátedra de Simulación (4K2 - 2026)")

st.sidebar.header("⚙️ Parámetros de Simulación")
semilla_input = st.sidebar.number_input("Semilla del Generador (LCG)", min_value=1, value=42, step=1)
tiempo_simulacion = st.sidebar.number_input("Tiempo total a simular (X minutos)", min_value=10.0, value=720.0, step=10.0)
max_iteraciones = st.sidebar.number_input("Cantidad máxima de iteraciones (N)", min_value=10, value=100000, step=100)

st.sidebar.subheader("📋 Ventana de Visualización")
hora_j = st.sidebar.number_input("Mostrar desde el minuto (j)", min_value=0.0, value=0.0, step=5.0)
iteraciones_i = st.sidebar.number_input("Cantidad de iteraciones a mostrar (i)", min_value=1, value=50, step=5)

st.sidebar.subheader("⏱️ Parámetros de Distribuciones")
media_gen = st.sidebar.number_input("Media Carga General (min)", value=15.0, step=0.5)
media_per = st.sidebar.number_input("Media Carga Perecedera (min)", value=40.0, step=0.5)

st.sidebar.markdown("---")
cd_min = st.sidebar.number_input("Mínimo Control Documental (min)", value=10.0, step=0.5)
cd_max = st.sidebar.number_input("Máximo Control Documental (min)", value=15.0, step=0.5)

st.sidebar.markdown("---")
rf_min = st.sidebar.number_input("Mínimo Revisión Física (min)", value=30.0, step=0.5)
rf_max = st.sidebar.number_input("Máximo Revisión Física (min)", value=60.0, step=0.5)

st.sidebar.markdown("---")
prob_rf_input = st.sidebar.number_input("Probabilidad Derivación a Revisión Física (%)", min_value=0.0, max_value=100.0, value=15.0, step=1.0)

# =========================================================================
# --- CONTROL DE ERRORES LÓGICOS Y PARAMÉTRICOS (BLOQUEO ESTRICTO) ---
# =========================================================================

if media_gen <= 0 or media_per <= 0:
    st.sidebar.error("❌ Error: Las medias exponenciales deben ser mayores a cero.")
    st.stop()

if cd_min < 0 or cd_max < 0 or rf_min < 0 or rf_max < 0:
    st.sidebar.error("❌ Error: Los tiempos uniformes no pueden ser negativos.")
    st.stop()

if cd_min >= cd_max or rf_min >= rf_max:
    st.sidebar.error("❌ Error: Los límites mínimos no pueden superar o igualar a los máximos.")
    st.stop()

# =========================================================================

if st.sidebar.button("▶️ Ejecutar Simulación"):
    engine = SimulationEngine(semilla_input, media_gen, media_per, cd_min, cd_max, rf_min, rf_max, prob_rf_input / 100.0)

    historial_completo = []
    fila_actual = engine.inicializar_sistema()
    historial_completo.append(fila_actual)

    iteracion = 1
    reloj = 0.0

    while reloj < tiempo_simulacion and iteracion < max_iteraciones:
        candidatos = [
            (engine.prox_llegada_gen, Evento.LLEGADA_GENERAL),
            (engine.prox_llegada_per, Evento.LLEGADA_PERECEDERA)
        ]

        for idx, c in enumerate(engine.controles):
            if c.fin_atencion is not None and c.fin_atencion != "-":
                candidatos.append((c.fin_atencion, f"fin_ocupacion_control{idx+1}"))

        if engine.revision.fin_atencion is not None and engine.revision.fin_atencion != "-":
            candidatos.append((engine.revision.fin_atencion, Evento.FIN_REVISION))

        candidatos.sort(key=lambda x: x[0])
        prox_reloj, prox_evento = candidatos[0]

        if prox_reloj > tiempo_simulacion:
            break

        reloj = prox_reloj
        fila_actual = engine.simular_paso(reloj, prox_evento)
        historial_completo.append(fila_actual)
        iteracion += 1

    if historial_completo[-1]["Reloj"] < tiempo_simulacion:
        fila_final = engine.evento_fin_simulacion(tiempo_simulacion)
        historial_completo.append(fila_final)

    # =========================================================================
    # --- FILTRADO PARA PREVENIR MESSAGE_SIZE_ERROR ---
    # =========================================================================

    # Capturo la última fila (para las métricas y el cuadro final) de forma aislada
    ultima_fila_datos = historial_completo[-1].copy()

    # Buscamos el valor máximo de camiones en la lista nativa
    max_camiones_historico = max(fila["Maximo Camiones"] for fila in historial_completo)

    # Filtramos la lista antes de convertirla a DataFrame de Pandas
    historial_filtrado_lista = [f for f in historial_completo if f["Reloj"] >= hora_j][:int(iteraciones_i)]

    # Creo DataFrames ligero solo con los fragmentos a mostrar
    df_filtrado = pd.DataFrame(historial_filtrado_lista).fillna("-")
    df_ultima = pd.DataFrame([ultima_fila_datos]).fillna("-")

    # libero memoria

    # =========================================================================

    st.subheader("📊 Resultados de la Simulación")
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Espera Promedio Gral (CD)", f"{ultima_fila_datos['Promedio Espera General']} min")
        st.metric("Espera Promedio Perecedera (CD)", f"{ultima_fila_datos['Promedio Espera Perecedera']} min")
    with m2:
        st.metric("Utilización Revisión Física", f"{ultima_fila_datos['Porcentaje Utilizacion Revision']} %")
    with m3:
        st.metric("Máximo de Camiones Simultáneos", f"{int(max_camiones_historico)}")

    st.subheader(f"📋 Vector de Estados (Muestra desde minuto {hora_j})")

    if not df_filtrado.empty:
        columnas_rnd = [c for c in df_filtrado.columns if "RND" in c]
        columnas_tiempo = [c for c in df_filtrado.columns if "Reloj" in c or "Fin" in c or "Tiempo" in c or "Proxima" in c]

        for col in columnas_rnd:
            df_filtrado[col] = df_filtrado[col].apply(format_rnd)
        for col in columnas_tiempo:
            df_filtrado[col] = df_filtrado[col].apply(format_time)

        st.dataframe(df_filtrado, use_container_width=True)
    else:
        st.warning("⚠️ No se encontraron iteraciones para mostrar en la ventana de tiempo seleccionada.")

    st.subheader("🏁 Última Fila del Vector de Estado (Instante X)")
    columnas_objetos = [c for c in df_ultima.columns if "Camion" in c]
    df_ultima_limpia = df_ultima.drop(columns=columnas_objetos, errors='ignore')
    st.dataframe(df_ultima_limpia, use_container_width=True)
