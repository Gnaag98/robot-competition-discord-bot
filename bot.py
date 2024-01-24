import os

import asyncio
from aiohttp import ClientConnectorError
from discord import Intents, utils
from dotenv import load_dotenv

from house_robot import HouseRobot, RoleAffixes

load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID'))
DOOR_BELL_CHANNEL_NAME = os.getenv('DOOR_BELL_CHANNEL_NAME')
DOOR_BELL_RESPONSE = os.getenv('DOOR_BELL_RESPONSE')

ROLE_AFFIXES = RoleAffixes(
    year_prefix=os.getenv('YEAR_ROLE_PREFIX'),
    badge_prefix=os.getenv('BADGE_ROLE_PREFIX'),
    badge_suffix=os.getenv('BADGE_ROLE_SUFFIX'))

intents = Intents.default()
intents.members = True

utils.setup_logging(root=False)


async def main():
    wait_time_seconds = 10

    while True:
        try:
            # XXX: Recreate client since I don't know how to reuse it.
            client = HouseRobot(GUILD_ID, DOOR_BELL_CHANNEL_NAME, DOOR_BELL_RESPONSE, ROLE_AFFIXES, intents=intents)
            await client.start(DISCORD_TOKEN)
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