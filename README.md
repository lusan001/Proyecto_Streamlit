# ⚽ Dashboard Interactivo de Fútbol

> Visualización de datos en tiempo real con **Python**, **Streamlit** y **Plotly**  
> Práctica UD5 — Visualización y comunicación de datos · Sistemas de Big Data

---

## 📋 Descripción

Dashboard interactivo que consume la API pública de [football-data.org](https://www.football-data.org/) para mostrar en tiempo real la clasificación y los máximos goleadores de las principales ligas europeas de fútbol.

El dashboard se actualiza automáticamente cada 5 minutos y permite al usuario cambiar de liga con un solo clic, actualizando simultáneamente todos los indicadores y gráficos.

---

## 🚀 Características

- 📡 **Datos en tiempo real** — conectado a la API de football-data.org
- 📊 **KPIs dinámicos** — líder de la liga, máximo goleador y total de goles
- 📈 **Dos tipos de gráficos** — barras horizontales y dispersión (Plotly)
- 🎛️ **Interactividad** — radio buttons para cambiar de liga (afecta a KPIs y gráficos simultáneamente)
- 🔄 **Automatización** — refresco automático cada 5 minutos con `time.sleep()` + `st.rerun()`
- 🛡️ **Gestión de errores** — manejo de fallos de conexión con reintento automático

---

## 🏆 Ligas disponibles

| Liga | Código |
|------|--------|
| 🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League | `PL` |
| 🇪🇸 La Liga | `PD` |
| 🇩🇪 Bundesliga | `BL1` |
| 🇮🇹 Serie A | `SA` |

---

## 🛠️ Tecnologías utilizadas

| Herramienta | Uso |
|-------------|-----|
| `Python 3.11+` | Lenguaje base |
| `Streamlit` | Framework del dashboard |
| `Plotly Express` | Gráficos interactivos |
| `Pandas` | Manipulación de datos |
| `Requests` | Llamadas a la API |

---

## ⚙️ Instalación y uso

### 1. Clona el repositorio

```bash
git clone https://github.com/tu-usuario/tu-repositorio.git
cd tu-repositorio
```

### 2. Instala las dependencias

```bash
pip install -r requirements.txt
```

### 3. Obtén tu API key gratuita

Regístrate en [football-data.org/client/register](https://www.football-data.org/client/register) — es gratis y no requiere tarjeta de crédito. Recibirás la clave en tu correo.

### 4. Añade tu API key al código

Abre `proyecto.py` y sustituye la línea:

```python
API_KEY = "TU_API_KEY_AQUI"
```

### 5. Ejecuta el dashboard

```bash
streamlit run proyecto.py
```

---

## 📁 Estructura del proyecto

```
📦 tu-repositorio
 ┣ 📄 proyecto.py        # Código principal del dashboard
 ┣ 📄 requirements.txt   # Dependencias del proyecto
 ┗ 📄 README.md          # Este archivo
```

---

## 📐 Arquitectura del código

```
proyecto.py
 ├── Configuración de página y constantes
 ├── obtener_clasificacion()   # Llama a /standings y devuelve DataFrame
 ├── obtener_goleadores()      # Llama a /scorers y devuelve DataFrame
 ├── Sidebar — st.radio()      # Control interactivo de liga
 ├── KPIs — st.metric()        # Tres indicadores dinámicos
 ├── Gráfico 1 — px.bar()      # Clasificación top 10
 ├── Gráfico 2 — px.scatter()  # Ataque vs. Defensa
 ├── Tabla completa
 └── time.sleep() + st.rerun() # Automatización
```

---

## 📊 Capturas de pantalla

> https://github.com/user-attachments/assets/34a40da3-9ecb-4c7a-8eba-1b07e6d27c16



---

## 📝 Requisitos académicos cubiertos

| Criterio | Implementación |
|----------|---------------|
| ✅ Fuente de datos externa | API football-data.org, carga encapsulada en funciones |
| ✅ KPIs calculados | Líder, máximo goleador y total de goles desde los datos |
| ✅ Dos gráficos distintos | Barras horizontales + Dispersión |
| ✅ Interactividad (no dropdown) | `st.radio()` afecta KPIs y gráficos simultáneamente |
| ✅ Automatización | `time.sleep(300)` + `st.rerun()` |
| ✅ Calidad del código | Comentado, modular, sin bloques duplicados |

---

## 📄 Licencia
Datos proporcionados por [football-data.org](https://www.football-data.org/) bajo su plan gratuito.
