import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Análisis de Estados de Agentes", layout="wide")
st.title("📊 Análisis de Estados de Agentes")

# Leer archivo
archivo = "Estadosinfo.xlsx"
df = pd.read_excel(archivo)

# Limpiar columnas
df.columns = df.columns.str.strip()

# Validar columnas
columnas_esperadas = ['Agent Name', 'State Transition Time', 'Agent State', 'Reason', 'Duration']
if not all(col in df.columns for col in columnas_esperadas):
    st.error("El archivo no contiene todas las columnas necesarias.")
    st.stop()

# Renombrar
df = df.rename(columns={
    'Agent Name': 'Agente',
    'State Transition Time': 'FechaHora',
    'Agent State': 'Estado',
    'Reason': 'Motivo',
    'Duration': 'Duración'
})

# Procesar fechas y duración
df['FechaHora'] = pd.to_datetime(df['FechaHora'])
df['Fecha'] = df['FechaHora'].dt.date
df['Hora'] = df['FechaHora'].dt.time
df['Duración'] = pd.to_timedelta(df['Duración'])
df['DuraciónHoras'] = df['Duración'].dt.total_seconds() / 3600

# Filtros en barra lateral
with st.sidebar:
    st.header("Filtros")
    agentes_unicos = df['Agente'].sort_values().unique()
    agente_seleccionado = st.selectbox("Selecciona un agente", options=np.insert(agentes_unicos, 0, "Todos"))
    
    fechas_min, fechas_max = df['Fecha'].min(), df['Fecha'].max()
    rango_fechas = st.date_input("Rango de fechas", (fechas_min, fechas_max), min_value=fechas_min, max_value=fechas_max)

# Aplicar filtros
df_filtrado = df[
    (df['Fecha'] >= rango_fechas[0]) & (df['Fecha'] <= rango_fechas[1])
]

if agente_seleccionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Agente'] == agente_seleccionado]

# Calcular primer Logged In por agente y fecha
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

def es_retraso(row):
    esperado = horarios.get(row['Agente'], 8)
    return row['FechaHora'].hour >= esperado

primer_logged['Retraso'] = primer_logged.apply(es_retraso, axis=1)

# Tiempo por estado por agente y fecha
tiempo_por_estado = df_filtrado.groupby(['Agente', 'Fecha', 'Estado'])['DuraciónHoras'].sum().reset_index()
tiempo_pivot = tiempo_por_estado.pivot_table(index=['Agente', 'Fecha'], columns='Estado', values='DuraciónHoras', fill_value=0).reset_index()

# Resumen total por agente
resumen_agente = df_filtrado.groupby('Agente')['DuraciónHoras'].sum().reset_index(name='Total de Horas')
resumen_agente = resumen_agente.sort_values(by='Total de Horas', ascending=False)

# Mostrar tablas
st.subheader("📌 Resumen de tiempo total por agente")
st.dataframe(resumen_agente, use_container_width=True)

st.subheader("🕓 Primer ingreso (Logged In) y retrasos")
st.dataframe(primer_logged[['Agente', 'Fecha', 'Hora Entrada', 'Retraso']], use_container_width=True)

st.subheader("⏱️ Tiempo invertido por estado por día")
st.dataframe(tiempo_pivot, use_container_width=True)

# Gráfica de tiempo por estado (barras)
tiempo_estado = df_filtrado.groupby('Estado')['DuraciónHoras'].sum().reset_index()

fig1 = px.bar(
    tiempo_estado,
    x='Estado',
    y='DuraciónHoras',
    title='⏳ Tiempo total por Estado',
    text='DuraciónHoras',
    labels={'DuraciónHoras': 'Horas'}
)
fig1.update_traces(texttemplate='%{text:.2f}', textposition='outside')
fig1.update_layout(yaxis_title='Horas', xaxis_title='Estado', uniformtext_minsize=8, uniformtext_mode='hide')
st.plotly_chart(fig1, use_container_width=True)

# Gráfica de motivos por estado
motivos = df_filtrado.groupby(['Estado', 'Motivo'])['DuraciónHoras'].sum().reset_index()
fig2 = px.bar(
    motivos,
    x='Estado',
    y='DuraciónHoras',
    color='Motivo',
    title='🎯 Tiempo por Motivo dentro de cada Estado',
    text='DuraciónHoras'
)
fig2.update_traces(texttemplate='%{text:.2f}', textposition='outside')
fig2.update_layout(barmode='stack', xaxis_title='Estado', yaxis_title='Horas')
st.plotly_chart(fig2, use_container_width=True)

# Gráfica de pastel por estado
tiempo_total_por_estado = df_filtrado.groupby('Estado')['DuraciónHoras'].sum().reset_index()
fig3 = px.pie(
    tiempo_total_por_estado,
    names='Estado',
    values='DuraciónHoras',
    title='📊 Distribución porcentual de tiempo por Estado',
    hole=0.4
)
fig3.update_traces(textposition='inside', textinfo='percent+label')
st.plotly_chart(fig3, use_container_width=True)

# Tabla con porcentajes
tiempo_total = tiempo_total_por_estado['DuraciónHoras'].sum()
tiempo_total_por_estado['Porcentaje'] = (tiempo_total_por_estado['DuraciónHoras'] / tiempo_total) * 100

st.subheader("📈 Porcentaje de tiempo por estado")
st.dataframe(
    tiempo_total_por_estado[['Estado', 'DuraciónHoras', 'Porcentaje']].rename(columns={
        'DuraciónHoras': 'Horas Totales',
        'Porcentaje': 'Porcentaje (%)'
    }).sort_values(by='Horas Totales', ascending=False),
    use_container_width=True
)
