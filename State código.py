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

# Convertir a datetime
df['Inicio Estado'] = pd.to_datetime(df['Inicio Estado'])
df['Fecha'] = df['Inicio Estado'].dt.date
df['Hora'] = df['Inicio Estado'].dt.time

# Convertir duración a segundos (si viene como timedelta)
if not np.issubdtype(df['Duración'].dtype, np.number):
    df['Duración'] = pd.to_timedelta(df['Duración']).dt.total_seconds()

# Definir horarios esperados por agente
horarios_esperados = {
    "Jonathan Alejandro Zúñiga": time(12, 0),
    "Jesús Armando Arrambide": time(8, 0),
    "Maria Teresa Loredo Morales": time(10, 0),
    "Jorge Cesar Flores Rivera": time(8, 0),
}

# Filtros por rango de fechas y agentes
try:
    min_fecha = pd.to_datetime(df['Fecha']).min().date()
    max_fecha = pd.to_datetime(df['Fecha']).max().date()
except Exception as e:
    st.error(f"Error al calcular fechas mínimas o máximas: {e}")
    st.stop()

st.sidebar.header("Filtros")
fecha_inicio, fecha_fin = st.sidebar.date_input(
    "Rango de fechas",
    value=(min_fecha, max_fecha),
    min_value=min_fecha,
    max_value=max_fecha
)

agentes_unicos = df['Agente'].unique().tolist()
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

# Primer "Logged In" por día por agente en datos filtrados
logged_in = df_filtrado[df_filtrado['Estado'].str.lower() == 'logged in']
primer_logged = logged_in.sort_values(by='Inicio Estado').groupby(['Agente', 'Fecha']).first().reset_index()

# Limpieza y aseguramiento tipo datetime.time para la columna 'Hora'
def fix_hora(h):
    if pd.isnull(h):
        return None
    if isinstance(h, pd.Timestamp):
        return h.time()
    if isinstance(h, str):
        try:
            return pd.to_datetime(h).time()
        except:
            return None
    return h

primer_logged['Hora'] = primer_logged['Hora'].apply(fix_hora)

# Función para calcular retraso con manejo de nulos
def es_retraso(row):
    esperado = horarios_esperados.get(row['Agente'], time(8, 0))
    hora = row['Hora']
    if hora is None:
        return False
    return hora > esperado

primer_logged['Retraso'] = primer_logged.apply(es_retraso, axis=1)

# Contabilizar tiempo por estado en datos filtrados
tiempo_por_estado = df_filtrado.groupby(['Agente', 'Fecha', 'Estado'])['Duración'].sum().reset_index()

# Mostrar tablas
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
