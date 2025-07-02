import streamlit as st
import json
import os
from pathlib import Path
from datetime import datetime
import random

DATA_DIR = Path(__file__).parent
USERS_PATH = DATA_DIR / "../users.json"
EVENTS_PATH = DATA_DIR / "events.json"
BETS_FILE = DATA_DIR / "betsb.json"


# ─────────────────── UTILIDADES ───────────────────

def cargar_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def guardar_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def obtener_luchadores_para_combate(bets_data, fight_name):
    for combate in bets_data.get("ufc", []):
        if combate["fight"] == fight_name:
            return combate["red"], combate["blue"]
    return {"fighter": "Red", "odds": 1.0}, {"fighter": "Blue", "odds": 1.0}


# ─────────────────── INTERFAZ ───────────────────

st.set_page_config("Editor de Datos")
st.title("🛠️ Editor de JSONs")

if st.session_state.user != "Thony":
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

    if st.button("❌ Eliminar usuario"):
        if usuario_seleccionado in users:
            users.pop(usuario_seleccionado)
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

    deporte = st.selectbox("Selecciona deporte", list(eventos.keys()))
    combates = eventos[deporte]

    combates_labels = [f"{e.get('event') or e.get('match')} ({e['date']})" for e in combates]
    seleccionado = st.selectbox("Selecciona combate", combates_labels, index=0, key="combate_select")

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

            # 🥇 Pelea estelar
            st.markdown("### 🥇 Pelea Estelar")
            main_red = st.text_input("🔴 Luchador esquina roja")
            main_blue = st.text_input("🔵 Luchador esquina azul")

            favorito = st.radio("¿Quién es el favorito?", [main_red, main_blue], horizontal=True)

            # Calcular odds para main event
            if favorito == main_red:
                red_odds = round(random.uniform(1.9, 2.5), 2)
                blue_odds = round(random.uniform(1.3, 1.7), 2)
            else:
                blue_odds = round(random.uniform(1.9, 2.5), 2)
                red_odds = round(random.uniform(1.3, 1.7), 2)

            # 🥊 Resto de peleas
            st.markdown("### 📋 Combates restantes")
            nuevas_pelea = st.text_area("Lista de peleas (una por línea, formato 'Nombre1 vs Nombre2')").splitlines()

            if st.form_submit_button("➕ Añadir combate"):
                nueva_lista = [f"{main_red} vs {main_blue}"] + nuevas_pelea

                # Guardar evento en events.json
                eventos[deporte].append({
                    "date": nueva_fecha,
                    "event": nuevo_evento,
                    "location": nuevo_lugar,
                    "time": nueva_hora,
                    "fights": nueva_lista
                })
                guardar_json(EVENTS_PATH, eventos)

                # Cargar o crear archivo de cuotas
                if not os.path.exists(BETS_FILE):
                    bets = {"ufc": []}
                else:
                    bets = cargar_json(BETS_FILE)
                    if "ufc" not in bets:
                        bets["ufc"] = []

                # Añadir pelea estelar con cuotas
                bets["ufc"].append({
                    "fight": f"{main_red} vs {main_blue}",
                    "red": {"fighter": main_red, "odds": red_odds},
                    "blue": {"fighter": main_blue, "odds": blue_odds}
                })

                # Añadir resto de peleas con cuotas aleatorias
                for pelea in nuevas_pelea:
                    try:
                        luchador1, luchador2 = [x.strip() for x in pelea.split("vs")]
                        odds1 = round(random.uniform(1.3, 1.9), 2)
                        odds2 = round(random.uniform(1.3, 1.9), 2)

                        bets["ufc"].append({
                            "fight": pelea,
                            "red": {"fighter": luchador1, "odds": odds1},
                            "blue": {"fighter": luchador2, "odds": odds2}
                        })
                    except:
                        st.error(f"❌ Error en el formato de la pelea: '{pelea}' (usa 'Nombre1 vs Nombre2')")

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

    from datetime import datetime

    RESULTS_PATH = DATA_DIR / "results.json"
    EVENTS_PAST_PATH = DATA_DIR / "eventsPast.json"

    eventos = cargar_json(EVENTS_PATH)
    eventos_pasados_archivo = cargar_json(EVENTS_PAST_PATH)
    bets_data = cargar_json(BETS_FILE)
    results_data = cargar_json(RESULTS_PATH)

    hoy = datetime.now().date()
    eventos_ufc = eventos.get("ufc", [])

    # Separar eventos pasados/actuales y futuros
    eventos_pasados = [e for e in eventos_ufc if datetime.strptime(e["date"], "%Y-%m-%d").date() <= hoy]
    eventos_futuros = [e for e in eventos_ufc if datetime.strptime(e["date"], "%Y-%m-%d").date() > hoy]

    # Seleccionar evento más reciente disponible
    if eventos_pasados:
        evento = sorted(eventos_pasados, key=lambda e: e["date"], reverse=True)[0]
    elif eventos_futuros:
        evento = sorted(eventos_futuros, key=lambda e: e["date"])[0]
    else:
        st.warning("No hay eventos disponibles en el archivo.")
        st.stop()

    # Calcular diferencia entre hoy y el evento
    fecha_evento = datetime.strptime(evento["date"], "%Y-%m-%d")
    diferencia_horas = (fecha_evento - datetime.now()).total_seconds() / 3600

    if diferencia_horas > 48:
        st.info("⏳ Aún faltan más de 48 horas para el próximo evento. Esta sección estará disponible 2 días antes.")
        st.stop()

    st.subheader(f"📅 Evento seleccionado: **{evento['event']}** ({evento['date']})")

    combates_restantes = []

    for idx, combate in enumerate(evento["fights"]):
        # Si ya está resuelto, no lo mostramos
        if results_data.get(evento["event"], {}).get(combate, {}).get("resolved", False):
            continue

        combates_restantes.append(combate)
        fid = f"fight_{idx}"

        st.markdown(f"---\n### 🥊 {combate}")

        # Buscar nombres de luchadores y cuotas desde las apuestas
        red = {"fighter": "Red", "odds": 1.0}
        blue = {"fighter": "Blue", "odds": 1.0}

        # Buscar nombres y cuotas desde bets.json
        for combate_data in bets_data.get("ufc", []):
            if combate_data["fight"].strip().lower() == combate.strip().lower():
                red = combate_data["red"]
                blue = combate_data["blue"]
                break

        with st.form(f"form_result_{fid}"):
            # 1️⃣ GANADOR
            winner = st.pills(
                "¿Quién gana?",
                [f"🔴 {red['fighter']} (x{red['odds']})",
                 f"🔵 {blue['fighter']} (x{blue['odds']})"],
                key=f"win_{fid}"
            )

            # 2️⃣ ROUND
            round_sel = st.pills(
                "Round x1.20 (opcional)",
                ["Sin round", "R1", "R2", "R3", "R4", "R5"],
                key=f"rnd_{fid}",
            )
            round_val = None if round_sel == "Sin round" else round_sel

            # 3️⃣ MÉTODO
            method_sel = st.pills(
                "Método x1.10 (opcional)",
                ["Sin método", "KO", "TKO", "Decisión", "Sumisión"],
                key=f"met_{fid}",
            )
            method_val = None if method_sel == "Sin método" else method_sel

            enviado = st.form_submit_button("✅ Aplicar resultado")

            if enviado:
                esquina_ganadora = "red" if "🔴" in winner else "blue"
                nombre_ganador = red["fighter"] if esquina_ganadora == "red" else blue["fighter"]

                # Guardar en results.json
                if evento["event"] not in results_data:
                    results_data[evento["event"]] = {}

                results_data[evento["event"]][combate] = {
                    "winner_corner": esquina_ganadora,
                    "winner_name": nombre_ganador,
                    "round": round_val,
                    "method": method_val,
                    "resolved": True
                }

                guardar_json(RESULTS_PATH, results_data)
                st.success(f"✔️ Resultado guardado para: {combate}")
                st.rerun()

    # Si no quedan combates, mover evento a eventsPast.json
    if not combates_restantes:
        st.info("✅ Todos los combates del evento han sido resueltos. Archivando evento...")

        # Eliminar de eventos.json
        eventos["ufc"] = [e for e in eventos["ufc"] if e["event"] != evento["event"]]
        guardar_json(EVENTS_PATH, eventos)

        # Añadir a eventsPast.json
        if "ufc" not in eventos_pasados_archivo:
            eventos_pasados_archivo["ufc"] = []

        eventos_pasados_archivo["ufc"].append(evento)
        guardar_json(EVENTS_PAST_PATH, eventos_pasados_archivo)

        st.success("🎉 Evento archivado correctamente.")
        st.rerun()




