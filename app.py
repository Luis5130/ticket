# app.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import BytesIO

st.set_page_config(layout="wide", page_title="Dashboard Heróis por Bairro")

@st.cache_data
def load_data(path="/mnt/data/Planilha sem título.xlsx"):
    df = pd.read_excel(path)
    # Normalizar nomes de colunas para facilitar (sem acento)
    df.columns = [c.strip() for c in df.columns]
    return df

def clean_price_column(series):
    s = series.astype(str).copy()
    s = s.str.replace("R$", "", regex=False)
    s = s.str.replace(".", "", regex=False)  # remove thousand sep if present
    s = s.str.replace(",", ".", regex=False)  # comma to dot
    s = s.str.replace("#REF!", "", regex=False)
    s = s.str.strip()
    return pd.to_numeric(s, errors="coerce")

def compute_flags(df):
    # price numeric
    df["preco_hospedagem_num"] = clean_price_column(df.get("Preço de Hospedagem", df.get("Preço de Hospedagem ", df.columns[-1])))
    # fallback: if there is a column named 'Preço de Hospedagem' with different cases, try to find
    if "preco_hospedagem_num" not in df.columns:
        df["preco_hospedagem_num"] = clean_price_column(df["Preço de Hospedagem"])

    # Ensure necessary numeric columns exist
    if "Necessidades" in df.columns:
        df["necessidades"] = pd.to_numeric(df["Necessidades"], errors="coerce")
    elif "Necessidades " in df.columns:
        df["necessidades"] = pd.to_numeric(df["Necessidades "], errors="coerce")
    if "Convertidas" in df.columns:
        df["convertidas"] = pd.to_numeric(df["Convertidas"], errors="coerce")
    if "Conversão" in df.columns:
        # If already fraction (0-1) keep; if percent string handle
        df["conversao_hero"] = pd.to_numeric(df["Conversão"], errors="coerce")
    else:
        # compute if missing
        df["conversao_hero"] = df["convertidas"] / df["necessidades"]

    # Global min/max price among heroes (used for tagging)
    global_min_price = df["preco_hospedagem_num"].min(skipna=True)
    global_max_price = df["preco_hospedagem_num"].max(skipna=True)
    df["eh_mais_barato_global"] = df["preco_hospedagem_num"] == global_min_price
    df["eh_mais_caro_global"] = df["preco_hospedagem_num"] == global_max_price

    return df

def neighborhood_stats(df):
    # group by Bairro
    grp = df.groupby("Bairro", dropna=False)
    summary = grp.agg(
        total_herois=("cod_prestador", "nunique"),
        total_necessidades=("necessidades", "sum"),
        total_convertidas=("convertidas", "sum"),
        preco_medio_bairro=("preco_hospedagem_num", "mean"),
    ).reset_index()

    # overall conversion for neighborhood
    summary["taxa_conversao_bairro"] = summary["total_convertidas"] / summary["total_necessidades"]
    return summary

def determine_price_status(price, mean_price):
    if pd.isna(price) or pd.isna(mean_price):
        return "Sem Preço"
    low = mean_price * 0.9
    high = mean_price * 1.1
    if price < low:
        return "Abaixo da Média"
    elif price > high:
        return "Acima da Média"
    else:
        return "Na Média"

df_raw = load_data()
df = df_raw.copy()
df = compute_flags(df)

# Prepare neighborhood summary
nb_summary = neighborhood_stats(df)

# Sidebar
st.sidebar.title("Controles")
page = st.sidebar.radio("Selecione a Visão", ["Visão Geral", "Por Bairro"])

