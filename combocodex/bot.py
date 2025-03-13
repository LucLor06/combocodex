import discord
from discord.ext import commands
from discord import app_commands
import requests
from environment_variables import DISCORD_TOKEN
import httpx
import asyncio
from datetime import datetime, timedelta, timezone

bot = commands.Bot(intents=discord.Intents.all(), command_prefix='.')

DOMAIN = 'https://www.combocodex.com'

DELETE_AFTER = 30
COLOR_BASE = discord.Color(int("239063", 16))
COLOR_SUCCESS = discord.Color(int("91db69", 16))
COLOR_ERROR = discord.Color(int("e83b3b", 16))

INVITE_LINK = 'https://discord.com/oauth2/authorize?client_id=1086175083107717150'

UPLOAD_GUILDS = [discord.Object(id=612653706730668033), discord.Object(id=338425553935925250)]

def build_url(path):
    url = DOMAIN + '/api' + path
    return url

def get_message_link(message: discord.Message):
    return f'https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}'

combocodex = None
trusted_role = None
submissions_channel = None
logging_channel = None
client = None

async def output_to_embed(upload_type, success, message):
    color = COLOR_SUCCESS if success else COLOR_ERROR
    emoji = '✅' if upload_type == 'discord' else '🔼'
    success_emoji = '👍' if success else '❗️'
    title = f'Upload to {upload_type.title()}'
    embed = discord.Embed(title=f'{emoji} **{title}** {emoji}', description=f'{success_emoji} {message}', color=color, timestamp=datetime.now())
    return embed

async def response_defer_embed(upload_type):
    title = f'Upload to {upload_type.title()}'
    embed = discord.Embed(title=title, description='Working on it. This may take a while...', color=COLOR_BASE)
    return embed

async def delete_original_response(interaction: discord.Interaction, delete_after=DELETE_AFTER):
    await asyncio.sleep(delete_after)
    original_response = await interaction.original_response()
    await original_response.delete()


legend_data = {legend['name'].lower(): legend for legend in requests.get(build_url('/legends/')).json()}
weapon_data = {weapon['name'].lower(): weapon for weapon in requests.get(build_url('/weapons/')).json()}


@bot.event
async def on_ready():
    await bot.tree.sync()
    for guild in UPLOAD_GUILDS:
        print(f'syncing guild: {guild.id}')
        try:
            await bot.tree.sync(guild=guild)
        except:
            print(f'Unable to sync guild: {guild.id}')
    print('Creating httpx client')
    global client
    client = httpx.AsyncClient()
    global combocodex
    combocodex = bot.get_guild(612653706730668033)
    global trusted_role
    trusted_role = combocodex.get_role(1169793321779089438)
    global submissions_channel
    submissions_channel = combocodex.get_channel(614586175189155840)
    global logging_channel
    logging_channel = combocodex.get_channel(1349496200956739645)

@bot.event
async def on_disconnect():
    print('Disconnecting...')
    if client:
        print('Closing httpx client')
        await client.aclose()

@bot.event
async def on_resumed():
    print('Resuming...')
    global client
    client = httpx.AsyncClient()

def build_payload(interaction: discord.Interaction | commands.Context, **kwargs):
    kwargs['discord_id'] = interaction.user.id if isinstance(interaction, discord.Interaction) else interaction.author.id
    return kwargs

@bot.tree.command(name='invite', description='Provides a link to invite this bot to your server')
async def invite(interaction: discord.Interaction):
    await interaction.response.send_message(f'Click the link below to invite ComboCodex to your server\n{INVITE_LINK}')

@bot.tree.command(name='link', description='Link your discord account to a ComboCodex account')
async def link(interaction: discord.Interaction, username: str, password: str):
    url = build_url('/link/')
    payload = build_payload(interaction, username=username, password=password)
    response = await client.post(url, data=payload).json()
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
        return
    response = await client.get(url, params={'legend': legends, 'weapon': weapons})
    response = response.json()
    await interaction.response.send_message(DOMAIN + f"/combos/{response[0]['id']}/", view=ComboView(interaction, response))

