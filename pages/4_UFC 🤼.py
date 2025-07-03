# UFC – Combinadas 2.0  (versión B con persistencia en GitHub)  💊
# Coloca este archivo en la raíz del proyecto y ejecuta:  streamlit run UFC 🤼old.py

import json, pandas as pd
from datetime import datetime
from collections import defaultdict
from pathlib import Path  # sigue importado por si lo necesitas en otro sitio

import streamlit as st
from github import Github
from bots.event_creator import sendMessage


# ───────────────────────────── GitHub helpers ────────────────────────────── #



@st.cache_resource
def get_repo():
    token = st.secrets["GITHUB_TOKEN"]
    repo_name = st.secrets["REPO_NAME"]
    return Github(token).get_repo(repo_name)


def load_json(path: str, default: dict = {}):
    """Lee un JSON desde el repo de GitHub; si no existe, devuelve default."""
    repo = get_repo()
    try:
        contents = repo.get_contents(path)
        return json.loads(contents.decoded_content.decode())
    except Exception:
        return default


def save_json(path: str, data: dict):
    """Guarda (o crea) un JSON en el repo de GitHub."""
    repo = get_repo()
    payload = json.dumps(data, indent=4, ensure_ascii=False)
    try:
        contents = repo.get_contents(path)
        repo.update_file(path, f"Update {path}", payload, contents.sha)
    except Exception:
        repo.create_file(path, f"Create {path}", payload)


# ───────────────────────────── Config básica ────────────────────────────── #

st.set_page_config(page_title="UFC Combinadas 2.0", page_icon="💊", layout="centered")

# Los nombres de archivo son *paths* dentro del repo remoto
EVENTS_FILE = "pages/events.json"
BETS_FILE = "pages/betsb.json"
HISTORY_FILE = "pages/bets_history.json"
USERS_FILE = "users.json"

SPORT = "ufc"
START_POINTS = 1000
STAKE_UNIT = 10
ROUND_BONUS = 1.20  # +20 %
METHOD_BONUS = 1.10  # +10 %

# ───────────────────────────── Login mínimo ─────────────────────────────── #

if "user" not in st.session_state:
    st.switch_page("Login.py")
if "points" not in st.session_state:
    st.session_state.points = START_POINTS
if "picks" not in st.session_state:
    st.session_state.picks = {}

# ───────────────────────────── Datos de eventos ─────────────────────────── #

events_data = load_json(EVENTS_FILE, {})
ufc_events = events_data.get(SPORT, [])

today = datetime.now().date()
next_event = min(
    (e for e in ufc_events if datetime.strptime(e["date"], "%Y-%m-%d").date() >= today),
    key=lambda e: datetime.strptime(e["date"], "%Y-%m-%d").date(),
    default=None
)

fights_next = set(next_event["fights"]) if next_event else set()

# Generar bets_data a partir del próximo evento (si solo trabajas con events.json)
bets_data = []
for fight_str in fights_next:
    if "vs" not in fight_str:
        continue
    red_name, blue_name = map(str.strip, fight_str.split("vs", 1))
    bets_data.append({
        "fight": fight_str,
        "red": {"fighter": red_name, "odds": 1.90},
        "blue": {"fighter": blue_name, "odds": 1.90},
    })

# ───────────────────────────── Layout principal ─────────────────────────── #

st.title("👊 UFC – Combinadas con Pills")

# 1) Calendario de eventos
if ufc_events:
    df_calendar = pd.DataFrame([
        {"📅 Fecha": e["date"], "🎪 Evento": e["event"],
         "📍 Lugar": e["location"], "🧑‍🤝‍🧑 Peleas": len(e["fights"])}
        for e in ufc_events
    ])
    st.subheader("📅 Próximos eventos UFC")
    st.table(df_calendar)
else:
    st.info("No hay eventos UFC disponibles.")

# 2) Ranking “Jugador más en racha”
bets_history = load_json(HISTORY_FILE, {})
user_streaks, max_streaks = defaultdict(int), defaultdict(int)

for user, ub in bets_history.items():
    cur = 0
    for bet in sorted(ub, key=lambda x: x["timestamp"]):
        if bet.get("sport") != SPORT:
            continue
        if bet.get("resolved") and bet.get("won"):
            cur += 1
            max_streaks[user] = max(max_streaks[user], cur)
        elif bet.get("resolved"):
            cur = 0

nombre_top, racha_top = max(max_streaks.items(), key=lambda x: x[1], default=("Nadie", 0))

# Sidebar
st.sidebar.header("💰 Saldo")
st.sidebar.write(f"**{st.session_state.points} pts**")
st.sidebar.markdown("---")
st.sidebar.markdown(f"🏆 **Jugador más en racha:** `{nombre_top}` con `{racha_top}` victorias consecutivas.")
st.sidebar.markdown("---")

# 3) Apuestas del próximo evento (usando betsb.json si existe)
events_all = events_data.get(SPORT, [])
prox_event = next_event
next_event_name = prox_event["event"] if prox_event else None
bets_full = load_json(BETS_FILE, {}).get(SPORT, {})
bets_data = bets_full.get(next_event_name, bets_data)  # prioriza betsb.json si existe

