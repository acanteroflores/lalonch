from datetime import datetime

# RUTA AL HISTORIAL DE APUESTAS
HISTORY_FILE = "bets/bets_history.json"


def append_bet_to_history(user: str, bets: list):
    history = load_json(HISTORY_FILE, {})
    history.setdefault(user, [])
    history[user].extend(bets)
    save_json(HISTORY_FILE, history)


# Construir apuestas realizadas
bet_records = []
timestamp = datetime.now().isoformat()

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


