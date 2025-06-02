import streamlit as st
import pandas as pd
import numpy as np
import os

# Título de la app
st.title("Análisis de Estados de Agentes")

# Ruta al archivo Excel
archivo = os.path.join(os.path.dirname(__file__), 'Estadosinfo.xlsx')

try:
    df = pd.read_excel(archivo)

    # Renombrar columnas para facilitar el análisis
    df.rename(columns={
        'Agent Name': 'Agente',
        'State Transition Time': 'Inicio',
        'Agent State': 'Estado',
        'Reason': 'Motivo',
        'Duration': 'Duración'
    }, inplace=True)

    # Convertir tipos de datos
    df['Inicio'] = pd.to_datetime(df['Inicio'], errors='coerce')
    df['Duración'] = pd.to_numeric(df['Duración'], errors='coerce')

    # Eliminar filas con valores inválidos
    df.dropna(subset=['Inicio', 'Duración'], inplace=True)

    # Extraer fecha
    df['Fecha'] = df['Inicio'].dt.date

    # ---- Calcular primer "Logged In" por día ----
    primer_logged = df[df['Estado'] == 'Logged In'].groupby(['Agente', 'Fecha'])['Inicio'].min().reset_index()
    primer_logged.rename(columns={'Inicio': 'Hora de Entrada'}, inplace=True)

    # Reglas de horario esperado por agente
    horarios = {
        'Jonathan Alejandro Zúñiga': '12:00',
        'Jesús Armando Arrambide': '08:00',
        'Maria Teresa Loredo Morales': '10:00',
        'Jorge Cesar Flores Rivera': '08:00'
    }

    # Función para evaluar retraso
    def es_retraso(row):
        hora_esperada = horarios.get(row['Agente'])
        if not hora_esperada:
            return 'Sin regla'
        hora_esperada_dt = pd.to_datetime(hora_esperada).time()
        return 'Sí' if row['Hora de Entrada'].time() > hora_esperada_dt else 'No'

    primer_logged['Retraso'] = primer_logged.apply(es_retraso, axis=1)

    st.subheader("Primer ingreso del día y retrasos")
    st.dataframe(primer_logged)

    # ---- Sumar duración total por estado y convertir a horas ----
    tiempo_por_estado = df.groupby(['Agente', 'Fecha', 'Estado'])['Duración'].sum().reset_index()
    tiempo_por_estado['Duración'] = tiempo_por_estado['Duración'] / 3600  # Convertir a horas
    tiempo_por_estado['Duración'] = tiempo_por_estado['Duración'].round(2)

    tiempo_pivot = tiempo_por_estado.pivot_table(
        index=['Agente', 'Fecha'],
        columns='Estado',
        values='Duración',
        fill_value=0
    ).reset_index()

    st.subheader("Duración total por estado (en horas)")
    st.dataframe(tiempo_pivot)

    # ---- Resumen total por agente ----
    resumen_agente = tiempo_por_estado.groupby(['Agente', 'Estado'])['Duración'].sum().unstack(fill_value=0).round(2)

    st.subheader("Resumen general por agente (en horas)")
    st.dataframe(resumen_agente)

    # ---- Botón de descarga ----
    st.download_button(
        label="📥 Descargar resumen general",
        data=resumen_agente.to_excel(index=True),
        file_name='resumen_estados_agente.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

except FileNotFoundError:
    st.error("❌ No se encontró el archivo 'Estadosinfo.xlsx' en la misma carpeta que el script.")