if prox_event:
    st.info(f"🎯 Apuestas para **{prox_event['event']}**")
else:
    st.warning("No hay evento futuro para mostrar apuestas.")

total_stake = 0
for idx, fight in enumerate(bets_data):
    if "red" not in fight or "blue" not in fight:
        continue
    fid, red, blue = fight["fight"], fight["red"], fight["blue"]

    # Bloque UI (estrella + peleas normales)
    if idx == 0:
        st.markdown(
            f"<div style='border:3px solid gold;border-radius:12px;padding:15px;background:#1e1e1e;margin-bottom:20px;'>"
            f"<h3 style='color:gold;text-align:center;'>🌟 PELEA ESTELAR 🌟</h3>"
            f"<h2 style='text-align:center;color:white;'>🥊 {fid}</h2>"
            f"</div>",
            unsafe_allow_html=True,
        )
    else:
        st.subheader(f"🥊 {fid}")

    winner = st.pills(
        "¿Quién gana?",
        [f"🔴 {red['fighter']} (x{red['odds']})", f"🔵 {blue['fighter']} (x{blue['odds']})"],
        key=f"win_{fid}",
    )

    stake = st.slider("Puntos a apostar", 0, st.session_state.points, step=STAKE_UNIT, key=f"stake_{fid}")

    round_val = st.pills(
        "Round x1.20 (opcional)",
        ["Sin round", "R1", "R2", "R3", "R4", "R5"],
        key=f"rnd_{fid}",
    )
    round_val = None if round_val == "Sin round" else round_val

    method_val = st.pills(
        "Método x1.10 (opcional)",
        ["Sin método", "KO", "TKO", "Decisión", "Sumisión"],
        key=f"met_{fid}",
    )
    method_val = None if method_val == "Sin método" else method_val

    st.markdown(
        "----" if idx else "<hr style='border:none;height:2px;background:linear-gradient(to right,gold,#FFD700,gold);margin:25px 0;'/>",
        unsafe_allow_html=True)

    # Cálculo de cuota
    if winner:
        corner = "red" if winner.startswith("🔴") else "blue"
        base_odds = fight[corner]["odds"]
        bonus = (ROUND_BONUS if round_val else 1) * (METHOD_BONUS if method_val else 1)
        eff_odds = round(base_odds * bonus, 2)
        emoji = "✔️" if bonus == 1 else ("💡" if bonus <= 1.1 else "⚡" if bonus < 1.5 else "🔥")

        st.markdown(
            f"<div style='font-size:20px;font-weight:bold;margin:10px 0 20px;text-align:center;'>"
            f"<span style='font-size:25px;'>{stake} pts ➡️ </span>"
            f"💥 <span style='font-size:28px;'>x{eff_odds:.2f}</span> {emoji}"
            f"<span style='font-size:25px;'> = {(stake * eff_odds):.2f} 💰</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

        if stake > 0:
            st.session_state.picks[fid] = {
                "corner": corner, "fighter": fight[corner]["fighter"],
                "stake": stake, "round": round_val, "method": method_val, "odds": eff_odds,
            }
            total_stake += stake
        elif fid in st.session_state.picks:
            st.session_state.picks.pop(fid)

# Resumen
st.markdown("### 📄 Resumen de tu boleto")
if st.session_state.picks:
    st.table(pd.DataFrame([
        {"Pelea": f, "Pick": p["fighter"], "Stake": p["stake"],
         "Cuota": p["odds"], "Round": p["round"] or "-", "Método": p["method"] or "-"}
        for f, p in st.session_state.picks.items()
    ]))
else:
    st.info("Todavía sin combinadas.")

st.markdown(f"**Total apostado:** {total_stake} pts")

# ───────────────────────────── Enviar combinada ─────────────────────────── #

if st.button("🚀 Enviar combinada"):
    if total_stake == 0:
        st.warning("Añade puntos a alguna apuesta.")
        st.stop()
    if total_stake > st.session_state.points:
        st.error("No tienes saldo suficiente.")
        st.stop()

    # 1) Descontar saldo y persistir
    st.session_state.points -= total_stake
    users = load_json(USERS_FILE, {})
    users.setdefault(st.session_state.user, {})["points"] = st.session_state.points
    save_json(USERS_FILE, users)

    # 2) Registrar en historial
    history = load_json(HISTORY_FILE, {})
    history.setdefault(st.session_state.user, [])
    ts = datetime.now().isoformat()

    for f, p in st.session_state.picks.items():
        history[st.session_state.user].append({
            "timestamp": ts, "sport": SPORT, "fight": f,
            "corner": p["corner"], "fighter": p["fighter"],
            "amount": p["stake"], "odds": p["odds"],
            "round": p["round"], "method": p["method"],
            "resolved": False, "won": None,
        })
    save_json(HISTORY_FILE, history)

    # 3) Feedback + Discord
    st.success("💥 Combinada enviada. ¡Mucha suerte!")
    sendMessage(f"🎰 @{st.session_state.user} ha apostado {total_stake} puntos a UFC")
    st.session_state.picks.clear()
    st.rerun()
