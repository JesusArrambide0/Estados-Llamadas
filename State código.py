import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Análisis de Estados de Agentes", layout="wide")
st.title("📊 Análisis de Estados de Agentes")

# Carga archivo
archivo = "Estadosinfo.xlsx"
df = pd.read_excel(archivo)
df.columns = df.columns.str.strip()

# Renombrar columnas para facilitar
df = df.rename(columns={
    'Agent Name': 'Agente',
    'State Transition Time': 'FechaHora',
    'Agent State': 'Estado',
    'Reason': 'Motivo',
    'Duration': 'Duración'
})

# Convertir datos
df['FechaHora'] = pd.to_datetime(df['FechaHora'])
df['Fecha'] = df['FechaHora'].dt.date
df['Duración'] = pd.to_timedelta(df['Duración'])
df['DuraciónHoras'] = df['Duración'].dt.total_seconds() / 3600

# Filtros en sidebar
st.sidebar.header("Filtros")
fecha_min = df['Fecha'].min()
fecha_max = df['Fecha'].max()

fecha_inicio, fecha_fin = st.sidebar.date_input(
    "Rango de fechas",
    value=(fecha_min, fecha_max),
    min_value=fecha_min,
    max_value=fecha_max
)

agentes = df['Agente'].dropna().unique()
agente_seleccionado = st.sidebar.selectbox("Selecciona un agente", agentes)

# Filtrar por agente y rango de fechas
df_filtrado = df[
    (df['Agente'] == agente_seleccionado) &
    (df['Fecha'] >= fecha_inicio) &
    (df['Fecha'] <= fecha_fin)
]

# Mostrar datos filtrados
st.subheader(f"Datos filtrados para agente: {agente_seleccionado} del {fecha_inicio} al {fecha_fin}")
st.dataframe(df_filtrado[['FechaHora', 'Estado', 'Motivo', 'DuraciónHoras']], use_container_width=True)

# Concentrado porcentual de tiempo por Estado
total_horas = df_filtrado['DuraciónHoras'].sum()
if total_horas > 0:
    porcentaje_estado = (
        df_filtrado.groupby('Estado')['DuraciónHoras'].sum() / total_horas * 100
    ).reset_index().sort_values(by='DuraciónHoras', ascending=False)
    porcentaje_estado = porcentaje_estado.rename(columns={'DuraciónHoras': 'Porcentaje (%)'})

    st.subheader("📊 Concentrado porcentual de tiempo invertido por Estado")
    st.dataframe(porcentaje_estado, use_container_width=True)

    # Gráfica de pastel interactiva
    fig_pie = px.pie(
        porcentaje_estado,
        names='Estado',
        values='Porcentaje (%)',
        title='Distribución porcentual del tiempo por Estado'
    )
    st.plotly_chart(fig_pie, use_container_width=True)
else:
    st.write("No hay datos suficientes para mostrar el concentrado de tiempos.")

