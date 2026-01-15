# dashboard_eda_caisse.py
# -*- coding: utf-8 -*-

from __future__ import annotations
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import matplotlib.dates as mdates
from matplotlib.ticker import MaxNLocator


# =========================
# CONFIG
# =========================
# Par défaut: on essaye de charger le fichier clean généré par ton script
DEFAULT_PATHS = [
    Path("output_caisse/data_clean/caisse_clean.csv"),
    Path.home() / "Desktop" / "caisse_sale_clean.csv",
]


# =========================
# Helpers
# =========================
def euro(x: float) -> str:
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")

@st.cache_data
def load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8", encoding_errors="ignore")

def prepare(df: pd.DataFrame) -> pd.DataFrame:
    # Ton schéma final attendu: item, amount, payment, employee, ticket, date, time, dt_iso, dt
    if "dt_iso" in df.columns:
        df["dt"] = pd.to_datetime(df["dt_iso"], errors="coerce")
    elif "dt" in df.columns:
        df["dt"] = pd.to_datetime(df["dt"], errors="coerce")
    else:
        # fallback date+time
        df["dt"] = pd.to_datetime(df["date"].astype(str) + " " + df["time"].astype(str),
                                  errors="coerce", dayfirst=True)

    df = df.dropna(subset=["dt"]).copy()

    # amount
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df = df.dropna(subset=["amount"]).copy()
    df = df[df["amount"] > 0].copy()

    # payment / item / employee / ticket
    for c in ["payment", "item", "employee", "ticket"]:
        if c not in df.columns:
            df[c] = "N/A"
        df[c] = df[c].astype(str).str.strip()

    df["payment"] = df["payment"].str.upper()
    df.loc[df["payment"] == "", "payment"] = "INCONNU"

    # time features
    df["date_only"] = df["dt"].dt.date
    df["hour"] = df["dt"].dt.hour
    df["weekday"] = df["dt"].dt.day_name()  # utile pour analyse jour semaine

    return df

def kpis(df: pd.DataFrame) -> dict:
    tx = int(len(df))
    ca = float(df["amount"].sum()) if tx else 0.0
    panier = float(df["amount"].mean()) if tx else 0.0
    return {"tx": tx, "ca": ca, "panier": panier}

def insights_auto(df: pd.DataFrame) -> list[str]:
    msgs = []
    if len(df) == 0:
        return ["Aucune donnée sur ces filtres."]

    # Heures creuses/fortes (sur CA)
    ca_hour = df.groupby("hour")["amount"].sum().sort_values(ascending=False)
    top = ca_hour.head(3)
    low = ca_hour.tail(3).sort_values()

    msgs.append(f"**Heures fortes (Top 3)** : " + ", ".join([f"{h}h ({euro(v)})" for h, v in top.items()]))
    msgs.append(f"**Heures creuses (Top 3)** : " + ", ".join([f"{h}h ({euro(v)})" for h, v in low.items()]))

    # Part CB / espèces
    ca_pay = df.groupby("payment")["amount"].sum()
    ca_total = ca_pay.sum()
    if ca_total > 0 and ("CB" in ca_pay.index or "ESPECES" in ca_pay.index):
        share_cb = float(ca_pay.get("CB", 0.0) / ca_total)
        share_cash = float(ca_pay.get("ESPECES", 0.0) / ca_total)
        msgs.append(f"**Répartition CA** : CB ~ **{share_cb*100:.1f}%** | Espèces ~ **{share_cash*100:.1f}%**")

    # Top prestation + top employé
    top_item = df.groupby("item")["amount"].sum().sort_values(ascending=False).head(1)
    if len(top_item):
        it, v = top_item.index[0], float(top_item.iloc[0])
        msgs.append(f"**Prestation #1** : {it} ({euro(v)})")

    top_emp = df.groupby("employee")["amount"].sum().sort_values(ascending=False).head(1)
    if len(top_emp):
        emp, v = top_emp.index[0], float(top_emp.iloc[0])
        msgs.append(f"**Employé #1 (CA)** : {emp} ({euro(v)})")

    # Suggestion business simple
    msgs.append("🎯 **Action rapide** : place une promo/pack uniquement sur les heures creuses et garde les heures fortes sans remise.")
    return msgs


# =========================
# UI
# =========================
st.set_page_config(page_title="EDA Caisse — Dashboard", layout="wide")
st.title("📊 Dashboard EDA — Exploitation d’un export de caisse")

# Choix du fichier
st.sidebar.header("Source")
use_upload = st.sidebar.toggle("Importer un fichier", value=False)
uploaded = None
if use_upload:
    uploaded = st.sidebar.file_uploader("CSV caisse nettoyé", type=["csv"])

