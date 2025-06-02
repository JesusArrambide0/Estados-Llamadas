import streamlit as st
import pandas as pd
import numpy as np

# Título de la app
st.title("Análisis de Estados de Agentes")

# Subida del archivo
archivo = st.file_uploader("Carga el archivo Excel", type=["xlsx"])
if archivo:
    df = pd.read_excel(archivo)

    # Renombrar columnas para facilitar
    df.rename(columns={
        'Agent Name': 'Agente',
        'State Transition Time': 'Inicio',
        'Agent State': 'Estado',
        'Reason': 'Motivo',
        'Duration': 'Duración'
    }, inplace=True)

    # Asegurarnos de que 'Inicio' sea datetime
    df['Inicio'] = pd.to_datetime(df['Inicio'], errors='coerce')

    # Quitar filas con fechas inválidas
    df.dropna(subset=['Inicio'], inplace=True)

    # Crear columna 'Fecha' para agrupar por día
    df['Fecha'] = df['Inicio'].dt.date

    # --------------------
    # Cálculo de Primer Logged In por día
    # --------------------
    primer_logged = df[df['Estado'] == 'Logged In'].groupby(['Agente', 'Fecha'])['Inicio'].min().reset_index()
    primer_logged.rename(columns={'Inicio': 'Hora de Entrada'}, inplace=True)

    # Reglas de horario por agente
    horarios = {
        'Jonathan Alejandro Zúñiga': '12:00',
        'Jesús Armando Arrambide': '08:00',
        'Maria Teresa Loredo Morales': '10:00',
        'Jorge Cesar Flores Rivera': '08:00'
    }

    def es_retraso(row):
        hora_esperada = horarios.get(row['Agente'])
        if not hora_esperada:
            return 'Sin regla'
        hora_esperada_dt = pd.to_datetime(hora_esperada).time()
        return 'Sí' if row['Hora de Entrada'].time() > hora_esperada_dt else 'No'

    primer_logged['Retraso'] = primer_logged.apply(es_retraso, axis=1)

    # Mostrar tabla de entradas
    st.subheader("Primer ingreso del día y retrasos")
    st.dataframe(primer_logged)

    # --------------------
    # Cálculo de tiempos por estado
    # --------------------
    df['Duración'] = pd.to_numeric(df['Duración'], errors='coerce')
    df.dropna(subset=['Duración'], inplace=True)

    tiempo_por_estado = df.groupby(['Agente', 'Fecha', 'Estado'])['Duración'].sum().reset_index()

    tiempo_pivot = tiempo_por_estado.pivot_table(
        index=['Agente', 'Fecha'],
        columns='Estado',
        values='Duración',
        fill_value=0
    ).reset_index()

    st.subheader("Duración total por estado y por día")
    st.dataframe(tiempo_pivot)

    # --------------------
    # Métricas agregadas
    # --------------------
    st.subheader("Métricas generales por agente")
    resumen_agente = tiempo_por_estado.groupby(['Agente', 'Estado'])['Duración'].sum().unstack(fill_value=0)
    st.dataframe(resumen_agente)

    # --------------------
    # Exportar resultados
    # --------------------
    st.download_button(
        label="📥 Descargar resumen por estado (Excel)",
        data=resumen_agente.to_excel(index=True),
        file_name='resumen_estados_agente.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
