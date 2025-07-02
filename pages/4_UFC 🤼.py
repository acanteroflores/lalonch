import json, pandas as pd
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import streamlit as st
from bots.event_creator import sendMessage

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# ───────── Config básica ──────────
DATA_DIR = Path(__file__).parent
EVENTS_FILE = DATA_DIR / "events.json"  # ← faltaba
BETS_FILE = DATA_DIR / "betsb.json"
HISTORY_FILE = DATA_DIR / "bets_history.json"
USERS_FILE = DATA_DIR / "../users.json"

SPORT = "ufc"
START_POINTS = 1000
STAKE_UNIT = 10
ROUND_BONUS = 1.20  # +20 %
METHOD_BONUS = 1.10  # +10 %

load_json = lambda p, d={}: json.loads(p.read_text("utf-8")) if p.exists() else d
events_data = load_json(EVENTS_FILE, {})
ufc_events = events_data.get("ufc", [])

# Detectar el evento más cercano
today = datetime.now().date()
next_event = min(
    (e for e in ufc_events if datetime.strptime(e["date"], "%Y-%m-%d").date() >= today),
    key=lambda e: datetime.strptime(e["date"], "%Y-%m-%d").date(),
    default=None
)

# Esta línea es la clave
fights_next = set(next_event["fights"]) if next_event else set()

# Generar bets_data desde el evento (solo con eventos.json)
bets_data = []
for fight_str in fights_next:
    if "vs" not in fight_str:
        continue  # combate mal formateado

    red_name, blue_name = map(str.strip, fight_str.split("vs", 1))

    bets_data.append({
        "fight": fight_str,
        "red": {
            "fighter": red_name,
            "odds": 1.90  # valor por defecto
        },
        "blue": {
            "fighter": blue_name,
            "odds": 1.90  # valor por defecto
        }
    })

# ───────── Login mínimo ──────────
if "user" not in st.session_state:
    st.switch_page("Login.py")
if "points" not in st.session_state:
    st.session_state.points = START_POINTS
if "picks" not in st.session_state:
    st.session_state.picks = {}

# ───────── Layout ──────────
st.set_page_config(page_title="UFC Combinadas 2.0", page_icon="💊", layout="centered")
st.title("👊 UFC – Combinadas con Pills")

# ───────── 1) Calendario de eventos ──────────
events_data = load_json(EVENTS_FILE, {})
ufc_events = events_data.get(SPORT, [])

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

# ───────── 2) Detectar el siguiente evento ──────────
today = datetime.now().date()
next_event = min(
    (e for e in ufc_events if datetime.strptime(e["date"], "%Y-%m-%d").date() >= today),
    key=lambda e: datetime.strptime(e["date"], "%Y-%m-%d").date(),
    default=None
)
fights_next = set(next_event["fights"]) if next_event else set()

# ───────── 3) Ranking “Jugador más en racha” ──────────
bets_history = load_json(HISTORY_FILE, {})
user_streaks = defaultdict(int)
max_streaks = defaultdict(int)

for user, user_bets in bets_history.items():
    current = 0
    for bet in sorted(user_bets, key=lambda x: x["timestamp"]):
        if bet.get("sport") != SPORT:
            continue
        if bet.get("resolved") and bet.get("won"):
            current += 1
            max_streaks[user] = max(max_streaks[user], current)
        elif bet.get("resolved"):
            current = 0

top_streak = max(max_streaks.items(), key=lambda x: x[1], default=("Nadie", 0))
nombre_top, racha_top = top_streak

# ───────── Sidebar ──────────
st.sidebar.header("💰 Saldo")
st.sidebar.write(f"**{st.session_state.points} pts**")
st.sidebar.markdown("---")
st.sidebar.markdown(f"🏆 **Jugador más en racha:** `{nombre_top}` con `{racha_top}` victorias consecutivas.")
st.sidebar.markdown("---")

# ───────── 4) Apuestas solo del próximo evento ──────────
# Obtener nombre del evento más próximo
events_all = load_json(EVENTS_FILE, {}).get(SPORT, [])
hoy = datetime.now().date()
prox_event = min(
    (e for e in events_all if datetime.strptime(e["date"], "%Y-%m-%d").date() >= hoy),
    key=lambda e: datetime.strptime(e["date"], "%Y-%m-%d").date(),
    default=None
)
next_event_name = prox_event["event"] if prox_event else None

# Obtener apuestas de ese evento
bets_full = load_json(BETS_FILE, {}).get(SPORT, {})
bets_data = bets_full.get(next_event_name, [])

if next_event:
    st.info(f"🎯 Apuestas para **{next_event['event']}**")
else:
    st.warning("No hay evento futuro para mostrar apuestas.")

total_stake = 0

