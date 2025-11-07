import streamlit as st

st.title("📊 Visão Geral")

df = st.session_state["df_filtrado"]

st.dataframe(df, use_container_width=True)
