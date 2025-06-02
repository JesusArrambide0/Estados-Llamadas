import streamlit as st
import pandas as pd
import numpy as np
from datetime import time

st.title("Análisis de Estados de Agentes")

# Archivo fijo
archivo = 'Estadosinfo.xlsx'
try:
    df = pd.read_excel(archivo)
except Exception as e:
    st.error(f"No se pudo leer el archivo '{archivo}'. Error: {e}")
    st.stop()

# Renombrar columnas por claridad (ajusta según tu Excel)
df = df.rename(columns={
    'Agent Name': 'Agente',
    'State Transition Time': 'Inicio Estado',
    'Agent State': 'Estado',
    'Reason': 'Motivo',
    'Duration': 'Duración'
})

# Validar que las columnas existan
required_cols = ['Agente', 'Inicio Estado', 'Estado', 'Duración']
missing = [col for col in required_cols if col not in df.columns]
if missing:
    st.error(f"Faltan columnas requeridas en el archivo: {missing}")
    st.stop()

# Convertir 'Inicio Estado' a datetime, eliminar filas con error
df['Inicio Estado'] = pd.to_datetime(df['Inicio Estado'], errors='coerce')
df = df.dropna(subset=['Inicio Estado'])

# Crear columna 'Fecha' con solo fecha (sin hora) con tipo datetime64
df['Fecha'] = df['Inicio Estado'].dt.normalize()

# Extraer hora para comparación
df['Hora'] = df['Inicio Estado'].dt.time

# Convertir 'Duración' a segundos si no es numérico
if not np.issubdtype(df['Duración'].dtype, np.number):
    df['Duración'] = pd.to_timedelta(df['Duración'], errors='coerce').dt.total_seconds()
df = df.dropna(subset=['Duración'])

# Definir horarios esperados por agente
horarios_esperados = {
    "Jonathan Alejandro Zúñiga": time(12, 0),
    "Jesús Armando Arrambide": time(8, 0),
    "Maria Teresa Loredo Morales": time(10, 0),
    "Jorge Cesar Flores Rivera": time(8, 0),
}

# Rangos para filtros
min_fecha = df['Fecha'].min()
max_fecha = df['Fecha'].max()

# Sidebar filtros
st.sidebar.header("Filtros")
fecha_inicio, fecha_fin = st.sidebar.date_input(
    "Rango de fechas",
    value=(min_fecha, max_fecha),
    min_value=min_fecha,
    max_value=max_fecha
)

agentes_unicos = sorted(df['Agente'].unique())
agentes_seleccionados = st.sidebar.multiselect(
    "Selecciona agentes",
    options=agentes_unicos,
    default=agentes_unicos
)

# Validar que fecha_inicio <= fecha_fin
if fecha_inicio > fecha_fin:
    st.error("La fecha de inicio no puede ser mayor que la fecha fin.")
    st.stop()

# Filtrar datos
df_filtrado = df[
    (df['Fecha'] >= pd.to_datetime(fecha_inicio)) &
    (df['Fecha'] <= pd.to_datetime(fecha_fin)) &
    (df['Agente'].isin(agentes_seleccionados))
]

if df_filtrado.empty:
    st.warning("No hay datos para el rango y agentes seleccionados.")
    st.stop()

# Filtrar sólo logged in para detectar primer ingreso
logged_in = df_filtrado[df_filtrado['Estado'].str.lower() == 'logged in']

# Primer logged in por agente y fecha
primer_logged = logged_in.sort_values(by='Inicio Estado').groupby(['Agente', 'Fecha']).first().reset_index()

# Agregar columna retraso (True si ingreso después del horario esperado)
def es_retraso(row):
    esperado = horarios_esperados.get(row['Agente'], time(8, 0))
    return row['Hora'] > esperado

primer_logged['Retraso'] = primer_logged.apply(es_retraso, axis=1)

# Calcular tiempo total invertido por estado
tiempo_por_estado = df_filtrado.groupby(['Agente', 'Fecha', 'Estado'])['Duración'].sum().reset_index()

# Pivot para mostrar tiempo por estado
tiempo_pivot = tiempo_por_estado.pivot_table(index=['Agente', 'Fecha'], columns='Estado', values='Duración', fill_value=0)

# Mostrar resultados
st.subheader("Primer 'Logged In' del día y retrasos")
st.dataframe(primer_logged[['Agente', 'Fecha', 'Hora', 'Retraso']])

st.subheader("Tiempo total por estado (segundos)")
st.dataframe(tiempo_pivot)

st.subheader("Resumen de retrasos por agente")
resumen_retrasos = primer_logged.groupby('Agente')['Retraso'].sum().reset_index()
resumen_retrasos.columns = ['Agente', 'Días con retraso']
st.dataframe(resumen_retrasos)

st.subheader("Tiempo total invertido por estado (suma total)")
tiempo_estado_sum = tiempo_por_estado.groupby('Estado')['Duración'].sum().sort_values(ascending=False)
st.bar_chart(tiempo_estado_sum)
