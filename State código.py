import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Análisis de Estados de Agentes", layout="wide")
st.title("📊 Análisis de Estados de Agentes")

# Cargar datos
archivo = "Estadosinfo.xlsx"
df = pd.read_excel(archivo)
df.columns = df.columns.str.strip()

# Verificación de columnas
columnas_necesarias = ['Agent Name', 'State Transition Time', 'Agent State', 'Reason', 'Duration']
if not all(col in df.columns for col in columnas_necesarias):
    st.error("❌ El archivo no contiene todas las columnas necesarias.")
    st.stop()

# Renombrar
df = df.rename(columns={
    'Agent Name': 'Agente',
    'State Transition Time': 'FechaHora',
    'Agent State': 'Estado',
    'Reason': 'Motivo',
    'Duration': 'Duración'
})

# Procesamiento de fechas y duración
df['FechaHora'] = pd.to_datetime(df['FechaHora'])
df['Fecha'] = df['FechaHora'].dt.date
df['Hora'] = df['FechaHora'].dt.time
df['Duración'] = pd.to_timedelta(df['Duración'])
df['DuraciónHoras'] = df['Duración'].dt.total_seconds() / 3600

# Filtros
agentes = df['Agente'].unique()
agente_seleccionado = st.selectbox("👤 Selecciona un agente:", options=np.append(["Todos"], agentes))

fechas = df['Fecha'].sort_values().unique()
fecha_inicio = st.date_input("📅 Fecha inicial:", min_value=min(fechas), value=min(fechas))
fecha_fin = st.date_input("📅 Fecha final:", max_value=max(fechas), value=max(fechas))

df_filtrado = df[(df['Fecha'] >= fecha_inicio) & (df['Fecha'] <= fecha_fin)]
if agente_seleccionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Agente'] == agente_seleccionado]

# Primer Logged-in
primer_logged = df_filtrado[df_filtrado['Estado'].str.lower() == 'logged-in'].copy()
primer_logged = primer_logged.sort_values(by='FechaHora').groupby(['Agente', 'Fecha']).first().reset_index()
primer_logged['Hora Entrada'] = primer_logged['FechaHora'].dt.time

# Reglas de horario esperado
horarios = {
    'Jonathan Alejandro Zúñiga': 12,
    'Jesús Armando Arrambide': 8,
    'Maria Teresa Loredo Morales': 10,
    'Jorge Cesar Flores Rivera': 8
}

def es_retraso(row):
    hora_esperada = horarios.get(row['Agente'], 8)
    return row['FechaHora'].hour >= hora_esperada

if not primer_logged.empty:
    primer_logged['Retraso'] = primer_logged.apply(es_retraso, axis=1)
else:
    st.warning("⚠️ No se encontraron registros de 'Logged-in' para los filtros aplicados.")

# Tiempo por estado
tiempo_estado = df_filtrado.groupby(['Agente', 'Fecha', 'Estado'])['DuraciónHoras'].sum().reset_index()
pivot_tiempo = tiempo_estado.pivot_table(index=['Agente', 'Fecha'], columns='Estado', values='DuraciónHoras', fill_value=0).reset_index()

# Gráfica de tiempo por estado
st.subheader("📊 Tiempo invertido por estado")
fig1 = px.bar(
    tiempo_estado,
    x='Estado',
    y='DuraciónHoras',
    color='Estado',
    text_auto='.2f',
    title='Distribución de tiempo por estado',
)
fig1.update_layout(xaxis_title=None, yaxis_title="Horas")
st.plotly_chart(fig1, use_container_width=True)

# Gráfica de motivos
st.subheader("🎯 Distribución de motivos")
motivos = df_filtrado.groupby('Motivo')['DuraciónHoras'].sum().reset_index().sort_values(by='DuraciónHoras', ascending=False)
fig2 = px.bar(motivos, x='Motivo', y='DuraciónHoras', text_auto='.2f', title='Tiempo por motivo', color='Motivo')
fig2.update_layout(xaxis_title=None, yaxis_title="Horas")
st.plotly_chart(fig2, use_container_width=True)

# Línea de tiempo
st.subheader("🕓 Línea de tiempo de estados")
fig3 = px.timeline(df_filtrado, x_start="FechaHora", x_end=df_filtrado["FechaHora"] + df_filtrado["Duración"],
                   y="Agente", color="Estado", hover_data=["Motivo"])
fig3.update_yaxes(autorange="reversed")
st.plotly_chart(fig3, use_container_width=True)

# Resumen por agente
st.subheader("📌 Resumen total por agente")
resumen = df_filtrado.groupby('Agente')['DuraciónHoras'].sum().reset_index(name='Total Horas')
st.dataframe(resumen, use_container_width=True)

# Primer ingreso con resaltado condicional
if not primer_logged.empty:
    st.subheader("🚦 Primer ingreso y retrasos")
    def resaltar_retraso(val):
        return 'background-color: red; color: white;' if val else ''
    st.dataframe(primer_logged[['Agente', 'Fecha', 'Hora Entrada', 'Retraso']].style.applymap(resaltar_retraso, subset=['Retraso']), use_container_width=True)

# Análisis de % de tiempo por estado
st.subheader("📈 Porcentaje de tiempo dedicado por estado")
estado_pct = df_filtrado.groupby('Estado')['DuraciónHoras'].sum().reset_index()
estado_pct['%'] = (estado_pct['DuraciónHoras'] / estado_pct['DuraciónHoras'].sum()) * 100
st.dataframe(estado_pct[['Estado', 'DuraciónHoras', '%']].sort_values(by='%', ascending=False), use_container_width=True)

# Análisis de productividad (Ready + Reserved)
st.subheader("⚙️ Análisis de productividad y ausencias")
prod_estados = ['Ready', 'Reserved']
df_prod = df_filtrado[df_filtrado['Estado'].isin(prod_estados)]
prod_summary = df_prod.groupby('Agente')['DuraciónHoras'].sum().reset_index(name='Horas Productivas')

# Ausencias
logged_days = df_filtrado.groupby('Agente')['Fecha'].nunique().reset_index(name='Días Conectado')
rango_total_dias = pd.date_range(start=fecha_inicio, end=fecha_fin).nunique()
logged_days['Ausencias'] = rango_total_dias - logged_days['Días Conectado']

# Combinar
productividad = pd.merge(prod_summary, logged_days, on='Agente', how='outer').fillna(0)
st.dataframe(productividad, use_container_width=True)
