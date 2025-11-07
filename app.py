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

# --- CONVERSÃO DE TIPOS ---
cols_numericas = ["gmv", "necessidades", "convertidas", "preco"]
for c in cols_numericas:
    df[c] = (
        df[c]
        .astype(str)
        .str.replace("R$", "", regex=False)
        .s
