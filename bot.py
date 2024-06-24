import discord
import os
# load our local env, so we don't have the token in public
from dotenv import load_dotenv
from discord.ext import tasks
from discord import FFmpegPCMAudio, app_commands
from yt_dlp import YoutubeDL
from itertools import islice
from datetime import datetime
import json, random, asyncio, re
from operator import itemgetter
import matplotlib.colors as mcolors

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
NWORD = os.getenv('NWORD')
DIR = os.getenv('DIRECTORY')
client = discord.Client(intents=discord.Intents.all())
slash = app_commands.CommandTree(client, fallback_to_global=True)
last_message = None
last_url = None
queue = asyncio.Queue()
voice = None
text_channel = None
user_mention = None
skip = 0
playing_sfx = False


# ---------------------------------------------
# Module Overview
# You can disable and enable different features of the bot here!

# /sfx to play sound effects in voice channels
soundboard_module = True

# /embed to easily create and send embeds!
# Note: Requires Manage Messages permission!
embed_builder_module = True
# Set to False to allow anyone to create embeds
embed_builder_permissions = True

# /huh to send a huh gif to the user who runs the command
# This doesn't really do anything useful, just for fun
huh_module = True

# /play, /stop, /skip, /pause, /resume to control the music bot
music_bot_module = True

# Add buttons to control music playback of the music bot
# Requires the music_bot_module to be enabled
playback_buttons_module = True

# Watches and tracks how many times users say a certain word
# By default, this is set to the n-word. You can change the word in the .env file
word_counter_module = True

# Assigns roles based on the server user's presence (online, idle, do not disturb, etc)
# Make sure there are roles called "Online", "Idle", "Do Not Disturb", and "Offline"
presence_roles_module = True

# Gives the bot a fun activity to play on its profile, purely cosmetic
fun_activity_module = True
# ---------------------------------------------

# Soundboard command
if soundboard_module:
    async def sounds(
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        dir_path = f'{DIR}/sfx'
        sfx = [os.path.splitext(f)[0] for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))]
        return [
            app_commands.Choice(name=sfx, value=sfx)
            for sfx in sfx if current.lower() in sfx.lower()
        ]


    # Remember to create a folder in the same folder as bot.py named sfx


    @slash.command(name="sfx", description="Plays a sound effect in your voice channel", nsfw=False, guild=None)
    @app_commands.autocomplete(sfx=sounds)
    async def sfx(ctx: discord.Interaction, sfx: str):
        try:
            global playing_sfx
            sfx = sfx.lower()
            # Joining vc
            try:
                channel = ctx.user.voice.channel
            except AttributeError:
                print(f"{ctx.user}({ctx.user.id}) tried to play sfx: {sfx}.mp3, but wasn't in a vc.")
                await ctx.response.send_message(content="You aren't in a voice channel!", 
                                                ephemeral=True, 
                                                delete_after=5)
                return

            if ctx.user.guild.voice_client:
                voice = ctx.user.guild.voice_client
                if voice.channel != channel:
                    voice.move_to(channel=channel)
            else:
                voice = await channel.connect()

            if voice.is_playing():
                await ctx.response.send_message(content="There's already something playing!", 
                                                ephemeral=True, 
                                                delete_after=5)
                print(f"{ctx.user}({ctx.user.id}) tried to play a sound, but one was already playing!")
            if not voice.is_connected():
                while not voice.is_connected():
                    await asyncio.sleep(1)

            # sfx check
            try:
                open(f'sfx/{sfx}.mp3')
                ffmpeg_options = {
                    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                    'options': '-vn'
                }
                print(f"{ctx.user.name}({ctx.user.id}) "
                      f"is playing sfx {sfx} in {ctx.user.voice.channel.name}"
                      f"({ctx.user.voice.channel.id})")
                await ctx.response.send_message(content=f"Playing sfx: **{sfx}**", ephemeral=True, delete_after=5)
                await asyncio.sleep(1)
                voice.play(FFmpegPCMAudio(source=f'[{DIR}]/{sfx}.mp3', 
                                          executable='ffmpeg.exe', 
                                          before_options=ffmpeg_options))
                voice.is_playing()
                playing_sfx = True
                while voice.is_playing:
                    await asyncio.sleep(1)
                playing_sfx = False
            except FileNotFoundError:
                await ctx.response.send_message(content=f"No sfx exists for **{sfx}**!", ephemeral=True, delete_after=5)
                print(f"{ctx.user}({ctx.user.id}) requested an invalid sound: {sfx}")
        except Exception as err:
            print(err)
            await ctx.channel.send(content=f"Error: {err}")

