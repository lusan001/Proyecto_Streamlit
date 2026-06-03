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
    page_title="Dashboard Fútbol", # Titulo de la pestaña
    page_icon="⚽", # Icono de la pestaña
    layout="wide", # Para usar todo el ancho de la pantalla
)

# ──────────────────────────────────────────────
# CONSTANTES
# ──────────────────────────────────────────────
API_KEY = "c0378fef7fae4b6c816376d85c320333" # Clave de API obtenida de football-data.org
BASE_URL = "https://api.football-data.org/v4" # URL base de la API es de football-data.org
HEADERS = {"X-Auth-Token": API_KEY} # Cabecera con la clave de API

INTERVALO_SEGUNDOS = 300             # Actualización automática cada 5 minutos

# Ligas disponibles en el plan gratuito de la API de football-data.org
LIGAS = { # Diccionario con el nombre de la liga y su código correspondiente en la API
    "🇬🇧 Premier League": "PL",      # Premier League
    "🇪🇸 La Liga":          "PD",      # La Liga
    "🇩🇪 Bundesliga":       "BL1",     # Bundesliga
    "🇮🇹 Serie A":          "SA",      # Serie A
}


# ──────────────────────────────────────────────
# FUNCIONES DE CARGA DE DATOS
# ──────────────────────────────────────────────

def obtener_clasificacion(codigo_liga: str):
    """Llama al endpoint de clasificación y devuelve un DataFrame.
    Devuelve None si la API falla (sin internet, clave inválida, límite de peticiones).
    """
    try:
        url = f"{BASE_URL}/competitions/{codigo_liga}/standings"    # Endpoint para obtener la clasificación de la liga
        r = requests.get(url, headers=HEADERS, timeout=8)           # Llamada a la API
        r.raise_for_status()                                         # Si la respuesta no es 200, lanza una excepción
        tabla = r.json()["standings"][0]["table"]   # Tipo TOTAL
        df = pd.DataFrame([                                    # Crea un DataFrame con los datos de la clasificación
            {
                "Pos":    equipo["position"],   # Posición en la tabla
                "Equipo": equipo["team"]["shortName"],  # Nombre corto del equipo
                "PJ":     equipo["playedGames"], # Partidos jugados
                "PG":     equipo["won"],         # Partidos ganados
                "PE":     equipo["draw"],     # Partidos empatados
                "PP":     equipo["lost"],   # Partidos perdidos
                "GF":     equipo["goalsFor"],       # Goles a favor
                "GC":     equipo["goalsAgainst"],    # Goles en contra
                "DG":     equipo["goalDifference"], # Diferencia de goles
                "Pts":    equipo["points"],        # Puntos
            }
            for equipo in tabla      # Recorre la tabla de la clasificación
        ])
        return df   # Devuelve el DataFrame
    except Exception as e:  # Si ocurre cualquier error (conexión, clave, límite), lo muestra y devuelve None
        print(f"Error clasificacion: {e}")
        return None


def obtener_goleadores(codigo_liga: str):   # Llama al endpoint de máximos goleadores y devuelve un DataFrame con los 10 primeros
    """Llama al endpoint de máximos goleadores y devuelve un DataFrame.
    Devuelve None si la API falla.
    """
    # este try catch es para manejar cualquier error que pueda ocurrir en la llamada a la API
    try:
        url = f"{BASE_URL}/competitions/{codigo_liga}/scorers?limit=10"  # Endpoint para obtener los máximos goleadores de la liga, limitando a los 10 primeros
        r = requests.get(url, headers=HEADERS, timeout=8)          # Llamada a la API con un timeout de 8 segundos para evitar que se quede colgado
        r.raise_for_status()                                        # Si la respuesta no es 200, lanza una excepción
        datos = r.json()["scorers"] # Lista de goleadores obtenida de la respuesta JSON

        df = pd.DataFrame([     # Crea un DataFrame con los datos de los goleadores
            {
                "Jugador": s["player"]["name"], # Nombre del jugador
                "Equipo":  s["team"]["shortName"], # Nombre corto del equipo
                "Goles":   s["goals"], # Número de goles
                "Asist":   s.get("assists") or 0, # Número de asistencias (si no existe, se asigna 0)
            }
            for s in datos  # Recorre la lista de goleadores
        ])
        return df  # Devuelve el DataFrame con los goleadores
    except Exception as e: # Si ocurre cualquier error (conexión, clave, límite), lo muestra y devuelve None
        print(f"Error goleadores: {e}")
        return None

