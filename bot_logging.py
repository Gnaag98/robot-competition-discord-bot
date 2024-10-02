from discord import TextChannel


async def log(channel: TextChannel, message: str):
    """Log a message to a channel and print it to the console."""
    await channel.send(message)
    print(message)
