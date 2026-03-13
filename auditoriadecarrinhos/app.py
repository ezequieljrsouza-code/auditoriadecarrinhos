import re
from collections import OrderedDict

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Auditoria de Carrinhos", page_icon="🛒", layout="wide")

ORANGE = "#f59e0b"
DARK = "#1f2937"
BORDER = "#d1d5db"
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
    Dashboard HH baseado na base de auditoria de carrinhos
    </div>
    """, unsafe_allow_html=True)

    file = st.file_uploader("Upload da base de auditoria", type=["xlsx","csv"])

    if not file:
        st.stop()

    # ---------------- LER ARQUIVO ----------------
    if file.name.endswith("csv"):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)

    # ---------------- VALIDAR COLUNAS ----------------
    if len(df.columns) < 5:
        st.error("A planilha precisa ter pelo menos 5 colunas (A até E).")
        st.stop()

    coluna_contagem = df.columns[0]   # Coluna A
    coluna_hora = df.columns[1]       # Coluna B
    coluna_nome = df.columns[4]       # Coluna E

    # ---------------- EXTRAIR HORA ----------------
    df["Hora"] = df[coluna_hora].apply(parse_hour)

    if df["Hora"].dropna().empty:
        st.error("Não foi possível identificar horas válidas na coluna B.")
        st.stop()

    # ---------------- MÉTRICA TOTAL ----------------
    total = df[coluna_contagem].count()

    c1 = st.columns(1)[0]
    c1.metric("Total de Carrinhos Auditados", total)

    # ---------------- HH TOTAL ----------------
    base_hour = int(df["Hora"].dropna().min())

    hours = list(range(base_hour, base_hour + 8))

    row = {"Carrinhos"}

    for h in hours:
        row[f"{h}h"] = (df["Hora"] == h).sum()

    row["TOTAL"] = total

    hh_df = pd.DataFrame([row])

    st.markdown("<div class='section-title'>HH Auditoria de Carrinhos</div>", unsafe_allow_html=True)

    render_table(hh_df)

    # ---------------- HH POR OPERADOR ----------------
    operadores = df[coluna_nome].dropna().unique()

    rows = []

    for op in operadores:

        sub = df[df[coluna_nome] == op]

        r = OrderedDict()

        r["Operador"] = op

        for h in hours:
            r[f"{h}h"] = (sub["Hora"] == h).sum()

        r["TOTAL"] = len(sub)

        rows.append(r)

    op_df = pd.DataFrame(rows)

    op_df = op_df.sort_values("TOTAL", ascending=False)

    st.markdown("<div class='section-title'>Quem Bipou Mais Carrinhos</div>", unsafe_allow_html=True)

    render_table(op_df)

    # ---------------- DOWNLOAD ----------------
    st.download_button(
        "Baixar base tratada",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="auditoria_carrinhos_tratada.csv"
    )


if __name__ == "__main__":
    main()