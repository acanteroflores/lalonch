"""
Login page con persistencia en GitHub 🔐🎲
------------------------------------------
• Este archivo reemplaza al antiguo Login.py y se conecta con GitHub.
• El archivo `users.json` vive en el repositorio remoto (no en disco local).
• Usa los secrets: GITHUB_TOKEN y REPO_NAME en Streamlit Cloud.

"""

from bots.event_creator import sendMessage
import streamlit as st
from github import Github
import json

# ────────────────────────────────
# Config
# ────────────────────────────────
st.set_page_config(
    page_title="Iniciar sesión",
    page_icon="🔐",
    layout="centered",
)

USERS_FILE = "users.json"  # Ahora es solo el path dentro del repo


# ────────────────────────────────
# GitHub Helpers
# ────────────────────────────────

@st.cache_resource
def get_repo():
    token = st.secrets["GITHUB_TOKEN"]
    repo_name = st.secrets["REPO_NAME"]
    return Github(token).get_repo(repo_name)


def load_json(path, default={}):
    repo = get_repo()
    try:
        contents = repo.get_contents(path)
        return json.loads(contents.decoded_content.decode("utf-8"))
    except Exception:
        return default


def save_json(path, data):
    repo = get_repo()
    try:
        contents = repo.get_contents(path)
        repo.update_file(
            path,
            f"Update {path}",
            json.dumps(data, indent=4, ensure_ascii=False),
            contents.sha
        )
    except Exception:
        repo.create_file(
            path,
            f"Create {path}",
            json.dumps(data, indent=4, ensure_ascii=False)
        )


# ────────────────────────────────
# App Helpers
# ────────────────────────────────

def load_users() -> dict:
    return load_json(USERS_FILE, {})


def save_users(users: dict):
    save_json(USERS_FILE, users)


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
                save_users(users)
                st.success("✅ Cuenta creada correctamente. ¡Ya puedes iniciar sesión!")
                sendMessage(f"{new_discord} acaba de crearse una cuenta en La Casa de Apuestas 👀")
                st.rerun()
