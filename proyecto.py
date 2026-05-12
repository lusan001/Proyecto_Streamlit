import streamlit as st
import requests
import plotly.express as px
import pandas as pd
import time
from datetime import datetime
import pytz

# ──────────────────────────────────────────────
# CONFIGURACIÓN DE LA PÁGINA
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard Fútbol",
    page_icon="⚽",
    layout="wide",
)

# ──────────────────────────────────────────────
# CONSTANTES
# ──────────────────────────────────────────────
API_KEY = "c0378fef7fae4b6c816376d85c320333"
BASE_URL = "https://api.football-data.org/v4"
HEADERS = {"X-Auth-Token": API_KEY}

INTERVALO_SEGUNDOS = 300             # Actualización automática cada 5 minutos

# Ligas disponibles en el plan gratuito
LIGAS = {
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League": "PL",
    "🇪🇸 La Liga":          "PD",
    "🇩🇪 Bundesliga":       "BL1",
    "🇮🇹 Serie A":          "SA",
}


# ──────────────────────────────────────────────
# FUNCIONES DE CARGA DE DATOS
# ──────────────────────────────────────────────

def obtener_clasificacion(codigo_liga: str) -> pd.DataFrame | None:
    """Llama al endpoint de clasificación y devuelve un DataFrame.
    Devuelve None si la API falla (sin internet, clave inválida, límite de peticiones).
    """
    try:
        url = f"{BASE_URL}/competitions/{codigo_liga}/standings"
        r = requests.get(url, headers=HEADERS, timeout=8)
        r.raise_for_status()
        tabla = r.json()["standings"][0]["table"]   # Tipo TOTAL
        df = pd.DataFrame([
            {
                "Pos":    equipo["position"],
                "Equipo": equipo["team"]["shortName"],
                "PJ":     equipo["playedGames"],
                "PG":     equipo["won"],
                "PE":     equipo["draw"],
                "PP":     equipo["lost"],
                "GF":     equipo["goalsFor"],
                "GC":     equipo["goalsAgainst"],
                "DG":     equipo["goalDifference"],
                "Pts":    equipo["points"],
            }
            for equipo in tabla
        ])
        return df
    except Exception as e:
        print(f"Error clasificacion: {e}")
        return None


def obtener_goleadores(codigo_liga: str) -> pd.DataFrame | None:
    """Llama al endpoint de máximos goleadores y devuelve un DataFrame.
    Devuelve None si la API falla.
    """
    try:
        url = f"{BASE_URL}/competitions/{codigo_liga}/scorers?limit=10"
        r = requests.get(url, headers=HEADERS, timeout=8)
        r.raise_for_status()
        datos = r.json()["scorers"]
        df = pd.DataFrame([
            {
                "Jugador": s["player"]["name"],
                "Equipo":  s["team"]["shortName"],
                "Goles":   s["goals"],
                "Asist":   s.get("assists") or 0,
            }
            for s in datos
        ])
        return df
    except Exception as e:
        print(f"Error goleadores: {e}")
        return None


# ──────────────────────────────────────────────
# SIDEBAR – CONTROL INTERACTIVO (radio buttons)
# ──────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Configuración")
    liga_nombre = st.radio(
        "Selecciona la liga:",
        options=list(LIGAS.keys()),
    )
    st.divider()
    st.caption("Los datos se actualizan automáticamente cada 5 minutos.")

codigo_liga = LIGAS[liga_nombre]   # Código de la liga seleccionada


# ──────────────────────────────────────────────
# CARGA DE DATOS
# ──────────────────────────────────────────────
df_clasificacion = obtener_clasificacion(codigo_liga)
df_goleadores    = obtener_goleadores(codigo_liga)

# Si alguna llamada falla, mostrar error y reintentar tras el intervalo
if df_clasificacion is None or df_goleadores is None:
    st.error("⚠️ No se pudo conectar con la API. Reintentando en 5 minutos...")
    time.sleep(INTERVALO_SEGUNDOS)
    st.rerun()


# ──────────────────────────────────────────────
# CABECERA
# ──────────────────────────────────────────────
st.title(f"⚽ Dashboard de Fútbol — {liga_nombre}")
st.caption(f"Última actualización: {datetime.now().strftime('%H:%M:%S')}")
st.divider()


# ──────────────────────────────────────────────
# KPIs – calculados a partir de los datos
# ──────────────────────────────────────────────
lider         = df_clasificacion.iloc[0]           # Equipo en 1ª posición
max_goleador  = df_goleadores.iloc[0]              # Máximo goleador
total_goles   = int(df_clasificacion["GF"].sum())  # Suma de todos los GF

kpi1, kpi2, kpi3 = st.columns(3)

kpi1.metric(
    label="🥇 Líder de la liga",
    value=lider["Equipo"],
    delta=f"{lider['Pts']} pts",
)
kpi2.metric(
    label="⚽ Máximo goleador",
    value=max_goleador["Jugador"],
    delta=f"{max_goleador['Goles']} goles ({max_goleador['Equipo']})",
)
kpi3.metric(
    label="📊 Total goles en la liga",
    value=f"{total_goles}",
    delta=f"{round(total_goles / len(df_clasificacion), 1)} goles/equipo (media)",
)

st.divider()


# ──────────────────────────────────────────────
# GRÁFICOS
# ──────────────────────────────────────────────
col_izq, col_der = st.columns(2)

# GRÁFICO 1 – Barras: Puntos por equipo (top 10)
with col_izq:
    top10 = df_clasificacion.head(10).sort_values("Pts", ascending=True)
    fig_barras = px.bar(
        top10,
        x="Pts",
        y="Equipo",
        orientation="h",
        color="Pts",
        color_continuous_scale="Teal",
        title="Clasificación — Top 10 equipos por puntos",
        labels={"Pts": "Puntos", "Equipo": "Equipo"},
        template="plotly_dark",
        text="Pts",
    )
    fig_barras.update_traces(textposition="outside")
    fig_barras.update_layout(
        coloraxis_showscale=False,
        yaxis_title="Equipo",
        xaxis_title="Puntos",
    )
    st.plotly_chart(fig_barras, use_container_width=True)

# GRÁFICO 2 – Dispersión: Goles a favor vs. Goles en contra
with col_der:
    fig_scatter = px.scatter(
        df_clasificacion,
        x="GF",
        y="GC",
        text="Equipo",
        color="Pts",
        size="Pts",
        color_continuous_scale="RdYlGn",
        title="Ataque vs. Defensa (GF vs. GC)",
        labels={"GF": "Goles a favor", "GC": "Goles en contra", "Pts": "Puntos"},
        template="plotly_dark",
    )
    fig_scatter.update_traces(textposition="top center", textfont_size=9)
    fig_scatter.update_layout(
        xaxis_title="Goles a favor (GF)",
        yaxis_title="Goles en contra (GC)",
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

st.divider()

# TABLA COMPLETA – Clasificación
st.subheader("📋 Clasificación completa")
st.dataframe(
    df_clasificacion.set_index("Pos"),
    use_container_width=True,
)

# ──────────────────────────────────────────────
# ACTUALIZACIÓN AUTOMÁTICA
# ──────────────────────────────────────────────
time.sleep(INTERVALO_SEGUNDOS)
st.rerun()