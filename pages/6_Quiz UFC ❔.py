import streamlit as st
import json
import random
from pathlib import Path
import os

DATA_DIR = Path(__file__).parent
QUESTIONS_FILE = DATA_DIR.parent / "quiz/ufcQ.json"
USERS_PATH = DATA_DIR / "../users.json"


def cargar_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def guardar_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


users = cargar_json(USERS_PATH)

# ---------- Config básica ----------
st.set_page_config(page_title="Quiz UFC", layout="centered")
st.title("🥊 Quiz Histórico de UFC")

username = st.session_state.get("user")

# ---------- Carga de preguntas una sola vez ----------
if "preguntas" not in st.session_state:
    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        st.session_state.preguntas = json.load(f)
    random.shuffle(st.session_state.preguntas)      # baraja 1 vez
    st.session_state.indice = 0                     # pregunta actual
    st.session_state.puntuacion = 0                 # aciertos
    st.session_state.respuesta_mostrada = False     # ya enseñó feedback
    st.session_state.ultima_correcta = False        # flag de acierto

# Alias cortos
preguntas = st.session_state.preguntas
i = st.session_state.indice

# ---------- Quiz en marcha ----------
if i < len(preguntas):
    q = preguntas[i]
    st.subheader(f"Pregunta {i + 1} de {len(preguntas)}")
    st.info(f"Puntuación: {st.session_state.puntuacion}")

    # --- FORMULARIO ---
    with st.form(key=f"form_{i}", clear_on_submit=False):
        seleccion = st.radio(
            q["pregunta"],
            q["opciones"],
            key=f"radio_{i}"
        )
        confirm = st.form_submit_button("✅ Confirmar respuesta")

    # Al pulsar Confirmar:
    if confirm and not st.session_state.respuesta_mostrada:
        st.session_state.ultima_correcta = (seleccion == q["respuesta_correcta"])
        st.session_state.respuesta_mostrada = True
        if st.session_state.ultima_correcta:
            st.session_state.puntuacion += 1

    # --- FEEDBACK + Botón Continuar ---
    if st.session_state.respuesta_mostrada:
        if st.session_state.ultima_correcta:
            st.success("¡Correcto! 🎉")
        else:
            st.error(f"Incorrecto 😢 La respuesta era: **{q['respuesta_correcta']}**")

        if st.button("➡️ Continuar"):
            st.session_state.indice += 1
            st.session_state.respuesta_mostrada = False
            st.rerun()

# ---------- Final del quiz ----------
else:
    st.balloons()
    if username in users:
        reward = int(st.session_state.puntuacion) * 75
        users[username]["points"] += reward
        guardar_json(USERS_PATH, users)
        st.success(f"✅ ¡{reward} puntos añadidos a {username}!")
    else:
        st.error("⚠️ No se encontró el usuario en sesión o en la base de datos.")
    st.success(f"🎯 Quiz completado: {st.session_state.puntuacion}/{len(preguntas)} correctas.")
    if st.button("🔁 Volver a jugar"):
        del st.session_state.preguntas   # reset total
        st.rerun()
