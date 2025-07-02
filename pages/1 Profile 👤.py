"""
Página de estadísticas del usuario 📊
-------------------------------------
• Muestra la información del usuario logueado: nombre, puntos actuales, historial de apuestas (futuro).
• Debe colocarse dentro del directorio `pages/` como `pages/user_stats.py`
• Asegúrate de tener un `users.json` actualizado.
• Puedes expandirlo luego para mostrar más detalles: combates favoritos, ganancias, racha, etc.
"""

import json
from pathlib import Path
import streamlit as st
import pandas as pd

# ────────────────────────────────
# Config
# ────────────────────────────────
st.set_page_config(
    page_title="Mis estadísticas",
    page_icon="📊"
)

DATA_DIR = Path(__file__).parent.parent
USERS_FILE = DATA_DIR / "users.json"
HISTORY_FILE = DATA_DIR / "pages/bets_history.json"

# ────────────────────────────────
# Auth check
# ────────────────────────────────
if "user" not in st.session_state:
    st.switch_page("Login.py")

# ────────────────────────────────
# Load user data
# ────────────────────────────────
user = st.session_state.user

try:
    with USERS_FILE.open("r", encoding="utf-8") as fp:
        users = json.load(fp)
except FileNotFoundError:
    st.error("No se encontró el archivo de usuarios 😢")
    st.stop()

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
try:
    with HISTORY_FILE.open("r", encoding="utf-8") as f:
        history_data = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    history_data = {}

user_bets = history_data.get(user, [])

if not user_bets:
    st.info("Todavía no has hecho ninguna apuesta.")
else:
    st.subheader("📄 Historial de apuestas")
    rows = []
    for bet in reversed(user_bets):  # invertir orden para mostrar los más nuevos arriba
        estado = "En progreso"
        color = "gray"
        if bet.get("resolved"):
            if bet.get("won"):
                estado = "Ganado"
                color = "green"
            else:
                estado = "Perdido"
                color = "red"

        if bet.get("reward") == 0:
            resultado = int(f"-{bet.get("amount")}")
        else:
            resultado = int(bet.get("reward", 0))

        # Convertir fecha
        raw_date = bet.get("timestamp", "-")
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(raw_date)
            fecha = dt.strftime("%d %b %Y")
        except:
            fecha = raw_date

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
    st.markdown(
        df.to_html(escape=False, index=False),
        unsafe_allow_html=True
    )
