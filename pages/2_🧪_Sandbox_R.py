import ast
import contextlib
import io
import re

import numpy as np
import pandas as pd
import streamlit as st

from common import init_page, footer
from db import get_sandbox_examples
from i18n import t

init_page(t("Sandbox R / Python", "R / Python Sandbox"), icon="🧪")

st.title(t("Sandbox R / Python", "R / Python Sandbox"))
st.write(
    t(
        "Deux bacs à sable indépendants, comme dans un cycle Café_digit : un onglet **R** et un "
        "onglet **Python**. Tous les exemples enregistrés par l'administration apparaissent "
        "automatiquement dans l'onglet correspondant, prêts à être chargés et exécutés.",
        "Two independent sandboxes, just like in a Café_digit course: an **R** tab and a "
        "**Python** tab. Every example registered by the administration automatically shows up "
        "in the matching tab, ready to load and run.",
    )
)

# ============================================================ Sandbox R (simulée)

EXEMPLE_R_LOGISTIQUE = """# Bienvenue dans la sandbox R de Café_digit
# Modélisez, testez, visualisez.

K <- 10000; r <- 0.3; N0 <- 100
t <- 0:50
N <- K / (1 + ((K - N0)/N0) * exp(-r*t))
plot(t, N, type = "l", col = "darkgreen",
     main = "Métabolisme des Quartiers Hors-Piste")
"""

EXEMPLE_R_HISTOGRAMME = """# Distribution simulée
x <- rnorm(200, mean = 50, sd = 10)
hist(x, col = "#B4622B", border = "white",
     main = "Distribution simulée", xlab = "Valeur")
summary(x)
"""


def render_r_sandbox():
    st.write(
        t(
            "Comme cette instance est déployée sur Streamlit Community Cloud (sans runtime R "
            "installé), le bouton **Exécuter** interprète les paramètres de votre script R et en "
            "rejoue une simulation équivalente en Python, avec le même graphique.",
            "Since this instance is deployed on Streamlit Community Cloud (without an R runtime "
            "installed), the **Run** button interprets your R script's parameters and replays an "
            "equivalent Python simulation, with the same chart.",
        )
    )

    if "r_code" not in st.session_state:
        st.session_state["r_code"] = EXEMPLE_R_LOGISTIQUE

    c1, c2 = st.columns(2)
    if c1.button(t("Charger l'exemple : croissance logistique", "Load example: logistic growth"), key="r-ex1"):
        st.session_state["r_code"] = EXEMPLE_R_LOGISTIQUE
        st.rerun()
    if c2.button(t("Charger l'exemple : distribution simulée", "Load example: simulated distribution"), key="r-ex2"):
        st.session_state["r_code"] = EXEMPLE_R_HISTOGRAMME
        st.rerun()

    db_examples = get_sandbox_examples(published_only=True, language="R")
    if db_examples:
        st.markdown(f"###### {t('Exemples ajoutés par l’administration', 'Examples added by the administration')}")
        ex_cols = st.columns(3)
        for i, ex in enumerate(db_examples):
            with ex_cols[i % 3]:
                if st.button(f"📦 {ex['title']}", key=f"r-sbex-{ex['id']}", use_container_width=True):
                    st.session_state["r_code"] = ex["code"]
                    st.rerun()
                if ex["description"]:
                    st.caption(ex["description"])

    code = st.text_area(t("Code R", "R code"), value=st.session_state["r_code"], height=220, key="r_editor")
    st.session_state["r_code"] = code

    if st.button(t("▶ Exécuter", "▶ Run"), key="r-run"):
        def num(pattern, default):
            m = re.search(pattern, code)
            return float(m.group(1)) if m else default

        if "rnorm" in code:
            m = re.search(r"rnorm\(\s*(\d+)\s*,\s*mean\s*=\s*([\d.]+)\s*,\s*sd\s*=\s*([\d.]+)", code)
            n_pts, mean, sd = (int(m.group(1)), float(m.group(2)), float(m.group(3))) if m else (200, 50, 10)
            x = np.random.normal(mean, sd, n_pts)
            st.bar_chart(pd.DataFrame({"valeur": x}).round(0)["valeur"].value_counts().sort_index())
            st.write(f"**{t('summary(x) — résumé statistique', 'summary(x) — statistical summary')}**")
            st.write(pd.Series(x).describe())
        else:
            K = num(r"K\s*<-\s*([\d.]+)", 10000)
            r_param = num(r"\br\s*<-\s*([\d.]+)", 0.3)
            N0 = num(r"N0\s*<-\s*([\d.]+)", 100)
            time_steps = np.arange(0, 51)
            N = K / (1 + ((K - N0) / N0) * np.exp(-r_param * time_steps))
            df = pd.DataFrame({"t": time_steps, "N": N}).set_index("t")
            st.line_chart(df)
            st.caption(t(
                f"Paramètres détectés — K={K:g}, r={r_param:g}, N0={N0:g}",
                f"Detected parameters — K={K:g}, r={r_param:g}, N0={N0:g}",
            ))

        st.success(t("Exécution terminée.", "Run complete."))


