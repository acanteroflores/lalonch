import streamlit as st
import json
import random
from datetime import datetime
from bots.event_creator import sendMessage


# ────── Funciones GitHub ────── #
@st.cache_resource
def get_repo():
    from github import Github
    token = st.secrets["GITHUB_TOKEN"]
    repo_name = st.secrets["REPO_NAME"]
    return Github(token).get_repo(repo_name)


def load_json(path: str, default: dict = {}):
    try:
        contents = get_repo().get_contents(path)
        return json.loads(contents.decoded_content.decode())
    except Exception:
        return default


def save_json(path: str, data: dict):
    repo = get_repo()
    payload = json.dumps(data, indent=4, ensure_ascii=False)
    try:
        contents = repo.get_contents(path)
        repo.update_file(path, f"Update {path}", payload, contents.sha)
    except Exception:
        repo.create_file(path, f"Create {path}", payload)


# ────── Config básica ────── #
st.set_page_config(page_title="Quiz UFC", layout="centered")
st.title("🥊 Quiz Histórico de UFC")

USERS_FILE = "users.json"
QUESTIONS_FILE = "quiz/ufcQ.json"  # desde el disco

username = st.session_state.get("user")
users = load_json(USERS_FILE, {})

# ────── Carga de preguntas (una sola vez) ────── #
if "preguntas" not in st.session_state:
    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        st.session_state.preguntas = json.load(f)
    random.shuffle(st.session_state.preguntas)
    st.session_state.indice = 0
    st.session_state.puntuacion = 0
    st.session_state.respuesta_mostrada = False
    st.session_state.ultima_correcta = False

# Alias útiles
preguntas = st.session_state.preguntas
i = st.session_state.indice

# ────── Quiz activo ────── #
if i < len(preguntas):
    q = preguntas[i]
    st.subheader(f"Pregunta {i + 1} de {len(preguntas)}")
    st.info(f"Puntuación: {st.session_state.puntuacion}")

    with st.form(key=f"form_{i}"):
        seleccion = st.radio(
            q["pregunta"],
            q["opciones"],
            key=f"radio_{i}"
        )
        confirm = st.form_submit_button("✅ Confirmar respuesta")

    if confirm and not st.session_state.respuesta_mostrada:
        st.session_state.ultima_correcta = (seleccion == q["respuesta_correcta"])
        st.session_state.respuesta_mostrada = True
        if st.session_state.ultima_correcta:
            st.session_state.puntuacion += 1

    if st.session_state.respuesta_mostrada:
        if st.session_state.ultima_correcta:
            st.success("¡Correcto! 🎉")
        else:
            st.error(f"Incorrecto 😢 La respuesta era: **{q['respuesta_correcta']}**")

        if st.button("➡️ Continuar"):
            st.session_state.indice += 1
            st.session_state.respuesta_mostrada = False
            st.rerun()

# ────── Quiz terminado ────── #
else:
    st.balloons()
    total = st.session_state.puntuacion
    reward = total * 75

    if username and username in users:
        users[username]["points"] += reward
        save_json(USERS_FILE, users)
        st.success(f"✅ ¡{reward} puntos añadidos a {username}!")
    else:
        st.warning("⚠️ Usuario no encontrado en sesión o base de datos.")

    st.success(f"🎯 Quiz completado: {total}/{len(preguntas)} correctas.")
    sendMessage(f"{username} ha completado el Quiz de UFC y ha ganado {reward} Puntos!")

    if st.button("🔁 Volver a jugar"):
        del st.session_state.preguntas
        st.rerun()
