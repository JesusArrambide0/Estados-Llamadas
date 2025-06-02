import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Análisis de Estados de Agentes", layout="wide")
st.title("📊 Análisis de Estados de Agentes")

archivo = "Estadosinfo.xlsx"
try:
    df = pd.read_excel(archivo)
except FileNotFoundError:
    st.error(f"No se encontró el archivo '{archivo}'. Por favor colócalo en la carpeta del proyecto.")
    st.stop()

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

# Procesamiento de fechas y duraciones
df['FechaHora'] = pd.to_datetime(df['FechaHora'], errors='coerce')
df = df.dropna(subset=['FechaHora'])  # eliminar registros inválidos
df['Fecha'] = df['FechaHora'].dt.date
df['Hora'] = df['FechaHora'].dt.time

df['Duración'] = pd.to_timedelta(df['Duración'], errors='coerce')
df['DuraciónHoras'] = df['Duración'].dt.total_seconds() / 3600
df['DuraciónHoras'] = df['DuraciónHoras'].fillna(0)

# Filtro de fechas
min_fecha = df['Fecha'].min()
max_fecha = df['Fecha'].max()

st.sidebar.header("📅 Filtro de fechas")
fecha_inicio, fecha_fin = st.sidebar.date_input(
    "Selecciona el rango de fechas",
    value=[min_fecha, max_fecha],
    min_value=min_fecha,
    max_value=max_fecha
)

# Aplicar filtro
df = df[(df['Fecha'] >= fecha_inicio) & (df['Fecha'] <= fecha_fin)]

# Calcular primer Logged In
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
    if pd.isnull(row['FechaHora']):
        return False
    return row['FechaHora'].hour > esperado

primer_logged['Retraso'] = primer_logged.apply(es_retraso, axis=1)
primer_logged['Retraso'] = primer_logged['Retraso'].map({True: 'Sí', False: 'No'})

# Tiempo por estado
tiempo_por_estado = df.groupby(['Agente', 'Fecha', 'Estado'])['DuraciónHoras'].sum().reset_index()
tiempo_pivot = tiempo_por_estado.pivot_table(index=['Agente', 'Fecha'], columns='Estado', values='DuraciónHoras', fill_value=0).reset_index()

# Tiempo total por agente
resumen_agente = df.groupby('Agente')['DuraciónHoras'].sum().reset_index(name='Total de Horas')
resumen_agente = resumen_agente.sort_values(by='Total de Horas', ascending=False)

# Motivos por duración
tiempo_por_motivo = df.groupby('Motivo')['DuraciónHoras'].sum().reset_index()
tiempo_por_motivo = tiempo_por_motivo[tiempo_por_motivo['Motivo'].notna()]
tiempo_por_motivo = tiempo_por_motivo.sort_values(by='DuraciónHoras', ascending=False)

# Mostrar resultados
st.subheader("📌 Resumen de tiempo total por agente")
st.dataframe(resumen_agente, use_container_width=True)

st.subheader("🕓 Primer ingreso (Logged In) y retrasos")
st.dataframe(primer_logged[['Agente', 'Fecha', 'Hora Entrada', 'Retraso']], use_container_width=True)

st.subheader("⏱️ Tiempo invertido por estado por día")
st.dataframe(tiempo_pivot, use_container_width=True)

# Visualizaciones
st.subheader("📊 Visualizaciones")

# Gráfico 1: Tiempo total por estado
tiempo_estado_total = df.groupby('Estado')['DuraciónHoras'].sum().reset_index()
tiempo_estado_total['DuraciónHoras'] = tiempo_estado_total['DuraciónHoras'].fillna(0)

fig1 = px.bar(
    tiempo_estado_total,
    x='Estado',
    y='DuraciónHoras',
    title='⏳ Tiempo total invertido por estado (horas)',
    labels={'DuraciónHoras': 'Horas', 'Estado': 'Estado'},
    text=tiempo_estado_total['DuraciónHoras'].round(2).astype(str)
)
fig1.update_traces(textposition='outside')
st.plotly_chart(fig1, use_container_width=True)

# Gráfico 2: Días con retraso por agente
retrasos_por_agente = primer_logged.groupby('Agente')['Retraso'].apply(lambda x: (x == 'Sí').sum()).reset_index(name='Días con Retraso')

fig2 = px.bar(
    retrasos_por_agente,
    x='Agente',
    y='Días con Retraso',
    title='⏰ Días con retraso por agente',
    labels={'Días con Retraso': 'Cantidad de días', 'Agente': 'Agente'},
    text=retrasos_por_agente['Días con Retraso'].astype(str)
)
fig2.update_traces(textposition='outside')
st.plotly_chart(fig2, use_container_width=True)

# Gráfico 3: Tiempo por motivo
st.subheader("📋 Tiempo total por motivo de estado")
fig3 = px.bar(
    tiempo_por_motivo,
    x='Motivo',
    y='DuraciónHoras',
    title='🔍 Tiempo total invertido por motivo',
    labels={'DuraciónHoras': 'Horas', 'Motivo': 'Motivo'},
    text=tiempo_por_motivo['DuraciónHoras'].round(2).astype(str)
)
fig3.update_layout(xaxis_tickangle=-45)
fig3.update_traces(textposition='outside')
st.plotly_chart(fig3, use_container_width=True)
