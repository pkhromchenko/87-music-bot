import discord
from discord.ext import commands
import asyncio
import os

# Create a Discord Intents object that enables all events to be received
intents = discord.Intents.all()

# Create a new Bot instance with command prefix "." and intents
bot = commands.Bot(command_prefix='.', intents=intents)

# vc join Functiom
async def join_voice_channel(ctx):
    # Check if the user is in a voice channel
    if not ctx.message.author.voice:
        await ctx.send("You're not in a channel idiota")
        return False
    else:
        channel = ctx.message.author.voice.channel
    # Connect to the voice channel
    await channel.connect()
    return True

# Play Function
async def play_song(ctx, url):
    # Check if the "songs" directory exists, if not create it
    if not os.path.exists("songs"):
        os.makedirs("songs")
    # Get the bot's voice client for the server the command was invoked on
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    # Check if a song is already playing
    song_there = os.path.isfile("songs/song.mp3")
    try:
        # If the bot is already connected to a voice channel, move to the user's channel
        if voice and voice.is_connected():
            await voice.move_to(ctx.author.voice.channel)
        # If the bot is not connected to a voice channel, join the user's channel
        else:
            await join_voice_channel(ctx)
    except:
        # If there was an error joining the voice channel, send a message to the user
        await ctx.send("Failed to join the voice channel.")
    try:
        # If there is a song playing, remove it
        if song_there:
            os.remove("songs/song.mp3")
    except PermissionError:
        # If there was an error removing the song file, send a message to the user
        await ctx.send("Wait for the current playing music to end or use the 'stop' command.")
        return
    # Download the song from YouTube
    await ctx.send("Downloading song...")
    os.system(f"youtube-dl --extract-audio --audio-format mp3 -o 'songs/song.%(ext)s' {url}")
    # Rename the downloaded file to "song.mp3"
    for file in os.listdir("./"):
        if file.endswith(".mp3"):
            os.rename(file, "songs/song.mp3")
    # Play the song
    if voice is None:
        await ctx.send("I am not currently connected to a voice channel.")
        return
    voice.play(discord.FFmpegPCMAudio("songs/song.mp3"), after=lambda e: print(f"Error: {e}") if e else None)
    # Set the volume of the song to 7%
    voice.source = discord.PCMVolumeTransformer(voice.source)
    voice.source.volume = 0.07
    # Get the name of the song without the file extension
    nname = os.path.splitext(os.path.basename("songs/song.mp3"))[0]
    # Send a message to the user indicating that the song is now playing
    await ctx.send(f"Now playing: {nname}")

# Play command
@bot.command()
async def play(ctx, url):
    # Invoke the play_song function with the provided URL
    await play_song(ctx, url)

# Stop command
@bot.command()
async def stop(ctx):
    # Get the voice client for the server the command was sent from
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    # Check if the voice client is currently playing audio
    if voice.is_playing():
        # Stop playing audio
        voice.stop()
    # Disconnect from the voice channel
    await voice.disconnect()

bot.run('MTA4Nzg0NzM3ODMxODUzMjY5OQ.Gn-tAt.mqWuA9pASik6rE3i2uWmKg3sgfDpBezalXli7c')