def obtener_partidos(codigo_liga: str):
    """Llama al endpoint de partidos y devuelve un DataFrame con los resultados.
    Devuelve None si la API falla.
    """
    try:    # este try catch es para manejar cualquier error que pueda ocurrir en la llamada a la API
        url = f"{BASE_URL}/competitions/{codigo_liga}/matches"  # Endpoint para obtener los partidos de la liga
        r = requests.get(url, headers=HEADERS, timeout=8)       # Llamada a la API con un timeout de 8 segundos para evitar que se quede colgado
        r.raise_for_status()                                    # Si la respuesta no es 200, lanza una excepción
        partidos = r.json()["matches"]  # Lista de partidos obtenida de la respuesta JSON
        df = pd.DataFrame([             # Crea un DataFrame con los datos de los partidos
            {
                "Jornada":   p["matchday"], # Número de jornada
                "Local":     p["homeTeam"]["shortName"],    # Nombre corto del equipo local
                "Visitante": p["awayTeam"]["shortName"], # Nombre corto del equipo visitante
                "Goles L":   p["score"]["fullTime"]["home"], # Goles del equipo local
                "Goles V":   p["score"]["fullTime"]["away"], # Goles del equipo visitante
                "Estado":    p["status"], # Estado del partido
            }
            for p in partidos
        ])
        # Solo partidos ya disputados
        df = df[df["Estado"] == "FINISHED"].reset_index(drop=True)  # Elimina los partidos no disputados
        return df
    except Exception as e:  # Si ocurre cualquier error (conexión, clave, límite), lo muestra y devuelve None
        print(f"Error partidos: {e}")
        return None

# ──────────────────────────────────────────────
# SIDEBAR – CONTROL INTERACTIVO (radio buttons)
# ──────────────────────────────────────────────
with st.sidebar: # Contenido del sidebar para seleccionar la liga
    st.header("⚙️ Configuración") # Título del sidebar
    liga_nombre = st.radio( # Radio buttons para seleccionar la liga, con las opciones definidas en el diccionario LIGAS
        "Selecciona la liga:",
        options=list(LIGAS.keys()), # Lista de nombres de las ligas para mostrar en el radio buttons
    )
    st.divider()    # Separador: una línea horizontal para separar secciones
    st.caption("Los datos se actualizan automáticamente cada 5 minutos.")   # Pie de página del sidebar con una nota sobre la actualización automática

codigo_liga = LIGAS[liga_nombre]   # Código de la liga seleccionada


# ──────────────────────────────────────────────
# CARGA DE DATOS
# ──────────────────────────────────────────────
df_clasificacion = obtener_clasificacion(codigo_liga)   # Llama a la función para obtener la clasificación de la liga seleccionada y devuelve un DataFrame
df_goleadores    = obtener_goleadores(codigo_liga)  # Llama a la función para obtener los máximos goleadores de la liga seleccionada y devuelve un DataFrame
df_partidos      = obtener_partidos(codigo_liga)   # Llama a la función para obtener los partidos de la liga seleccionada y devuelve un DataFrame

# Si alguna llamada falla, mostrar error y reintentar tras el intervalo
if df_clasificacion is None or df_goleadores is None or df_partidos is None:   # Si alguna de las llamadas a la API devuelve None, significa que hubo un error
    st.error("⚠️ No se pudo conectar con la API. Reintentando en 5 minutos...") # Muestra un mensaje de error en la aplicación
    time.sleep(INTERVALO_SEGUNDOS)  # time.sleep para esperar el intervalo definido antes de reintentar
    st.rerun()  # st.rerun() para reiniciar la aplicación y volver a intentar cargar los datos


