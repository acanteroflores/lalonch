import discord
import asyncio
import aiohttp
import io
from datetime import datetime, timedelta, timezone
from pathlib import Path
import json


p1 = "MTM4OTI5NTc2MDIwMTIyNDIxMg.G"
p2 = "2hP_8.OXQ2TqMr-x0eGvjnd7B"
p3 = "0deg5LH2BEx_o4Tc7D8"


def get_token():
    return f"{p1}.{p2}.{p3}"


GUILD_ID = 1389213421144248473  # Reemplaza con tu servidor
CHANNEL_ID = 1389213421144248476
DATA_DIR = Path(__file__).parent.parent
USERS_JSON = DATA_DIR / "users.json"

class DiscordEventCreator(discord.Client):
    def __init__(self, title, description, image_path, date, time, url):
        super().__init__(intents=discord.Intents.default())
        self.title = title
        self.description = description
        self.image_path = image_path
        self.date = date
        self.time = time
        self.url = url
        self.guild = None

    async def on_ready(self):
        print(f"Bot conectado como {self.user}")
        self.guild = self.get_guild(GUILD_ID)

        if not self.guild:
            print("No se encontró el servidor.")
            await self.close()
            return


        # Parsear fecha y hora con zona horaria UTC
        try:
            start_dt = datetime.strptime(f"{self.date} {self.time}", "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            end_dt = start_dt + timedelta(hours=1)
        except ValueError:
            print("Fecha u hora inválidas")
            await self.close()
            return

        # Leer imagen local
        try:
            with open(self.image_path, "rb") as f:
                image_bytes = f.read()
        except Exception as e:
            print(f"❌ Error al leer la imagen: {e}")
            await self.close()
            return

        # Crear evento externo con enlace clicable
        try:
            await self.guild.create_scheduled_event(
                name=self.title,
                description=self.description,
                start_time=start_dt,
                end_time=end_dt,
                location=self.url,  # Enlace clicable en el banner
                entity_type=discord.EntityType.external,
                privacy_level=discord.PrivacyLevel.guild_only,
                image=image_bytes
            )
            print("✅ Evento creado correctamente.")
        except Exception as e:
            print(f"❌ Error al crear el evento: {e}")

        await self.close()


class DiscordMessenger(discord.Client):
    def __init__(self, message):
        super().__init__(intents=discord.Intents.default())
        self.message = message
        self.guild = None

    async def on_ready(self):
        print(f"📬 Bot conectado como {self.user}")
        channel = self.get_channel(CHANNEL_ID)
        if not channel:
            print("❌ Canal no encontrado.")
            await self.close()
            return

        # Cargar users.json
        try:
            with open(USERS_JSON, "r") as f:
                users = json.load(f)
        except Exception as e:
            print(f"❌ Error cargando users.json: {e}")
            await self.close()
            return

        # Buscar si hay un nombre de usuario en el mensaje
        detected_user = None
        for username in users:
            if username.lower() in self.message.lower():
                detected_user = username
                break

        # Obtener color o usar color por defecto
        color_hex = users[detected_user]["color"] if detected_user else "#808080"
        color_int = int(color_hex.replace("#", ""), 16)

        # Crear Embed con color
        embed = discord.Embed(
            title=f"📢 Nuevo mensaje",
            description=self.message,
            color=color_int
        )

        if detected_user:
            embed.set_footer(text=f"Mensaje detectado de {detected_user}", icon_url=None)

        try:
            await channel.send(embed=embed)
            print("✅ Mensaje enviado correctamente.")
        except Exception as e:
            print(f"❌ Error al enviar mensaje: {e}")

        await self.close()


def createEvent(title, description, image_path, date, time, url):
    client = DiscordEventCreator(title, description, image_path, date, time, url)
    asyncio.run(client.start(get_token()))


def sendMessage(message):
    client = DiscordMessenger(message)
    asyncio.run(client.start(get_token()))



