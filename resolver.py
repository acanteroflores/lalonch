"""
Evaluador de apuestas (versión B, con persistencia en GitHub) ✅
---------------------------------------------------------------
• Lee `users.json`, `bets_history.json` y `results.json` desde el repositorio.
• Actualiza puntos y marca apuestas/resultados como resueltos.
• Todo en una única función `evaluar_apuestas()`.
• Necesita los *Secrets* o variables de entorno:

   GITHUB_TOKEN (= Personal Access Token)
   REPO_NAME    (= "usuario/repositorio")
"""

import json
import os
from github import Github
import streamlit as st  # Si lo usas fuera de Streamlit, cambia por os.environ


# ─────────────────── GITHUB HELPERS ───────────────────

def _get_repo():
    """Devuelve el repo usando GITHUB_TOKEN + REPO_NAME."""
    token = st.secrets.get("GITHUB_TOKEN", os.environ.get("GITHUB_TOKEN"))
    repo_name = st.secrets.get("REPO_NAME", os.environ.get("REPO_NAME"))
    return Github(token).get_repo(repo_name)


def _cargar_json(repo, path: str) -> dict:
    try:
        contents = repo.get_contents(path)
        return json.loads(contents.decoded_content.decode())
    except Exception:
        return {}  # archivo inexistente o vacío


def _guardar_json(repo, path: str, data: dict):
    payload = json.dumps(data, indent=4, ensure_ascii=False)
    try:
        contents = repo.get_contents(path)
        repo.update_file(path, f"Update {path}", payload, contents.sha)
    except Exception:  # si no existe, se crea
        repo.create_file(path, f"Create {path}", payload)


# ─────────────────── FUNCIÓN PRINCIPAL ───────────────────

def evaluar_apuestas():
    """Procesa resultados UFC y actualiza users/bets_history/results."""
    repo = _get_repo()

    USERS_PATH = "users.json"
    BETS_PATH = "pages/bets_history.json"
    RESULTS_PATH = "pages/results.json"

    users = _cargar_json(repo, USERS_PATH)
    bets = _cargar_json(repo, BETS_PATH)
    results = _cargar_json(repo, RESULTS_PATH)

    for event_name, event_data in results.items():
        if event_data.get("checked"):
            continue  # evento ya procesado

        for username, apuestas in bets.items():
            for apuesta in apuestas:
                if apuesta.get("resolved") or apuesta.get("sport") != "ufc":
                    continue

                resultado = event_data.get(apuesta["fight"])
                if not resultado:
                    continue  # combate sin resultado

                apuesta["resolved"] = True
                win = (
                        apuesta["corner"] == resultado["winner_corner"] and
                        apuesta["fighter"].strip().lower() ==
                        resultado["winner_name"].strip().lower()
                )
                apuesta["won"] = win

                if win:
                    reward = apuesta["amount"] * apuesta["odds"]

                    # Bonus round
                    if (apuesta.get("round") and
                            apuesta["round"] == resultado.get("round")):
                        reward *= 1.20

                    # Bonus método
                    if (apuesta.get("method") and
                            apuesta["method"] == resultado.get("method")):
                        reward *= 1.10

                    reward = round(reward)
                    apuesta["reward"] = reward
                    users[username]["points"] += reward
                else:
                    apuesta["reward"] = 0

        # marcar evento evaluado
        results[event_name]["checked"] = True

    # persistir cambios
    _guardar_json(repo, USERS_PATH, users)
    _guardar_json(repo, BETS_PATH, bets)
    _guardar_json(repo, RESULTS_PATH, results)

    print("✅ Apuestas evaluadas y puntos actualizados.")


# ─────────────────── EJECUCIÓN DIRECTA ───────────────────
if __name__ == "__main__":
    evaluar_apuestas()
