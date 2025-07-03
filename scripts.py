from datetime import datetime
import json
import os
from github import Github
import streamlit as st  # si usas fuera de Streamlit, cambia por os.environ

# ─────────────────── CONFIGURACIÓN ───────────────────

HISTORY_PATH = "bets_history.json"  # Ruta relativa dentro del repo


def _get_repo():
    token = st.secrets.get("GITHUB_TOKEN", os.environ.get("GITHUB_TOKEN"))
    repo_name = st.secrets.get("REPO_NAME", os.environ.get("REPO_NAME"))
    return Github(token).get_repo(repo_name)


def _load_json(repo, path: str, default: dict = {}) -> dict:
    try:
        contents = repo.get_contents(path)
        return json.loads(contents.decoded_content.decode())
    except Exception:
        return default


def _save_json(repo, path: str, data: dict):
    payload = json.dumps(data, indent=4, ensure_ascii=False)
    try:
        contents = repo.get_contents(path)
        repo.update_file(path, f"Update {path}", payload, contents.sha)
    except Exception:
        repo.create_file(path, f"Create {path}", payload)


# ─────────────────── FUNCIÓN DE APPEND ───────────────────

def append_bet_to_history_github(user: str, bets: list):
    """Añade apuestas al historial en GitHub."""
    repo = _get_repo()
    history = _load_json(repo, HISTORY_PATH, {})
    history.setdefault(user, [])
    history[user].extend(bets)
    _save_json(repo, HISTORY_PATH, history)
