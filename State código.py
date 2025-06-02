import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Análisis de Estados de Agentes", layout="wide")
st.title("📊 Análisis de Estados de Agentes")

# Leer el archivo
archivo = "Estadosinfo.xlsx"
df = pd.read_excel(archivo)
df.columns = df.columns.str.strip()

# Validar columnas necesarias
columnas_esperadas = ['Agent Name', 'State Transition Time', 'Agent State', 'Reason', 'Duration']
if not all(col in df.columns for col in columnas_esperadas):
    st.error("El archivo no contiene todas las columnas necesarias.")
    st.stop()

# Renombrar columnas
df = df.rename(columns={
    'Agent Name': 'Agente',
    'State Transition Time': 'FechaHora',
    'Agent State': 'Estado',
    'Reason': 'Motivo',
    'Duration': 'Duración'
})

# Convertir columnas
df['FechaHora'] = pd.to_datetime(df['FechaHora'])
df['Fecha'] = df['FechaHora'].dt.date
df['Hora'] = df['FechaHora'].dt.time
df['Duración'] = pd.to_timedelta(df['Duración'], errors='coerce')
df['DuraciónHoras'] = df['Duración'].dt.total_seconds() / 3600

# Filtros en sidebar
with st.sidebar:
    st.header("Filtros")
    fechas = st.date_input("📅 Rango de Fechas", [df['Fecha'].min(), df['Fecha'].max()])
    agentes_disponibles = df['Agente'].unique().tolist()
    agente_sel = st.selectbox("👤 Selecciona un agente", options=["Todos"] + agentes_disponibles)

# Aplicar filtros
df_filtrado = df.copy()
df_filtrado = df_filtrado[(df_filtrado['Fecha'] >= fechas[0]) & (df_filtrado['Fecha'] <= fechas[1])]
if agente_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Agente'] == agente_sel]

# Resumen de horas totales
resumen_agente = df_filtrado.groupby('Agente')['DuraciónHoras'].sum().reset_index(name='Total de Horas')
resumen_agente = resumen_agente.sort_values(by='Total de Horas', ascending=False)

st.subheader("📌 Tiempo Total por Agente")
st.dataframe(resumen_agente, use_container_width=True)

# Tiempo por estado y motivo
tiempo_por_estado = df_filtrado.groupby(['Agente', 'Fecha', 'Estado'])['DuraciónHoras'].sum().reset_index()
pivot_estado = tiempo_por_estado.pivot_table(index=['Agente', 'Fecha'], columns='Estado', values='DuraciónHoras', fill_value=0).reset_index()

st.subheader("⏱️ Tiempo Invertido por Estado")
st.dataframe(pivot_estado, use_container_width=True)

# Gráfica de barras por estado
st.subheader("📊 Distribución de tiempo por estado")
fig1 = px.bar(
    df_filtrado.groupby('Estado')['DuraciónHoras'].sum().reset_index(),
    x='Estado', y='DuraciónHoras',
    title='Duración total por Estado',
    labels={'DuraciónHoras': 'Horas'},
    color='Estado'
)
st.plotly_chart(fig1, use_container_width=True)

# Gráfica de motivos por estado
st.subheader("📈 Motivos registrados por Estado")
fig2 = px.bar(
    df_filtrado.groupby(['Estado', 'Motivo'])['DuraciónHoras'].sum().reset_index(),
    x='Motivo', y='DuraciónHoras', color='Estado',
    title="Motivos por Estado",
    labels={'DuraciónHoras': 'Horas'}
)
st.plotly_chart(fig2, use_container_width=True)

# Concentrado porcentual por estado
st.subheader("📌 Porcentaje de tiempo por estado")
total_horas = df_filtrado['DuraciónHoras'].sum()
porcentaje_estado = (
    df_filtrado.groupby('Estado')['DuraciónHoras'].sum()
    .reset_index()
    .assign(Porcentaje=lambda x: round((x['DuraciónHoras'] / total_horas) * 100, 2))
)
st.dataframe(porcentaje_estado, use_container_width=True)

# Análisis de retrasos
st.subheader("⏰ Análisis de retrasos")

# Filtrar sólo "Logged In"
logged = df_filtrado[df_filtrado['Estado'] == 'Logged In'].copy()
logged['Fecha'] = pd.to_datetime(logged['FechaHora']).dt.date
logged['HoraEntrada'] = pd.to_datetime(logged['FechaHora']).dt.time

# Primer ingreso por agente y fecha
primer_logged = logged.sort_values(by='FechaHora').groupby(['Agente', 'Fecha']).first().reset_index()

# Límites de entrada por agente
horarios_esperados = {
    'Jonathan Alejandro Zúñiga': pd.to_datetime('12:00').time(),
    'Jesús Armando Arrambide': pd.to_datetime('08:00').time(),
    'Maria Teresa Loredo Morales': pd.to_datetime('10:00').time(),
    'Jorge Cesar Flores Rivera': pd.to_datetime('08:00').time()
}

def es_retraso(row):
    hora_limite = horarios_esperados.get(row['Agente'])
    if hora_limite is None:
        return None
    return row['HoraEntrada'] > hora_limite

primer_logged['Retraso'] = primer_logged.apply(es_retraso, axis=1)

# Contar días con retraso
retrasos_por_agente = (
    primer_logged.groupby('Agente')['Retraso']
    .agg(['sum', 'count'])
    .rename(columns={'sum': 'Días con Retraso', 'count': 'Días Evaluados'})
)
retrasos_por_agente['% Días con Retraso'] = (retrasos_por_agente['Días con Retraso'] / retrasos_por_agente['Días Evaluados']) * 100

# Mostrar tabla
st.dataframe(retrasos_por_agente.reset_index(), use_container_width=True)
