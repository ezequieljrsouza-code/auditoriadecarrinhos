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
        margin-top:20px;
    }}

    table.hh-table {{
        width:100%;
        border-collapse:collapse;
    }}

    table.hh-table th {{
        background:{ORANGE};
        color:white;
        border:2px solid black;
        padding:6px;
    }}

    table.hh-table td {{
        border:2px solid black;
        padding:6px;
        text-align:center;
        background:#e5e7eb;
    }}

    table.hh-table td:first-child {{
        text-align:left;
        font-weight:700;
        background:#fde68a;
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


# ---------------- RENDER TABELA ----------------
def render_table(df):

    html = "<table class='hh-table'>"

    html += "<tr>"
    for c in df.columns:
        html += f"<th>{c}</th>"
    html += "</tr>"

    for _, r in df.iterrows():

        html += "<tr>"

        for v in r:
            html += f"<td>{v}</td>"

        html += "</tr>"

    html += "</table>"

    st.markdown(html, unsafe_allow_html=True)


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

    if len(df.columns) < 5:
        st.error("A planilha precisa ter pelo menos 5 colunas.")
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
    horas = sorted(df["Hora"].unique())

    hh_data = []

    row = {"Carrinhos"}

    for h in horas:
        qtd = (df["Hora"] == h).sum()
        row[f"{h}h"] = qtd

    row["TOTAL"] = total

    hh_data.append(row)

    hh_df = pd.DataFrame(hh_data)

    st.markdown("<div class='section-title'>HH Auditoria</div>", unsafe_allow_html=True)

    render_table(hh_df)

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