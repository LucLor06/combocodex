import discord
from discord.ext import commands
from discord import app_commands
import requests
from environment_variables import DISCORD_TOKEN
from datetime import datetime, timedelta, timezone

bot = commands.Bot(intents=discord.Intents.all(), command_prefix='.')

DOMAIN = 'http://127.0.0.1:8000'

UPLOAD_GUILDS = [discord.Object(id=612653706730668033), discord.Object(id=338425553935925250)]

def build_url(path):
    url = DOMAIN + '/api' + path
    return url

def get_message_link(message: discord.Message):
    return f'https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}'

combocodex = None
manager_role = None
submissions_channel = None

def output_to_message(success, message):
    emoji = '❗️' if not success else '✅'
    prefix = 'Error' if not success else 'Success' 
    return f'{emoji}**{prefix}**{emoji} {message}'


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
    url = build_url('/combos/search/')
    try:
        legends = [legend_data[legend.lower()]['id'] for legend in [legend_one, legend_two] if legend]
        weapons = [weapon_data[weapon.lower()]['id'] for weapon in [weapon_one, weapon_two] if weapon]
    except KeyError:
        await interaction.response.send_message('There was an error with the legend/weapon names you entered.')
    response = requests.get(url, params={'legend': legends, 'weapon': weapons}).json()
    await interaction.response.send_message(DOMAIN + f'/combos/{response[0]['id']}/', view=ComboView(interaction, response))

async def upload_combo(interaction, legend_one, weapon_one, legend_two, weapon_two, users, video):
    legend_one = legend_data[legend_one.lower()]['id']
    weapon_one = weapon_data[weapon_one.lower()]['id']
    legend_two = legend_data[legend_two.lower()]['id']
    weapon_two = weapon_data[weapon_two.lower()]['id']
    user_one_id = '0'
    user_one_name = ''
    if users[0]:
        user_one_id = users[0].id
        user_one_name = users[0].display_name
    user_two_id = '0'
    user_two_name = ''
    if users[1]:
        user_two_id = users[1].id
        user_two_name = users[1].display_name
    payload = build_payload(interaction, legend_one=legend_one, weapon_one=weapon_one, legend_two=legend_two, weapon_two=weapon_two, user_one_id=user_one_id, user_one_name=user_one_name, user_two_id=user_two_id, user_two_name=user_two_name)
    response = requests.post(build_url('/combos/submit/'), payload, files={'video': ('video.mp4', video)})
    return response

async def parse_legends_weapons(message: discord.Message):
    message = message.content.lower().split()
    legends = []
    for i, word in enumerate(message):
        for legend in legend_data.keys():
            if word == legend:
                legends.append(word)
            elif word in legend and i + 1 < len(message):
                word = f'{word} {message[i + 1]}'
                if word == legend:
                    legends.append(word)
                    message.pop(i + 1)
    legends = legends[:2]
    weapons = []
    for i, word in enumerate(message):
        for weapon in weapon_data.keys():
            if word == weapon:
                weapons.append(word)
            elif word in weapon and i + 1 < len(message):
                word = f'{word} {message[i + 1]}'
                if word == weapon:
                    weapons.append(word)
                    message.pop(i + 1)
    weapons = weapons[:2]
    return legends[0], weapons[0], legends[1], weapons[1]
    
async def parse_users(message: discord.Message):
    mentions = message.mentions[:2]
    while len(mentions) < 2:
        mentions.append(None)
    return mentions

async def upload_site(interaction: discord.Interaction, message: discord.Message):
    if '🔼' in list(map(lambda reaction: reaction.emoji, message.reactions)):
        return False, 'This combo has already been uploaded to the site'
    try:
        legends_weapon = await parse_legends_weapons(message)
    except IndexError:
        return False, 'Was not able to properly parse the legends and weapons in the referenced message'
    users = await parse_users(message)
    try:    
        if not message.attachments[0].content_type.startswith('video'):
            return False, 'Not a valid video format'
        video = await message.attachments[0].read()
    except IndexError:
        return False, 'No video attached'
    response = await upload_combo(interaction, *legends_weapon, users, video)
    if response.status_code != 200:
        return False, 'Something went wrong with handling your combo upload'    
    await message.add_reaction('🔼')
    return True, 'Combo successfully submitted'

@bot.tree.context_menu(name='Upload to site')
async def upload_site_context_menu(interaction: discord.Interaction, message: discord.Message):
    upload_site_success, upload_site_message = await upload_site(interaction, message)
    await interaction.response.send_message(output_to_message(upload_site_success, upload_site_message), ephemeral=True)