# Embed builder command
if embed_builder_module:
    def get_color_int(name):
        rgb = mcolors.to_rgb(name)
        return (int(rgb[0]*255) << 16) | (int(rgb[1]*255) << 8) | int(rgb[2]*255)


    @slash.command(name="embed", description="Create and send an embed in the current channel!", nsfw=False, guild=None)
    async def embed(ctx: discord.Interaction = None, 
                    title: str = None, 
                    description: str = None, 
                    url: str = None, 
                    color: str = "white", 
                    image_url: str = None):
        try:
            if not ctx.user.guild_permissions.manage_messages and embed_builder_permissions:
                await ctx.response.send_message("You need the **Manage Messages** permission to send embeds!", 
                                                ephemeral=True)
                print(f"{ctx.user}({ctx.user.id}) lacked the permissions to send this embed: {title}, "
                      f"{description}, {url}, {color}")
                return
            if color.isdigit():
                embed_color = int(color)
            else:
                try:
                    embed_color = getColorInt(color.lower())
                except:
                    await ctx.response.send_message("I couldn't find that color!!", ephemeral=True)
                    return
            embed = discord.Embed(title=title, 
                                  description=description, 
                                  url=url, 
                                  color=embed_color).set_image(url=image_url)
            await ctx.response.send_message(embed=embed)
            print(f"{ctx.user}({ctx.user.id}) sent this embed: {title}, {description}, {url}, {color}, {image_url}")
        except Exception as err:
            print(err)
            await ctx.channel.send(content=f"Error: {err}")

# /huh command
if huh_module:
    @slash.command(name="huh", nsfw=False, guild=None)
    async def mystery(ctx: discord.Interaction):
        try:
            print(f"{ctx.user}({ctx.user.id}) used the huh command")
            await ctx.response.send_message(content="https://tenor.com/view/huh-cat-huh-m4rtin-huh-huh-meme-what-cat"
                                                    "-gif-13719248636774070662", 
                                            ephemeral=True)
        except Exception as err:
            print(err)
            await ctx.channel.send(content=f"Error: {err}")