# ──────────────────────────────────────────────
# CABECERA
# ──────────────────────────────────────────────
st.title(f"⚽ Dashboard de Fútbol — {liga_nombre} 🏆")   # Título de la página
st.caption(f"Última actualización: {datetime.now().strftime('%H:%M:%S')}")  # Pie de página con la hora de la última actualización

# datetime.now devuelve la fecha y hora actual del sistema.
# Con .strftime('%H:%M:%S') se formatea para mostrar solo la hora, minutos y segundos.

st.divider()    # Separador para dividir la cabecera del resto del contenido con una línea horizontal


# ──────────────────────────────────────────────
# KPIs – calculados a partir de los datos
# ──────────────────────────────────────────────

# Un KPI (Key Performance Indicator) es un indicador clave de rendimiento que se utiliza para medir el desempeño de un equipo, jugador o liga en función de ciertos criterios. En este caso, se han definido tres KPIs:
#1. Líder de la liga: El equipo que ocupa la primera posición en la clasificación, mostrando su nombre y puntos.
#2. Máximo goleador: El jugador con más goles en la liga, mostrando su nombre, número de goles y el equipo al que pertenece.
#3. Total goles en la liga: La suma de todos los goles a favor (GF) de todos los equipos, que representa el total de goles anotados en la liga, junto con la media de goles por equipo. Estos KPIs proporcionan una visión rápida y clara del rendimiento general de la liga, destacando al equipo líder, al máximo goleador y la cantidad total de goles anotados.


lider         = df_clasificacion.iloc[0]           # Equipo en 1ª posición
max_goleador  = df_goleadores.iloc[0]              # Máximo goleador
total_goles   = int(df_clasificacion["GF"].sum())  # Suma de todos los goles a favor (GF) de todos los equipos, que representa el total de goles en la liga

kpi1, kpi2, kpi3 = st.columns(3)    # Divide la página en tres columnas. Si cambio el número, se ajusta el ancho de cada columna automáticamente (3 columnas = 1/3 del ancho cada una)

kpi1.metric(    # Muestra el KPI del líder de la liga, con su nombre y puntos
    label="🥇 Líder de la liga",
    value=lider["Equipo"],  # Nombre del equipo líder
    delta=f"{lider['Pts']} pts",    # Puntos del equipo lider. delta es el valor que se muestra debajo del nombre del equipo, indicando su puntuación actual
)
kpi2.metric(    # Muestra el KPI del máximo goleador, con su nombre, número de goles y el equipo al que pertenece
    label="⚽ Máximo goleador",
    value=max_goleador["Jugador"],  # Nombre del máximo goleador
    delta=f"{max_goleador['Goles']} goles ({max_goleador['Equipo']})",  # Número de goles y el equipo al que pertenece
)
kpi3.metric(    # Muestra el KPI del total de goles en la liga, con la suma de todos los goles a favor (GF) de todos los equipos, junto con la media de goles por equipo
    label="📊 Total goles en la liga",
    value=f"{total_goles}", # Total de goles anotados en la liga
    delta=f"{round(total_goles / len(df_clasificacion), 1)} goles/equipo (media)",  # Media de goles por equipo, calculada dividiendo el total de goles entre el número de equipos en la clasificación (len(df_clasificacion))
)

st.divider()    # Separador para dividir los KPIs del resto del contenido con una línea horizontal


# ──────────────────────────────────────────────
# GRÁFICOS
# ──────────────────────────────────────────────
col_izq, col_der = st.columns(2)    # Divide la página en dos columnas. Si cambio el número, se ajusta el ancho de cada columna automáticomente (2 columnas)

# GRÁFICO 1 – Barras: Puntos por equipo (top 10)

