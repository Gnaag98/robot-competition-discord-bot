import json

import asyncio
from aiohttp import ClientConnectorError
from discord import Intents, utils

from house_robot import HouseRobot

# Choose which events to listen for. Some need to be enabled in the developer
# portal as well.
intents = Intents.default()
intents.members = True
intents.message_content = True

# Enable logging
utils.setup_logging(root=False)


async def main():
    connection_retry_delay = 10 # seconds

    # Load data from files.
    with open('settings.json', encoding='utf-8') as json_file:
        settings = json.load(json_file)
    with open('responses.json', encoding='utf-8') as json_file:
        doorbell_responses = json.load(json_file)

    # Keep the client connected. Only exits if the client stops without error.
    while True:
        try:
            # XXX: Recreate client each try. Could probably be reused instead.
            client = HouseRobot(intents=intents, settings=settings,
                                doorbell_responses=doorbell_responses)
            # Short for login() + connect().
            await client.start(settings['discord_token'])
            # Exit if client stopped without error.
            break
        # XXX: This is an asyncio exception. Maybe Discord.py exceptions should
        # be caught instead.
        except ClientConnectorError:
            print('Connection failed.')
            # XXX: Close the client before recreating it.
            await client.close()
            print(f'Retrying in { connection_retry_delay } seconds...')
            await asyncio.sleep(connection_retry_delay)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    # Exit without error if user presses CTRL+C.
    except KeyboardInterrupt:
        pass
