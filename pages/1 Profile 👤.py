"""
Página de estadísticas del usuario 📊
-------------------------------------
Versión B: con lectura de users.json y bets_history.json desde GitHub.

Requiere que los archivos estén en la raíz del repo o en la ruta correcta dentro del repo.
Asegúrate de definir correctamente GITHUB_TOKEN y REPO_NAME en tus secrets.
"""

import streamlit as st
import pandas as pd
import json
from github import Github
from datetime import datetime

# ────────────────────────────────
# Config
# ────────────────────────────────
st.set_page_config(
    page_title="Mis estadísticas",
    page_icon="📊"
)

USERS_FILE = "users.json"
HISTORY_FILE = "pages/bets_history.json"


# ────────────────────────────────
# GitHub Helpers
# ────────────────────────────────

@st.cache_resource
def get_repo():
    token = st.secrets["GITHUB_TOKEN"]
    repo_name = st.secrets["REPO_NAME"]
    return Github(token).get_repo(repo_name)


def load_json(path: str, default: dict = {}):
    try:
        contents = get_repo().get_contents(path)
        return json.loads(contents.decoded_content.decode("utf-8"))
    except Exception:
        return default


# ────────────────────────────────
# Auth check
# ────────────────────────────────

if "user" not in st.session_state:
    st.switch_page("Login.py")

# ────────────────────────────────
# Load user data
# ────────────────────────────────

user = st.session_state.user
users = load_json(USERS_FILE, {})
user_data = users.get(user, {})

if not user_data:
    st.error("Tu usuario no está en la base de datos.")
    st.stop()

# ────────────────────────────────
# UI
# ────────────────────────────────

st.title("📊 Tus estadísticas")

st.markdown(f"**Nombre:** `{user}`")
st.markdown(f"**Puntos disponibles:** `{user_data.get('points', 0)}`")
st.markdown("---")

# ────────────────────────────────
# Historial de apuestas
# ────────────────────────────────

history_data = load_json(HISTORY_FILE, {})
user_bets = history_data.get(user, [])

if not user_bets:
    st.info("Todavía no has hecho ninguna apuesta.")
else:
    st.subheader("📄 Historial de apuestas")

    rows = []
    for bet in reversed(user_bets):  # Mostrar los más nuevos primero
        estado = "En progreso"
        color = "gray"
        if bet.get("resolved"):
            if bet.get("won"):
                estado = "Ganado"
                color = "green"
            else:
                estado = "Perdido"
                color = "red"

        reward = bet.get("reward", 0)
        resultado = (
            int(f"-{bet.get('amount')}") if reward == 0 else int(reward)
        )

        try:
            dt = datetime.fromisoformat(bet.get("timestamp", ""))
            fecha = dt.strftime("%d %b %Y")
        except:
            fecha = bet.get("timestamp", "-")

        rows.append({
            "Fecha": fecha,
            "Deporte": bet.get("sport", "-"),
            "Apuesta": bet.get("description", "-"),
            "Cantidad": bet.get("amount", 0),
            "Cuota": bet.get("odds", 0),
            "Estado": f"<span style='color:{color}; font-weight:bold'>{estado}</span>",
            "Resultado": f"<span style='color:{'green' if resultado > 0 else ('red' if bet.get('resolved') and not bet.get('won') else 'gray')}'>{'+' + str(resultado) if resultado > 0 else ('-' + str(bet.get('amount', 0)) if bet.get('resolved') and not bet.get('won') else '0')}</span>"
        })

    df = pd.DataFrame(rows)

    st.write("", unsafe_allow_html=True)
    st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)