# with es para mostrar el gráfico de barras en la columna izquierda. 
# En esta sección se muestra un gráfico de barras con los puntos por equipo, mostrando solo los 10 primeros equipos de la clasificación. 
# Se utiliza Plotly Express para crear el gráfico, con una orientación horizontal y un esquema de colores continuo basado en los puntos.
# El gráfico incluye etiquetas para los puntos y se ajusta para mostrar el nombre del equipo en el eje y y los puntos en el eje x.

with col_izq:
    top10 = df_clasificacion.head(10).sort_values("Pts", ascending=True) # Selecciona los 10 primeros equipos de la clasificación y los ordena por puntos de forma ascendente para que el equipo con más puntos aparezca arriba en el gráfico de barras

    # Crea un gráfico de barras con Plotly Express, utilizando el DataFrame de los 10 primeros equipos de la clasificación.
    # El eje x representa los puntos (Pts), el eje y representa el nombre del equipo (Equipo),
    # y el color de las barras también se basa en los puntos para crear un esquema de colores continuo.
    # El gráfico tiene un título, etiquetas para los ejes y utiliza una plantilla oscura.

    fig_barras = px.bar(
        top10,
        x="Pts",    # Eje x representa los puntos de cada equipo
        y="Equipo",   # Eje y representa el nombre del equipo
        orientation="h", # Orientación horizontal para que el nombre del equipo se muestre en el eje y y los puntos en el eje x
        color="Pts",    # Color de las barras se basa en los puntos
        color_continuous_scale="Teal", # Esquema de colores continuo basado en los puntos, utilizando la paleta "Teal"
        title="Clasificación — Top 10 equipos por puntos",  # Título del gráfico
        labels={"Pts": "Puntos", "Equipo": "Equipo"}, # Etiquetas para los ejes
        template="plotly_dark", # Plantilla oscura para el gráfico
        text="Pts", # Etiqueta para mostrar los puntos en el gráfico
    )

    fig_barras.update_traces(textposition="outside") # update_traces para ajustar la posición de las etiquetas de los puntos, colocándolas fuera de las barras para que sean más legibles, especialmente en el caso de equipos con pocos puntos donde las etiquetas podrían superponerse con las barras.
    fig_barras.update_layout( # update_layout para ajustar el gráfico
        coloraxis_showscale=False, # Oculta la barra de colores que aparece por defecto cuando se utiliza color_continuous_scale, ya que en este caso no es necesaria para interpretar el gráfico
        yaxis_title="Equipo", # Etiqueta para el eje y
        xaxis_title="Puntos", # Etiqueta para el eje x
    )
    st.plotly_chart(fig_barras, use_container_width=True) # Muestra el gráfico de barras en la aplicación, ajustando su tamaño para que ocupe todo el ancho disponible en la columna izquierda

# GRÁFICO 2 – Dispersión: Goles a favor vs. Goles en contra
with col_der:
    fig_scatter = px.scatter(   # Crea un gráfico de dispersión con Plotly Express, utilizando el DataFrame completo de la clasificación
        df_clasificacion,
        x="GF", # Eje x representa los goles a favor (GF) de cada equipo
        y="GC", # Eje y representa los goles en contra (GC) de cada equipo
        text="Equipo",  # Etiqueta para mostrar el nombre del equipo
        color="Pts",    # Color de los puntos se basa en los puntos de cada equipo para crear un esquema de colores continuo
        size="Pts", # Tamaño de los puntos también se basa en los puntos de cada equipo para resaltar visualmente a los equipos con más puntos
        color_continuous_scale="RdYlGn",    # Esquema de colores continuo basado en los puntos, utilizando la paleta "RdYlGn"
        title="Ataque vs. Defensa (GF vs. GC)", # Título del gráfico
        labels={"GF": "Goles a favor", "GC": "Goles en contra", "Pts": "Puntos"},   # Etiquetas para los ejes y la leyenda de colores
        template="plotly_dark", # Plantilla oscura para el gráfico
    )


    # update_traces para ajustar la posición de las etiquetas de los equipos, colocándolas en la parte superior central
    # de cada punto para mejorar la legibilidad, especialmente en casos donde los puntos están muy juntos, y ajustando
    # el tamaño de la fuente de las etiquetas para que sean legibles sin superponerse demasiado con los puntos del gráfico.

    # update_layout para ajustar el gráfico, ocultando la barra de colores que aparece por defecto cuando se utiliza
    # color_continuous_scale, ya que en este caso no es necesaria para interpretar el gráfico, y añadiendo etiquetas
    # para los ejes x e y.

    fig_scatter.update_traces(textposition="top center", textfont_size=9)
    fig_scatter.update_layout(
        xaxis_title="Goles a favor (GF)",   # Etiqueta para el eje x
        yaxis_title="Goles en contra (GC)", # Etiqueta para el eje y
    )
    st.plotly_chart(fig_scatter, use_container_width=True)  # Muestra el gráfico de dispersión en la aplicación, ajustando su tamaño para que ocupe todo el ancho disponible en la columna derecha

