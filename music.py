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
    if voice.is_playing():
        queue.append(title)
        position = len(queue)
        embed = discord.Embed(title="Added to queue", description=(f"{title} is in position #{position}"), color=discord.Color.blue())

    # Send the embed to the user
        await ctx.send(embed=embed)
    else:
        queue.append(title)
        position = 0

    # If there is no song playing, start playing the queued songs
    if not voice.is_playing():
        await play_next(ctx)

# Initialize queue array
queue = []

# Play the next song function
async def play_next(ctx):
    # Get the bot's voice client for where the command was invoked
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    # Check if queue is empty
    if not queue:
        # Wait 600s before disconnecting
        await asyncio.sleep(600)
        # Check if queue is still empty, if so, disconnect
        if not queue:
            await voice.disconnect()
            return

    # Get first song
    next_song = queue.pop(0)

    # Play the next song
    try:
        # Play the next song
        voice.play(discord.FFmpegPCMAudio(f"songs/{next_song}.mp3"), after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))
        # Set the volume of the song to 15%
        voice.source = discord.PCMVolumeTransformer(voice.source)
        voice.source.volume = 0.15
        # Send a message to the user indicating that the next song is playing
        # Create an embedded message with information about the current song
        embed = discord.Embed(title="Now Playing", description=f"{next_song}", color=discord.Color.blue())
        await ctx.send(embed=embed)
    except:
        # If there was an error playing the next song, send a message to the user
        await ctx.send("*The queue is now empty*")
    return



# Play command
@bot.command(aliases=['p'])
async def play(ctx, *, query_or_url):
    # Check if the argument is a valid YouTube URL
    if "youtube.com/watch?v=" in query_or_url or "youtu.be/" in query_or_url:
        # If it's a valid URL, call the play_song function
        await play_song(ctx, query_or_url)
    else:
        # If it's not a URL, assume it's a search query
        # await ctx.send(f"*Searching for `{query_or_url}` on YouTube...*")

        # Use yt_dlp to search for videos matching the query
        with yt_dlp.YoutubeDL() as ydl:
            try:
                # Search YouTube for the best match
                info = ydl.extract_info(f"ytsearch:{query_or_url}", download=False)['entries'][0]
                url = info['webpage_url']

                # Send a message to the user indicating the found video
                # await ctx.send(f"*Found `{info['title']}`*")

                # Call the play_song function with the found video URL
                await play_song(ctx, url)
            except:
                # If there was an error searching for videos or extracting information, send a message to the user
                await ctx.send("*There was an error searching for videos (or extracting info).*")

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
    
@bot.command(aliases=['queue'])
async def q(ctx):
    # Check if queue is empty
    if not queue:
        # Create an embed with a title and description indicating that the queue is empty
        embed = discord.Embed(title="Queue", description="The queue is currently empty", color=discord.Color.blue())
        await ctx.send(embed=embed)
        return

    # Create a list of strings containing the current song queue using tuples
    queue_list = [f"{i+1}. {song}" for i, song in enumerate(queue)]

    # Create a string containing the list of songs separated by line breaks
    queue_string = "\n".join(queue_list)

    # Create an embed with a title and description containing the current song queue
    embed = discord.Embed(title="Current Song Queue", description=queue_string, color=discord.Color.blue())

    # Send the embed to the user
    await ctx.send(embed=embed)

bot.remove_command('help')
@bot.command()
async def help(ctx):
    # Add your custom help message here
    embed = discord.Embed(title="87 Documentation", description="▶️ `.play` Loads your input and adds it to the queue\n ⏭️ `.skip` Skips to next song\n ⏹️ `.stop` Disconnects the bot (currently disabled)\n ⌛ `.queue` Displays the song queue", color=discord.Color.blue())

    # Send the embed to the user
    await ctx.send(embed=embed)
    
bot.run('TOKEN')