# --- VISÃO GERAL ---
if page == "Visão Geral":
    st.title("Visão Geral - Heróis por Bairro")

    # Top metrics
    total_bairros = df["Bairro"].nunique()
    total_herois = df["cod_prestador"].nunique()
    conversao_media = (df["convertidas"].sum() / df["necessidades"].sum()) if df["necessidades"].sum() > 0 else np.nan
    preco_medio_geral = df["preco_hospedagem_num"].mean()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total de Bairros", f"{int(total_bairros)}")
    c2.metric("Total de Heróis", f"{int(total_herois)}")
    c3.metric("Conversão Média", f"{conversao_media:.2%}" if not pd.isna(conversao_media) else "N/A")
    c4.metric("Preço Médio Geral", f"R$ {preco_medio_geral:.2f}" if not pd.isna(preco_medio_geral) else "N/A")

    st.markdown("---")
    st.subheader("Status de Preço - Heróis com Melhor Conversão")

    # For each neighborhood, find hero with best conversion
    best_heroes = df.loc[df.groupby("Bairro")["conversao_hero"].idxmax().dropna()]
    # Merge to get neighborhood mean price
    best_heroes = best_heroes.merge(nb_summary[["Bairro", "preco_medio_bairro"]], on="Bairro", how="left")
    best_heroes["status_preco_relativo"] = best_heroes.apply(lambda row: determine_price_status(row["preco_hospedagem_num"], row["preco_medio_bairro"]), axis=1)

    counts = best_heroes["status_preco_relativo"].value_counts().reindex(["Abaixo da Média", "Na Média", "Acima da Média", "Sem Preço"], fill_value=0)

    fig_pie = px.pie(
        names=counts.index,
        values=counts.values,
        title="Distribuição dos heróis com melhor conversão (vs média do bairro)"
    )
    st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("---")
    st.subheader("Oportunidades de Otimização de Preço")
    # A oportunidade definida: bairros onde existe herói com preço menor que o preço do herói de melhor conversão
    opportunities = []
    for _, row in best_heroes.iterrows():
        bairro = row["Bairro"]
        price_best = row["preco_hospedagem_num"]
        if pd.isna(price_best):
            continue
        menores = df[(df["Bairro"] == bairro) & (df["preco_hospedagem_num"] < price_best)]
        if not menores.empty:
            opportunities.append(bairro)

    num_with_opportunity = len(set(opportunities))
    num_without = total_bairros - num_with_opportunity

    fig_op = px.pie(
        names=["Com Oportunidade", "Sem Oportunidade"],
        values=[num_with_opportunity, num_without],
        title="Bairros onde existe herói com preço menor que o herói de melhor conversão"
    )
    st.plotly_chart(fig_op, use_container_width=True)

    # List bairros com oportunidade
    if num_with_opportunity > 0:
        st.markdown("**Bairros com oportunidade:**")
        st.write(sorted(list(set(opportunities))))