st.divider()    # Separador para dividir los gráficos del resto del contenido con una línea horizontal

# TABLA COMPLETA – Clasificación
st.subheader("📋 Clasificación completa")    # Subtítulos
st.dataframe(   # Muestra el DataFrame completo de la clasificación
    df_clasificacion.set_index(""),  # Establece la columna "Pos" como el nuevo indice
    use_container_width=True,   # Ajusta el tamaño de la tabla para que ocupe todo el ancho disponible
)

# ──────────────────────────────────────────────
# ESTADÍSTICAS INDIVIDUALES — Goleadores y Asistentes
# ──────────────────────────────────────────────
st.subheader("🏅 Estadísticas individuales") # Subtitulo de estadisticas individuales

col_gol, col_ast = st.columns(2)    # Divide la página en dos columnas para mostrar las estadísticas individuales de goleadores y asistentes. Si cambio el número, se ajusta el ancho de cada columna automáticamente (2 columnas)

with col_gol:
    # Ordenar por goles descendente y mostrar top 10
    top_goleadores = df_goleadores.sort_values("Goles", ascending=False).head(10)
    fig_goleadores = px.bar( # Crea un gráfico de barras con Plotly Express, utilizando el DataFrame de los 10 máximos goleadores.
        top_goleadores.sort_values("Goles", ascending=True),    # Ordena los goleadores por número de goles de forma ascendente para que el máximo goleador aparezca arriba en el gráfico de barras
        x="Goles",  # Eje x representa los goles de cada jugador
        y="Jugador",    # Eje y representa el nombre del jugador
        orientation="h",    # Orientación horizontal para que el nombre del jugador se muestre en el eje y y los goles en el eje x
        color="Goles",  # Color de las barras se basa en el número de goles para crear un esquema de colores continuo
        color_continuous_scale="Oranges",   # Esquema de colores continuo basado en el número de goles, utilizando la paleta "Oranges"
        title="🥇 Máximos goleadores", # Titulo
        labels={"Goles": "Goles", "Jugador": "Jugador"},    # Etiquetas para los ejes
        template="plotly_dark", # Plantilla oscura para el gráfico
        text="Goles",   # Etiqueta para mostrar el número de goles en el gráfico
    )
    fig_goleadores.update_traces(textposition="outside")    # update_traces para ajustar la posición de las etiquetas de los goles, colocándolas fuera de las barras para que sean más legibles, especialmente en el caso de jugadores con pocos goles donde las etiquetas podrían superponerse con las barras.
    fig_goleadores.update_layout(coloraxis_showscale=False) # update_layout para ocultar la barra de colores que aparece por defecto cuando se utiliza color_continuous_scale, ya que en este caso no es necesaria para interpretar el gráfico
    st.plotly_chart(fig_goleadores, use_container_width=True)   # Muestra el gráfico de barras de los máximos goleadores en la aplicación, ajustando su tamaño para que ocupe todo el ancho disponible en la columna izquierda

