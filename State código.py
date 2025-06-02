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

# Asegurar que las columnas clave existen
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

# Normalizar valores de Estado para evitar problemas con guiones, mayúsculas, espacios, etc.
df['Estado'] = df['Estado'].str.strip().str.lower().str.replace('-', ' ')

# Convertir fechas y obtener la fecha (sin hora)
df['FechaHora'] = pd.to_datetime(df['FechaHora'])
df['Fecha'] = df['FechaHora'].dt.date
df['Hora'] = df['FechaHora'].dt.time

# Convertir duración a horas
df['Duración'] = pd.to_timedelta(df['Duración'])
df['DuraciónHoras'] = df['Duración'].dt.total_seconds() / 3600

# Filtros de usuario
fecha_min = df['Fecha'].min()
fecha_max = df['Fecha'].max()

with st.sidebar:
    st.header("Filtros")
    rango_fechas = st.date_input("Rango de fechas", [fecha_min, fecha_max])
    agentes_disponibles = sorted(df['Agente'].unique())
    agente_seleccionado = st.selectbox("Selecciona un agente", options=["Todos"] + agentes_disponibles)

# Filtrar por fechas
df_filtrado = df[(df['Fecha'] >= rango_fechas[0]) & (df['Fecha'] <= rango_fechas[1])]

# Filtrar por agente si no es "Todos"
if agente_seleccionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Agente'] == agente_seleccionado]

# Reglas de horario esperado
horarios = {
    'Jonathan Alejandro Zúñiga': 12,
    'Jesús Armando Arrambide': 8,
    'Maria Teresa Loredo Morales': 10,
    'Jorge Cesar Flores Rivera': 8
}

# Procesar primer Logged In (recordar que normalizamos estado a minúsculas y sin guion)
logged = df_filtrado[df_filtrado['Estado'] == 'logged in'].copy()

if not logged.empty:
    primer_logged = logged.sort_values(by='FechaHora').groupby(['Agente', 'Fecha']).first().reset_index()
    primer_logged['Hora Entrada'] = primer_logged['FechaHora'].dt.time

    def es_retraso(row):
        esperado = horarios.get(row['Agente'], 8)
        # Retraso si la hora es mayor o igual a la esperada (consideramos la hora entera)
        return row['FechaHora'].hour >= esperado

    primer_logged['Retraso'] = primer_logged.apply(es_retraso, axis=1)

    st.subheader("🕓 Primer ingreso (Logged In) y retrasos")
    st.dataframe(primer_logged[['Agente', 'Fecha', 'Hora Entrada', 'Retraso']], use_container_width=True)
else:
    st.warning("No se encontraron registros de primer Logged In para los filtros aplicados.")

# Tiempo total por estado por agente y día
tiempo_por_estado = df_filtrado.groupby(['Agente', 'Fecha', 'Estado'])['DuraciónHoras'].sum().reset_index()

# Tabla pivote para mostrar el tiempo distribuido por estado
tiempo_pivot = tiempo_por_estado.pivot_table(index=['Agente', 'Fecha'], columns='Estado', values='DuraciónHoras', fill_value=0).reset_index()

st.subheader("⏱️ Tiempo invertido por estado por día")
st.dataframe(tiempo_pivot, use_container_width=True)

# Gráfica tiempo por estado total en el rango (suma para agente o para todos)
tiempo_estado_total = tiempo_por_estado.groupby('Estado')['DuraciónHoras'].sum().reset_index()

fig1 = px.bar(tiempo_estado_total.sort_values(by='DuraciónHoras', ascending=False),
              x='Estado', y='DuraciónHoras',
              title='Tiempo total invertido por Estado',
              text='DuraciónHoras')

fig1.update_traces(texttemplate='%{text:.2f}', textposition='outside')
fig1.update_layout(yaxis_title='Horas', xaxis_title='Estado', uniformtext_minsize=8, uniformtext_mode='hide')
st.plotly_chart(fig1, use_container_width=True)

# Gráfica de motivos más comunes (por duración total)
motivos_total = df_filtrado.groupby('Motivo')['DuraciónHoras'].sum().reset_index().sort_values(by='DuraciónHoras', ascending=False).head(10)

st.subheader("📋 Motivos con mayor tiempo invertido")
fig2 = px.bar(motivos_total, x='Motivo', y='DuraciónHoras', text='DuraciónHoras', title="Top 10 motivos por tiempo invertido")
fig2.update_traces(texttemplate='%{text:.2f}', textposition='outside')
fig2.update_layout(yaxis_title='Horas', xaxis_title='Motivo', uniformtext_minsize=8, uniformtext_mode='hide')
st.plotly_chart(fig2, use_container_width=True)

# Análisis porcentaje tiempo por estado (concentrado)
total_horas = df_filtrado['DuraciónHoras'].sum()
if total_horas > 0:
    porcentaje_estado = tiempo_estado_total.copy()
    porcentaje_estado['Porcentaje'] = (porcentaje_estado['DuraciónHoras'] / total_horas) * 100
    porcentaje_estado = porcentaje_estado.sort_values(by='Porcentaje', ascending=False)
    st.subheader("📊 Porcentaje de tiempo invertido por estado")
    st.dataframe(porcentaje_estado[['Estado', 'DuraciónHoras', 'Porcentaje']].round(2), use_container_width=True)
else:
    st.info("No hay datos para calcular porcentajes de tiempo.")

# Análisis productividad y ausencias (ejemplo simple)
# Definir estados que consideramos productivos
estados_productivos = ['logged in', 'ready', 'reserved']
tiempo_productivo = tiempo_por_estado[tiempo_por_estado['Estado'].isin(estados_productivos)].groupby('Agente')['DuraciónHoras'].sum().reset_index()
tiempo_total_agente = df_filtrado.groupby('Agente')['DuraciónHoras'].sum().reset_index()

productividad = pd.merge(tiempo_productivo, tiempo_total_agente, on='Agente', suffixes=('_productivo', '_total'))
productividad['% Productividad'] = (productividad['DuraciónHoras_productivo'] / productividad['DuraciónHoras_total']) * 100
productividad = productividad.sort_values(by='% Productividad', ascending=False)

st.subheader("🚀 Productividad por agente (%)")
st.dataframe(productividad[['Agente', 'DuraciónHoras_productivo', 'DuraciónHoras_total', '% Productividad']].round(2), use_container_width=True)

# Ausencias: tiempo en estados que no sean productivos (por ejemplo, "not working", "logout", "logged out")
estados_ausencia = ['not working', 'logout', 'logged out']
tiempo_ausente = tiempo_por_estado[tiempo_por_estado['Estado'].isin(estados_ausencia)].groupby('Agente')['DuraciónHoras'].sum().reset_index()
tiempo_ausente = tiempo_ausente.rename(columns={'DuraciónHoras': 'Horas de Ausencia'})

st.subheader("⚠️ Tiempo de ausencia por agente (horas)")
st.dataframe(tiempo_ausente, use_container_width=True)
