import discord
from discord.ext import commands
from discord import app_commands
import requests
from environment_variables import DISCORD_TOKEN

DOMAIN = 'http://127.0.0.1:8000'

def build_url(path):
    url = DOMAIN + '/api' + path
    return url

bot = commands.Bot(intents=discord.Intents.all(), command_prefix='.')

legend_data = {legend['name'].lower(): legend for legend in requests.get(build_url('/legends/')).json()}
weapon_data = {weapon['name'].lower(): weapon for weapon in requests.get(build_url('/weapons/')).json()}

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


class ComboView(discord.ui.View):
    def __init__(self, interaction: discord.Interaction, combos):
        super().__init__()
        self.combos = combos
        self.combo = combos[0]
        self.length = len(combos)
        self.index = 0
        self.interaction = interaction
        self.next_button = discord.ui.Button(style=discord.ButtonStyle.green, label='Next ▶️')
        self.next_button.callback = self.next_combo
        self.previous_button = discord.ui.Button(style=discord.ButtonStyle.green, label='◀️ Previous')
        self.previous_button.callback = self.previous_combo
        self.first_button = discord.ui.Button(style=discord.ButtonStyle.green, label='⏪ First')
        self.first_button.callback = self.first_combo
        self.last_button = discord.ui.Button(style=discord.ButtonStyle.green, label='Last ⏩')
        self.last_button.callback = self.last_combo
        self.add_item(self.first_button)
        self.add_item(self.previous_button)
        self.add_item(self.next_button)
        self.add_item(self.last_button)

    async def next_combo(self, interaction: discord.Interaction):
        self.index += 1
        if self.index + 1 > self.length:
            self.index = 0
        await interaction.response.defer()
        await self.update()

    async def previous_combo(self, interaction: discord.Interaction):
        self.index -= 1
        if self.index < 0:
            self.index = self.length - 1
        await interaction.response.defer()
        await self.update()
    
    async def first_combo(self, interaction: discord.Interaction):
        self.index = 0
        await interaction.response.defer()
        await self.update()

    async def last_combo(self, interaction: discord.Interaction):
        self.index = self.length - 1
        await interaction.response.defer()
        await self.update()

    async def update(self):
        self.combo = self.combos[self.index]
        await self.interaction.edit_original_response(content=f"**{self.index + 1}/{self.length} Combos**\n{DOMAIN}/combos/{self.combo['id']}/")

@bot.tree.command(name='search', description='Search for combos from ComboCodex')
async def search(interaction: discord.Interaction, legend_one: str | None = None, weapon_one: str | None = None, legend_two: str | None = None, weapon_two: str | None = None):
    url = build_url('/combos/')
    try:
        legends = [legend_data[legend.lower()]['id'] for legend in [legend_one, legend_two] if legend]
        weapons = [weapon_data[weapon.lower()]['id'] for weapon in [weapon_one, weapon_two] if weapon]
    except KeyError:
        await interaction.response.send_message('There was an error with the legend/weapon names you entered.')
    response = requests.get(url, params={'legend': legends, 'weapon': weapons}).json()
    await interaction.response.send_message(DOMAIN + f'/combos/{response[0]['id']}/', view=ComboView(interaction, response))

bot.run(DISCORD_TOKEN)