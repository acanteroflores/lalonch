import discord
import asyncio
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import streamlit as st
from github import Github
import nest_asyncio

nest_asyncio.apply()  # ← Para evitar conflictos con bucles ya activos


# ────────────────────────────── SECRETS ───────────────────────────── #
TOKEN = st.secrets["DOKEN"]
GUILD_ID = 1389213421144248473
CHANNEL_ID = 1389213421144248476


# ────────────────────────────── GITHUB I/O ────────────────────────── #
@st.cache_resource
def get_repo():
    token = st.secrets["GITHUB_TOKEN"]
    repo_name = st.secrets["REPO_NAME"]
    return Github(token).get_repo(repo_name)


def load_json(path: str, default: dict = {}):
    try:
        contents = get_repo().get_contents(path)
        return json.loads(contents.decoded_content.decode())
    except Exception:
        return default


USERS_PATH = "users.json"  # ← ahora se lee del repo remoto


# ──────────────────────── CREAR EVENTOS DISCORD ───────────────────── #
class DiscordEventCreator(discord.Client):
    def __init__(self, title, description, image_path, date, time, url):
        super().__init__(intents=discord.Intents.default())
        self.title = title
        self.description = description
        self.image_path = image_path
        self.date = date
        self.time = time
        self.url = url

    async def on_ready(self):
        print(f"Bot conectado como {self.user}")
        guild = self.get_guild(GUILD_ID)
        if not guild:
            print("No se encontró el servidor.")
            await self.close();
            return

        try:
            start_dt = datetime.strptime(f"{self.date} {self.time}", "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            end_dt = start_dt + timedelta(hours=1)
        except ValueError:
            print("Fecha u hora inválidas");
            await self.close();
            return

        try:
            with open(self.image_path, "rb") as f:
                image_bytes = f.read()
        except Exception as e:
            print(f"❌ Error al leer la imagen: {e}");
            await self.close();
            return

        try:
            await guild.create_scheduled_event(
                name=self.title,
                description=self.description,
                start_time=start_dt,
                end_time=end_dt,
                location=self.url,
                entity_type=discord.EntityType.external,
                privacy_level=discord.PrivacyLevel.guild_only,
                image=image_bytes
            )
            print("✅ Evento creado correctamente.")
        except Exception as e:
            print(f"❌ Error al crear el evento: {e}")

        await self.close()


# ──────────────────────── ENVIAR MENSAJES DISCORD ─────────────────── #
class DiscordMessenger(discord.Client):
    def __init__(self, message):
        super().__init__(intents=discord.Intents.default())
        self.message = message

    async def on_ready(self):
        print(f"📬 Bot conectado como {self.user}")
        channel = self.get_channel(CHANNEL_ID)
        if not channel:
            print("❌ Canal no encontrado.");
            await self.close();
            return

        users = load_json(USERS_PATH, {})
        detected_user = next((u for u in users if u.lower() in self.message.lower()), None)
        color_hex = users.get(detected_user, {}).get("color", "#808080")
        color_int = int(color_hex.lstrip("#"), 16)

        embed = discord.Embed(title="📢 Nuevo mensaje", description=self.message, color=color_int)
        if detected_user:
            embed.set_footer(text=f"Mensaje detectado de {detected_user}")

        try:
            await channel.send(embed=embed)
            print("✅ Mensaje enviado correctamente.")
        except Exception as e:
            print(f"❌ Error al enviar mensaje: {e}")

        await self.close()


# ─────────────────────────── FUNCIONES PÚBLICAS ───────────────────── #
def createEvent(title, description, image_path, date, time, url):
    client = DiscordEventCreator(title, description, image_path, date, time, url)
    asyncio.run(client.start(TOKEN))


def sendMessage(message):
    client = DiscordMessenger(message)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(client.start(TOKEN))