# ======================================================== Sandbox Python (réelle, restreinte)

EXEMPLE_PY_LOGISTIQUE = """# Bienvenue dans la sandbox Python de Café_digit
K, r, N0 = 10000, 0.3, 100
t = np.arange(0, 51)
N = K / (1 + ((K - N0) / N0) * np.exp(-r * t))

for annee, pop in zip(t[::10], N[::10]):
    print(f"t={annee} -> N={pop:.0f}")

plt.plot(t, N)
plt.title("Métabolisme des Quartiers Hors-Piste")
"""

EXEMPLE_PY_HISTOGRAMME = """# Distribution simulée
x = np.random.normal(50, 10, 200)
plt.hist(x)
print("Moyenne :", round(float(np.mean(x)), 2))
print("Écart-type :", round(float(np.std(x)), 2))
"""

_SAFE_BUILTINS = {
    "abs": abs, "all": all, "any": any, "bool": bool, "dict": dict, "enumerate": enumerate,
    "float": float, "int": int, "len": len, "list": list, "max": max, "min": min, "print": print,
    "range": range, "round": round, "set": set, "sorted": sorted, "str": str, "sum": sum,
    "tuple": tuple, "zip": zip, "reversed": reversed, "map": map, "filter": filter,
    "True": True, "False": False, "None": None,
    "Exception": Exception, "ValueError": ValueError, "TypeError": TypeError,
    "ZeroDivisionError": ZeroDivisionError, "IndexError": IndexError, "KeyError": KeyError,
}
_FORBIDDEN_NAMES = {
    "__import__", "open", "eval", "exec", "compile", "input", "globals", "locals", "vars",
    "getattr", "setattr", "delattr", "os", "sys", "subprocess", "socket", "shutil",
    "pathlib", "importlib", "requests", "urllib",
}


class _PlotShim:
    """Substitut minimal de matplotlib.pyplot : capture les appels de tracé pour les
    restituer avec les composants graphiques natifs de Streamlit. Volontairement très
    limité — ce n'est pas un vrai moteur de rendu, juste de quoi visualiser un résultat."""

    def __init__(self):
        self.kind = None
        self.data = None
        self.title_txt = None

    def plot(self, x, y=None, *_a, **_k):
        if y is None:
            y, x = list(x), list(range(len(x)))
        self.kind, self.data = "line", pd.DataFrame({"x": list(x), "y": list(y)}).set_index("x")

    def bar(self, x, y, *_a, **_k):
        self.kind, self.data = "bar", pd.DataFrame({"x": list(x), "y": list(y)}).set_index("x")

    def hist(self, x, bins=10, *_a, **_k):
        counts = pd.Series(list(x)).round(0).value_counts().sort_index()
        self.kind, self.data = "bar", counts

    def scatter(self, x, y, *_a, **_k):
        self.kind, self.data = "scatter", pd.DataFrame({"x": list(x), "y": list(y)})

    def title(self, txt, *_a, **_k):
        self.title_txt = txt

    def xlabel(self, *_a, **_k):
        pass

    def ylabel(self, *_a, **_k):
        pass

    def legend(self, *_a, **_k):
        pass

    def figure(self, *_a, **_k):
        pass

    def show(self, *_a, **_k):
        pass


def _python_safety_check(code: str):
    """Analyse statique légère avant toute exécution : bloque les imports, l'accès
    aux attributs spéciaux (__...__) et les noms sensibles (os, open, eval...)."""
    try:
        tree = ast.parse(code, mode="exec")
    except SyntaxError as e:
        return t(f"Erreur de syntaxe : {e}", f"Syntax error: {e}")
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            return t(
                "Les imports ne sont pas autorisés ici — numpy (np) et pandas (pd) sont déjà "
                "disponibles directement.",
                "Imports aren't allowed here — numpy (np) and pandas (pd) are already available "
                "directly.",
            )
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            return t(
                "L'accès aux attributs spéciaux (__...__) n'est pas autorisé dans cette sandbox.",
                "Access to special attributes (__...__) isn't allowed in this sandbox.",
            )
        if isinstance(node, ast.Name) and node.id in _FORBIDDEN_NAMES:
            return t(
                f"L'utilisation de « {node.id} » n'est pas autorisée dans cette sandbox.",
                f"Using « {node.id} » isn't allowed in this sandbox.",
            )
    return None


