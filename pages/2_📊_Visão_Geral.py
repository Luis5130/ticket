import streamlit as st

st.title("📊 Visão Geral")
df = st.session_state["df_filtrado"]

st.write("Dados filtrados:")
st.dataframe(df)
