import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Análisis de Estados de Agentes", layout="wide")
st.title("📊 Análisis de Estados de Agentes")

# Leer el archivo
archivo = "Estadosinfo.xlsx"
df = pd.read_excel(archivo)

# Normalizar nombres de columnas
df.columns = df.columns.str.strip()

# Verificar columnas necesarias
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

# Convertir columnas de fecha y duración
df['FechaHora'] = pd.to_datetime(df['FechaHora'])
df['Fecha'] = df['FechaHora'].dt.date
df['Hora'] = df['FechaHora'].dt.time
df['Duración'] = pd.to_timedelta(df['Duración'], errors='coerce')
df['DuraciónHoras'] = df['Duración'].dt.total_seconds() / 3600

# ----------- 🎯 Filtros en barra lateral -----------
st.sidebar.header("📋 Filtros")

min_fecha = df['Fecha'].min()
max_fecha = df['Fecha'].max()

fecha_inicio, fecha_fin = st.sidebar.date_input(
    "Selecciona el rango de fechas",
    value=(min_fecha, max_fecha),
    min_value=min_fecha,
    max_value=max_fecha
)

df_fecha = df[(df['Fecha'] >= fecha_inicio) & (df['Fecha'] <= fecha_fin)]

agentes_disponibles = sorted(df_fecha['Agente'].dropna().unique())
agente_seleccionado = st.sidebar.selectbox(
    "Selecciona un agente",
    options=agentes_disponibles
)

# Aplicar filtros al DataFrame
df = df_fecha[df_fecha['Agente'] == agente_seleccionado]

# Si no hay datos después de los filtros, mostrar mensaje y detener
if df.empty:
    st.warning("No hay datos para los filtros seleccionados.")
    st.stop()

# Calcular primer "Logged In" del día
logged = df[df['Estado'] == 'Logged In'].copy()
primer_logged = logged.sort_values(by='FechaHora').groupby(['Agente', 'Fecha']).first().reset_index()
primer_logged['Hora Entrada'] = primer_logged['FechaHora'].dt.time

# Reglas de horario esperado
horarios = {
    'Jonathan Alejandro Zúñiga': 12,
    'Jesús Armando Arrambide': 8,
    'Maria Teresa Loredo Morales': 10,
    'Jorge Cesar Flores Rivera': 8
}

def es_retraso(row):
    esperado = horarios.get(row['Agente'], 8)
    return row['FechaHora'].hour >= esperado

primer_logged['Retraso'] = primer_logged.apply(es_retraso, axis=1)

# Tiempo total por estado por agente y día
tiempo_por_estado = df.groupby(['Agente', 'Fecha', 'Estado'])['DuraciónHoras'].sum().reset_index()
tiempo_pivot = tiempo_por_estado.pivot_table(index=['Agente', 'Fecha'], columns='Estado', values='DuraciónHoras', fill_value=0).reset_index()

# Resumen general del agente filtrado
resumen_agente = df.groupby('Agente')['DuraciónHoras'].sum().reset_index(name='Total de Horas')
resumen_agente = resumen_agente.sort_values(by='Total de Horas', ascending=False)

# ----------- 📋 Mostrar información ------------------
st.subheader("📌 Resumen de tiempo total del agente")
st.dataframe(resumen_agente, use_container_width=True)

st.subheader("🕓 Primer ingreso (Logged In) y retrasos")
st.dataframe(primer_logged[['Agente', 'Fecha', 'Hora Entrada', 'Retraso']], use_container_width=True)

st.subheader("⏱️ Tiempo invertido por estado por día")
st.dataframe(tiempo_pivot, use_container_width=True)

# ----------- 📊 Gráfica de motivos --------------------
st.subheader("📈 Distribución de motivos por estado")

motivos_estado = df.groupby(['Estado', 'Motivo'])['DuraciónHoras'].sum().reset_index()
fig = px.bar(
    motivos_estado,
    x='Motivo',
    y='DuraciónHoras',
    color='Estado',
    title=f"Motivos registrados por estado - {agente_seleccionado}",
    labels={'DuraciónHoras': 'Horas acumuladas'},
    barmode='group'
)
st.plotly_chart(fig, use_container_width=True)
