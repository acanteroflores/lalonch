"""
Home / Login page for the Streamlit betting app 🔐🎲
--------------------------------------------------
• Coloca este archivo en la raíz del proyecto (junto a `pages/4 4_UFC 🤼.py`).
• Los demás deportes irán dentro de `pages/<deporte>.py` y DEBEN empezar con
  un chequeo sencillo de sesión para que nadie entre sin loguearse:

    import streamlit as st
    if "user" not in st.session_state:
        st.switch_page("Login.py")  # redirige al login

• Los usuarios viven en `users.json` en el mismo directorio:
  {
    "thony": {"password": "1234", "points": 1000},
    "goku":  {"password": "kamehameha", "points": 800}
  }
• Contraseñas en texto plano para la demo 🤙 (mete bcrypt si lo subes online).

Run:
    streamlit run Login.py
"""

from bots.event_creator import sendMessage




import json
from pathlib import Path

import streamlit as st

# ────────────────────────────────
# Config
# ────────────────────────────────
st.set_page_config(
    page_title="Iniciar sesión",
    page_icon="🔐",
    layout="centered",
)

DATA_DIR = Path(__file__).parent
USERS_FILE = DATA_DIR / "users.json"


# ────────────────────────────────
# Helpers
# ────────────────────────────────

def load_users() -> dict:
    """Carga el diccionario de usuarios."""
    try:
        with USERS_FILE.open("r", encoding="utf-8") as fp:
            return json.load(fp)
    except FileNotFoundError:
        return {}


def check_credentials(username: str, password: str) -> bool:
    users = load_users()
    return username in users and users[username]["password"] == password


def init_session(username: str):
    users = load_users()
    user = users.get(username, {})
    st.session_state.user = username
    st.session_state.points = user.get("points", 1000)


# ────────────────────────────────
# UI
# ────────────────────────────────

st.title("Bienvenido a la casa de apuestas 🎲")

if "user" in st.session_state:
    st.success(f"Ya estás logueado como **{st.session_state.user}** ✅")
    st.write("Puedes navegar a la barra lateral y elegir tu deporte.")
    if st.button("Cerrar sesión"):
        st.session_state.clear()
        st.rerun()
else:
    with st.form("login_form"):
        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        submitted = st.form_submit_button("Entrar")
        if submitted:
            if check_credentials(username, password):
                init_session(username)
                st.success("Login correcto, redirigiendo…")
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos 😓")

st.markdown("---")

st.markdown("---")
# st.subheader("🆕 Crear cuenta nueva")
st.info("🆕 Crear cuenta nueva")

with st.expander(" ¿No tienes cuenta? Pincha aquí ✍️"):
    with st.form("registro_form"):
        new_user = st.text_input("Nuevo usuario")
        new_pass = st.text_input("Contraseña", type="password")
        new_discord = st.text_input("Usuario de Discord (opcional)")
        new_color = st.color_picker("Color", "#ffffff")
        crear = st.form_submit_button("Crear cuenta")

        if crear:
            users = load_users()
            if new_user.strip() in users:
                st.error("❌ Ese usuario ya existe.")
            elif not new_user.strip() or not new_pass:
                st.error("❌ El usuario y la contraseña son obligatorios.")
            else:
                users[new_user.strip()] = {
                    "password": new_pass,
                    "points": 1000,
                    "color": new_color,
                    "discord": new_discord
                }
                with USERS_FILE.open("w", encoding="utf-8") as f:
                    json.dump(users, f, indent=4, ensure_ascii=False)

                st.success("✅ Cuenta creada correctamente. ¡Ya puedes iniciar sesión!")
                sendMessage(f"{new_user} acaba de crearse una cuenta en La Casa de Apuestas 👀")
                st.rerun()

# st.info("No tienes cuenta? Añade tu usuario directamente al `users.json` ✍️")