async def upload_discord(interaction: discord.Interaction, message: discord.Message):
    combocodex = bot.get_guild(612653706730668033)
    manager_role = combocodex.get_role(894343287526277153)
    if manager_role not in interaction.user.roles and interaction.user.id != 319651518603198465:
        return False, 'Only combo managers can upload to the discord'
    if '✅' in message.reactions:
        return False, 'This combo has already been uploaded to the discord'
    server = combocodex
    try:
        legends_weapons = await parse_legends_weapons(message)
    except IndexError:
        return False, 'Was not able to properly parse the legends and weapons in the referenced message'
    legends = [legends_weapons[0], legends_weapons[2]]
    weapons = [legends_weapons[1], legends_weapons[3]]
    for i, weapon in enumerate(weapons):
        if weapon == 'battle boots':
            weapons[i] = 'boots'
        elif weapon == 'gauntlets':
            weapon[i] = 'gaunts'
    channels = []
    if legends[0] == 'universal' and legends[1] == 'universal':
        channels = [discord.utils.get(server.channels, name=f'{weapons[0]}-universals'), discord.utils.get(server.channels, name=f'{weapons[1]}-universals')]
        if channels[0] == channels [1]:
            channels = [channels[0]]
    elif weapons[0] == weapons[1]:
        channels = [discord.utils.get(server.channels, name=f'dual-{weapons[1]}')]
    else:
        channels = [discord.utils.get(server.channels, name=f'{weapons[0]}-{weapons[1]}'), discord.utils.get(server.channels, name=f'{weapons[1]}-{weapons[0]}')]
    try:    
        if not message.attachments[0].content_type.startswith('video'):
            return False, 'Not a valid video format'
    except IndexError:
            return False, 'No video attached to message'
    for channel in channels:
        video = await message.attachments[0].to_file()
        await channel.send(file=video)
    await message.add_reaction('✅')
    return True, 'Combo uploaded to discord'

@bot.tree.context_menu(name='Upload to discord')
async def upload_discord_context_menu(interaction: discord.Interaction, message: discord.Message):
    upload_discord_success, upload_discord_message = await upload_discord(interaction, message)
    await interaction.response.send_message(output_to_message(upload_discord_success, upload_discord_message), ephemeral=True)

@bot.tree.context_menu(name='Upload to both')
async def upload_both(interaction: discord.Interaction, message: discord.Message):
    upload_site_success, upload_site_message = await upload_site(interaction, message)
    upload_discord_success, upload_discord_message = await upload_discord(interaction, message)
    await interaction.response.send_message(f'Upload to site: {output_to_message(upload_site_success, upload_site_message)}\nUpload to discord: {output_to_message(upload_discord_success, upload_discord_message)}')

@bot.tree.command(name='upload_last', description='Upload all combos sent by you in submissions in the past x minutes')
async def upload_last(interaction: discord.Interaction, minutes: int = 15, log_output: bool = False):
    if not 0 < minutes <= 60:
        await interaction.response.send_message('Please provide a valid amount of minutes (1 - 60).')
        return
    await interaction.response.send_message(f'Uploading combos sent by you in the last {minutes} minutes. This may take a while.', ephemeral=True)
    combocodex = bot.get_guild(612653706730668033)
    submissions_channel = combocodex.get_channel(614586175189155840)
    after_time = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    upload_site_count = 0
    upload_discord_count = 0
    log = []
    async for message in submissions_channel.history(after=after_time):
        if message.author == interaction.user and len(message.attachments) == 1 and message.attachments[0].content_type.startswith('video'):
            upload_discord_success, upload_discord_message = await upload_discord(interaction, message)
            if upload_discord_success:
                upload_discord_count += 1
            upload_site_success, upload_site_message = await upload_site(interaction, message)
            if upload_site_success:
                upload_site_count += 1
            if log_output:
                log.append(f'{get_message_link(message)}\nUpload to site: {output_to_message(upload_site_success, upload_site_message)}\nUpload to discord: {output_to_message(upload_discord_success, upload_discord_message)}')
    response = f'{upload_site_count} combos uploaded to the site and {upload_discord_count} uploaded to the discord'
    if log_output:
        response += f'\n\n{"\n\n".join(log)}'
    await interaction.edit_original_response(content=response)

bot.run(DISCORD_TOKEN)