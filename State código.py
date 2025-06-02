import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Análisis de Estados de Agentes", layout="wide")
st.title("📊 Análisis de Estados de Agentes")

# Cargar datos
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

# Convertir columnas
df['FechaHora'] = pd.to_datetime(df['FechaHora'])
df['Fecha'] = df['FechaHora'].dt.date
df['Duración'] = pd.to_timedelta(df['Duración'])
df['DuraciónHoras'] = df['Duración'].dt.total_seconds() / 3600

# Sidebar: filtro rango fechas
min_fecha = df['Fecha'].min()
max_fecha = df['Fecha'].max()
rango_fechas = st.sidebar.date_input("Selecciona rango de fechas", [min_fecha, max_fecha])

if len(rango_fechas) != 2:
    st.warning("Selecciona un rango válido de dos fechas.")
    st.stop()

# Filtrar por fechas
df_fecha = df[(df['Fecha'] >= rango_fechas[0]) & (df['Fecha'] <= rango_fechas[1])]

# Sidebar: filtro agente basado en datos filtrados por fecha
agentes = sorted(df_fecha['Agente'].dropna().unique())

if not agentes:
    st.warning("No hay agentes con datos en el rango de fechas seleccionado.")
    st.stop()

agente_seleccionado = st.sidebar.selectbox("Selecciona un agente", agentes)

# Filtrar por agente
df_filtrado = df_fecha[df_fecha['Agente'] == agente_seleccionado]

if df_filtrado.empty:
    st.warning("No hay datos para el agente y rango de fechas seleccionados.")
    st.stop()

# ----------- Resumen tiempo por estado -----------
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

# ----------- Resumen tiempo por motivo -----------
resumen_motivo = df_filtrado.groupby('Motivo')['DuraciónHoras'].sum().reset_index()
resumen_motivo = resumen_motivo.sort_values(by='DuraciónHoras', ascending=False)

st.subheader(f"📋 Tiempo invertido por motivo para {agente_seleccionado}")
st.dataframe(resumen_motivo, use_container_width=True)

fig_bar_motivo = px.bar(resumen_motivo, x='Motivo', y='DuraciónHoras',
                       title='Horas invertidas por motivo',
                       labels={'DuraciónHoras':'Horas'})
fig_bar_motivo.update_layout(xaxis_tickangle=-45)
st.plotly_chart(fig_bar_motivo, use_container_width=True)
