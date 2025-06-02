import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Análisis de Estados de Agentes", layout="wide")
st.title("📊 Análisis de Estados de Agentes")

# Cargar archivo Excel
archivo = "Estadosinfo.xlsx"
df = pd.read_excel(archivo)
df.columns = df.columns.str.strip()

# Renombrar columnas para facilitar el trabajo
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
df['Duración'] = pd.to_timedelta(df['Duración'])
df['DuraciónHoras'] = df['Duración'].dt.total_seconds() / 3600

# Sidebar: filtros
st.sidebar.header("Filtros")
fecha_min = df['Fecha'].min()
fecha_max = df['Fecha'].max()

fecha_inicio, fecha_fin = st.sidebar.date_input(
    "Rango de fechas",
    value=(fecha_min, fecha_max),
    min_value=fecha_min,
    max_value=fecha_max
)

agentes = sorted(df['Agente'].dropna().unique())
agentes_seleccionados = st.sidebar.multiselect(
    "Selecciona uno o varios agentes",
    options=agentes,
    default=agentes  # todos seleccionados por defecto
)

# Validar selección
if not agentes_seleccionados:
    st.warning("Por favor, selecciona al menos un agente para mostrar los datos.")
    st.stop()

# Filtrar datos
df_filtrado = df[
    (df['Agente'].isin(agentes_seleccionados)) &
    (df['Fecha'] >= fecha_inicio) &
    (df['Fecha'] <= fecha_fin)
]

# Mostrar datos filtrados
st.subheader(f"Datos filtrados para agentes: {', '.join(agentes_seleccionados)}\nDel {fecha_inicio} al {fecha_fin}")
st.dataframe(df_filtrado[['Agente', 'FechaHora', 'Estado', 'Motivo', 'DuraciónHoras']], use_container_width=True)

# Análisis porcentual tiempo por Estado
total_horas = df_filtrado['DuraciónHoras'].sum()
if total_horas > 0:
    porcentaje_estado = (
        df_filtrado.groupby('Estado')['DuraciónHoras'].sum() / total_horas * 100
    ).reset_index().sort_values(by='DuraciónHoras', ascending=False)
    porcentaje_estado = porcentaje_estado.rename(columns={'DuraciónHoras': 'Porcentaje (%)'})

    st.subheader("📊 Porcentaje de tiempo invertido por Estado")
    st.dataframe(porcentaje_estado, use_container_width=True)

    # Gráfica pie interactiva
    fig_pie = px.pie(
        porcentaje_estado,
        names='Estado',
        values='Porcentaje (%)',
        title='Distribución porcentual del tiempo por Estado'
    )
    st.plotly_chart(fig_pie, use_container_width=True)

    # Gráfica barras horas totales por Estado
    st.subheader("📈 Horas totales por Estado")
    total_horas_estado = df_filtrado.groupby('Estado')['DuraciónHoras'].sum().reset_index()
    fig_bar = px.bar(
        total_horas_estado,
        x='Estado',
        y='DuraciónHoras',
        title='Horas totales por Estado',
        labels={'DuraciónHoras': 'Horas'}
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # Horas trabajadas por día
    st.subheader("🗓️ Horas trabajadas por día")
    horas_por_dia = df_filtrado.groupby('Fecha')['DuraciónHoras'].sum().reset_index()
    fig_line = px.bar(
        horas_por_dia,
        x='Fecha',
        y='DuraciónHoras',
        title='Horas trabajadas por día',
        labels={'DuraciónHoras': 'Horas'}
    )
    st.plotly_chart(fig_line, use_container_width=True)

    # Análisis de motivos
    st.subheader("🔍 Distribución de motivos (Reason)")
    motivos_conteo = df_filtrado['Motivo'].value_counts().reset_index()
    motivos_conteo.columns = ['Motivo', 'Conteo']
    motivos_conteo['Porcentaje (%)'] = (motivos_conteo['Conteo'] / motivos_conteo['Conteo'].sum()) * 100
    st.dataframe(motivos_conteo, use_container_width=True)

    fig_motivos = px.bar(
        motivos_conteo,
        x='Motivo',
        y='Conteo',
        title='Conteo de motivos',
        labels={'Conteo': 'Cantidad'},
        text='Porcentaje (%)'
    )
    fig_motivos.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    st.plotly_chart(fig_motivos, use_container_width=True)
else:
    st.info("No hay datos suficientes para mostrar análisis con los filtros seleccionados.")
