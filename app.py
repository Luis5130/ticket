import streamlit as st
import pandas as pd

st.set_page_config(page_title="Melhor Herói por Bairro", layout="wide")

# -----------------------
# Upload do arquivo
# -----------------------
@st.cache_data
def load_data(uploaded_file):
    return pd.read_excel(uploaded_file)

st.sidebar.title("⚙️ Configurações")
uploaded_file = st.sidebar.file_uploader("Envie a planilha (.xlsx):", type=["xlsx"])

if uploaded_file is None:
    st.warning("Envie uma planilha para iniciar.")
    st.stop()

df = load_data(uploaded_file)

# Renomeando colunas para consistência
df = df.rename(columns={
    "cod_prestador": "Herói",
    "Preço de Hospedagem": "Preco",
})

# Conversão por Herói
df["Conversao"] = df["Convertidas"] / df["Necessidades"]
df["Conversao"] = df["Conversao"].fillna(0)

# -----------------------
# Cálculo do Status de Preço por Bairro
# -----------------------
def calcular_status(df):
    status_list = []
    for bairro, group in df.groupby("Bairro"):

        media_preco = group["Preco"].mean()
        min_preco = group["Preco"].min()
        max_preco = group["Preco"].max()

        for _, row in group.iterrows():

            preco = row["Preco"]
            threshold_low = media_preco * 0.9
            threshold_high = media_preco * 1.1

            if preco == min_preco:
                status = "Mais Barato da Região"
            elif preco == max_preco:
                status = "Mais Caro da Região"
            elif preco < threshold_low:
                status = "Abaixo da Média"
            elif preco > threshold_high:
                status = "Acima da Média"
            else:
                status = "Na Média"

            status_list.append(status)

    df["Status_Preco"] = status_list
    return df

df = calcular_status(df)

# -----------------------
# VISÃO GERAL
# -----------------------
st.title("📍 Visão Geral dos Heróis por Bairro")

agregado = df.groupby("Bairro").agg(
    Total_Herois=("Herói", "nunique"),
    Total_Necessidades=("Necessidades", "sum"),
    Total_Convertidas=("Convertidas", "sum")
).reset_index()

agregado["Conversao_Bairro"] = agregado["Total_Convertidas"] / agregado["Total_Necessidades"]

st.dataframe(agregado)

# -----------------------
# FILTRO DE BAIRRO
# -----------------------
bairro = st.selectbox("Selecione um Bairro:", sorted(df["Bairro"].unique()))

df_bairro = df[df["Bairro"] == bairro]

st.subheader(f"📊 Análise detalhada - {bairro}")

col1, col2 = st.columns(2)

with col1:
    st.metric("Total de Heróis", df_bairro["Herói"].nunique())
    st.metric("Média de Preço", round(df_bairro["Preco"].mean(), 2))

with col2:
    st.metric("Total Necessidades", df_bairro["Necessidades"].sum())
    st.metric("Total Convertidas", df_bairro["Convertidas"].sum())

# Herói com melhor conversão
melhor = df_bairro.sort_values("Conversao", ascending=False).iloc[0]
pior = df_bairro.sort_values("Preco").iloc[0]
caro = df_bairro.sort_values("Preco").iloc[-1]

st.write("### ⭐ Melhor Conversão no Bairro")
st.write(melhor)

st.write("### 💸 Menor Preço no Bairro")
st.write(pior)

st.write("### 🏆 Maior Preço no Bairro")
st.write(caro)

# -----------------------
# GRÁFICO
# -----------------------
st.write("### 📉 Distribuição de Preços")
st.bar_chart(df_bairro.set_index("Herói")["Preco"])

# -----------------------
# TABELA COMPLETA DO BAIRRO
# -----------------------
st.write("### 📄 Todos Heróis do Bairro")
st.dataframe(df_bairro)

# -----------------------
# Aba Geral — Status de Preço
# -----------------------
st.write("## 🧭 Status de Preço - Geral")
st.dataframe(df[["Bairro", "Herói", "Preco", "Status_Preco", "Conversao"]])
