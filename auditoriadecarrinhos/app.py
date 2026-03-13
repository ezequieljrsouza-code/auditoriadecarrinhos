import io
import re
from collections import OrderedDict

import pandas as pd
import streamlit as st

st.set_page_config(page_title="HH Inventário", page_icon="📦", layout="wide")

ORANGE = "#f59e0b"
DARK = "#1f2937"
BORDER = "#d1d5db"
BG = "#f8fafc"
WHITE = "#ffffff"

STATUS_ORDER = ["Verificados", "Pendente", "Deslocado"]


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

    .metric-card {{
        background:white;
        border:1px solid {BORDER};
        border-radius:12px;
        padding:15px;
        text-align:center;
    }}

    .section-title {{
        background:{ORANGE};
        color:white;
        padding:10px;
        border-radius:10px 10px 0 0;
        font-weight:700;
        margin-top:15px;
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


# ---------------- NORMALIZAR COLUNAS ----------------
def normalize_columns(df):

    rename = {}

    for c in df.columns:

        low = c.lower()

        if "data" in low:
            rename[c] = "Data de Escaneamento"

        if "situa" in low:
            rename[c] = "Situação"

        if "operador" in low:
            rename[c] = "Operador"

        if "area" in low or "área" in low:
            rename[c] = "Área"

    return df.rename(columns=rename)


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


# ---------------- RENDER TABLE ----------------
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
    <h1>HH Inventário</h1>
    Dashboard automático baseado na BASE INICIAL INVENTÁRIO
    </div>
    """, unsafe_allow_html=True)

    file = st.file_uploader("Upload BASE INICIAL INVENTÁRIO", type=["xlsx","csv"])

    if not file:
        st.stop()

    if file.name.endswith("csv"):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)

    df = normalize_columns(df)

    if "Data de Escaneamento" not in df.columns:
        st.error("Coluna Data de Escaneamento não encontrada.")
        st.stop()

    df["Hora"] = df["Data de Escaneamento"].apply(parse_hour)

    if df["Hora"].dropna().empty:
        st.error("Não foi possível identificar horas válidas.")
        st.stop()

    # ---------------- MÉTRICAS ----------------
    total = len(df)
    ver = (df["Situação"] == "Verificados").sum()
    pen = (df["Situação"] == "Pendente").sum()
    des = (df["Situação"] == "Deslocado").sum()

    c1,c2,c3,c4 = st.columns(4)

    c1.metric("Base", total)
    c2.metric("Verificados", ver)
    c3.metric("Pendentes", pen)
    c4.metric("Deslocados", des)


    # ---------------- ZONAS ----------------
    if "Área" in df.columns:

        st.markdown("<div class='section-title'>Pendentes Zona</div>", unsafe_allow_html=True)

        zonas = [
        "Returns","Sorting","Problem Solving","Missort",
        "Fraude","Damaged","Buffered","Dispatch",
        "Containerized","Bulky returns"
        ]

        counts = df[df["Situação"]=="Pendente"]["Área"].value_counts().to_dict()

        cols = st.columns(5)

        for i,z in enumerate(zonas):

            val = counts.get(z,0)

            cols[i%5].markdown(f"""
            <div style="
            background:white;
            border-left:6px solid {ORANGE};
            padding:15px;
            border-radius:10px;
            text-align:center;
            box-shadow:0px 2px 6px rgba(0,0,0,0.08)
            ">
            <div style="font-size:13px;color:#64748b">{z}</div>
            <div style="font-size:28px;font-weight:bold;color:{DARK}">{val}</div>
            </div>
            """, unsafe_allow_html=True)


    # ---------------- HH ----------------
    base_hour = int(df["Hora"].dropna().min())

    hours = list(range(base_hour, base_hour + 8))

    rows = []

    for s in STATUS_ORDER:

        sub = df[df["Situação"] == s]

        r = {"QTD / Status": s}

        for h in hours:
            r[f"{h}h"] = (sub["Hora"] == h).sum()

        r["TOTAL"] = len(sub)

        rows.append(r)

    status_df = pd.DataFrame(rows)

    st.markdown("<div class='section-title'>HH Inventário</div>", unsafe_allow_html=True)

    render_table(status_df)


    # ---------------- OPERADORES ----------------
    if "Operador" in df.columns:

        ops = df["Operador"].dropna().unique()

        rows = []

        for op in ops:

            sub = df[df["Operador"] == op]

            r = OrderedDict()

            r["Operador"] = op

            for h in hours:
                r[f"{h}h"] = (sub["Hora"] == h).sum()

            r["TOTAL"] = len(sub)

            rows.append(r)

        op_df = pd.DataFrame(rows)

        st.markdown("<div class='section-title'>HH por Operador</div>", unsafe_allow_html=True)

        render_table(op_df)


    # ---------------- DOWNLOAD BASE ----------------
    st.download_button(
        "Baixar base tratada",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="base_tratada.csv"
    )


if __name__ == "__main__":
    main()