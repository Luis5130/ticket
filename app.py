import streamlit as st
import pandas as pd

st.set_page_config(page_title="Hero Lens", layout="wide")

@st.cache_data
def get_data():
    sheet_id = "1KZeV67DkWe9JDrKm-ijuCuCh42B0oZ0bAIhKUrQfQ-4"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    return pd.read_csv(url)

df = get_data()

# Renomeando colunas
df = df.rename(columns={
    "Região": "regiao",
    "UF": "uf",
    "Cidade": "cidade",
    "Bairro": "bairro",
    "GMV": "gmv",
    "Necessidades": "necessidades",
    "Convertidas": "convertidas",
    "Conversão": "conversao",
    "Preço de Hospedagem": "preco"
})

# Sidebar - Filtros
with st.sidebar:
    st.header("Filtros")
    regiao = st.selectbox("Região", ["Todos"] + sorted(df.regiao.dropna().unique()))
    uf = st.selectbox("UF", ["Todos"] + sorted(df.uf.dropna().unique()))
    cidade = st.selectbox("Cidade", ["Todos"] + sorted(df.cidade.dropna().unique()))
    bairro = st.selectbox("Bairro", ["Todos"] + sorted(df.bairro.dropna().unique()))

# Aplicar filtros
f = df.copy()
if regiao != "Todos": f = f[f.regiao == regiao]
if uf != "Todos": f = f[f.uf == uf]
if cidade != "Todos": f = f[f.cidade == cidade]
if bairro != "Todos": f = f[f.bairro == bairro]

# Guardar dataset filtrado
st.session_state["df_filtrado"] = f

st.title("🐶 Hero Lens")
st.write("Bem-vindo! Navegue pelas páginas no menu lateral.")
