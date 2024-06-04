import discord
import os
# load our local env, so we don't have the token in public
from dotenv import load_dotenv
from discord.ext import tasks
from discord import FFmpegPCMAudio, app_commands
from yt_dlp import YoutubeDL
from itertools import islice
from datetime import datetime
import json, random, asyncio
from operator import itemgetter

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
NWORD = os.getenv('NWORD')
intents = discord.Intents.all()
client = discord.Client(intents=intents)
slash = app_commands.CommandTree(client, fallback_to_global=True)
last_message = None
last_url = None

class Buttons(discord.ui.View):
    def __init__(self, timeout=180):
        super().__init__(timeout=timeout)

    @discord.ui.button(label="Pause", disabled=False, style=discord.ButtonStyle.primary)
    async def pause_button(self, ctx=discord.Interaction, button=discord.ui.button):
        try:
            channel = ctx.user.voice.channel
        except AttributeError:
            await ctx.response.send_message(content="You aren't in a voice channel!", ephemeral=True)
            return
        voice = ctx.user.guild.voice_client

        if voice.is_playing():
            print("Pausing...")
            voice.pause()
            await ctx.response.send_message(content="Paused!", ephemeral=True)

    @discord.ui.button(label="Resume", disabled=False, style=discord.ButtonStyle.primary)
    async def resume_button(self, ctx: discord.Interaction, button=discord.ui.button):
        try:
            channel = ctx.user.voice.channel
        except AttributeError:
            await ctx.response.send_message(content="You aren't in a voice channel!", ephemeral=True)
            return
        voice = ctx.user.guild.voice_client

        if not voice.is_playing():
            print("Resuming...")
            voice.resume()
            await ctx.response.send_message(content="Resumed!", ephemeral=True)

    @discord.ui.button(label="Stop", disabled=False, style=discord.ButtonStyle.danger)
    async def stop_button(self, ctx: discord.Interaction, button=discord.ui.button):
        try:
            channel = ctx.user.voice.channel
        except AttributeError:
            await ctx.response.send_message(content="You aren't in a voice channel!", ephemeral=True)
            return

        voice = ctx.user.guild.voice_client

        guild_id = ctx.guild.id

        if voice.is_playing():
            print("Stopping...")
            voice.stop()
            embed = discord.Embed(title="Stopped", url=last_url, description=f"Music was stopped by **{ctx.user}**",
                                  color=discord.Color.blue())
            await last_message.edit(embed=embed, delete_after=120, view=None)
            await ctx.response.send_message(content="Music has stopped!", ephemeral=True)
            return
        else:
            print("Stopping... But no music was playing.")
            await ctx.response.send_message(content="No music is playing!", ephemeral=True)

'''# command to play sound from a youtube URL
@slash.command(name="join", description="Joins your voice channel", nsfw=False, guild=None)
async def join(ctx: discord.Interaction):
    try:
        channel = ctx.user.voice.channel
    except AttributeError:
        print(f"{ctx.user} requested the bot, but wasn't in a vc.")
        await ctx.response.send_message(content="You aren't in a voice channel!", ephemeral=True, delete_after=5)
        return
    voice = await channel.connect()

    if voice.is_connected():
        print(f"Bot joined {ctx.user}'s voice channel: {ctx.user.voice.channel.name}({ctx.user.voice.channel.id}) in guild: {ctx.user.guild.name}({ctx.user.guild.id})")
        await voice.move_to(channel=channel)
        await ctx.response.send_message(content="Connected to your vc!", ephemeral=True, delete_after=5)
    else:
        await ctx.response.send_message(content="Something went wrong...", ephemeral=True, delete_after=15)'''