# --- POR BAIRRO ---
else:
    st.title("Análise por Bairro")
    bairros = sorted(df["Bairro"].dropna().unique())
    selected_bairro = st.selectbox("Selecione um Bairro", bairros)

    df_b = df[df["Bairro"] == selected_bairro].copy()
    summary_b = nb_summary[nb_summary["Bairro"] == selected_bairro].squeeze()

    # Basic metrics
    total_herois_b = int(summary_b["total_herois"]) if not summary_b.empty else 0
    total_necessidades_b = int(summary_b["total_necessidades"]) if not pd.isna(summary_b["total_necessidades"]) else 0
    total_convertidas_b = int(summary_b["total_convertidas"]) if not pd.isna(summary_b["total_convertidas"]) else 0
    taxa_conv_b = (total_convertidas_b / total_necessidades_b) if total_necessidades_b > 0 else np.nan
    preco_medio_b = summary_b.get("preco_medio_bairro", np.nan) if not summary_b.empty else np.nan

    # Top row: metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total de Heróis", f"{total_herois_b}")
    m2.metric("Total Necessidades", f"{total_necessidades_b}")
    m3.metric("Total Convertidas", f"{total_convertidas_b}")
    m4.metric("Preço Médio", f"R$ {preco_medio_b:.2f}" if not pd.isna(preco_medio_b) else "N/A")

    st.markdown("")
    st.subheader(f"Taxa de Conversão do Bairro: {taxa_conv_b:.2%}" if not pd.isna(taxa_conv_b) else "Taxa de Conversão do Bairro: N/A")
    st.write(f"{total_convertidas_b} de {total_necessidades_b} necessidades")

    st.markdown("---")
    st.subheader("Análise de Heróis")

    # Melhor conversão
    if df_b["conversao_hero"].dropna().empty:
        st.write("Não há dados de conversão para este bairro.")
    else:
        melhor_idx = df_b["conversao_hero"].idxmax()
        melhor = df_b.loc[melhor_idx]
        menor_idx = df_b["preco_hospedagem_num"].idxmin()
        maior_idx = df_b["preco_hospedagem_num"].idxmax()
        menor = df.loc[menor_idx]
        maior = df.loc[maior_idx]

        # Determine status relative to bairro
        melhor_status = determine_price_status(melhor["preco_hospedagem_num"], preco_medio_b)
        menor_status = determine_price_status(menor["preco_hospedagem_num"], preco_medio_b)
        maior_status = determine_price_status(maior["preco_hospedagem_num"], preco_medio_b)

        # Add global cheapest/most expensive tags
        def tag_global(row):
            tags = []
            if row.get("eh_mais_barato_global", False):
                tags.append("Mais barato de todos")
            if row.get("eh_mais_caro_global", False):
                tags.append("Mais caro de todos")
            return " • ".join(tags) if tags else ""

        col_a, col_b, col_c = st.columns(3)

        with col_a:
            st.markdown("#### Melhor Conversão")
            st.markdown(f"**Herói {int(melhor['cod_prestador'])}**")
            st.markdown(f"Preço de Hospedagem: R$ {melhor['preco_hospedagem_num']:.2f}" if not pd.isna(melhor['preco_hospedagem_num']) else "Preço de Hospedagem: N/A")
            st.markdown(f"Status (vs média do bairro): **{melhor_status}**")
            tg = tag_global(melhor)
            if tg:
                st.markdown(f"**{tg}**")
            st.write("---")
            st.write(f"Necessidades: {int(melhor['necessidades']) if not pd.isna(melhor['necessidades']) else 'N/A'}")
            st.write(f"Convertidas: {int(melhor['convertidas']) if not pd.isna(melhor['convertidas']) else 'N/A'}")
            st.write(f"Conversão: {melhor['conversao_hero']:.2%}")

        with col_b:
            st.markdown("#### Menor Preço")
            st.markdown(f"**Herói {int(menor['cod_prestador'])}**")
            st.markdown(f"Preço de Hospedagem: R$ {menor['preco_hospedagem_num']:.2f}" if not pd.isna(menor['preco_hospedagem_num']) else "Preço de Hospedagem: N/A")
            st.markdown(f"Status (vs média do bairro): **{menor_status}**")
            tg = tag_global(menor)
            if tg:
                st.markdown(f"**{tg}**")
            st.write("---")
            st.write(f"Necessidades: {int(menor['necessidades']) if not pd.isna(menor['necessidades']) else 'N/A'}")
            st.write(f"Convertidas: {int(menor['convertidas']) if not pd.isna(menor['convertidas']) else 'N/A'}")
            st.write(f"Conversão: {menor['conversao_hero']:.2%}" if not pd.isna(menor['conversao_hero']) else "Conversão: N/A")

        with col_c:
            st.markdown("#### Maior Preço")
            st.markdown(f"**Herói {int(maior['cod_prestador'])}**")
            st.markdown(f"Preço de Hospedagem: R$ {maior['preco_hospedagem_num']:.2f}" if not pd.isna(maior['preco_hospedagem_num']) else "Preço de Hospedagem: N/A")
            st.markdown(f"Status (vs média do bairro): **{maior_status}**")
            tg = tag_global(maior)
            if tg:
                st.markdown(f"**{tg}**")
            st.write("---")
            st.write(f"Necessidades: {int(maior['necessidades']) if not pd.isna(maior['necessidades']) else 'N/A'}")
            st.write(f"Convertidas: {int(maior['convertidas']) if not pd.isna(maior['convertidas']) else 'N/A'}")
            st.write(f"Conversão: {maior['conversao_hero']:.2%}" if not pd.isna(maior['conversao_hero']) else "Conversão: N/A")

    st.markdown("---")
    st.subheader("Tabela de Heróis no Bairro")
    display_cols = [
        "cod_prestador", "preco_hospedagem_num", "necessidades", "convertidas", "conversao_hero",
        "eh_mais_barato_global", "eh_mais_caro_global"
    ]
    df_show = df_b[display_cols].copy()
    df_show = df_show.rename(columns={
        "cod_prestador": "cod_prestador",
        "preco_hospedagem_num": "preco_hospedagem",
        "necessidades": "necessidades",
        "convertidas": "convertidas",
        "conversao_hero": "conversao",
        "eh_mais_barato_global": "mais_barato_global",
        "eh_mais_caro_global": "mais_caro_global"
    })
    df_show["preco_hospedagem"] = df_show["preco_hospedagem"].map(lambda x: f"R$ {x:.2f}" if pd.notna(x) else "N/A")
    df_show["conversao"] = df_show["conversao"].map(lambda x: f"{x:.2%}" if pd.notna(x) else "N/A")

    st.dataframe(df_show.reset_index(drop=True), use_container_width=True)

    # Download CSV
    def to_csv_bytes(df_to_convert):
        buf = BytesIO()
        df_to_convert.to_csv(buf, index=False)
        buf.seek(0)
        return buf

    csv_buf = to_csv_bytes(df_show)
    st.download_button("Baixar dados do bairro (CSV)", data=csv_buf, file_name=f"{selected_bairro}_herois.csv", mime="text/csv")
