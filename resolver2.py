import json
import os
from pathlib import Path

DATA_DIR = Path(__file__).parent
USERS_PATH = DATA_DIR / "users.json"
BETS_PATH = DATA_DIR / "pages/bets_history.json"
RESULTS_PATH = DATA_DIR / "pages/results.json"


def cargar_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def guardar_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# Cargar archivos
users = cargar_json(USERS_PATH)
bets = cargar_json(BETS_PATH)
results = cargar_json(RESULTS_PATH)

for event_name, event_data in results.items():
    if event_data.get("checked") is True:
        continue  # Ya fue procesado

    for username, apuestas in bets.items():
        for apuesta in apuestas:
            if apuesta.get("resolved"):
                continue  # Ya procesada

            if apuesta["sport"] != "ufc":
                continue  # Solo UFC por ahora

            fight = apuesta["fight"]
            resultado = event_data.get(fight)

            if not resultado:
                continue  # Combate sin resultado

            apuesta["resolved"] = True

            win = (
                    apuesta["corner"] == resultado["winner_corner"] and
                    apuesta["fighter"].strip().lower() == resultado["winner_name"].strip().lower()
            )

            apuesta["won"] = win

            if win:
                reward = apuesta["amount"] * apuesta["odds"]

                # Bonus por round
                if apuesta.get("round") and apuesta["round"].startswith("R") and apuesta["round"] == resultado.get(
                        "round"):
                    reward *= 1.2

                # Bonus por método
                metodos_validos = {"KO", "TKO", "Decisión", "Sumisión"}
                if apuesta.get("method") in metodos_validos and apuesta["method"] == resultado.get("method"):
                    reward *= 1.1

                reward = round(reward)

                # ✅ GUARDAR GANANCIA EN LA APUESTA
                apuesta["reward"] = reward

                # ✅ SUMAR A USUARIO
                users[username]["points"] += reward
            else:
                apuesta["reward"] = 0

    # Marcar evento como ya revisado
    results[event_name]["checked"] = True

# Guardar cambios
guardar_json(USERS_PATH, users)
guardar_json(BETS_PATH, bets)
guardar_json(RESULTS_PATH, results)

print("✅ Apuestas evaluadas y puntos actualizados.")