async def upload_combo(interaction, legend_one, weapon_one, legend_two, weapon_two, users, video):
    legend_one = legend_data[legend_one.lower()]['id']
    weapon_one = weapon_data[weapon_one.lower()]['id']
    legend_two = legend_data[legend_two.lower()]['id']
    weapon_two = weapon_data[weapon_two.lower()]['id']
    user_one_id = '0'
    user_one_name = ''
    if users[0]:
        user_one_id = users[0].id
        user_one_name = users[0].name
    user_two_id = '0'
    user_two_name = ''
    if users[1]:
        user_two_id = users[1].id
        user_two_name = users[1].name
    payload = build_payload(interaction, legend_one=legend_one, weapon_one=weapon_one, legend_two=legend_two, weapon_two=weapon_two, user_one_id=user_one_id, user_one_name=user_one_name, user_two_id=user_two_id, user_two_name=user_two_name)
    response = await client.post(build_url('/combos/submit/'), data=payload, files={'video': ('video.mp4', video)}, timeout=300)
    return response

async def parse_legends_weapons(string: str):
    message = string.lower().replace('_', ' ').replace('-', ' ').replace('+', ' ').replace('(', '').replace(')', '').replace('[', '').replace(']', '').replace('{', '').replace('}', '').split()
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

async def upload_site(interaction: discord.Interaction | commands.Context, message: discord.Message):
    if '🔼' in list(map(lambda reaction: reaction.emoji, message.reactions)):
        return False, 'This combo has already been uploaded to the site'
    try:
        legends_weapon = await parse_legends_weapons(message.content)
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
    return True, 'Combo uploaded to site'

@bot.tree.context_menu(name='Upload to Site', guilds=UPLOAD_GUILDS)
async def upload_site_context_menu(interaction: discord.Interaction, message: discord.Message):
    await interaction.response.send_message(embed= await response_defer_embed('site'))
    upload_site_success, upload_site_message = await upload_site(interaction, message)
    embed = await output_to_embed('site', upload_site_success, upload_site_message)
    await interaction.edit_original_response(embed=embed)
    await logging_channel.send(content=message.jump_url, embed=embed)
    await delete_original_response(interaction)

@bot.command(name='upload_site')
async def upload_site_old(ctx: commands.Context):
    if ctx.guild != combocodex:
        await ctx.reply('This command is only available in ComboCodex!', delete_after=DELETE_AFTER)
        return
    message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
    original_response = await ctx.reply(embed= await response_defer_embed('site'))
    await ctx.message.delete()
    upload_site_success, upload_site_message = await upload_site(ctx, message)
    embed = await output_to_embed('site', upload_site_success, upload_site_message)
    await original_response.edit(embed=embed, delete_after=DELETE_AFTER)
    await logging_channel.send(content=message.jump_url, embed=embed)

async def upload_discord(interaction: discord.Interaction, message: discord.Message):
    sender_roles = interaction.user.roles if isinstance(interaction, discord.Interaction) else interaction.author.roles
    if trusted_role not in sender_roles:
        return False, 'Only combo managers can upload to the discord'
    if '✅' in list(map(lambda reaction: reaction.emoji, message.reactions)):
        return False, 'This combo has already been uploaded to the discord'
    server = combocodex
    try:
        legends_weapons = await parse_legends_weapons(message.content)
    except IndexError:
        return False, 'Was not able to properly parse the legends and weapons in the referenced message'
    legends = [legends_weapons[0], legends_weapons[2]]
    weapons = [legends_weapons[1], legends_weapons[3]]
    channel_weapons = []
    for i, weapon in enumerate(weapons):
        if weapon == 'battle boots':
            weapon = 'boots'
        elif weapon == 'gauntlets':
            weapon = 'gaunts'
        channel_weapons.append(weapon)
    channels = []
    if legends[0] == 'universal' and legends[1] == 'universal':
        channels = [discord.utils.get(server.channels, name=f'{channel_weapons[0]}-universals'), discord.utils.get(server.channels, name=f'{channel_weapons[1]}-universals')]
        if channels[0] == channels [1]:
            channels = [channels[0]]
    elif channel_weapons[0] == channel_weapons[1]:
        channels = [discord.utils.get(server.channels, name=f'dual-{channel_weapons[1]}')]
    else:
        channels = [discord.utils.get(server.channels, name=f'{channel_weapons[0]}-{channel_weapons[1]}'), discord.utils.get(server.channels, name=f'{channel_weapons[1]}-{channel_weapons[0]}')]
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

