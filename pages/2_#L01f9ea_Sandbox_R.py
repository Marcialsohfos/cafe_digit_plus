import re

import numpy as np
import pandas as pd
import streamlit as st

from common import init_page, footer
from db import get_sandbox_examples

init_page("Sandbox R", icon="🧪")

st.title("Sandbox R")
st.write(
    "Un environnement de test pour vos modèles R — tapez ou collez du code R comme dans un "
    "cycle Café_digit. Comme cette instance est déployée sur Streamlit Community Cloud "
    "(sans runtime R installé), le bouton **Exécuter** interprète les paramètres de votre "
    "script et en rejoue une simulation équivalente en Python, avec le même graphique."
)

EXEMPLE_LOGISTIQUE = """# Bienvenue dans la sandbox R de Café_digit
# Modélisez, testez, visualisez.

K <- 10000; r <- 0.3; N0 <- 100
t <- 0:50
N <- K / (1 + ((K - N0)/N0) * exp(-r*t))
plot(t, N, type = "l", col = "darkgreen",
     main = "Métabolisme des Quartiers Hors-Piste")
"""

EXEMPLE_HISTOGRAMME = """# Distribution simulée
x <- rnorm(200, mean = 50, sd = 10)
hist(x, col = "#B4622B", border = "white",
     main = "Distribution simulée", xlab = "Valeur")
summary(x)
"""

if "r_code" not in st.session_state:
    st.session_state["r_code"] = EXEMPLE_LOGISTIQUE

c1, c2 = st.columns(2)
if c1.button("Charger l'exemple : croissance logistique"):
    st.session_state["r_code"] = EXEMPLE_LOGISTIQUE
    st.rerun()
if c2.button("Charger l'exemple : distribution simulée"):
    st.session_state["r_code"] = EXEMPLE_HISTOGRAMME
    st.rerun()

db_examples = get_sandbox_examples(published_only=True)
if db_examples:
    st.markdown("###### Exemples ajoutés par l'administration")
    ex_cols = st.columns(3)
    for i, ex in enumerate(db_examples):
        with ex_cols[i % 3]:
            if st.button(f"📦 {ex['title']}", key=f"sbex-{ex['id']}", use_container_width=True):
                st.session_state["r_code"] = ex["code"]
                st.rerun()
            if ex["description"]:
                st.caption(ex["description"])

code = st.text_area("Code R", value=st.session_state["r_code"], height=220, key="r_editor")
st.session_state["r_code"] = code

if st.button("▶ Exécuter"):
    def num(pattern, default):
        m = re.search(pattern, code)
        return float(m.group(1)) if m else default

    if "rnorm" in code:
        m = re.search(r"rnorm\(\s*(\d+)\s*,\s*mean\s*=\s*([\d.]+)\s*,\s*sd\s*=\s*([\d.]+)", code)
        n_pts, mean, sd = (int(m.group(1)), float(m.group(2)), float(m.group(3))) if m else (200, 50, 10)
        x = np.random.normal(mean, sd, n_pts)
        st.bar_chart(pd.DataFrame({"valeur": x}).round(0)["valeur"].value_counts().sort_index())
        st.write("**summary(x)**")
        st.write(pd.Series(x).describe())
    else:
        K = num(r"K\s*<-\s*([\d.]+)", 10000)
        r = num(r"\br\s*<-\s*([\d.]+)", 0.3)
        N0 = num(r"N0\s*<-\s*([\d.]+)", 100)
        t = np.arange(0, 51)
        N = K / (1 + ((K - N0) / N0) * np.exp(-r * t))
        df = pd.DataFrame({"t": t, "N": N}).set_index("t")
        st.line_chart(df)
        st.caption(f"Paramètres détectés — K={K:g}, r={r:g}, N0={N0:g}")

    st.success("Exécution terminée.")

footer()
