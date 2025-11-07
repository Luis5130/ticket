import streamlit as st
import pandas as pd

st.title("📍 Desempenho por Região")

# Verifica se df filtrado existe
if "df_filtrado" not in st.session_state:
    st.error("Volte à página inicial e aplique os filtros primeiro.")
    st.stop()

df = st.session_state["df_filtrado"].copy()

# Agrupamento por região
regioes = (
    df.groupby("regiao")
    .agg({
        "gmv": "sum",
        "necessidades": "sum",
        "convertidas": "sum",
        "preco": "mean"
    })
    .reset_index()
)

regioes["conversao"] = regioes["convertidas"] / regioes["necessidades"]
regioes["preco"] = regioes["preco"].fillna(0)

# --- EXIBIÇÃO FORMATADA ---
regioes_display = regioes.copy()
regioes_display["gmv"] = "R$ " + regioes_display["gmv"].round(0).astype(int).astype(str)
regioes_display["preco"] = "R$ " + regioes_display["preco"].round(0).astype(int).astype(str)
regioes_display["conversao"] = (regioes_display["conversao"] * 100).round(1).astype(str) + "%"

st.dataframe(regioes_display, use_container_width=True)
