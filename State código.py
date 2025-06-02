import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Análisis de Estados de Agentes", layout="wide")

st.title("📊 Análisis de Estados de Agentes")

# --- Carga de datos ---
archivo = "Estadosinfo.xlsx"
df = pd.read_excel(archivo)

# Normalizar nombres de columnas
df.columns = df.columns.str.strip()

# Validar columnas necesarias
columnas_esperadas = ['Agent Name', 'State Transition Time', 'Agent State', 'Reason', 'Duration']
if not all(col in df.columns for col in columnas_esperadas):
    st.error("El archivo no contiene todas las columnas necesarias.")
    st.stop()

# Renombrar columnas para facilitar manejo
df = df.rename(columns={
    'Agent Name': 'Agente',
    'State Transition Time': 'FechaHora',
    'Agent State': 'Estado',
    'Reason': 'Motivo',
    'Duration': 'Duración'
})

# Convertir columnas de fechas y tiempo
df['FechaHora'] = pd.to_datetime(df['FechaHora'])
df['Fecha'] = df['FechaHora'].dt.date
df['Hora'] = df['FechaHora'].dt.time
df['Duración'] = pd.to_timedelta(df['Duración'])
df['DuraciónHoras'] = df['Duración'].dt.total_seconds() / 3600

# Filtros de fecha
fecha_min = df['Fecha'].min()
fecha_max = df['Fecha'].max()

st.sidebar.header("Filtros")
fecha_inicio, fecha_fin = st.sidebar.date_input(
    "Rango de fechas",
    [fecha_min, fecha_max],
    min_value=fecha_min,
    max_value=fecha_max
)

# Filtro de agentes
agentes = df['Agente'].unique()
agentes_seleccionados = st.sidebar.multiselect("Selecciona agente(s)", agentes, default=list(agentes))

# Aplicar filtros
df_filtrado = df[
    (df['Fecha'] >= fecha_inicio) &
    (df['Fecha'] <= fecha_fin) &
    (df['Agente'].isin(agentes_seleccionados))
].copy()

if df_filtrado.empty:
    st.warning("No hay datos para los filtros seleccionados.")
    st.stop()

# Calcular primer Logged In por agente y fecha
logged = df_filtrado[df_filtrado['Estado'] == 'Logged In'].copy()
primer_logged = logged.sort_values(by='FechaHora').groupby(['Agente', 'Fecha']).first().reset_index()
primer_logged['Hora Entrada'] = primer_logged['FechaHora'].dt.time

# Horarios esperados
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
tiempo_por_estado = df_filtrado.groupby(['Agente', 'Fecha', 'Estado'])['DuraciónHoras'].sum().reset_index()

# Pivot para tiempo por estado
tiempo_pivot = tiempo_por_estado.pivot_table(
    index=['Agente', 'Fecha'],
    columns='Estado',
    values='DuraciónHoras',
    fill_value=0
).reset_index()

# Resumen general de horas totales por agente
resumen_agente = df_filtrado.groupby('Agente')['DuraciónHoras'].sum().reset_index(name='Total de Horas')
resumen_agente = resumen_agente.sort_values(by='Total de Horas', ascending=False)

# Motivos de estados - sumatoria de duración
motivos_agg = df_filtrado.groupby('Motivo')['DuraciónHoras'].sum().reset_index().sort_values(by='DuraciónHoras', ascending=False)

# --- Visualizaciones ---

st.subheader("📌 Resumen de tiempo total por agente")
st.dataframe(resumen_agente, use_container_width=True)

st.subheader("🕓 Primer ingreso (Logged In) y retrasos")
st.dataframe(primer_logged[['Agente', 'Fecha', 'Hora Entrada', 'Retraso']], use_container_width=True)

st.subheader("⏱️ Tiempo invertido por estado por día")
st.dataframe(tiempo_pivot, use_container_width=True)

# Gráfica tiempo por estado
fig1 = px.bar(
    tiempo_por_estado,
    x='Fecha',
    y='DuraciónHoras',
    color='Estado',
    barmode='stack',
    facet_col='Agente',
    title='⏱️ Tiempo invertido por estado (por día y agente)',
    labels={'DuraciónHoras': 'Horas'}
)
fig1.update_traces(texttemplate='%{y:.2f}', textposition='inside')
st.plotly_chart(fig1, use_container_width=True)

# Gráfica motivos
fig2 = px.bar(
    motivos_agg,
    x='Motivo',
    y='DuraciónHoras',
    title='Motivos de los estados - duración total',
    labels={'DuraciónHoras': 'Horas'},
    text='DuraciónHoras'
)
fig2.update_traces(texttemplate='%{text:.2f} hrs', textposition='outside')
fig2.update_layout(xaxis_tickangle=-45)
st.plotly_chart(fig2, use_container_width=True)

# --- Análisis adicional: productividad y ausencias ---

# Definir estados productivos y no productivos
estados_productivos = ['Ready', 'Logged In']
estados_no_productivos = ['Not Working', 'Reserved', 'Logout']

df_filtrado['Tipo Estado'] = np.where(df_filtrado['Estado'].isin(estados_productivos), 'Productivo', 'No Productivo')

# Tiempo total productivo y no productivo por agente
tiempo_productividad = df_filtrado.groupby(['Agente', 'Tipo Estado'])['DuraciónHoras'].sum().reset_index()

fig_productividad = px.bar(
    tiempo_productividad,
    x='Agente',
    y='DuraciónHoras',
    color='Tipo Estado',
    barmode='group',
    title='⏳ Tiempo Productivo vs No Productivo por Agente',
    text='DuraciónHoras'
)
fig_productividad.update_traces(texttemplate='%{text:.2f} hrs', textposition='outside')
st.plotly_chart(fig_productividad, use_container_width=True)

# Análisis de ausencias (tiempo no productivo)
ausencias = df_filtrado[df_filtrado['Tipo Estado'] == 'No Productivo']

ausencias_agg = ausencias.groupby('Agente').agg(
    Cantidad_Ausencias=('Estado', 'count'),
    Duracion_Ausencias_Horas=('DuraciónHoras', 'sum')
).reset_index()

st.subheader("🚨 Ausencias y tiempos inactivos por agente")
st.dataframe(ausencias_agg, use_container_width=True)

fig_ausencias = px.bar(
    ausencias_agg,
    x='Agente',
    y='Duracion_Ausencias_Horas',
    text='Duracion_Ausencias_Horas',
    title='Duración total de ausencias (estados no productivos) por agente'
)
fig_ausencias.update_traces(texttemplate='%{text:.2f} hrs', textposition='outside')
st.plotly_chart(fig_ausencias, use_container_width=True)