for idx, fight in enumerate(bets_data):
    if "red" not in fight or "blue" not in fight:
        continue

    fid, red, blue = fight["fight"], fight["red"], fight["blue"]

    if idx == 0:
        with st.container():
            st.markdown(f"""
            <div style="border: 3px solid gold; border-radius: 12px; padding: 15px; background-color: #1e1e1e; margin-bottom: 20px;">
                <h3 style="color: gold; text-align: center;">🌟 PELEA ESTELAR 🌟</h3>
                <h2 style="text-align: center; color: white;">🥊 {fid}</h2>
            </div>
            """, unsafe_allow_html=True)

            winner = st.pills(
                "¿Quién gana?",
                [f"🔴 {red['fighter']} (x{red['odds']})",
                 f"🔵 {blue['fighter']} (x{blue['odds']})"],
                key=f"win_{fid}"
            )

            stake = st.slider("Puntos a apostar", 0, st.session_state.points, step=STAKE_UNIT,
                              key=f"stake_{fid}")

            round_sel = st.pills(
                "Round x1.20 (opcional)",
                ["Sin round", "R1", "R2", "R3", "R4", "R5"],
                key=f"rnd_{fid}",
            )
            round_val = None if round_sel == "Sin round" else round_sel

            method_sel = st.pills(
                "Método x1.10 (opcional)",
                ["Sin método", "KO", "TKO", "Decisión", "Sumisión"],
                key=f"met_{fid}",
            )
            method_val = None if method_sel == "Sin método" else method_sel

            st.markdown("""
                            <hr style='border: none; height: 2px; background: linear-gradient(to right, gold, #FFD700, gold); margin: 25px 0;' />
                            """, unsafe_allow_html=True)
    else:
        st.subheader(f"🥊 {fid}")

        winner = st.pills(
            "¿Quién gana?",
            [f"🔴 {red['fighter']} (x{red['odds']})",
             f"🔵 {blue['fighter']} (x{blue['odds']})"],
            key=f"win_{fid}"
        )

        stake = st.slider("Puntos a apostar", 0, st.session_state.points, step=STAKE_UNIT,
                          key=f"stake_{fid}")

        round_sel = st.pills(
            "Round x1.20 (opcional)",
            ["Sin round", "R1", "R2", "R3", "R4", "R5"],
            key=f"rnd_{fid}",
        )
        round_val = None if round_sel == "Sin round" else round_sel

        method_sel = st.pills(
            "Método x1.10 (opcional)",
            ["Sin método", "KO", "TKO", "Decisión", "Sumisión"],
            key=f"met_{fid}",
        )
        method_val = None if method_sel == "Sin método" else method_sel

        st.markdown("----")

# ─── Cálculo de cuota final + display minimalista ───
if winner:
    corner = "red" if winner.startswith("🔴") else "blue"
    base_odds = fight[corner]["odds"]

    bonus = 1.0
    if round_val:  bonus *= ROUND_BONUS
    if method_val: bonus *= METHOD_BONUS

    eff_odds = round(base_odds * bonus, 2)

    # Emoji según riesgo
    emoji = "✔️" if bonus == 1.0 else ("💡" if bonus <= 1.1
                                       else "⚡" if bonus < 1.5 else "🔥")

    st.markdown(f"""
    <div style='font-size:20px;font-weight:bold;margin:10px 0 20px;
                color:#ffffff;text-align:center;'>
        <span style='font-size:25px;'>{stake} pts ➡️ </span>
        💥 <span style='font-size:28px;'>x{eff_odds:.2f}</span> {emoji}
        <span style='font-size:25px;'> = {(stake * eff_odds):.2f} 💰</span>
    </div>
    """, unsafe_allow_html=True)

    if stake > 0:
        st.session_state.picks[fid] = dict(
            corner=corner, fighter=fight[corner]["fighter"],
            stake=stake, round=round_val, method=method_val, odds=eff_odds
        )
        total_stake += stake
    elif fid in st.session_state.picks:
        st.session_state.picks.pop(fid)

# ───────── Resumen ──────────
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

# ───────── Enviar ──────────
if st.button("🚀 Enviar combinada"):
    if total_stake == 0:
        st.warning("Añade puntos a alguna apuesta.")
        st.stop()
    if total_stake > st.session_state.points:
        st.error("No tienes saldo suficiente.")
        st.stop()

    # 1. Actualizar saldo
    st.session_state.points -= total_stake
    users = load_json(USERS_FILE, {})
    users.setdefault(st.session_state.user, {})["points"] = st.session_state.points
    save_json(USERS_FILE, users)

    # 2. Registrar apuestas
    history = load_json(HISTORY_FILE, {})
    history.setdefault(st.session_state.user, [])
    ts = datetime.now().isoformat()

    for f, p in st.session_state.picks.items():
        history[st.session_state.user].append({
            "timestamp": ts, "sport": SPORT, "fight": f, "corner": p["corner"],
            "fighter": p["fighter"], "amount": p["stake"], "odds": p["odds"],
            "round": p["round"], "method": p["method"], "resolved": False
        })
    save_json(HISTORY_FILE, history)

    # 3. Feedback + Discord
    st.success("💥 Combinada enviada. ¡Mucha suerte!")
    sendMessage(f"🎰 @{st.session_state.user} ha apostado {total_stake} puntos a UFC")
    st.session_state.picks.clear()
    st.rerun()