with col_ast:
    # Ordenar por asistencias descendente y mostrar top 10
    top_asistentes = df_goleadores.sort_values("Asist", ascending=False).head(10)
    fig_asistentes = px.bar(
        top_asistentes.sort_values("Asist", ascending=True),
        x="Asist",      # Eje x representa las asistencias de cada jugador
        y="Jugador",    # Eje y representa el nombre del jugador
        orientation="h",    # Orientación horizontal para que el nombre del jugador se muestre en el eje y y las asistencias en el eje x
        color="Asist",  # Color de las barras se basa en el número de asistencias para crear un esquema de colores continuo
        color_continuous_scale="Blues",  # Esquema de colores continuo basado en el número de asistencias, utilizando la paleta "Blues"
        title="🎯 Máximos asistentes",  # Titulo
        labels={"Asist": "Asistencias", "Jugador": "Jugador"},  # Etiquetas para los ejes
        template="plotly_dark", # Plantilla oscura para el gráfico
        text="Asist",   # Etiqueta para mostrar el número de asistencias en el gráfico
    )
    fig_asistentes.update_traces(textposition="outside")    # update_traces para ajustar la posición de las etiquetas de las asistencias, colocándolas fuera de las barras para que sean más legibles, especialmente en el caso de jugadores con pocas asistencias donde las etiquetas podrían superponerse con las barras.
    fig_asistentes.update_layout(coloraxis_showscale=False) # update_layout para ocultar la barra de colores que aparece por defecto cuando se utiliza color_continuous_scale, ya que en este caso no es necesaria para interpretar el gráfico
    st.plotly_chart(fig_asistentes, use_container_width=True)   # Muestra el gráfico de barras de los máximos asistentes en la aplicación, ajustando su tamaño para que ocupe todo el ancho disponible en la columna derecha

st.divider()    # Separador para dividir las estadísticas individuales del resto del contenido con una línea horizontal

# ──────────────────────────────────────────────
# RESULTADOS POR JORNADA — Slider interactivo
# ──────────────────────────────────────────────
st.subheader("📅 Resultados por jornada")    # Subtítulos

jornadas_disponibles = sorted(df_partidos["Jornada"].unique())   # Lista de jornadas disponibles en el DataFrame de partidos, ordenada de forma ascendente. Esto se utiliza para configurar el rango del slider que permite seleccionar la jornada a visualizar.

# Slider para seleccionar la jornada — afecta a la tabla de resultados
jornada_sel = st.slider(
    "Selecciona la jornada:",
    min_value=int(jornadas_disponibles[0]),   # Por defecto la primera jornada
    max_value=int(jornadas_disponibles[-1]),    # Por defecto la última jornada
    value=int(jornadas_disponibles[-1]),   # Por defecto la última jornada jugada
)

# Filtrar y mostrar solo los partidos de la jornada seleccionada
df_jornada = df_partidos[df_partidos["Jornada"] == jornada_sel][    # Filtra el DataFrame de partidos para mostrar solo los partidos de la jornada seleccionada
    ["Local", "Goles L", "Goles V", "Visitante"]    # Selecciona las columnas "Local", "Goles L", "Goles V" y "Visitante"
].reset_index(drop=True)    # Resetea el index para que los partidos se muestren en orden secuencial

# Mostrar la tabla de resultados de la jornada seleccionada, ajustando su tamaño para que ocupe todo el ancho disponible y ocultando el índice de la tabla para una presentación más limpia.
st.dataframe(df_jornada, use_container_width=True, hide_index=True)

# ──────────────────────────────────────────────
# ACTUALIZACIÓN AUTOMÁTICA
# ──────────────────────────────────────────────
time.sleep(INTERVALO_SEGUNDOS)  # Espera el intervalo de tiempo establecido
st.rerun()  # st.rerun() para reiniciar la aplicación y volver a cargar los datos actualizados de la API, lo que permite que el dashboard se mantenga actualizado automáticamente cada 5 minutos.
