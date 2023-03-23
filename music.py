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
        await ctx.send("*You're not in a voice channel*")
        return False

    # Get the voice channel object
    channel = ctx.message.author.voice.channel

    # Connect to the voice channel
    try:
        voice_client = await channel.connect()
        #Prints exception if failed to connect
    except Exception as e:
        await ctx.send(f"*Failed to connect to voice channel: {e}*")
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

            # Get the bot's voice client again after joining the channel
            voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)

        # If voice is None, the bot failed to join a voice channel
        if voice is None:
            await ctx.send("*Failed to join a voice channel*")
            return

    except:
        # If there was an error joining the voice channel, send a message to the user
        await ctx.send("*Failed to join the voice channel*")
        return

    # Download the song from YouTube
    # await ctx.send("*Downloading song files...*")
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
        info_dict = ydl.extract_info(url, download=False)
        title = info_dict.get('title', 'song')

        # Check if the file already exists before downloading it
        if not os.path.isfile(f"songs/{title}.mp3"):
            ydl.download([url])

    # Add the downloaded song to the queue
    queue.append(title)

    # If there is no song playing, start playing the queued songs
    if not voice.is_playing():
        await play_next(ctx)

    # Send a message to the user indicating that the song has been added to the queue
    await ctx.send(f"*Enqueued `{title}` in position `{len(queue)}`*")


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

        # Get the bot's voice client for where the command was invoked
        voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)

        # Play the next song
    try:
        # Play the next song
        voice.play(discord.FFmpegPCMAudio(f"songs/{next_song}.mp3"), after=lambda e: print(f"Error: {e}") if e else None)
        # Set the volume of the song to 7%
        voice.source = discord.PCMVolumeTransformer(voice.source)
        voice.source.volume = 0.07
        # Send a message to the user indicating that the next song is playing
        await ctx.send(f"*Now playing: `{next_song}` 🎵*")
    except:
        # If there was an error playing the next song, send a message to the user
        await ctx.send("*Failed to play next song*")
    else:
        # If queue is empty
        # Wait 60s before disconnecting
        await asyncio.sleep(600)
        # Check if queue is still empty, if so, disconnect
        if not queue:
            voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
            await voice.disconnect()

# Play command
@bot.command(aliases=['p'])
async def play(ctx, *, query_or_url):
    # Check if the argument is a valid YouTube URL
    if "youtube.com/watch?v=" in query_or_url or "youtu.be/" in query_or_url:
        # If it's a valid URL, call the play_song function
        await play_song(ctx, query_or_url)
    else:
        # If it's not a URL, assume it's a search query
        await ctx.send(f"*Searching for `{query_or_url}` on YouTube...*")

        # Use yt_dlp to search for videos matching the query
        with yt_dlp.YoutubeDL() as ydl:
            try:
                # Search YouTube for the best match
                info = ydl.extract_info(f"ytsearch:{query_or_url}", download=False)['entries'][0]
                url = info['webpage_url']

                # Send a message to the user indicating the found video
                await ctx.send(f"*Found `{info['title']}`*")

                # Call the play_song function with the found video URL
                await play_song(ctx, url)
            except:
                # If there was an error searching for videos or extracting information, send a message to the user
                await ctx.send("*Failed to find a video matching the search query.*")



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

    
bot.run('BOT_TOKEN')
