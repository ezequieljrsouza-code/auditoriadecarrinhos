import re
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Auditoria de Carrinhos", page_icon="🛒", layout="wide")

ORANGE = "#f59e0b"
BG = "#f8fafc"

# ---------------- CSS ----------------
def inject_css():
    st.markdown(f"""
    <style>
    .stApp {{ background:{BG}; }}

    .hero {{
        background: linear-gradient(135deg,{ORANGE} 0%,#fb923c 100%);
        color:white;
        padding:20px;
        border-radius:16px;
        margin-bottom:20px;
    }}

    .section-title {{
        background:{ORANGE};
        color:white;
        padding:10px;
        border-radius:10px 10px 0 0;
        font-weight:700;
        margin-top:25px;
    }}
    </style>
    """, unsafe_allow_html=True)


# ---------------- EXTRAIR HORA ----------------
def parse_hour(valor):

    if pd.isna(valor):
        return None

    texto = str(valor)

    match = re.search(r'(\d{1,2}):(\d{2})', texto)

    if match:
        return int(match.group(1))

    try:
        return pd.to_datetime(texto).hour
    except:
        return None


# ---------------- MAIN ----------------
def main():

    inject_css()

    st.markdown("""
    <div class='hero'>
    <h1>Auditoria de Carrinhos</h1>
    Dashboard HH baseado na base de auditoria
    </div>
    """, unsafe_allow_html=True)

    file = st.file_uploader("Upload da base de auditoria", type=["xlsx","csv"])

    if not file:
        st.stop()

    # ---------------- LER BASE ----------------
    if file.name.endswith("csv"):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)

    # ---------------- VALIDAR COLUNAS ----------------
    if len(df.columns) < 5:
        st.error("A planilha precisa ter pelo menos 5 colunas (A até E).")
        st.stop()

    coluna_contagem = df.columns[0]
    coluna_hora = df.columns[1]
    coluna_nome = df.columns[4]

    # ---------------- HORA ----------------
    df["Hora"] = df[coluna_hora].apply(parse_hour)

    df = df.dropna(subset=["Hora"])

    # ---------------- TOTAL ----------------
    total = len(df)

    st.metric("Total de Carrinhos Auditados", total)

    # ---------------- HH ----------------
    hh = df.groupby("Hora").size().reset_index(name="Carrinhos")

    st.markdown("<div class='section-title'>HH Auditoria</div>", unsafe_allow_html=True)

    st.dataframe(hh, use_container_width=True)

    # ---------------- TOP 10 AUDITORES ----------------
    ranking = (
        df.groupby(coluna_nome)
        .size()
        .reset_index(name="Carrinhos")
        .sort_values("Carrinhos", ascending=False)
        .head(10)
    )

    st.markdown("<div class='section-title'>🏆 Top 10 Auditores</div>", unsafe_allow_html=True)

    st.dataframe(ranking, use_container_width=True)

    # ---------------- PRODUTIVIDADE ----------------
    prod = (
        df.groupby([coluna_nome, "Hora"])
        .size()
        .reset_index(name="Carrinhos")
    )

    produtividade = (
        prod.groupby(coluna_nome)["Carrinhos"]
        .mean()
        .reset_index()
        .rename(columns={"Carrinhos": "Carrinhos/Hora"})
        .sort_values("Carrinhos/Hora", ascending=False)
    )

    st.markdown("<div class='section-title'>⚡ Produtividade (Carrinhos/Hora)</div>", unsafe_allow_html=True)

    st.dataframe(produtividade, use_container_width=True)

    # ---------------- DOWNLOAD ----------------
    st.download_button(
        "Baixar base tratada",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="auditoria_carrinhos_tratada.csv"
    )


if __name__ == "__main__":
    main()