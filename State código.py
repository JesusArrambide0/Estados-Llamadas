import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Análisis de Estados de Agentes", layout="wide")

st.title("📊 Análisis de Estados de Agentes")

# Leer el archivo desde la misma carpeta
archivo = "Estadosinfo.xlsx"
df = pd.read_excel(archivo)

# Normalizar nombres de columnas
df.columns = df.columns.str.strip()

# Validar columnas esperadas
columnas_esperadas = ['Agent Name', 'State Transition Time', 'Agent State', 'Reason', 'Duration']
if not all(col in df.columns for col in columnas_esperadas):
    st.error("El archivo no contiene todas las columnas necesarias.")
    st.stop()

# Renombrar columnas para facilitar el trabajo
df = df.rename(columns={
    'Agent Name': 'Agente',
    'State Transition Time': 'FechaHora',
    'Agent State': 'Estado',
    'Reason': 'Motivo',
    'Duration': 'Duración'
})

# Convertir fechas y separar
df['FechaHora'] = pd.to_datetime(df['FechaHora'])
df['Fecha'] = df['FechaHora'].dt.date
df['Hora'] = df['FechaHora'].dt.time

# Convertir duración a horas
df['Duración'] = pd.to_timedelta(df['Duración'])
df['DuraciónHoras'] = df['Duración'].dt.total_seconds() / 3600

# Filtros de fecha
min_fecha = df['Fecha'].min()
max_fecha = df['Fecha'].max()

fecha_inicio, fecha_fin = st.sidebar.date_input("Rango de fechas", [min_fecha, max_fecha], min_value=min_fecha, max_value=max_fecha)

# Filtro de agente (selectbox)
agentes_unicos = sorted(df['Agente'].unique())
agente_seleccionado = st.sidebar.selectbox("Selecciona un agente (opcional)", options=["Todos"] + agentes_unicos)

# Aplicar filtros
df_filtrado = df[(df['Fecha'] >= fecha_inicio) & (df['Fecha'] <= fecha_fin)]
if agente_seleccionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Agente'] == agente_seleccionado]

# Calcular primer Logged In del día por agente
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

# Función para determinar retraso
def es_retraso(row):
    esperado = horarios.get(row['Agente'], 8)
    if pd.isna(row['FechaHora']):
        return False
    return row['FechaHora'].hour >= esperado

if not primer_logged.empty:
    primer_logged['Retraso'] = primer_logged.apply(es_retraso, axis=1)
else:
    st.warning("No se encontraron registros de primer Logged In para los filtros aplicados.")
    primer_logged['Retraso'] = pd.Series(dtype=bool)

# Tiempo total por estado por agente y día
tiempo_por_estado = df_filtrado.groupby(['Agente', 'Fecha', 'Estado'])['DuraciónHoras'].sum().reset_index()

# Tabla pivote para mostrar el tiempo distribuido por estado
tiempo_pivot = tiempo_por_estado.pivot_table(index=['Agente', 'Fecha'], columns='Estado', values='DuraciónHoras', fill_value=0).reset_index()

# Resumen general
resumen_agente = df_filtrado.groupby('Agente')['DuraciónHoras'].sum().reset_index(name='Total de Horas')
resumen_agente = resumen_agente.sort_values(by='Total de Horas', ascending=False)

# Análisis porcentual de tiempo por estado (sobre total)
tiempo_estado_total = df_filtrado.groupby('Estado')['DuraciónHoras'].sum()
total_horas = tiempo_estado_total.sum()
porcentaje_estado = (tiempo_estado_total / total_horas * 100).sort_values(ascending=False).reset_index()
porcentaje_estado.columns = ['Estado', 'Porcentaje de Tiempo']

# Análisis motivos (sumar duración por motivo)
motivos_sum = df_filtrado.groupby('Motivo')['DuraciónHoras'].sum().sort_values(ascending=False).reset_index()

# Productividad y ausencias (definir productividad = tiempo Logged In, ausencia = Not Working)
prod_aus = df_filtrado[df_filtrado['Estado'].isin(['Logged In', 'Not Working'])]
prod_aus_resumen = prod_aus.groupby(['Agente', 'Estado'])['DuraciónHoras'].sum().unstack(fill_value=0).reset_index()

# Mostrar tablas
st.subheader("📌 Resumen de tiempo total por agente")
st.dataframe(resumen_agente, use_container_width=True)

st.subheader("🕓 Primer ingreso (Logged In) y retrasos")
st.dataframe(primer_logged[['Agente', 'Fecha', 'Hora Entrada', 'Retraso']], use_container_width=True)

st.subheader("⏱️ Tiempo invertido por estado por día")
st.dataframe(tiempo_pivot, use_container_width=True)

st.subheader("📊 Porcentaje de tiempo dedicado a cada estado")
st.dataframe(porcentaje_estado, use_container_width=True)

st.subheader("🔍 Análisis de motivos (duración total)")
st.dataframe(motivos_sum, use_container_width=True)

st.subheader("⚙️ Productividad y Ausencias por agente")
st.dataframe(prod_aus_resumen, use_container_width=True)

# Gráfica porcentaje de tiempo por estado con valores numéricos
fig1 = px.bar(porcentaje_estado, x='Estado', y='Porcentaje de Tiempo', text=porcentaje_estado['Porcentaje de Tiempo'].round(2),
              title="Porcentaje de Tiempo dedicado a cada Estado")
fig1.update_traces(textposition='outside')
fig1.update_layout(yaxis_title="Porcentaje (%)", xaxis_title="Estado", uniformtext_minsize=8, uniformtext_mode='hide')
st.plotly_chart(fig1, use_container_width=True)

# Gráfica motivos con valores numéricos
fig2 = px.bar(motivos_sum, x='Motivo', y='DuraciónHoras', text=motivos_sum['DuraciónHoras'].round(2),
              title="Duración Total por Motivo")
fig2.update_traces(textposition='outside')
fig2.update_layout(yaxis_title="Horas", xaxis_title="Motivo", uniformtext_minsize=8, uniformtext_mode='hide')
st.plotly_chart(fig2, use_container_width=True)
