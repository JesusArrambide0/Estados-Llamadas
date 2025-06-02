import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, time

st.title("Análisis de Estados de Agentes")

# Cargar archivo fijo
archivo = 'Estadosinfo.xlsx'
try:
    df = pd.read_excel(archivo)
except Exception as e:
    st.error(f"No se pudo leer el archivo '{archivo}'. Error: {e}")
    st.stop()

# Renombrar columnas por claridad
df = df.rename(columns={
    'Agent Name': 'Agente',
    'State Transition Time': 'Inicio Estado',
    'Agent State': 'Estado',
    'Reason': 'Motivo',
    'Duration': 'Duración'
})

# Convertir a datetime y extraer fecha y hora
df['Inicio Estado'] = pd.to_datetime(df['Inicio Estado'], errors='coerce')
df.dropna(subset=['Inicio Estado'], inplace=True)
df['Fecha'] = df['Inicio Estado'].dt.date
df['Hora'] = df['Inicio Estado'].dt.time

# Convertir duración a segundos (si viene como timedelta)
if not np.issubdtype(df['Duración'].dtype, np.number):
    df['Duración'] = pd.to_timedelta(df['Duración'], errors='coerce').dt.total_seconds()

# Definir horarios esperados por agente
horarios_esperados = {
    "Jonathan Alejandro Zúñiga": time(12, 0),
    "Jesús Armando Arrambide": time(8, 0),
    "Maria Teresa Loredo Morales": time(10, 0),
    "Jorge Cesar Flores Rivera": time(8, 0),
}

# Filtros por rango de fechas y agentes
min_fecha = df['Fecha'].min()
max_fecha = df['Fecha'].max()

st.sidebar.header("Filtros")
fecha_inicio, fecha_fin = st.sidebar.date_input(
    "Rango de fechas",
    value=(min_fecha, max_fecha),
    min_value=min_fecha,
    max_value=max_fecha
)

agentes_unicos = df['Agente'].dropna().unique().tolist()
agentes_seleccionados = st.sidebar.multiselect(
    "Selecciona agentes",
    options=agentes_unicos,
    default=agentes_unicos
)

# Aplicar filtros
df_filtrado = df[
    (df['Fecha'] >= fecha_inicio) & (df['Fecha'] <= fecha_fin) &
    (df['Agente'].isin(agentes_seleccionados))
]

if df_filtrado.empty:
    st.warning("No hay datos para el rango y agentes seleccionados.")
    st.stop()

# Obtener el primer "Logged In" del día
logged_in = df_filtrado[df_filtrado['Estado'].str.lower() == 'logged in']
primer_logged = logged_in.sort_values(by='Inicio Estado').groupby(['Agente', 'Fecha']).first().reset_index()

# Asegurar que la hora esté limpia
def fix_hora(h):
    if pd.isnull(h):
        return None
    try:
        if isinstance(h, str):
            return pd.to_datetime(h).time()
        elif isinstance(h, pd.Timestamp):
            return h.time()
        elif isinstance(h, time):
            return h
    except Exception:
        return None
    return None

primer_logged['Hora'] = primer_logged['Hora'].apply(fix_hora)

# Determinar si hay retraso
def es_retraso(row):
    esperado = horarios_esperados.get(row['Agente'], time(8, 0))
    hora = row['Hora']
    if isinstance(hora, time):
        return hora > esperado
    return False

primer_logged['Retraso'] = primer_logged.apply(es_retraso, axis=1)

# Calcular tiempo por estado
tiempo_por_estado = df_filtrado.groupby(['Agente', 'Fecha', 'Estado'])['Duración'].sum().reset_index()

# Mostrar resultados
st.subheader("Primer 'Logged In' del día y retrasos")
st.dataframe(primer_logged[['Agente', 'Fecha', 'Hora', 'Retraso']])

st.subheader("Tiempo total por estado")
tiempo_pivot = tiempo_por_estado.pivot_table(index=['Agente', 'Fecha'], columns='Estado', values='Duración', fill_value=0)
st.dataframe(tiempo_pivot)

st.subheader("Resumen de retrasos")
resumen_retrasos = primer_logged.groupby('Agente')['Retraso'].sum().reset_index()
resumen_retrasos.columns = ['Agente', 'Días con retraso']
st.dataframe(resumen_retrasos)

# Gráfico: tiempo total invertido por estado (suma total por agente)
tiempo_estado_sum = tiempo_por_estado.groupby(['Estado'])['Duración'].sum().sort_values(ascending=False)

st.subheader("Tiempo total invertido por estado (segundos)")
st.bar_chart(tiempo_estado_sum)
