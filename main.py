import json

import asyncio
from aiohttp import ClientConnectorError
from discord import Intents, utils

from house_robot import HouseRobot

intents = Intents.default()
intents.members = True
intents.message_content = True

utils.setup_logging(root=False)


async def main():
    wait_time_seconds = 10

    while True:
        try:
            with open('settings.json', encoding='utf-8') as json_file:
                settings = json.load(json_file)
            with open('responses.json', encoding='utf-8') as json_file:
                doorbell_responses = json.load(json_file)

            # XXX: Recreate client since I don't know how to reuse it.
            client = HouseRobot(intents=intents, settings=settings,
                                doorbell_responses=doorbell_responses)
            await client.start(settings['discord_token'])
            break
        except ClientConnectorError:
            print('Connection failed.')
            # XXX: Close the client since it is recreated each time.
            await client.close()
            print(f'Retrying in { wait_time_seconds } seconds...')
            await asyncio.sleep(wait_time_seconds)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
