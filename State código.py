import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Análisis de Estados de Agentes", layout="wide")
st.title("📊 Análisis de Estados de Agentes")

# Cargar datos
archivo = "Estadosinfo.xlsx"
df = pd.read_excel(archivo)

# Limpiar y renombrar columnas
df.columns = df.columns.str.strip()
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
df['Duración'] = pd.to_timedelta(df['Duración'])
df['DuraciónHoras'] = df['Duración'].dt.total_seconds() / 3600

# Filtros en la barra lateral
st.sidebar.header("📅 Filtros")

# Filtro de fechas
min_fecha = df['Fecha'].min()
max_fecha = df['Fecha'].max()
rango_fechas = st.sidebar.date_input("Rango de fechas", (min_fecha, max_fecha))

# Filtrar por rango de fechas
df_filtrado = df[(df['Fecha'] >= rango_fechas[0]) & (df['Fecha'] <= rango_fechas[1])]

# Filtro de agente (después de filtrar por fechas)
agentes = sorted(df_filtrado['Agente'].dropna().unique())
agente_seleccionado = st.sidebar.selectbox("👤 Selecciona un agente", options=agentes)

# Filtrar por agente seleccionado
df_filtrado = df_filtrado[df_filtrado['Agente'] == agente_seleccionado]

# Calcular primer "Logged In"
logged = df_filtrado[df_filtrado['Estado'] == 'Logged In'].copy()
primer_logged = logged.sort_values(by='FechaHora').groupby(['Agente', 'Fecha']).first().reset_index()
primer_logged['Hora Entrada'] = primer_logged['FechaHora'].dt.time

# Reglas de horario esperado
horarios = {
    'Jonathan Alejandro Zúñiga': 12,
    'Jesús Armando Arrambide': 8,
    'Maria Teresa Loredo Morales': 10,
    'Jorge Cesar Flores Rivera': 8
}

# Verificar retraso
def es_retraso(row):
    esperado = horarios.get(row['Agente'], 8)
    return row['FechaHora'].hour >= esperado

if not primer_logged.empty:
    primer_logged['Retraso'] = primer_logged.apply(es_retraso, axis=1)
else:
    primer_logged['Retraso'] = False

# Tiempo total por estado por día
tiempo_por_estado = df_filtrado.groupby(['Agente', 'Fecha', 'Estado'])['DuraciónHoras'].sum().reset_index()

# Tabla pivote
tiempo_pivot = tiempo_por_estado.pivot_table(
    index=['Agente', 'Fecha'], 
    columns='Estado', 
    values='DuraciónHoras', 
    fill_value=0
).reset_index()

# Resumen general por agente
resumen_agente = df_filtrado.groupby('Agente')['DuraciónHoras'].sum().reset_index(name='Total de Horas')
resumen_agente = resumen_agente.sort_values(by='Total de Horas', ascending=False)

# Mostrar datos
st.subheader("📌 Resumen de tiempo total por agente")
st.dataframe(resumen_agente, use_container_width=True)

st.subheader("🕓 Primer ingreso (Logged In) y retrasos")
if not primer_logged.empty:
    st.dataframe(primer_logged[['Agente', 'Fecha', 'Hora Entrada', 'Retraso']], use_container_width=True)
else:
    st.info("No hay eventos de 'Logged In' para el agente y fechas seleccionadas.")

st.subheader("⏱️ Tiempo invertido por estado por día")
st.dataframe(tiempo_pivot, use_container_width=True)

# Gráfico de motivos
st.subheader("📈 Distribución de motivos de estados")
if df_filtrado['Motivo'].notna().sum() > 0:
    motivo_data = df_filtrado.groupby('Motivo')['DuraciónHoras'].sum().reset_index()
    fig_motivos = px.bar(motivo_data, x='Motivo', y='DuraciónHoras', title="Duración total por motivo de estado")
    st.plotly_chart(fig_motivos, use_container_width=True)
else:
    st.info("No hay motivos registrados para el agente en el rango seleccionado.")