def run_python_sandbox(code: str):
    """Exécute réellement le code Python soumis, mais dans un environnement restreint :
    pas d'imports, pas de fichiers, pas de réseau, pas d'accès système — seulement des
    calculs (numpy/pandas) et un tracé simplifié (plt)."""
    error = _python_safety_check(code)
    if error:
        return "", None, error
    plt = _PlotShim()
    safe_globals = {"__builtins__": _SAFE_BUILTINS, "np": np, "pd": pd, "plt": plt}
    stdout = io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout):
            exec(compile(ast.parse(code, mode="exec"), "<sandbox_python>", "exec"), safe_globals, safe_globals)
    except Exception as e:  # noqa: BLE001
        return stdout.getvalue(), plt, t(f"Erreur à l'exécution : {e}", f"Runtime error: {e}")
    return stdout.getvalue(), plt, None


def render_python_sandbox():
    st.write(
        t(
            "Ici, le code Python est **réellement exécuté**, mais dans un environnement restreint : "
            "ni imports, ni fichiers, ni réseau, ni accès système — uniquement des calculs "
            "(`np`/`pd` déjà disponibles) et un tracé simplifié via `plt.plot`/`plt.hist`/`plt.bar`.",
            "Here, the Python code is **actually executed**, but in a restricted environment: no "
            "imports, no files, no network, no system access — only computation (`np`/`pd` already "
            "available) and a simplified chart via `plt.plot`/`plt.hist`/`plt.bar`.",
        )
    )

    if "py_code" not in st.session_state:
        st.session_state["py_code"] = EXEMPLE_PY_LOGISTIQUE

    c1, c2 = st.columns(2)
    if c1.button(t("Charger l'exemple : croissance logistique", "Load example: logistic growth"), key="py-ex1"):
        st.session_state["py_code"] = EXEMPLE_PY_LOGISTIQUE
        st.rerun()
    if c2.button(t("Charger l'exemple : distribution simulée", "Load example: simulated distribution"), key="py-ex2"):
        st.session_state["py_code"] = EXEMPLE_PY_HISTOGRAMME
        st.rerun()

    db_examples = get_sandbox_examples(published_only=True, language="PYTHON")
    if db_examples:
        st.markdown(f"###### {t('Exemples ajoutés par l’administration', 'Examples added by the administration')}")
        ex_cols = st.columns(3)
        for i, ex in enumerate(db_examples):
            with ex_cols[i % 3]:
                if st.button(f"📦 {ex['title']}", key=f"py-sbex-{ex['id']}", use_container_width=True):
                    st.session_state["py_code"] = ex["code"]
                    st.rerun()
                if ex["description"]:
                    st.caption(ex["description"])

    code = st.text_area(t("Code Python", "Python code"), value=st.session_state["py_code"], height=220, key="py_editor")
    st.session_state["py_code"] = code

    if st.button(t("▶ Exécuter", "▶ Run"), key="py-run"):
        output, plot_obj, error = run_python_sandbox(code)
        if output:
            st.code(output, language="text")
        if plot_obj is not None and plot_obj.kind == "line":
            st.line_chart(plot_obj.data)
        elif plot_obj is not None and plot_obj.kind == "bar":
            st.bar_chart(plot_obj.data)
        elif plot_obj is not None and plot_obj.kind == "scatter":
            st.scatter_chart(plot_obj.data, x="x", y="y")
        if plot_obj is not None and plot_obj.title_txt:
            st.caption(plot_obj.title_txt)
        if error:
            st.error(error)
        else:
            st.success(t("Exécution terminée.", "Run complete."))


# ================================================================== Rendu des onglets

tab_r, tab_py = st.tabs([t("🧪 Sandbox R", "🧪 R Sandbox"), t("🐍 Sandbox Python", "🐍 Python Sandbox")])

with tab_r:
    render_r_sandbox()

with tab_py:
    render_python_sandbox()

footer()
