from asyncio import sleep

from discord import Message
# Dont load the GPIO library in debug mode. This allows developing without the
# Raspberry Pi.
if not __debug__:
    from gpiozero import DigitalOutputDevice

async def check_doorbell(message: Message, doorbell_settings: dict,
                         doorbell_responses: dict):
    # Ignore messages from other channels.
    if message.channel.name != doorbell_settings['channel']:
        return

    # Only allow some members to ring the doorbell if there is a doorbell role
    # specified.
    author_roles = [role.name for role in message.author.roles]
    allowed_user_role = doorbell_settings['allowed_user_role']
    if allowed_user_role and not allowed_user_role in author_roles:
        await message.channel.send(doorbell_responses['invalidRole'])
        print(f'{message.author} tried to use the doorbell.')
        return

    if __debug__:
        text = 'Doorbell disabled in debug mode.'
        await message.channel.send(text)
        print(text)
    else:
        # Toggle pin to ring door bell.
        pin = DigitalOutputDevice(doorbell_settings['pin'])
        pin.on()
        await sleep(0.5)
        pin.off()

        # Respond to the request to open the door by writing a message in the
        # same channel.
        await message.channel.send(doorbell_responses['ok'])
        print(f'{message.author} used the doorbell.')
