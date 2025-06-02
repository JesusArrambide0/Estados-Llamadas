import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Análisis de Estados de Agentes", layout="wide")
st.title("📊 Análisis de Estados de Agentes")

# Cargar datos
archivo = "Estadosinfo.xlsx"
df = pd.read_excel(archivo)
df.columns = df.columns.str.strip()

# Validar columnas
columnas_esperadas = ['Agent Name', 'State Transition Time', 'Agent State', 'Reason', 'Duration']
if not all(col in df.columns for col in columnas_esperadas):
    st.error("❌ El archivo no contiene todas las columnas necesarias.")
    st.stop()

# Renombrar columnas
df = df.rename(columns={
    'Agent Name': 'Agente',
    'State Transition Time': 'FechaHora',
    'Agent State': 'Estado',
    'Reason': 'Motivo',
    'Duration': 'Duración'
})

# Transformar datos
df['FechaHora'] = pd.to_datetime(df['FechaHora'])
df['Fecha'] = df['FechaHora'].dt.date
df['Duración'] = pd.to_timedelta(df['Duración'])
df['DuraciónHoras'] = df['Duración'].dt.total_seconds() / 3600

# Filtros
with st.sidebar:
    st.header("Filtros")

    # Rango de fechas
    fechas_disponibles = sorted(df['Fecha'].unique())
    fecha_inicio = st.date_input("📅 Fecha inicio", min_value=min(fechas_disponibles), max_value=max(fechas_disponibles), value=min(fechas_disponibles))
    fecha_fin = st.date_input("📅 Fecha fin", min_value=min(fechas_disponibles), max_value=max(fechas_disponibles), value=max(fechas_disponibles))

    # Filtro de agente
    agentes = df['Agente'].unique()
    agente_seleccionado = st.selectbox("👤 Selecciona un agente", options=['Todos'] + sorted(agentes.tolist()))

# Aplicar filtros
df_filtrado = df[(df['Fecha'] >= fecha_inicio) & (df['Fecha'] <= fecha_fin)]
if agente_seleccionado != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['Agente'] == agente_seleccionado]

# Cálculo de primer ingreso ("Logged In")
logged = df_filtrado[df_filtrado['Estado'] == 'Logged In']
primer_logged = logged.sort_values(by='FechaHora').groupby(['Agente', 'Fecha']).first().reset_index()
primer_logged['Hora Entrada'] = primer_logged['FechaHora'].dt.time

# Reglas de horario esperado
horarios = {
    'Jonathan Alejandro Zúñiga': 8,
    'Jesús Armando Arrambide': 8,
    'Maria Teresa Loredo Morales': 10,
    'Jorge Cesar Flores Rivera': 8
}

# Calcular retraso
primer_logged['Hora Esperada'] = primer_logged['Agente'].map(horarios).fillna(8)
primer_logged['Retraso'] = primer_logged['FechaHora'].dt.hour >= primer_logged['Hora Esperada']

# Tiempo por estado por día
tiempo_por_estado = df_filtrado.groupby(['Agente', 'Fecha', 'Estado'])['DuraciónHoras'].sum().reset_index()
tiempo_pivot = tiempo_por_estado.pivot_table(index=['Agente', 'Fecha'], columns='Estado', values='DuraciónHoras', fill_value=0).reset_index()

# Resumen general
resumen_agente = df_filtrado.groupby('Agente')['DuraciónHoras'].sum().reset_index(name='Total de Horas')
resumen_agente = resumen_agente.sort_values(by='Total de Horas', ascending=False)

# Motivos por estado
motivos = df_filtrado.groupby(['Estado', 'Motivo'])['DuraciónHoras'].sum().reset_index()

# Mostrar tablas
st.subheader("📌 Tiempo total por agente")
st.dataframe(resumen_agente, use_container_width=True)

st.subheader("🕓 Primer ingreso y retrasos")
st.dataframe(primer_logged[['Agente', 'Fecha', 'Hora Entrada', 'Hora Esperada', 'Retraso']], use_container_width=True)

st.subheader("⏱️ Tiempo invertido por estado por día")
st.dataframe(tiempo_pivot, use_container_width=True)

# Gráfica de tiempo por estado
st.subheader("📊 Distribución de tiempo por estado")
fig1 = px.bar(
    df_filtrado.groupby('Estado')['DuraciónHoras'].sum().reset_index(),
    x='Estado', y='DuraciónHoras', text='DuraciónHoras',
    title="Horas acumuladas por estado",
    color='Estado'
)
fig1.update_traces(texttemplate='%{text:.2f}', textposition='outside')
fig1.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
st.plotly_chart(fig1, use_container_width=True)

# Gráfica de motivos
st.subheader("📌 Distribución de motivos por estado")
fig2 = px.bar(
    motivos,
    x='Motivo', y='DuraciónHoras', color='Estado',
    title="Motivos dentro de cada estado", text='DuraciónHoras'
)
fig2.update_traces(texttemplate='%{text:.2f}', textposition='outside')
fig2.update_layout(xaxis_tickangle=-45)
st.plotly_chart(fig2, use_container_width=True)

# Análisis porcentual de tiempo por estado
st.subheader("📈 Análisis porcentual del tiempo por estado")
total_tiempo = df_filtrado['DuraciónHoras'].sum()
porcentaje_estado = df_filtrado.groupby('Estado')['DuraciónHoras'].sum().reset_index()
porcentaje_estado['Porcentaje'] = (porcentaje_estado['DuraciónHoras'] / total_tiempo * 100).round(2)
st.dataframe(porcentaje_estado, use_container_width=True)