# Playback control commands
if music_bot_module:
    @client.event
    async def on_voice_state_update(member, before, after):
        voice = member.guild.voice_client
        if voice and voice.is_connected():
            if len(voice.channel.members) == 1:  # If bot is the only one in the channel
                print(f"Leaving empty voice channel")
                await voice.disconnect(force=False)
                voice.stop()


    # command to resume voice if it is paused
    @slash.command(name="resume", description="Resumes playback", nsfw=False, guild=None)
    async def resume(ctx: discord.Interaction):
        try:
            try:
                channel = ctx.user.voice.channel
            except AttributeError:
                await ctx.response.send_message(content="You aren't in a voice channel!", ephemeral=True)
                print(f"{ctx.user}({ctx.user.id}) tried resuming, but wasn't in a vc.")
                return
            voice = ctx.user.guild.voice_client

            if playing_sfx:
                await ctx.response.send_message(content="You can't resume sounds!", ephemeral=True)
                print(f"{ctx.user}({ctx.user.id}) tried resuming a sound.")
                return
            else:
                print(f"{ctx.user}({ctx.user.id}) resumed the music.")
                voice.resume()
                await ctx.response.send_message(content="Resumed!", ephemeral=True)

        except Exception as err:
            print(err)
            await ctx.channel.send(content=f"Error: {err}")


    @slash.command(name="pause", description="Pauses playback", nsfw=False, guild=None)
    async def pause(ctx: discord.Interaction):
        try:
            try:
                channel = ctx.user.voice.channel
            except AttributeError:
                await ctx.response.send_message(content="You aren't in a voice channel!", ephemeral=True)
                print(f"{ctx.user}({ctx.user.id}) tried to pause, but wasn't in a vc.")
                return
            voice = ctx.user.guild.voice_client

            if playing_sfx:
                await ctx.response.send_message(content="You can't pause sounds!", ephemeral=True)
                print(f"{ctx.user}({ctx.user.id}) tried to pause a sound")
                return
            else:
                print(f"{ctx.user}({ctx.user.id}) paused music.")
                voice.pause()
                await ctx.response.send_message(content="Paused!", ephemeral=True)

        except Exception as err:
            print(err)
            await ctx.channel.send(content=f"Error: {err}")


    @slash.command(name="stop", description="Stops playback", nsfw=False, guild=None)
    async def stop(ctx: discord.Interaction):
        global queue
        try:
            try:
                channel = ctx.user.voice.channel
            except AttributeError:
                await ctx.response.send_message(content="You aren't in a voice channel!", ephemeral=True)
                print(f"{ctx.user}({ctx.user.id}) used stop command but wasn't in a vc!")
                return

            voice = ctx.user.guild.voice_client

            queue = asyncio.Queue()
            voice.stop()
            if playing_sfx:
                await ctx.response.send_message(content="Sound has stopped!", ephemeral=True)
                print(f"{ctx.user}({ctx.user.id}) stopped a sound.")
                return
            else:
                embed = discord.Embed(description=f"[Music]({last_url}) "
                                                  f"was stopped by **{ctx.user.mention}**", 
                                      color=discord.Color.blue())
                await last_message.edit(embed=embed, delete_after=120, view=None)
                await ctx.response.send_message(content="Music has stopped!", ephemeral=True)
                print(f"{ctx.user}({ctx.user.id}) stopped the music.")
                return

        except Exception as err:
            print(err)
            await ctx.channel.send(content=f"Error: {err}")


    @slash.command(name="skip", description="Skips the current song", nsfw=False, guild=None)
    async def skip(ctx: discord.Interaction):
        global queue
        global skip
        try:
            try:
                channel = ctx.user.voice.channel
            except AttributeError:
                await ctx.response.send_message(content="You aren't in a voice channel!", ephemeral=True)
                print(f"{ctx.user}({ctx.user.id}) used stop command but wasn't in a vc!")
                return

            voice = ctx.user.guild.voice_client

            skip = 1
            voice.stop()
            if playing_sfx:
                await ctx.response.send_message(content="Sound is skipped!", ephemeral=True)
                print(f"{ctx.user}({ctx.user.id}) skipped a sound.")
                return
            else:
                embed = discord.Embed(description=f"[Music]({last_url}) was skipped by **{ctx.user.mention}**", 
                                      color=discord.Color.blue())
                await last_message.edit(embed=embed, delete_after=120, view=None)
                await ctx.response.send_message(content="Music was skipped!", ephemeral=True)
                print(f"{ctx.user}({ctx.user.id}) skipped the music.")
                return

        except Exception as err:
            print(err)
            await ctx.channel.send(content=f"Error: {err}")