@bot.tree.context_menu(name='Upload to Discord', guilds=UPLOAD_GUILDS)
async def upload_discord_context_menu(interaction: discord.Interaction, message: discord.Message):
    await interaction.response.send_message(embed= await response_defer_embed('discord'))
    upload_discord_success, upload_discord_message = await upload_discord(interaction, message)
    embed = await output_to_embed('discord', upload_discord_success, upload_discord_message)
    await interaction.edit_original_response(embed=embed)
    await logging_channel.send(content=message.jump_url, embed=embed)
    await delete_original_response(interaction)

@bot.command(name='upload_discord')
async def upload_discord_old(ctx: commands.Context):
    if ctx.guild != combocodex:
        await ctx.reply('This command is only available in ComboCodex!', delete_after=DELETE_AFTER)
        return
    original_response = await ctx.reply(embed= await response_defer_embed('discord'))
    message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
    await ctx.message.delete()
    upload_discord_success, upload_discord_message = await upload_discord(ctx, message)
    embed = await output_to_embed('discord', upload_discord_success, upload_discord_message)
    await original_response.edit(embed=embed, delete_after=DELETE_AFTER)
    await logging_channel.send(content=message.jump_url, embed=embed)

@bot.tree.context_menu(name='Upload to Both', guilds=UPLOAD_GUILDS)
async def upload_both(interaction: discord.Interaction, message: discord.Message):
    await interaction.response.send_message(embed= await response_defer_embed('both'))
    upload_site_success, upload_site_message = await upload_site(interaction, message)
    upload_site_embed = await output_to_embed('site', upload_site_success, upload_site_message)
    upload_discord_success, upload_discord_message = await upload_discord(interaction, message)
    upload_discord_embed = await output_to_embed('discord', upload_discord_success, upload_discord_message)
    await interaction.edit_original_response(embeds=[upload_discord_embed, upload_site_embed])
    await logging_channel.send(content=message.jump_url, embeds=[upload_discord_embed, upload_site_embed])
    await delete_original_response(interaction)

@bot.command(name='upload')
async def upload_discord_old(ctx: commands.Context):
    if ctx.guild != combocodex:
        await ctx.reply('This command is only available in ComboCodex!', delete_after=DELETE_AFTER)
        return
    original_response = await ctx.reply(embed= await response_defer_embed('both'))
    message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
    await ctx.message.delete()
    upload_site_success, upload_site_message = await upload_site(ctx, message)
    upload_site_embed = await output_to_embed('site', upload_site_success, upload_site_message)
    upload_discord_success, upload_discord_message = await upload_discord(ctx, message)
    upload_discord_embed = await output_to_embed('discord', upload_discord_success, upload_discord_message)
    await original_response.edit(embeds=[upload_discord_embed, upload_site_embed], delete_after=DELETE_AFTER)
    await logging_channel.send(content=message.jump_url, embeds=[upload_discord_embed, upload_site_embed])



@bot.tree.command(name='upload_last', description='Upload all combos sent by you in submissions in the past x minutes', guilds=UPLOAD_GUILDS)
async def upload_last(interaction: discord.Interaction, minutes: int = 15):
    if not 0 < minutes <= 600:
        await interaction.response.send_message('Please provide a valid amount of minutes (1 - 60).')
        return
    await interaction.response.send_message(f'Uploading combos sent by you in the last {minutes} minutes. This may take a while.')
    after_time = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    upload_site_count = 0
    upload_discord_count = 0
    async for message in submissions_channel.history(after=after_time):
        if message.author == interaction.user and len(message.attachments) == 1 and message.attachments[0].content_type.startswith('video'):
            upload_discord_success, upload_discord_message = await upload_discord(interaction, message)
            if upload_discord_success:
                upload_discord_count += 1
            upload_site_success, upload_site_message = await upload_site(interaction, message)
            if upload_site_success:
                upload_site_count += 1
    response = f'{upload_site_count} combos uploaded to the site and {upload_discord_count} uploaded to the discord'
    await interaction.edit_original_response(content=response)
    await delete_original_response(interaction)

