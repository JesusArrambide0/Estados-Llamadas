import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
from datetime import datetime

st.set_page_config(layout="wide")

st.title("📊 Panel de Análisis de Estados de Agentes")

uploaded_file = st.file_uploader("Carga el archivo Excel", type=["xlsx"])
if uploaded_file:
    df = pd.read_excel(uploaded_file)

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

    agentes = df["Agente"].unique()
    col1, col2 = st.columns(2)
    with col1:
        fecha_inicio = st.date_input("📅 Fecha inicial", value=df["Inicio"].min().date())
    with col2:
        fecha_fin = st.date_input("📅 Fecha final", value=df["Inicio"].max().date())

    agente_seleccionado = st.multiselect("👥 Selecciona agente(s)", agentes, default=list(agentes))

    df_filtrado = df[
        (df["Inicio"].dt.date >= fecha_inicio) &
        (df["Inicio"].dt.date <= fecha_fin) &
        (df["Agente"].isin(agente_seleccionado))
    ]

    if df_filtrado.empty:
        st.warning("No hay datos disponibles con los filtros aplicados.")
        st.stop()

    # ---------- Cálculo de retrasos ----------
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

    # Ausentes
    agentes_presentes = primer_logged["Agente"].tolist()
    ausentes = set(agente_seleccionado) - set(agentes_presentes)

    # ---------- Cálculo de productividad ----------
    df_filtrado["Productivo"] = df_filtrado["Estado"].isin(["Ready", "Reserved", "Working"])
    productividad = df_filtrado[df_filtrado["Productivo"]].groupby("Agente")["Duración"].sum().reset_index()
    productividad["Horas Efectivas"] = productividad["Duración"].dt.total_seconds() / 3600
    productividad = productividad[["Agente", "Horas Efectivas"]]

    # ---------- Porcentaje por estado ----------
    estado_total = df_filtrado.groupby("Estado")["Duración"].sum()
    estado_porcentaje = (estado_total / estado_total.sum()).sort_values(ascending=False)
    estado_porcentaje_df = estado_porcentaje.reset_index()
    estado_porcentaje_df["%"] = estado_porcentaje_df["Duración"].dt.total_seconds() / estado_total.sum().total_seconds() * 100

    # ---------- Gráficas ----------
    grafica_estados = px.bar(
        df_filtrado.groupby(["Agente", "Estado"])["Duración"].sum().dt.total_seconds().reset_index(),
        x="Agente", y="Duración", color="Estado", barmode="stack",
        labels={"Duración": "Segundos"}, title="📌 Distribución de Estados por Agente"
    )
    grafica_estados.update_traces(texttemplate="%{y}", textposition="inside")

    grafica_motivos = px.bar(
        df_filtrado.groupby("Motivo")["Duración"].sum().dt.total_seconds().sort_values(ascending=False).reset_index(),
        x="Motivo", y="Duración", title="📌 Duración por Motivo", labels={"Duración": "Segundos"}
    )
    grafica_motivos.update_traces(texttemplate="%{y}", textposition="outside")

    grafica_gantt = px.timeline(
        df_filtrado,
        x_start="Inicio", x_end="Fin", y="Agente", color="Estado", title="⏱️ Línea de Tiempo de Estados"
    )
    grafica_gantt.update_yaxes(autorange="reversed")

    # ---------- Tabs ----------
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Vista General", "⏰ Retrasos y Ausencias", "📊 Gráficas", "📈 Productividad"])

    with tab1:
        st.markdown("### Datos filtrados")
        st.dataframe(df_filtrado)

    with tab2:
        st.markdown("### 🕒 Primer Logged-in y retrasos")
        st.dataframe(
            primer_logged[["Agente", "Inicio", "Retraso"]].style.applymap(
                lambda val: "background-color: yellow" if val is True else "", subset=["Retraso"]
            )
        )
        if ausentes:
            st.warning(f"⚠️ Agentes sin log-in en el periodo: {', '.join(ausentes)}")

    with tab3:
        st.plotly_chart(grafica_estados, use_container_width=True)
        st.plotly_chart(grafica_motivos, use_container_width=True)
        st.plotly_chart(grafica_gantt, use_container_width=True)

    with tab4:
        st.markdown("### 🧠 Horas efectivas trabajadas")
        st.dataframe(productividad)

        st.markdown("### 🧮 Distribución porcentual por estado")
        st.dataframe(estado_porcentaje_df[["Estado", "%"]].round(2))

else:
    st.info("📎 Carga un archivo para comenzar el análisis.")
