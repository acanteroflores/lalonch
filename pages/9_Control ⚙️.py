"""
🛠️ Editor de JSONs – Versión B (persistencia en GitHub)
-------------------------------------------------------
• Todos los archivos (`users.json`, `events.json`, `betsb.json`, `results.json`,
  `eventsPast.json`) se leen y guardan directamente en el repositorio remoto.
• Necesitas definir en los *Secrets* de Streamlit:
    GITHUB_TOKEN = "TU_TOKEN"
    REPO_NAME    = "usuario/repositorio"
"""

import streamlit as st
import json
import random
from github import Github
from resolver import evaluar_apuestas


# ─────────────────── GITHUB HELPERS ───────────────────

@st.cache_resource
def get_repo():
    token = st.secrets["GITHUB_TOKEN"]
    repo_name = st.secrets["REPO_NAME"]
    return Github(token).get_repo(repo_name)


def cargar_json(path: str) -> dict:
    """Lee un JSON del repo. Devuelve {} si no existe o está vacío."""
    try:
        contents = get_repo().get_contents(path)
        return json.loads(contents.decoded_content.decode("utf-8"))
    except Exception:
        return {}


def guardar_json(path: str, data: dict):
    """Crea o actualiza un JSON en el repo."""
    repo = get_repo()
    payload = json.dumps(data, indent=4, ensure_ascii=False)
    try:
        contents = repo.get_contents(path)
        repo.update_file(path, f"Update {path}", payload, contents.sha)
    except Exception:
        repo.create_file(path, f"Create {path}", payload)


# ─────────────────── RUTAS (relativas a la raíz del repo) ───────────────────
USERS_PATH = "users.json"
EVENTS_PATH = "pages/events.json"
BETS_FILE = "pages/betsb.json"
RESULTS_PATH = "pages/results.json"
EVENTS_PAST_PATH = "pages/eventsPast.json"

# ─────────────────── INTERFAZ ───────────────────

st.set_page_config("Editor de Datos")
st.title("🛠️ Editor de JSONs")

# Solo Thony y Artesuave pueden pasar
if st.session_state.get("user") not in ["Thony", "Artesuave"]:
    st.warning("⚠️ Acceso denegado. Redirigiendo a tu perfil...")
    st.switch_page("/Users/thonyshub/PycharmProjects/lonch/pages/1 Profile 👤.py")

seccion = st.sidebar.radio("Selecciona sección", ["👤 Usuarios", "🥊 Eventos"])

# ══════════════════════ USUARIOS ══════════════════════
if seccion == "👤 Usuarios":
    st.header("👤 Editar `users.json`")
    users = cargar_json(USERS_PATH)

    if users:
        usuario_seleccionado = st.selectbox("Selecciona usuario", list(users.keys()))

        if usuario_seleccionado:
            with st.form(f"editar_usuario_{usuario_seleccionado}"):
                st.subheader(f"Editar usuario: {usuario_seleccionado}")
                password = st.text_input("Contraseña", users[usuario_seleccionado]["password"])
                points = st.number_input("Puntos", value=users[usuario_seleccionado]["points"], step=1)
                color = st.color_picker("Color", users[usuario_seleccionado]["color"])
                discord = st.text_input("Discord", users[usuario_seleccionado].get("discord", ""))

                if st.form_submit_button("💾 Guardar cambios"):
                    users[usuario_seleccionado] = {
                        "password": password,
                        "points": points,
                        "color": color,
                        "discord": discord
                    }
                    guardar_json(USERS_PATH, users)
                    st.success("Usuario actualizado.")
    else:
        st.warning("No hay usuarios disponibles para editar.")

    if st.button("❌ Eliminar usuario") and users:
        users.pop(usuario_seleccionado, None)
        guardar_json(USERS_PATH, users)
        st.success("Usuario eliminado.")
        st.rerun()

    st.markdown("---")
    st.subheader("➕ Añadir nuevo usuario")
    with st.form("nuevo_usuario"):
        nuevo_usuario = st.text_input("Nombre de usuario")
        nueva_contraseña = st.text_input("Contraseña", type="password")
        nuevos_puntos = st.number_input("Puntos", min_value=0, step=1, value=100)
        nuevo_color = st.color_picker("Color")
        nuevo_discord = st.text_input("Discord")
        if st.form_submit_button("➕ Añadir"):
            if nuevo_usuario in users:
                st.error("Ese usuario ya existe.")
            else:
                users[nuevo_usuario] = {
                    "password": nueva_contraseña,
                    "points": nuevos_puntos,
                    "color": nuevo_color,
                    "discord": nuevo_discord
                }
                guardar_json(USERS_PATH, users)
                st.success("Usuario añadido.")
                st.rerun()

