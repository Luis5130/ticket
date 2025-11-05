import streamlit as st
import pandas as pd

st.set_page_config(page_title="Dash Melhor Herói", layout="wide")

@st.cache_data
def load_data(uploaded_file):
    df = pd.read_excel(uploaded_file)
    df.rename(columns={
        "Preço de Hospedagem": "Preco",
        "Necessidades": "Necessidades",
        "Convertidas": "Convertidas"
    }, inplace=True)

    # Garantir número
    df["Preco"] = pd.to_numeric(df["Preco"], errors="coerce")
    df["Necessidades"] = pd.to_numeric(df["Necessidades"], errors="coerce")
    df["Convertidas"] = pd.to_numeric(df["Convertidas"], errors="coerce")

    # Conversão
    df["Conversao"] = df["Convertidas"] / df["Necessidades"]
    df["Conversao"].fillna(0, inplace=True)

    return df

def calcular_status(df):
    resultados = []

    for bairro, group in df.groupby("Bairro"):
        media_preco = group["Preco"].mean()
        max_preco = group["Preco"].max()
        min_preco = group["Preco"].min()

        # Melhor herói = quem tem mais convertidas, empatou → maior conversão
        melhor = group.sort_values(["Convertidas", "Conversao"], ascending=[False, False]).iloc[0]

        # Status de Preço desse melhor
        if melhor["Preco"] == max_preco:
            status = "Mais Caro do Bairro"
        elif melhor["Preco"] == min_preco:
            status = "Mais Barato do Bairro"
        elif melhor["Preco"] > media_preco * 1.10:
            status = "Acima da Média"
        elif melhor["Preco"] < media_preco * 0.90:
            status = "Abaixo da Média"
        else:
            status = "Na Média"

        resultados.append({
            "Bairro": bairro,
            "Herói": melhor["Herói"] if "Herói" in melhor else melhor["cod_prestador"],
            "Cidade": melhor["Cidade"] if "Cidade" in melhor else "",
            "Necessidades": melhor["Necessidades"],
            "Convertidas": melhor["Convertidas"],
            "Conversão (%)": round(melhor["Conversao"] * 100, 1),
            "Preço": melhor["Preco"],
            "Status de Preço": status
        })

    return pd.DataFrame(resultados)

uploaded_file = st.file_uploader("📂 Envie a planilha", type=["xlsx"])

if uploaded_file:
    df = load_data(uploaded_file)
    resultado = calcular_status(df)

    st.markdown("## ⭐ Heróis com Melhor Conversão (por Bairro)")
    st.dataframe(resultado, use_container_width=True)

    # Gráfico Status
    st.markdown("### 📊 Status de Preço entre os Melhores Convertidos")
    graf = resultado.groupby("Status de Preço").size().reset_index(name="Qtd")
    st.bar_chart(graf, x="Status de Preço", y="Qtd")