async def bulk_upload_from_video(interaction: discord.Interaction, message: discord.Message):
    async def upload_discord(interaction, attachment, legends_weapons):
        server = combocodex
        legends = [legends_weapons[0], legends_weapons[2]]
        weapons = [legends_weapons[1], legends_weapons[3]]
        channel_weapons = []
        for i, weapon in enumerate(weapons):
            if weapon == 'battle boots':
                weapon = 'boots'
            elif weapon == 'gauntlets':
                weapon = 'gaunts'
            channel_weapons.append(weapon)
        channels = []
        if legends[0] == 'universal' and legends[1] == 'universal':
            channels = [discord.utils.get(server.channels, name=f'{channel_weapons[0]}-universals'), discord.utils.get(server.channels, name=f'{channel_weapons[1]}-universals')]
            if channels[0] == channels [1]:
                channels = [channels[0]]
        elif channel_weapons[0] == channel_weapons[1]:
            channels = [discord.utils.get(server.channels, name=f'dual-{channel_weapons[1]}')]
        else:
            channels = [discord.utils.get(server.channels, name=f'{channel_weapons[0]}-{channel_weapons[1]}'), discord.utils.get(server.channels, name=f'{channel_weapons[1]}-{channel_weapons[0]}')]
        for channel in channels:
            video = await attachment.to_file()
            await channel.send(file=video)
        return True, 'Combo uploaded to discord'

    users = await parse_users(message)
    output = {'attachments': [], 'video_count': 0, 'attachment_count': len(message.attachments)}
    for attachment in message.attachments:
        attachment_data = {'name': attachment.filename, 'is_video': False, 'parse_success': False, 'combo_name': '', 'upload_site': {'success': False, 'message': ''}, 'upload_discord': {'success': False, 'message': ''}}
        print(attachment_data)
        print(attachment.content_type)
        if attachment.content_type.startswith('video'):
            attachment_data['is_video'] = True
            output['video_count'] += 1
            attachment_name = attachment.filename.split('.')[0]
            try:
                legends_weapons = await parse_legends_weapons(attachment_name)
            except IndexError:
                output['attachments'].append(attachment_data)
                continue
            attachment_data['parse_success'] = True
            combo_name = ' '.join([item.title() for item in legends_weapons])
            attachment_data['combo_name'] = combo_name
            video = await attachment.read()
            response = await upload_combo(interaction, *legends_weapons, users, video)
            upload_site_success = True if response.status_code == 200 else False
            upload_site_message = 'Combo uploaded to site' if upload_site_success else 'Something went wrong with handling your combo upload'
            attachment_data.update({'upload_site': {'success': upload_site_success, 'message': upload_site_message}})
            upload_discord_success, upload_discord_message = await upload_discord(interaction, attachment, legends_weapons)
            attachment_data.update({'upload_discord': {'success': upload_discord_success, 'message': upload_discord_message}})
        output['attachments'].append(attachment_data)
    embeds = []
    for attachment in output['attachments']:
        color = COLOR_ERROR
        description = ''
        if not attachment['is_video']:
            description = 'This attachment is not a video'
        elif not attachment['parse_success']:
            description = 'Could not parse legends/weapons from the attachment name'
        embed = discord.Embed(title=attachment['name'], description=description)
        if not attachment['is_video'] or not attachment['parse_success']:
            embed.color = COLOR_ERROR
            embeds.append(embed)
            continue
        embed.color = COLOR_SUCCESS
        description = f'Parsed to {attachment["combo_name"]}'
        embed.description = description
        emoji = '👍' if attachment['upload_site']['success'] else '❗️'
        embed.add_field(name='🔼 **Upload to Site** 🔼', value=f'{emoji} {attachment["upload_site"]["message"]}', inline=False)
        emoji = '👍' if attachment['upload_discord']['success'] else '❗️'
        embed.add_field(name='✅ **Upload to Discord** ✅', value=f'{emoji} {attachment["upload_discord"]["message"]}', inline=False)
        embeds.append(embed)
    await message.add_reaction('⏫')
    return embeds

@bot.tree.context_menu(name='Bulk Upload From Video', guilds=UPLOAD_GUILDS)
async def bulk_upload_from_video_context_menu(interaction: discord.Interaction, message: discord.Message):
    sender_roles = interaction.user.roles if isinstance(interaction, discord.Interaction) else interaction.author.roles
    if trusted_role not in sender_roles:
        return False, 'Only trusted users can use this command!'
    await interaction.response.send_message(embed= await response_defer_embed('Bulk Video'))
    embeds = await bulk_upload_from_video(interaction, message)
    await interaction.edit_original_response(embeds=embeds)
    await logging_channel.send(content=message.jump_url, embeds=embeds)

bot.run(DISCORD_TOKEN)