@slash.command(name="play", description="Plays a YouTube video audio in your voice channel", nsfw=False, guild=None)
async def play(ctx: discord.Interaction, url: str):
    global skip
    global last_message
    global last_url
    global queue
    #Joining vc
    try:
        channel = ctx.user.voice.channel
    except AttributeError:
        print(f"{ctx.user} requested url: {url}, but wasn't in a vc.")
        await ctx.response.send_message(content="You aren't in a voice channel!", ephemeral=True)
        return

    if ctx.user.guild.voice_client:
        voice = ctx.user.guild.voice_client
        if voice.channel != channel:
            voice.move_to(channel=channel)
    else:
        voice = await channel.connect()

    #Actually playing music
    if "youtube.com" in url or "soundcloud.com" in url or "youtu.be" in url:
        url = url
    else:
        print(f"{ctx.user} provided an invalid link ({url})")
        await ctx.response.send_message(content="That doesn't look like a YouTube or SoundCloud link!", ephemeral=True)
        return

    if voice.is_playing():
        print(f"{ctx.user} requested url: {url}, added to queue. New queue: {queue}")
        await ctx.response.send_message(content=f"There's already something playing!\nI've added it to the queue at position WIP.", ephemeral=True)
        queue.insert(len(queue), url)
        return
    else:
        print(f"{ctx.user} started playing url: {url} in vc {ctx.user.voice.channel.name}")
        await ctx.response.send_message(content="Music is starting...", ephemeral=True)
        queue.insert(len(queue), url)

        YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'True'}
        FFMPEG_OPTIONS = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }
        with YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)
            #print(info)
        URL = info['url']
        TITLE = info['title']
        ARTIST = info['uploader']
        ARTIST_ID = info['uploader_id']
        DURATION = info['duration']
        voice.play(FFmpegPCMAudio(URL, **FFMPEG_OPTIONS))
        voice.is_playing()
        embed = discord.Embed(description=f"### Now Playing:\n\n**[{TITLE}]({url})** by **[{ARTIST}](https://www.youtube.com/{ARTIST_ID})**, requested by **{ctx.user.mention}**", color=discord.Color.blue())
        last_message = await ctx.channel.send(embed=embed, delete_after=600, view=Buttons())
        last_url = url

async def sounds(current: str) -> list[app_commands.Choice[str]]:
    dir_path = 'C:/Users/joema/PycharmProjects/Journey Bot/sfx'
    sfx = [os.path.splitext(f)[0] for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))]
    return [app_commands.Choice(name=sfx, value=sfx)for sfx in sfx if current.lower() in sfx.lower()]

@slash.command(name="sfx", description="Plays a sound effect in your voice channel", nsfw=False, guild=None)
@app_commands.autocomplete(sfx=sounds)
async def sfx(ctx: discord.Interaction, sfx: str):
    global last_message
    global last_url
    sfx = sfx.lower()
    #Joining vc
    try:
        channel = ctx.user.voice.channel
    except AttributeError:
        print(f"{ctx.user} tried to play sfx: {sfx}.mp3, but wasn't in a vc.")
        await ctx.response.send_message(content="You aren't in a voice channel!", ephemeral=True, delete_after=5)
        return

    if ctx.user.guild.voice_client:
        voice = ctx.user.guild.voice_client
        if voice.channel != channel:
            voice.move_to(channel=channel)
    else:
        voice = await channel.connect()

    '''try:
        print("VC")
        voice = ctx.user.guild.voice_client
        await voice.move_to(channel)
    except:
        print("Connecting VC")
        voice = channel.connect()'''

    if voice.is_playing():
        await ctx.response.send_message(content="There's already something playing!", ephemeral=True, delete_after=5)

    # sfx check
    try:
        file = open(f'sfx/{sfx}.mp3')
        FFMPEG_OPTIONS = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }
        print(f"{ctx.user.name}({ctx.user.id}) is playing sfx {sfx} in {ctx.user.voice.channel.name}({ctx.user.voice.channel.id})")
        await ctx.response.send_message(content=f"Playing sfx: **{sfx}**", ephemeral=True, delete_after=5)
        await asyncio.sleep(0.5)
        voice.play(FFmpegPCMAudio(source=f'C:/Users/joema/PycharmProjects/Journey Bot/sfx/{sfx}.mp3', executable='ffmpeg.exe', before_options=FFMPEG_OPTIONS))
        voice.is_playing()
        last_message = None
        last_url = None
    except FileNotFoundError:
        await ctx.response.send_message(content=f"No sfx exists for **{sfx}**!", ephemeral=True, delete_after=5)