data_path = None
if uploaded is not None:
    tmp = Path("uploaded_caisse_clean.csv")
    tmp.write_bytes(uploaded.getbuffer())
    data_path = tmp
else:
    for p in DEFAULT_PATHS:
        if p.exists():
            data_path = p
            break

if data_path is None:
    st.error("Aucun fichier trouvé. Place 'caisse_clean.csv' dans output_caisse/data_clean/ ou importe un CSV.")
    st.stop()

df0 = load_csv(data_path)
df = prepare(df0)

st.sidebar.success(f"Fichier chargé : {data_path.as_posix()}")
st.sidebar.caption(f"Lignes : {len(df)}")

# Filtres
st.sidebar.header("Filtres")
min_d = df["date_only"].min()
max_d = df["date_only"].max()
date_range = st.sidebar.date_input("Période", value=(min_d, max_d), min_value=min_d, max_value=max_d)

payments = sorted(df["payment"].unique())
pay_sel = st.sidebar.multiselect("Paiement", payments, default=payments)

employees = sorted(df["employee"].unique())
emp_sel = st.sidebar.multiselect("Employé", employees, default=employees)

items = sorted(df["item"].unique())
item_sel = st.sidebar.multiselect("Prestation", items, default=items)

ticket_search = st.sidebar.text_input("Recherche ticket (optionnel)", value="").strip()

# Application filtres
start_d, end_d = date_range
mask = (
    (df["date_only"] >= start_d) &
    (df["date_only"] <= end_d) &
    (df["payment"].isin(pay_sel)) &
    (df["employee"].isin(emp_sel)) &
    (df["item"].isin(item_sel))
)

df_f = df[mask].copy()
if ticket_search:
    df_f = df_f[df_f["ticket"].str.contains(ticket_search, case=False, na=False)].copy()

# KPI
m = kpis(df_f)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Transactions", f"{m['tx']:,}".replace(",", " "))
c2.metric("Chiffre d’affaires", euro(m["ca"]))
c3.metric("Panier moyen", euro(m["panier"]))
c4.metric("Période", f"{start_d} → {end_d}")

# Insights auto
st.subheader("🧠 Insights automatiques (pilotage)")
for msg in insights_auto(df_f):
    st.markdown(f"- {msg}")

# Graphs
g1, g2 = st.columns(2)

with g1:
    st.subheader("🥧 Répartition CA — CB vs Espèces")
    if len(df_f) == 0:
        st.info("Aucune donnée.")
    else:
        ca_pay = df_f.groupby("payment")["amount"].sum().sort_values(ascending=False)
        fig = plt.figure()
        plt.pie(ca_pay.values, labels=ca_pay.index, autopct="%1.1f%%")
        plt.title("CA par paiement")
        st.pyplot(fig, clear_figure=True)

with g2:
    st.subheader("🧾 Répartition Transactions — CB vs Espèces")
    if len(df_f) == 0:
        st.info("Aucune donnée.")
    else:
        tx_pay = df_f["payment"].value_counts()
        fig = plt.figure()
        plt.pie(tx_pay.values, labels=tx_pay.index, autopct="%1.1f%%")
        plt.title("Transactions par paiement")
        st.pyplot(fig, clear_figure=True)

st.divider()

h1, h2 = st.columns(2)

with h1:
    st.subheader("⏰ CA par heure")
    if len(df_f) == 0:
        st.info("Aucune donnée.")
    else:
        ca_hour = df_f.groupby("hour")["amount"].sum().sort_index()

        fig, ax = plt.subplots(figsize=(9, 4.5), dpi=120)
        ax.bar(ca_hour.index.astype(int), ca_hour.values)

        ax.set_xlabel("Heure")
        ax.set_ylabel("CA (€)")
        ax.set_title("CA par heure")

        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        if ca_hour.index.nunique() > 10:
            ax.set_xticks(ca_hour.index.astype(int)[::2])

        ax.grid(axis="y", alpha=0.25)
        fig.tight_layout()
        st.pyplot(fig, clear_figure=True)

with h2:
    st.subheader("📈 CA par jour")
    if len(df_f) == 0:
        st.info("Aucune donnée.")
    else:
        ca_day = df_f.groupby("date_only")["amount"].sum().sort_index()
        x = pd.to_datetime(ca_day.index)
        y = ca_day.values

        fig, ax = plt.subplots(figsize=(10, 4.5), dpi=120)
        ax.plot(x, y, marker="o", linewidth=2)

        ax.set_xlabel("Date")
        ax.set_ylabel("CA (€)")
        ax.set_title("CA par jour")

        locator = mdates.AutoDateLocator(minticks=5, maxticks=8)
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))

        ax.grid(alpha=0.25)
        fig.tight_layout()
        st.pyplot(fig, clear_figure=True)
