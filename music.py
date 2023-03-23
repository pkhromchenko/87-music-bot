import discord
from discord.ext import commands
import os
import yt_dlp
import logging
import asyncio

logger = logging.getLogger('my_bot')


# Create a Discord Intents object that enables all events to be received
intents = discord.Intents.all()

# Create a new Bot instance with command prefix "." and intents
bot = commands.Bot(command_prefix='.', intents=intents)

# VC join Function
async def join_voice_channel(ctx):
    # Check if the user is in a voice channel
    if not ctx.message.author.voice:
        await ctx.send("You're not in a voice channel.")
        return False
    
    # Get the voice channel object
    channel = ctx.message.author.voice.channel
    
    # Connect to the voice channel
    try:
        voice_client = await channel.connect()
        #Prints exception if failed to connect
    except Exception as e:
        await ctx.send(f"Failed to connect to voice channel: {e}")
        return False
    
    return True

# Play Function
async def play_song(ctx, url):
    # Check if the "songs" directory exists, if not create it
    if not os.path.exists("songs"):
        os.makedirs("songs")
    # Get the bot's voice client for where the command was invoked
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
    await ctx.send("Downloading song files...")
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'songs/%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192'
        }]
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # Uses ydl to extract the title
        info_dict = ydl.extract_info(url, download=True)
        title = info_dict.get('title', 'song')
    # Play the song
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice is None:
        await ctx.send("I am not currently connected to a voice channel.")
        return
    # Creates an anonymous function, prints error message
    voice.play(discord.FFmpegPCMAudio(f"songs/{title}.mp3"), after=lambda e: print(f"Error: {e}") if e else None)
    # Set the volume of the song to 7%
    voice.source = discord.PCMVolumeTransformer(voice.source)
    voice.source.volume = 0.07
    # Send a message to the user indicating that the song is now playing
    await ctx.send(f"*Now playing: {title} 🎵*")
    
# Initialize queue array
queue = []

# Play next song function
async def play_next(ctx):
    # Check if queue is empty
    if queue:
        # Get first song
        next_song = queue[0]
        # Remove first song before playing it
        queue.pop(0)
        # Play the next song
        await play_song(ctx, next_song)
    # If queue is empty, disconnect
    else:
        voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
        await voice.disconnect()
        
# Play command
@bot.command()
async def play(ctx, url):
    # Add URL to queue
    queue.append(url)
    # If queue length is 1, play it
    if len(queue) == 1:
        await play_song(ctx, queue[0])
    else:
        # Indicate that song has been added
        await ctx.send(f"{url} has been added to the queue.")
        
# Skip command
@bot.command()
async def skip(ctx):
    # Get the voice client info
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    # Stop playing audio
    voice.stop()
    # Play the next song in queue
    await play_next(ctx)
        
# Stop command
@bot.command()
async def stop(ctx):
    # Get the voice client for the server the command was sent from
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    # Leave voice
    voice.stop()
    # Disconnect from the voice channel
    await voice.disconnect()

bot.run('MTA4Nzg0NzM3ODMxODUzMjY5OQ.GQ07Hi.2qKaPA9T7s8tqH-828dHjUeI5PFX4_qYCewz8w')