@client.event
async def on_voice_state_update(member, before, after):
    voice = member.guild.voice_client
    if voice and voice.is_connected():
        if len(voice.channel.members) == 1:  # If bot is the only one in the channel
            print(f"Leaving empty voice channel")
            await voice.disconnect(force=False)
            voice.stop()

# command to resume voice if it is paused
@slash.command(name="resume", description="Resumes music playback", nsfw=False, guild=None)
async def resume(ctx: discord.Interaction):
    try:
        channel = ctx.user.voice.channel
    except AttributeError:
        await ctx.response.send_message(content="You aren't in a voice channel!", ephemeral=True)
        return
    voice = ctx.user.guild.voice_client

    if voice.is_playing():
        if last_message is None:
            await ctx.response.send_message(content="You can't resume sounds!", ephemeral=True)
            return
        else:
            print("Resuming...")
            voice.resume()
            await ctx.response.send_message(content="Resumed!", ephemeral=True)

# command to pause voice if it is playing
@slash.command(name="pause", description="Pauses music playback", nsfw=False, guild=None)
async def pause(ctx: discord.Interaction):
    try:
        channel = ctx.user.voice.channel
    except AttributeError:
        await ctx.response.send_message(content="You aren't in a voice channel!", ephemeral=True)
        return
    voice = ctx.user.guild.voice_client

    if voice.is_playing():
        if last_message is None:
            await ctx.response.send_message(content="You can't pause sounds!", ephemeral=True)
            return
        else:
            print("Pausing...")
            voice.pause()
            await ctx.response.send_message(content="Paused!", ephemeral=True)

@slash.command(name="huh", nsfw=False, guild=None)
async def mystery(ctx: discord.Interaction):
    await ctx.response.send_message(content="https://tenor.com/view/huh-cat-huh-m4rtin-huh-huh-meme-what-cat-gif-13719248636774070662", ephemeral=True)

# command to stop voice
@slash.command(name="stop", description="Stops music or sound playback", nsfw=False, guild=None)
async def stop(ctx: discord.Interaction):
    try:
        channel = ctx.user.voice.channel
    except AttributeError:
        await ctx.response.send_message(content="You aren't in a voice channel!", ephemeral=True)
        return

    voice = ctx.user.guild.voice_client

    guild_id = ctx.guild.id

    if voice.is_playing():
        print("Stopping...")
        voice.stop()
        if last_message is None:
            await ctx.response.send_message(content="Sound has stopped!", ephemeral=True)
            return
        else:
            embed = discord.Embed(description=f"[Music]({last_url}) was stopped by **{ctx.user.mention}**",                color=discord.Color.blue())
            await last_message.edit(embed=embed, delete_after=120, view=None)
            await ctx.response.send_message(content="Music has stopped!", ephemeral=True)
            return
    else:
        print("Stopping... But no music was playing.")
        await ctx.response.send_message(content="No music is playing!", ephemeral=True)

'''@slash.command(name="skip", description="Skips the current song", nsfw=False, guild=None)
async def skip(ctx: discord.Interaction):
    global skip
    try:
        channel = ctx.user.voice.channel
    except AttributeError:
        await ctx.response.send_message(content="You aren't in a voice channel!", ephemeral=True)
        return

    voice = ctx.user.guild.voice_client

    guild_id = ctx.guild.id

    if voice.is_playing():
        print("Skipping...")
        skip = True
        embed = discord.Embed(description=f"[Song]({last_url} was skipped by **{ctx.user.mention}**", color=discord.Color.blue())
        await last_message.edit(embed=embed, delete_after=120, view=None)
        await ctx.response.send_message(content="Skipped!", ephemeral=True)
        return
    else:
        print("Skipping... But no music was playing.")
        await ctx.response.send_message(content="No music is playing!", ephemeral=True)
'''