# ══════════════════════ EVENTOS ══════════════════════
elif seccion == "🥊 Eventos":
    st.header("🥊 Editar `events.json`")
    eventos = cargar_json(EVENTS_PATH)

    if not eventos:
        st.error("No hay eventos en el archivo.")
        st.stop()

    deporte = st.selectbox("Selecciona deporte", list(eventos.keys()))
    combates = eventos[deporte]

    combates_labels = [f"{e.get('event') or e.get('match')} ({e['date']})" for e in combates]
    seleccionado = st.selectbox("Selecciona combate", combates_labels, key="combate_select")

    combate = combates[combates_labels.index(seleccionado)]

    with st.form("editar_combate"):
        st.subheader("✏️ Editar combate")
        combate["date"] = st.text_input("Fecha", combate["date"])
        if deporte == "ufc":
            combate["event"] = st.text_input("Evento", combate["event"])
            combate["location"] = st.text_input("Lugar", combate["location"])
            combate["time"] = st.text_input("Hora", combate["time"])
            combate["fights"] = st.text_area("Lista de combates (uno por línea)",
                                             "\n".join(combate["fights"])).splitlines()
        elif deporte == "csgo":
            combate["match"] = st.text_input("Partido", combate["match"])
        if st.form_submit_button("💾 Guardar cambios"):
            guardar_json(EVENTS_PATH, eventos)
            st.success("Cambios guardados.")

    if st.button("❌ Eliminar combate"):
        eventos[deporte].remove(combate)
        guardar_json(EVENTS_PATH, eventos)
        st.success("Combate eliminado.")
        st.rerun()

    st.markdown("---")
    st.subheader("➕ Añadir Nuevo Evento 🏟")

    with st.form("nuevo_combate"):
        nueva_fecha = st.text_input("Fecha del nuevo combate")

        if deporte == "ufc":
            nuevo_evento = st.text_input("Nombre del evento")
            nuevo_lugar = st.text_input("Lugar")
            nueva_hora = st.text_input("Hora")

            st.markdown("### 🥇 Pelea Estelar")
            main_red = st.text_input("🔴 Luchador esquina roja")
            main_blue = st.text_input("🔵 Luchador esquina azul")

            favorito = st.radio("¿Quién es el favorito?", [main_red, main_blue], horizontal=True)

            red_odds = round(random.uniform(1.3, 1.7), 2) if favorito == main_blue else round(random.uniform(1.9, 2.5),
                                                                                              2)
            blue_odds = round(random.uniform(1.3, 1.7), 2) if favorito == main_red else round(random.uniform(1.9, 2.5),
                                                                                              2)

            st.markdown("### 📋 Combates restantes")
            nuevas_pelea = st.text_area("Lista de peleas (una por línea, formato 'Nombre1 vs Nombre2')").splitlines()

            if st.form_submit_button("➕ Añadir combate"):
                nueva_lista = [f"{main_red} vs {main_blue}"] + nuevas_pelea

                eventos[deporte].append({
                    "date": nueva_fecha,
                    "event": nuevo_evento,
                    "location": nuevo_lugar,
                    "time": nueva_hora,
                    "fights": nueva_lista
                })
                guardar_json(EVENTS_PATH, eventos)

                # Cargar o crear archivo de cuotas
                bets = cargar_json(BETS_FILE)
                bets.setdefault("ufc", [])

                # Añadir pelea estelar
                bets["ufc"].append({
                    "fight": f"{main_red} vs {main_blue}",
                    "red": {"fighter": main_red, "odds": red_odds},
                    "blue": {"fighter": main_blue, "odds": blue_odds}
                })

                # Añadir resto
                for pelea in nuevas_pelea:
                    try:
                        luchador1, luchador2 = [x.strip() for x in pelea.split("vs")]
                        odds1, odds2 = round(random.uniform(1.3, 1.9), 2), round(random.uniform(1.3, 1.9), 2)
                        bets["ufc"].append({
                            "fight": pelea,
                            "red": {"fighter": luchador1, "odds": odds1},
                            "blue": {"fighter": luchador2, "odds": odds2}
                        })
                    except:
                        st.error(f"❌ Formato incorrecto: '{pelea}'")

                guardar_json(BETS_FILE, bets)
                st.success("✅ Evento y apuestas añadidos correctamente.")
                st.rerun()

        elif deporte == "csgo":
            nuevo_match = st.text_input("Match")
            if st.form_submit_button("➕ Añadir combate"):
                eventos[deporte].append({
                    "date": nueva_fecha,
                    "match": nuevo_match
                })
                guardar_json(EVENTS_PATH, eventos)
                st.success("Match añadido.")
                st.rerun()

    # ══════════════════════ RESULTADOS MÁS RECIENTES ══════════════════════
    st.markdown("---")
    st.header("✅ Añadir resultados del evento más reciente")

    eventos = cargar_json(EVENTS_PATH)
    eventos_pasados_db = cargar_json(EVENTS_PAST_PATH)
    bets_data = cargar_json(BETS_FILE)
    results_data = cargar_json(RESULTS_PATH)

    from datetime import datetime as dt

    hoy = dt.now().date()
    eventos_ufc = eventos.get("ufc", [])

    eventos_pasados = [e for e in eventos_ufc if dt.strptime(e["date"], "%Y-%m-%d").date() <= hoy]
    eventos_futuros = [e for e in eventos_ufc if dt.strptime(e["date"], "%Y-%m-%d").date() > hoy]

    evento = sorted(eventos_pasados, key=lambda e: e["date"], reverse=True)[0] if eventos_pasados else \
        sorted(eventos_futuros, key=lambda e: e["date"])[0] if eventos_futuros else None

    if not evento:
        st.warning("No hay eventos disponibles.")
        st.stop()

    # Solo editable 48 h antes o después
    diferencia_horas = (dt.strptime(evento["date"], "%Y-%m-%d") - dt.now()).total_seconds() / 3600
    if diferencia_horas > 48:
        st.info("⏳ Disponible 48 h antes del evento.")
        st.stop()

    st.subheader(f"📅 Evento seleccionado: **{evento['event']}** ({evento['date']})")

    combates_restantes = []
    for idx, combate in enumerate(evento["fights"]):
        if results_data.get(evento["event"], {}).get(combate, {}).get("resolved"):
            continue

        combates_restantes.append(combate)
        fid = f"fight_{idx}"
        st.markdown(f"---\n### 🥊 {combate}")

        red, blue = {"fighter": "Red", "odds": 1.0}, {"fighter": "Blue", "odds": 1.0}
        for cb in bets_data.get("ufc", []):
            if cb["fight"].strip().lower() == combate.strip().lower():
                red, blue = cb["red"], cb["blue"];
                break

        with st.form(f"form_{fid}"):
            winner = st.pills("¿Quién gana?",
                              [f"🔴 {red['fighter']} (x{red['odds']})",
                               f"🔵 {blue['fighter']} (x{blue['odds']})"],
                              key=f"win_{fid}")

            round_val = st.pills("Round x1.20 (opcional)",
                                 ["Sin round", "R1", "R2", "R3", "R4", "R5"],
                                 key=f"rnd_{fid}")
            round_val = None if round_val == "Sin round" else round_val

            method_val = st.pills("Método x1.10 (opcional)",
                                  ["Sin método", "KO", "TKO", "Decisión", "Sumisión"],
                                  key=f"met_{fid}")
            method_val = None if method_val == "Sin método" else method_val

            if st.form_submit_button("✅ Aplicar resultado"):
                esquina_ganadora = "red" if "🔴" in winner else "blue"
                nombre_ganador = red["fighter"] if esquina_ganadora == "red" else blue["fighter"]

                results_data.setdefault(evento["event"], {})[combate] = {
                    "winner_corner": esquina_ganadora,
                    "winner_name": nombre_ganador,
                    "round": round_val,
                    "method": method_val,
                    "resolved": True
                }
                guardar_json(RESULTS_PATH, results_data)
                st.success(f"Resultado guardado para: {combate}")
                st.rerun()

    if not combates_restantes:
        st.info("✅ Todos los combates resueltos. Archivando evento…")
        eventos["ufc"] = [e for e in eventos["ufc"] if e["event"] != evento["event"]]
        guardar_json(EVENTS_PATH, eventos)

        eventos_pasados_db.setdefault("ufc", []).append(evento)
        guardar_json(EVENTS_PAST_PATH, eventos_pasados_db)

        st.success("🎉 Evento archivado.")
        evaluar_apuestas()
        st.rerun()
