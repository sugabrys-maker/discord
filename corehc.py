import os
import asyncio
from flask import Flask
from threading import Thread
import discord
from discord.ext import commands

# --- Serwer HTTP dla Render (zapobiega wyłączeniu aplikacji) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot Discord jest uruchomiony!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- Konfiguracja Bota Discord ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Zamknij Ticket", style=discord.ButtonStyle.red, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Kanał zostanie zamknięty za 3 sekundy...")
        await asyncio.sleep(3)
        await interaction.channel.delete()

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Stwórz Ticket", style=discord.ButtonStyle.green, custom_id="create_ticket")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        category = discord.utils.get(guild.categories, name="Tickety")
        if not category:
            category = await guild.create_category("Tickety")

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        }

        # Nazwa kanału musi być napisana małymi literami
        channel_name = f"ticket-{interaction.user.name.lower()}"
        ticket_channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites
        )

        await ticket_channel.send(
            f"Witaj {interaction.user.mention}! Opisz swój problem, a administracja wkrótce odpowie.",
            view=CloseTicketView()
        )
        await interaction.response.send_message(f"Utworzono ticket: {ticket_channel.mention}", ephemeral=True)

@bot.event
async def on_ready():
    bot.add_view(TicketView())
    bot.add_view(CloseTicketView())
    print(f"Zalogowano jako {bot.user.name}")

@bot.command()
@commands.has_permissions(administrator=True)
async def panel(ctx):
    await ctx.send("Kliknij poniższy przycisk, aby otworzyć ticket:", view=TicketView())

if __name__ == "__main__":
    keep_alive()
    TOKEN = os.getenv("DISCORD_TOKEN")
    if not TOKEN:
        raise ValueError("Brak zmiennej środowiskowej DISCORD_TOKEN! Ustaw ją w panelu Render.")
    bot.run(TOKEN)