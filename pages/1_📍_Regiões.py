import streamlit as st
st.title("📍 Desempenho por Região")
df = st.session_state["df_filtrado"]
regioes = df.groupby("regiao", as_index=False).agg({
    "gmv": "sum",
    "necessidades": "sum",
    "convertidas": "sum"
})
regioes["conversao"] = regioes["convertidas"] / regioes["necessidades"]
regioes = regioes.fillna(0)
cols = st.columns(3)
for i, row in regioes.iterrows():
    col = cols[i % 3]
    with col:
        st.metric(
            label=row.regiao,
            value=f"R${row.gmv:,.0f}",
            delta=f"{row.conversao:.1%}"
        )