try:
    with open('waffles_counter.json', 'r') as f:
        waffles_counter = json.load(f)
except FileNotFoundError:
    waffles_counter = {}

#NWORD Trigger
@client.event
async def on_message(message):
    if message.author.bot:  # ignore bots
        return

    if NWORD in message.content.lower():
        count =  message.content.lower().count(NWORD)
        user = message.author.name
        print(f"{message.author} said the n-word.")
        if user in waffles_counter:
            waffles_counter[user] += count
        else:
            waffles_counter[user] = count
    with open('waffles_counter.json', 'w') as f:
        json.dump(waffles_counter, f)

@slash.command(name="score", description="Displays a users score, if you wanna call it that", nsfw=False, guild=None)
async def score(ctx: discord.Interaction, member: discord.Member):
    if ctx.guild is None:  # the command is used in a dm
        user = ctx.user if member is None else member
    else:  # the command is used in a guild
        if member is None:
            member = ctx.user
        user = member.name
        count = waffles_counter.get(user, 0)
        print(f"{ctx.user} requested score for {member}, in guild {ctx.guild}")
        await ctx.response.send_message(content=f'{user} has said the n-word {count} times(s)', silent=True)

@slash.command(name="leaderboard", description="Displays the top five users with the highest score", nsfw=False, guild=None)
async def leaderboard(ctx: discord.Interaction):
    leaderboard = sorted(waffles_counter.items(), key=itemgetter(1), reverse=True)[:5]
    if ctx.guild is None: #It's used in a dm
        print(f"{ctx.user} requested a leaderboard in a dm.")
        await ctx.response.send_message(content='Use this command in a server!')
    else:
        print(f"{ctx.user} requested leaderboard for guild {ctx.guild}")
        await ctx.response.send_message(content="**Leaderboard**")
        for i, (key, value) in enumerate(leaderboard, start=1):
            await ctx.channel.send(f'{i}. {key} has said the n-word {value} time(s)')

@client.event
async def on_ready():
    for guild in client.guilds:
        if guild.name == GUILD:
            break

    print(f'Connected to: \n{guild.name}({guild.id})')

    role_mapping = {
        discord.Status.online: "Online",
        discord.Status.idle: "Idle",
        discord.Status.do_not_disturb: "Do Not Disturb",
        discord.Status.offline: "Offline",
    }

    def chunks(data, size=25):
        iterator = iter(data)
        for first in range(0, len(data), size):
            yield list(islice(iterator, size))

    @tasks.loop(minutes=5)
    async def update_roles():
        try:
            for server in client.guilds:
                for members_chunk in chunks(server.members):
                    for member in members_chunk:
                        if member.bot:
                            continue
                        for status, role_name in role_mapping.items():
                            role = discord.utils.get(server.roles, name=role_name)

                            if role is None:
                                continue

                            if role in member.roles and member.status != status:
                                await member.remove_roles(role)
                            elif role not in member.roles and member.status == status:
                                await member.add_roles(role)
                    print(f"[{datetime.now().strftime("%I:%M %p")}] Updated roles for group in guild: {server}")
                    await asyncio.sleep(1)  # wait 1 second between processing each group
        except Exception as e:
            print(f"An error occurred: {e}")

    @update_roles.before_loop
    async def before_update_roles():
        await client.wait_until_ready()
        await slash.sync()
        games = ["with a slinky", "Minecraft and griefing Gabe's house", "Overwatch and losing", "with a rubiks cube", "soccer with an ice cube", "tic-tac-toe with ice", "Titanfall 3", "Half Life 3: Part 2", "Team Fortress 3", "Super Smash Bros Ultimate", "signs at Travis's"]
        activity = discord.Game(random.choice(games))
        await client.change_presence(status=discord.Status.online, activity=activity)

    update_roles.start()

client.run(TOKEN)
