import streamlit as st
import pandas as pd

st.title("📍 Desempenho por Região")

df = st.session_state["df_filtrado"]

regioes = df.groupby("regiao", as_index=False).agg({
    "gmv": "sum",
    "necessidades": "sum",
    "convertidas": "sum"
})
regioes["conversao"] = regioes["convertidas"] / regioes["necessidades"]

cols = st.columns(3)

for i, row in regioes.iterrows():
    col = cols[i % 3]
    with col:
        st.metric(
            label=f"{row.regiao}",
            value=f"R${row.gmv:,.0f}",
            delta=f"{row.conversao:.1%}"
        )
