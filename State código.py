import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Análisis de Estados de Agentes", layout="wide")
st.title("📊 Análisis de Estados de Agentes")

# Carga de datos
archivo = "Estadosinfo.xlsx"
df = pd.read_excel(archivo)

# Normalizar columnas y renombrar
df.columns = df.columns.str.strip()
df = df.rename(columns={
    'Agent Name': 'Agente',
    'State Transition Time': 'FechaHora',
    'Agent State': 'Estado',
    'Reason': 'Motivo',
    'Duration': 'Duración'
})

# Convertir columnas fecha y duración
df['FechaHora'] = pd.to_datetime(df['FechaHora'])
df['Fecha'] = df['FechaHora'].dt.date
df['Duración'] = pd.to_timedelta(df['Duración'])
df['DuraciónHoras'] = df['Duración'].dt.total_seconds() / 3600

# Sidebar: filtro rango fechas
min_fecha = df['Fecha'].min()
max_fecha = df['Fecha'].max()
fecha_seleccion = st.sidebar.date_input("Selecciona rango de fechas", [min_fecha, max_fecha])

if len(fecha_seleccion) != 2:
    st.warning("Por favor selecciona un rango válido de dos fechas.")
    st.stop()

# Sidebar: filtro agente (todos los agentes en el dataset, sin filtrar aún)
lista_agentes = sorted(df['Agente'].dropna().unique())
agente_seleccionado = st.sidebar.selectbox("Selecciona un agente", lista_agentes)

# Filtrar datos según agente y rango fechas
df_filtrado = df[
    (df['Agente'] == agente_seleccionado) &
    (df['Fecha'] >= fecha_seleccion[0]) &
    (df['Fecha'] <= fecha_seleccion[1])
]

if df_filtrado.empty:
    st.warning("No hay datos para el agente y rango de fechas seleccionados.")
    st.stop()

# Mostrar resumen por Estado
resumen_estado = df_filtrado.groupby('Estado')['DuraciónHoras'].sum().reset_index()
resumen_estado['Porcentaje'] = 100 * resumen_estado['DuraciónHoras'] / resumen_estado['DuraciónHoras'].sum()
resumen_estado = resumen_estado.sort_values(by='Porcentaje', ascending=False)

st.subheader(f"⏱️ Tiempo invertido por estado para {agente_seleccionado}")
st.dataframe(resumen_estado, use_container_width=True)

fig_bar_estado = px.bar(resumen_estado, x='Estado', y='DuraciónHoras',
                       title='Horas invertidas por estado',
                       labels={'DuraciónHoras':'Horas'})
st.plotly_chart(fig_bar_estado, use_container_width=True)

fig_pie_estado = px.pie(resumen_estado, names='Estado', values='Porcentaje',
                       title='Distribución porcentual de tiempo por estado')
st.plotly_chart(fig_pie_estado, use_container_width=True)

# Mostrar resumen por Motivo
resumen_motivo = df_filtrado.groupby('Motivo')['DuraciónHoras'].sum().reset_index()
resumen_motivo = resumen_motivo.sort_values(by='DuraciónHoras', ascending=False)

st.subheader(f"📋 Tiempo invertido por motivo para {agente_seleccionado}")
st.dataframe(resumen_motivo, use_container_width=True)

fig_bar_motivo = px.bar(resumen_motivo, x='Motivo', y='DuraciónHoras',
                       title='Horas invertidas por motivo',
                       labels={'DuraciónHoras':'Horas'})
fig_bar_motivo.update_layout(xaxis_tickangle=-45)
st.plotly_chart(fig_bar_motivo, use_container_width=True)
