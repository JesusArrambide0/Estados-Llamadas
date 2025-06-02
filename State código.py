import streamlit as st
import pandas as pd
import numpy as np
import io
import plotly.express as px

st.set_page_config(page_title="Análisis de Estados de Agentes", layout="wide")

st.title("📊 Análisis de Estados de Agentes")

archivo = "Estadosinfo.xlsx"
try:
    df = pd.read_excel(archivo)
except FileNotFoundError:
    st.error(f"No se encontró el archivo '{archivo}'. Por favor colócalo en la carpeta del proyecto.")
    st.stop()
except Exception as e:
    st.error(f"Error al leer el archivo: {e}")
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

# Convertir tipos de datos
df['FechaHora'] = pd.to_datetime(df['FechaHora'], errors='coerce')  # convertir errores en NaT
df['Fecha'] = df['FechaHora'].dt.date
df['Hora'] = df['FechaHora'].dt.time

df['Duración'] = pd.to_timedelta(df['Duración'], errors='coerce')
df['DuraciónHoras'] = df['Duración'].dt.total_seconds() / 3600
df['DuraciónHoras'] = df['DuraciónHoras'].fillna(0)

# Filtrar registros Logged In para calcular primer ingreso del día
logged = df[df['Estado'] == 'Logged In'].copy()
logged = logged.dropna(subset=['FechaHora'])  # eliminar filas con FechaHora nula

primer_logged = logged.sort_values(by='FechaHora').groupby(['Agente', 'Fecha']).first().reset_index()
primer_logged['Hora Entrada'] = primer_logged['FechaHora'].dt.time

# Horarios esperados
horarios = {
    'Jonathan Alejandro Zúñiga': 12,
    'Jesús Armando Arrambide': 8,
    'Maria Teresa Loredo Morales': 10,
    'Jorge Cesar Flores Rivera': 8
}

# Función corregida para evitar errores con valores nulos
def es_retraso(row):
    esperado = horarios.get(row['Agente'], 8)
    if pd.isnull(row['FechaHora']):
        return False
    return row['FechaHora'].hour > esperado

primer_logged['Retraso'] = primer_logged.apply(es_retraso, axis=1)
primer_logged['Retraso'] = primer_logged['Retraso'].map({True: 'Sí', False: 'No'})

# Tiempo total por estado por agente y día
tiempo_por_estado = df.groupby(['Agente', 'Fecha', 'Estado'])['DuraciónHoras'].sum().reset_index()
tiempo_pivot = tiempo_por_estado.pivot_table(index=['Agente', 'Fecha'], columns='Estado', values='DuraciónHoras', fill_value=0).reset_index()

# Resumen total de horas por agente
resumen_agente = df.groupby('Agente')['DuraciónHoras'].sum().reset_index(name='Total de Horas')
resumen_agente = resumen_agente.sort_values(by='Total de Horas', ascending=False)

# Mostrar tablas en Streamlit
st.subheader("📌 Resumen de tiempo total por agente")
st.dataframe(resumen_agente, use_container_width=True)

st.subheader("🕓 Primer ingreso (Logged In) y retrasos")
st.dataframe(primer_logged[['Agente', 'Fecha', 'Hora Entrada', 'Retraso']], use_container_width=True)

st.subheader("⏱️ Tiempo invertido por estado por día")
st.dataframe(tiempo_pivot, use_container_width=True)

# Visualizaciones

st.subheader("📊 Visualizaciones")

# Tiempo total invertido por estado
tiempo_estado_total = df.groupby('Estado')['DuraciónHoras'].sum().reset_index()
tiempo_estado_total['DuraciónHoras'] = tiempo_estado_total['DuraciónHoras'].fillna(0)

fig1 = px.bar(
    tiempo_estado_total,
    x='Estado',
    y='DuraciónHoras',
    title='⏳ Tiempo total invertido por estado (horas)',
    labels={'DuraciónHoras': 'Horas', 'Estado': 'Estado'},
    text=tiempo_estado_total['DuraciónHoras'].round(2).astype(str).tolist()
)
fig1.update_traces(textposition='outside')
st.plotly_chart(fig1, use_container_width=True)

# Días con retraso por agente
retrasos_por_agente = primer_logged.groupby('Agente')['Retraso'].apply(lambda x: (x == 'Sí').sum()).reset_index(name='Días con Retraso')
retrasos_por_agente['Días con Retraso'] = retrasos_por_agente['Días con Retraso'].fillna(0)

fig2 = px.bar(
    retrasos_por_agente,
    x='Agente',
    y='Días con Retraso',
    title='⏰ Días con retraso por agente',
    labels={'Días con Retraso': 'Cantidad de días', 'Agente': 'Agente'},
    text=retrasos_por_agente['Días con Retraso'].astype(str).tolist()
)
fig2.update_traces(textposition='outside')
st.plotly_chart(fig2, use_container_width=True)

# Botón para descargar Excel con resultados
buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
    resumen_agente.to_excel(writer, index=False, sheet_name='Resumen Total')
    primer_logged[['Agente', 'Fecha', 'Hora Entrada', 'Retraso']].to_excel(writer, index=False, sheet_name='Primer Logged In')
    tiempo_pivot.to_excel(writer, index=False, sheet_name='Tiempo por Estado')
    buffer.seek(0)

st.download_button(
    label="📥 Descargar resumen en Excel",
    data=buffer,
    file_name="Resumen_Estados_Agentes.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
