import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(layout="wide")

# --- Cargar archivo ---
st.title("Análisis de Estados de Agentes")

uploaded_file = st.file_uploader("Carga el archivo Excel", type=["xlsx"])
if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # --- Normalización de columnas ---
    df.columns = df.columns.str.strip()
    df = df.rename(columns={
        "Agent Name": "Agente",
        "State Transition Time": "Inicio",
        "Agent State": "Estado",
        "Reason": "Motivo",
        "Duration": "Duración"
    })
    df["Inicio"] = pd.to_datetime(df["Inicio"])
    df["Duración"] = pd.to_timedelta(df["Duración"], unit="s")
    df["Fin"] = df["Inicio"] + df["Duración"]

    # --- Filtros por fecha y agente ---
    agentes = df["Agente"].unique()
    col1, col2 = st.columns(2)
    with col1:
        fecha_inicio = st.date_input("Fecha inicial", value=df["Inicio"].min().date())
    with col2:
        fecha_fin = st.date_input("Fecha final", value=df["Inicio"].max().date())
    agente_seleccionado = st.multiselect("Filtrar por agente", agentes, default=list(agentes))

    df_filtrado = df[
        (df["Inicio"].dt.date >= fecha_inicio) &
        (df["Inicio"].dt.date <= fecha_fin) &
        (df["Agente"].isin(agente_seleccionado))
    ]

    # --- Retrasos ---
    horarios_esperados = {
        "Jonathan Alejandro Zúñiga": datetime.strptime("12:00", "%H:%M").time(),
        "Jesús Armando Arrambide": datetime.strptime("08:00", "%H:%M").time(),
        "Maria Teresa Loredo Morales": datetime.strptime("10:00", "%H:%M").time(),
        "Jorge Cesar Flores Rivera": datetime.strptime("08:00", "%H:%M").time()
    }

    primer_logged = df_filtrado[df_filtrado["Estado"].str.lower().str.contains("logged")].sort_values("Inicio").groupby("Agente").first().reset_index()

    def evaluar_retraso(row):
        esperado = horarios_esperados.get(row["Agente"])
        if esperado:
            return row["Inicio"].time() > esperado
        return False

    primer_logged["Retraso"] = primer_logged.apply(evaluar_retraso, axis=1)

    # --- Estados productivos ---
    estados_productivos = ["Ready", "Reserved", "Working"]
    df_filtrado["Productivo"] = df_filtrado["Estado"].isin(estados_productivos)

    # --- Análisis de productividad ---
    productividad = df_filtrado[df_filtrado["Productivo"]].groupby("Agente")["Duración"].sum().reset_index()
    productividad["Horas Efectivas"] = productividad["Duración"].dt.total_seconds() / 3600
    productividad = productividad[["Agente", "Horas Efectivas"]]

    # --- Análisis porcentual de estados ---
    estado_total = df_filtrado.groupby("Estado")["Duración"].sum()
    estado_porcentaje = (estado_total / estado_total.sum()).sort_values(ascending=False)
    estado_porcentaje_df = estado_porcentaje.reset_index()
    estado_porcentaje_df["%"] = estado_porcentaje_df["Duración"].dt.total_seconds() / estado_total.sum().total_seconds() * 100

    # --- Ausencias (sin log-in) ---
    agentes_con_retraso = primer_logged["Agente"].tolist()
    ausentes = set(agente_seleccionado) - set(agentes_con_retraso)

    # --- Gráfica de estados ---
    fig1 = px.bar(
        df_filtrado.groupby(["Agente", "Estado"])["Duración"].sum().dt.total_seconds().reset_index(),
        x="Agente", y="Duración", color="Estado", barmode="stack",
        title="Distribución de Estados por Agente",
        labels={"Duración": "Segundos"}
    )
    fig1.update_traces(texttemplate="%{y}", textposition="inside")

    # --- Gráfica de motivos ---
    fig2 = px.bar(
        df_filtrado.groupby("Motivo")["Duración"].sum().dt.total_seconds().sort_values(ascending=False).reset_index(),
        x="Motivo", y="Duración", title="Motivos más frecuentes",
        labels={"Duración": "Segundos"}
    )
    fig2.update_traces(texttemplate="%{y}", textposition="outside")

    # --- Línea de tiempo tipo Gantt ---
    fig_gantt = px.timeline(
        df_filtrado,
        x_start="Inicio", x_end="Fin", y="Agente", color="Estado", title="Línea de Tiempo de Estados"
    )
    fig_gantt.update_yaxes(autorange="reversed")

    # --- Mostrar gráficas y tablas ---
    st.plotly_chart(fig1, use_container_width=True)
    st.plotly_chart(fig2, use_container_width=True)
    st.plotly_chart(fig_gantt, use_container_width=True)

    st.subheader("Retrasos Detectados")
    st.dataframe(primer_logged[["Agente", "Inicio", "Retraso"]].style.applymap(
        lambda val: "background-color: yellow" if val is True else "", subset=["Retraso"]
    ))

    st.subheader("Horas Efectivas Trabajadas")
    st.dataframe(productividad)

    st.subheader("Porcentaje de Tiempo por Estado")
    st.dataframe(estado_porcentaje_df[["Estado", "%"]].round(2))

    if ausentes:
        st.warning(f"Agentes sin log-in en este periodo: {', '.join(ausentes)}")
else:
    st.info("Por favor sube un archivo Excel para comenzar.")
