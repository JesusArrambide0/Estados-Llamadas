import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Análisis de Estados de Agentes", layout="wide")

st.title("📊 Análisis de Estados de Agentes")

# Leer el archivo desde la misma carpeta
archivo = "Estadosinfo.xlsx"
df = pd.read_excel(archivo)

# Normalizar nombres de columnas
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

# Procesamiento de fechas y duración
df['FechaHora'] = pd.to_datetime(df['FechaHora'])
df['Fecha'] = df['FechaHora'].dt.date
df['Hora'] = df['FechaHora'].dt.time
df['Duración'] = pd.to_timedelta(df['Duración'])
df['DuraciónHoras'] = df['Duración'].dt.total_seconds() / 3600

# ----------- 🎯 Filtros en barra lateral -----------
st.sidebar.header("📋 Filtros")

# Rango de fechas
min_fecha = df['Fecha'].min()
max_fecha = df['Fecha'].max()
fecha_inicio, fecha_fin = st.sidebar.date_input(
    label="Selecciona el rango de fechas",
    value=(min_fecha, max_fecha),
    min_value=min_fecha,
    max_value=max_fecha
)

# Agente
agentes_unicos = sorted(df['Agente'].dropna().unique())
agente_seleccionado = st.sidebar.selectbox(
    "Selecciona un agente",
    options=agentes_unicos
)

# Aplicar filtros
df = df[
    (df['Fecha'] >= fecha_inicio) &
    (df['Fecha'] <= fecha_fin) &
    (df['Agente'] == agente_seleccionado)
]

# ---------- 🔍 Análisis ----------

# Primer Logged In
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

if not primer_logged.empty:
    primer_logged['Retraso'] = primer_logged.apply(es_retraso, axis=1)
else:
    primer_logged['Retraso'] = []

# Tiempo por estado por día
tiempo_por_estado = df.groupby(['Agente', 'Fecha', 'Estado'])['DuraciónHoras'].sum().reset_index()
tiempo_pivot = tiempo_por_estado.pivot_table(index=['Agente', 'Fecha'], columns='Estado', values='DuraciónHoras', fill_value=0).reset_index()

# Resumen total por agente
resumen_agente = df.groupby('Agente')['DuraciónHoras'].sum().reset_index(name='Total de Horas')
resumen_agente = resumen_agente.sort_values(by='Total de Horas', ascending=False)

# ---------- 📋 Mostrar Resultados ----------

st.subheader("📌 Resumen de tiempo total por agente")
st.dataframe(resumen_agente, use_container_width=True)

st.subheader("🕓 Primer ingreso (Logged In) y retrasos")
st.dataframe(primer_logged[['Agente', 'Fecha', 'Hora Entrada', 'Retraso']], use_container_width=True)

st.subheader("⏱️ Tiempo invertido por estado por día")
st.dataframe(tiempo_pivot, use_container_width=True)

# ---------- 🎯 Extra: Motivos más frecuentes ----------
st.subheader("📈 Distribución de motivos de estados")
motivos = df.groupby(['Estado', 'Motivo'])['DuraciónHoras'].sum().reset_index()
st.dataframe(motivos.sort_values(by='DuraciónHoras', ascending=False), use_container_width=True)
