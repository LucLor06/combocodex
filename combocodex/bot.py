import discord
from discord.ext import commands
from discord import app_commands
import requests
from environment_variables import DISCORD_TOKEN

DOMAIN = 'http://127.0.0.1:8000/api'

def build_url(path):
    url = DOMAIN + path
    return url

bot = commands.Bot(intents=discord.Intents.all(), command_prefix='.')

legends = {legend['name'].lower(): legend for legend in requests.get(build_url('/legends/')).json()}
weapons = {weapon['name'].lower(): weapon for weapon in requests.get(build_url('/weapons/')).json()}
print(legends)
print(weapons)

@bot.event
async def on_ready():
    await bot.tree.sync()


def build_payload(interaction: discord.Interaction, **kwargs):
    kwargs['discord_id'] = interaction.user.id
    return kwargs

@bot.tree.command(name='link', description='Link your discord account to a ComboCodex account')
async def link(interaction: discord.Interaction, username: str, password: str):
    url = build_url('/link/')
    payload = build_payload(interaction, username=username, password=password)
    response = requests.post(url, payload).json()
    await interaction.response.send_message(response['message'], ephemeral=True)

bot.run(DISCORD_TOKEN)