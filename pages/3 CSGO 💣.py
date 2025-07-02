"""
Streamlit Sports Betting Template 🏆
----------------------------------
Este archivo define una app multipágina "fake" (controlada por un selector en la barra lateral)
que lee dos archivos JSON situados en el mismo directorio:

- **events.json** → calendario de próximos eventos por deporte
- **bets.json**   → apuestas disponibles por deporte (cuota, recompensa…)

Ambos archivos pueden editarse en caliente y la app reflejará los cambios tras recargar
(pulsa `R` ó `↺` en la UI de Streamlit).

Estructura mínima de los JSON:
```
{
  "soccer": [
    {"date": "2025-07-15", "match": "Athletic vs Real Sociedad"},
    {"date": "2025-07-18", "match": "Barça vs Madrid"}
  ],
  "nba": [
    {"date": "2025-07-20", "match": "Lakers vs Celtics"}
  ]
}
```
```
{
  "soccer": [
    {"id": "s1", "description": "Gana Athletic", "odds": 2.1, "reward": 2.1},
    {"id": "s2", "description": "Empate", "odds": 3.3, "reward": 3.3}
  ],
  "nba": [
    {"id": "n1", "description": "Más de 220 puntos", "odds": 1.9, "reward": 1.9}
  ]
}
```
Cada jugador arranca con **1000 puntos**.
Las apuestas se ajustan en saltos de 10 puntos con los botones ➖/➕.
La lógica de negocio es ultra‑simple y sirve solo como demo.
"""

import json
from pathlib import Path
from datetime import datetime

import pandas as pd
import streamlit as st

if "user" not in st.session_state:
    st.switch_page("Login.py")  # manda al login si no hay sesión

# ────────────────────────────────────────────
# Configuración básica de la app
# ────────────────────────────────────────────
st.set_page_config(
    page_title="Deportes & Apuestas",
    page_icon="🎲",
    layout="centered",
    initial_sidebar_state="expanded",
)

DATA_DIR = Path(__file__).parent
EVENTS_FILE = DATA_DIR / "events.json"
BETS_FILE = DATA_DIR / "bets.json"
USERS_FILE = DATA_DIR / "../users.json"

STEP = 10  # puntos que suma / resta cada clic

HISTORY_FILE = DATA_DIR / "bets_history.json"


def append_bet_to_history(user: str, bets: list):
    history = load_json(HISTORY_FILE, {})
    history.setdefault(user, [])
    history[user].extend(bets)
    save_json(HISTORY_FILE, history)


# ────────────────────────────────────────────
# Utils
# ────────────────────────────────────────────

def load_json(path: Path, default: dict) -> dict:
    """Devuelve el JSON del disco o un default si no existe."""
    try:
        with path.open("r", encoding="utf-8") as fp:
            return json.load(fp)
    except FileNotFoundError:
        return default


def save_json(path: Path, data: dict) -> None:
    """Helper opcional si decides persistir cambios en bets/events."""
    with path.open("w", encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=2)


# ────────────────────────────────────────────
# App principal
# ────────────────────────────────────────────

def main():
    events_data = load_json(EVENTS_FILE, {})
    bets_data = load_json(BETS_FILE, {})

    sports = sorted(set(events_data.keys()) | set(bets_data.keys()))
    if not sports:
        st.error("No hay deportes definidos en los JSON. Añade alguno para empezar ✍️")
        st.stop()

    # Estado global por sesión
    if "points" not in st.session_state:
        st.session_state.points = 1000
    if "stakes" not in st.session_state:
        st.session_state.stakes = {}  # key → cantidad apostada

    # ───── Barra lateral
    st.sidebar.markdown("## Menú de deportes 🏟️")
    sport = "csgo"
    title = "ESL🎮 - Counter Strike 🔫 - 2025 SEASSON"
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Puntos disponibles:** {st.session_state.points}")

    # ───── Página principal
    st.header(f"{title.title().upper()}")

    # 1️⃣  Calendario de eventos
    st.subheader("📅 Próximos eventos")
    events = events_data.get(sport, [])
    if events:
        df_events = pd.DataFrame(events)
        df_events["date"] = pd.to_datetime(df_events["date"]).dt.date
        st.table(df_events)
    else:
        st.info("Sin eventos programados. ¡Añade alguno en events.json!")

    # 2️⃣  Apuestas disponibles
    st.subheader("💸 Apuestas disponibles")
    bets = bets_data.get(sport, [])
    total_stake = 0

    if not bets:
        st.warning("No hay apuestas definidas para este deporte, bro 🙃")
    for bet in bets:
        bet_id = bet["id"]
        desc = bet["description"]
        odds = bet.get("odds", "-")
        reward = bet.get("reward", "-")

        key = f"{sport}_{bet_id}"
        st.session_state.stakes.setdefault(key, 0)

        col_desc, col_odds, col_minus, col_amt, col_plus = st.columns([4, 1, 1, 1, 1])
        with col_desc:
            st.markdown(f"**{desc}**")
        with col_odds:
            st.write(f"x{odds}")
        with col_minus:
            if st.button("➖", key=f"minus_{key}"):
                st.session_state.stakes[key] = max(0, st.session_state.stakes[key] - STEP)
        with col_amt:
            st.write(st.session_state.stakes[key])
        with col_plus:
            if st.button("➕", key=f"plus_{key}"):
                if st.session_state.stakes[key] + STEP <= st.session_state.points:
                    st.session_state.stakes[key] += STEP
        total_stake += st.session_state.stakes[key]

    # 3️⃣  Resumen y envío
    st.divider()
    st.markdown(f"### Total apostado: **{total_stake}** puntos")

    send = st.button("🚀 Enviar apuesta")
    if send:
        if total_stake == 0:
            st.warning("No has apostado nada todavía, crack. Dale al + para empezar 💪")
        elif total_stake > st.session_state.points:
            st.error("Te faltan puntos para cubrir esa apuesta 😅")
        else:
            # 1️⃣ Calcula y actualiza los puntos en la sesión
            new_points = st.session_state.points - total_stake
            st.session_state.points = new_points  # ← ya están en memoria

            # 2️⃣ Persiste el cambio en users.json
            users = load_json(USERS_FILE, {})
            users.setdefault(st.session_state.user, {})["points"] = new_points
            save_json(USERS_FILE, users)  # ← se escribe en disco

            timestamp = datetime.now().isoformat()
            bet_records = []

            for bet in bets:
                key = f"{sport}_{bet['id']}"
                amount = st.session_state.stakes.get(key, 0)
                if amount > 0:
                    bet_records.append({
                        "timestamp": timestamp,
                        "sport": sport,
                        "bet_id": bet["id"],
                        "description": bet["description"],
                        "amount": amount,
                        "odds": bet["odds"]
                    })

            # 4️⃣ Guardar en historial
            append_bet_to_history(st.session_state.user, bet_records)

            # 3️⃣ Mensaje de éxito y reseteo de stakes
            st.success(f"Apuesta registrada. ¡Mucha suerte! Te quedan {new_points} puntos.")
            for bet in bets:
                st.session_state.stakes[f"{sport}_{bet['id']}"] = 0

            # ♻️ Fuerza un rerender para que cualquier parte de la app
            #     refresque el valor de puntos inmediatamente
            st.rerun()


if __name__ == "__main__":
    main()