# Playback buttons
if playback_buttons_module:
    if not music_bot_module:
        print("You need the music_bot_module enabled to user playback buttons!")
    else:
        class Buttons(discord.ui.View):
            def __init__(self, timeout=180):
                super().__init__(timeout=timeout)

            @discord.ui.button(label="Pause", disabled=False, style=discord.ButtonStyle.primary, emoji="⏸")
            async def pause_button(self, ctx=discord.Interaction, button=discord.ui.button):
                await slash.get_command('pause').callback(ctx=ctx)

            @discord.ui.button(label="Resume", disabled=False, style=discord.ButtonStyle.primary, emoji="▶")
            async def resume_button(self, ctx: discord.Interaction, button=discord.ui.button):
                await slash.get_command('resume').callback(ctx=ctx)

            @discord.ui.button(label="Skip", disabled=False, style=discord.ButtonStyle.primary, emoji="⏭")
            async def skip_button(self, ctx: discord.Interaction, button=discord.ui.button):
                await slash.get_command('skip').callback(ctx=ctx)

            @discord.ui.button(label="Stop", disabled=False, style=discord.ButtonStyle.danger, emoji="⏹")
            async def stop_button(self, ctx: discord.Interaction, button=discord.ui.button):
                await slash.get_command('stop').callback(ctx=ctx)

# /play command
if music_bot_module:

    async def video_info_extractor(query):
        ydl_opts = {
            'default_search': 'ytsearch',
            'ignoreerrors': True
        }

        loop = asyncio.get_event_loop()
        with YoutubeDL(ydl_opts) as ydl:
            # Run yt-dlp function in a separate thread
            video_info = await loop.run_in_executor(None, lambda: ydl.extract_info(query, download=False))

        return video_info


    async def video_search(query: str):
        video_info = await video_info_extractor(query)
        if not video_info['entries']:
            return []
        video_url = video_info['entries'][0]['webpage_url']
        return video_url


    def is_url(url):
        regex = re.compile(
            r'^(?:http|ftp)s?://'  # http:// or https:// or ftp:// or ftps://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        return re.match(regex, url) is not None


    @slash.command(name="play", description="Plays music in your voice channel", nsfw=False, guild=None)
    async def play(ctx: discord.Interaction, url: str):
        try:
            global queue
            global text_channel
            global last_message
            global last_url
            global voice
            global user_mention
            global skip
            # Joining vc
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
            if not voice.is_connected():
                while not voice.is_connected():
                    await asyncio.sleep(1)

            if playing_sfx:
                voice.stop()
                await ctx.response.send_message(content="I've stopped a sound effect to play music!", ephemeral=True)
                print(f"{ctx.user}({ctx.user.id}) stopped a sound effect to play music.")

            if voice.is_playing():
                print(f"{ctx.user}({ctx.user.id}) requested url: {url}, added to queue.")
                await ctx.response.send_message(content=f"There's already something playing, "
                                                        f"but I've added it to the queue!", 
                                                ephemeral=True)
            else:
                print(f"{ctx.user} started playing url: {url} in vc {ctx.user.voice.channel.name}")
                await ctx.response.send_message(content="Music is starting...", ephemeral=True)

            if not is_url(url):
                url = await video_search(url)
            await queue.put(url)
            text_channel = ctx.channel
            user_mention = ctx.user.mention
        except Exception as err:
            print(err)
            await ctx.channel.send(content=f"Error: {err}")


    @tasks.loop(seconds=2)
    async def play_queue():
        global queue
        global last_message
        global last_url
        global voice
        global user_mention
        if queue.empty() or voice.is_playing():
            return
        url = await queue.get()
        ydl_options = {'format': 'bestaudio', 'noplaylist': 'True'}
        ffmpeg_options = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }
        with YoutubeDL(ydl_options) as ydl:
            info = ydl.extract_info(url, download=False)
            # print(info)
        url = info['url']
        title = info['title']
        artist = info['uploader']
        artist_id = info['uploader_id']
        duration = info['duration']
        voice.play(FFmpegPCMAudio(url, **ffmpeg_options))
        voice.is_playing()
        embed = discord.Embed(
            description=f"### Now Playing:\n\n**[{title}]({url})** "
                        f"by **[{artist}](https://www.youtube.com/{artist_id})**, "
                        f"requested by **{user_mention}**",
            color=discord.Color.blue())
        view = Buttons() if playback_buttons_module else None
        send_or_edit = dict(embed=embed, delete_after=600, view=view)

        if last_message is None:
            last_message = await text_channel.send(**send_or_edit)
        else:
            last_message = await last_message.edit(**send_or_edit)

        last_url = url
        counter = 0
        if duration:
            while counter < duration or not voice.is_playing():
                if skip == 1:
                    break
                await asyncio.sleep(0.5)
                counter += 0.5
        embed = discord.Embed(
            description=f"### Finished playing:\n\n**[{TITLE}]({url})**"
                        f" by **[{ARTIST}](https://www.youtube.com/{ARTIST_ID})**, "
                        f"requested by **{user_mention}**",
            color=discord.Color.blue())
        last_message = await last_message.edit(embed=embed, delete_after=600)

