import discord
import os
# load our local env so we dont have the token in public
from dotenv import load_dotenv
from discord.ext import commands, tasks
from discord.utils import get
from discord import FFmpegPCMAudio
from yt_dlp import YoutubeDL
from itertools import islice
import asyncio
from datetime import datetime


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
intents = discord.Intents.default()
intents.presences = True
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix='.', intents=intents)  # prefix our commands with '.'

players = {}

@bot.event  # check if bot is ready
async def on_ready():
    print('Music module online')

# command to play sound from a youtube URL

@bot.command()
async def join(ctx):
    channel = ctx.message.author.voice.channel
    voice = get(bot.voice_clients, guild=ctx.guild)
    if voice and voice.is_connected():
        await voice.move_to(channel)
    else:
        voice = await channel.connect()

@bot.command()
async def play(ctx, url):
    channel = ctx.message.author.voice.channel
    voice = get(bot.voice_clients, guild=ctx.guild)
    if voice and voice.is_connected():
        await voice.move_to(channel)
    else:
        voice = await channel.connect()
    YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'True'}
    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
    voice = get(bot.voice_clients, guild=ctx.guild)

    if not voice.is_playing():
        with YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)
        URL = info['url']
        voice.play(FFmpegPCMAudio(URL, **FFMPEG_OPTIONS))
        voice.is_playing()
        await ctx.send('Bot is playing')

# check if the bot is already playing
    else:
        await ctx.send("Bot is already playing")
        return


# command to resume voice if it is paused
@bot.command()
async def resume(ctx):
    voice = get(bot.voice_clients, guild=ctx.guild)

    if not voice.is_playing():
        voice.resume()
        await ctx.send('Bot is resuming')


# command to pause voice if it is playing
@bot.command()
async def pause(ctx):
    voice = get(bot.voice_clients, guild=ctx.guild)

    if voice.is_playing():
        voice.pause()
        await ctx.send('Bot has been paused')


# command to stop voice
@bot.command()
async def stop(ctx):
    voice = get(bot.voice_clients, guild=ctx.guild)

    if voice.is_playing():
        voice.stop()
        await ctx.send('Stopping...')


# command to clear channel messages
@bot.command()
async def clear(ctx, amount=5):
    await ctx.channel.purge(limit=amount)
    await ctx.send("Messages have been cleared")

@bot.command()
async def leave(ctx):
    channel = ctx.message.author.voice.channel
    voice = get(bot.voice_clients, guild=ctx.guild)
    voiceClient = ctx.voice_client
    await voiceClient.disconnect()

@bot.event
async def on_ready():
    for guild in bot.guilds:
        if guild.name == GUILD:
            break

    print(f'QOL module is online and monitoring: \n{guild.name}(id: {guild.id})')


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

    @tasks.loop(minutes=1)
    async def update_roles():
        try:
            for server in bot.guilds:
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
        await bot.wait_until_ready()

    update_roles.start()

bot.run(TOKEN)