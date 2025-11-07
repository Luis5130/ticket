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
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.strip()
        .replace("", "0")
    )

df[cols_numericas] = df[cols_numericas].apply(pd.to_numeric, errors="coerce").fillna(0)

# --- TAXA DE CONVERSÃO ---
df["conversao"] = (df["convertidas"] / df["necessidades"]).fillna(0)

# --- FILTROS ---
st.sidebar.header("Filtros")

f_uf = st.sidebar.selectbox("UF", ["Todas"] + sorted(df.uf.dropna().unique().tolist()))
if f_uf != "Todas":
    df = df[df.uf == f_uf]

f_cidade = st.sidebar.selectbox("Cidade", ["Todas"] + sorted(df.cidade.dropna().unique().tolist()))
if f_cidade != "Todas":
    df = df[df.cidade == f_cidade]

f_bairro = st.sidebar.selectbox("Bairro", ["Todas"] + sorted(df.bairro.dropna().unique().tolist()))
if f_bairro != "Todas":
    df = df[df.bairro == f_bairro]

# ✅ Guarda para outras páginas
st.session_state["df_filtrado"] = df.copy()

# --- KPIs ---
gmv_total = df.gmv.sum()
nec_total = df.necessidades.sum()
conv_total = df.convertidas.sum()
taxa_conv = conv_total / nec_total if nec_total > 0 else 0
preco_med = df.preco.mean()

st.title("📊 Hero Lens — Visão Geral")

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("GMV", f"R${gmv_total:,.0f}".replace(",", "."))
col2.metric("Necessidades", f"{nec_total:,.0f}".replace(",", "."))
col3.metric("Convertidas", f"{conv_total:,.0f}".replace(",", "."))
col4.metric("Conversão", f"{taxa_conv:.1%}")
col5.metric("Preço Médio Hospedagem", f"R${preco_med:,.0f}".replace(",", "."))

st.markdown("---")

# --- TABELA ---
df_display = df.copy()
df_display["conversao"] = (df_display["conversao"] * 100).round(1).astype(str) + "%"
st.subheader("📍 Detalhamento")
st.dataframe(df_display, use_container_width=True)