# Tracks how many times users say a certain word
if word_counter_module:
    try:
        with open('waffles_counter.json', 'r') as f:
            waffles_counter = json.load(f)
    except FileNotFoundError:
        waffles_counter = {}

    # NWORD Trigger
    @client.event
    async def on_message(message):
        if message.author.bot:  # ignore bots
            return

        if NWORD in message.content.lower():
            count = message.content.lower().count(NWORD)
            user = message.author.name
            print(f"{message.author}({message.author.id}) said the n-word.")
            if user in waffles_counter:
                waffles_counter[user] += count
            else:
                waffles_counter[user] = count
        with open('waffles_counter.json', 'w') as f:
            json.dump(waffles_counter, f)


    @slash.command(
        name="score", 
        description="Displays a users score, if you wanna call it that", 
        nsfw=False, 
        guild=None)
    async def score(ctx: discord.Interaction, member: discord.Member = None):
        try:
            if ctx.guild is None or member is None:  # the command is used in a dm
                member = ctx.user
            user = member.display_name
            count = waffles_counter.get(user, 0)
            print(f"{ctx.user}({ctx.user.id}) "
                  f"requested score for: {member}({member.id}), in guild:"
                  f" {ctx.guild}({ctx.guild.id})")
            await ctx.response.send_message(content=f'{user} has said the n-word {count} times(s)', silent=True)
        except Exception as err:
            print(err)
            await ctx.channel.send(content=f"Error: {err}")


    @slash.command(name="leaderboard", description="Displays the top five users with the highest score", 
                   nsfw=False, 
                   guild=None)
    async def leaderboard(ctx: discord.Interaction):
        try:
            leaderboard = sorted(waffles_counter.items(), key=itemgetter(1), reverse=True)[:5]
            if ctx.guild is None:  # It's used in a dm
                print(f"{ctx.user}({ctx.user.id}) requested a leaderboard in a dm.")
                await ctx.response.send_message(content='Use this command in a server!')
            else:
                print(f"{ctx.user}({ctx.user.id}) requested leaderboard for guild {ctx.guild}({ctx.guild.id})")
                await ctx.response.send_message(content="**Leaderboard**")
                for i, (key, value) in enumerate(leaderboard, start=1):
                    await ctx.channel.send(f'{i}. {key} has said the n-word {value} time(s)')
        except Exception as err:
            print(err)
            await ctx.channel.send(content=f"Error: {err}")


@client.event
async def on_ready():
    for guild in client.guilds:
        if guild.name == GUILD:
            break

    # You're not supposed to do this but idrc
    await slash.sync()

    if fun_activity_module:
        games = ["with a slinky", "Poker on the last day of school", "Blackjack on the last day of school",
                 "BS on the last day of school", "Minecraft and griefing Gabe's house", "Overwatch and losing",
                 "with a rubiks cube", "soccer with an ice cube", "tic-tac-toe with ice", "Titanfall 3",
                 "Half Life 3: Part 2", "Team Fortress 3", "Super Smash Bros Ultimate", "signs at Travis's"]
        await client.change_presence(status=discord.Status.online, activity=discord.Game(random.choice(games)))

    print(f'Connected to: \n{guild.name}({guild.id})')
    global queue
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

    if presence_roles_module:
        update_roles.start()
    play_queue.start()
client.run(TOKEN)
