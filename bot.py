import os

import discord
from discord import Member

from dotenv import load_dotenv

load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID'))

YEAR_ROLE_PREFIX = os.getenv('YEAR_ROLE_PREFIX')
BADGE_ROLE_PREFIX = os.getenv('BADGE_ROLE_PREFIX')
BADGE_ROLE_SUFFIX = os.getenv('BADGE_ROLE_SUFFIX')

intents = discord.Intents.default()
intents.members = True

client = discord.Client(intents=intents)


async def adjust_badge_roles(member: Member):
    badge_roles = [
        role for role in member.guild.roles
        if role.name.startswith(BADGE_ROLE_PREFIX)
        and role.name.endswith(BADGE_ROLE_SUFFIX)]

    
    # Add None to the list of badge roles so that the index correspond to the
    # number of years participated. This works because the roles are retrieved
    # from lowest role to highest.
    badge_roles = (
        None,
        *badge_roles
    )
    
    current_year_roles = [
        role for role in member.roles
        if role.name.startswith(YEAR_ROLE_PREFIX)]

    # Clamp the badge index to the valid range [0, len(badge_roles))
    badge_role_index = min(len(current_year_roles), len(badge_roles))

    # Choose the correct role based on the number of years participated.
    correct_badge_role = badge_roles[badge_role_index]

    current_badge_roles = [
        role for role in member.roles
        if role.name.startswith(BADGE_ROLE_PREFIX)]

    roles_to_remove = [
        role for role in current_badge_roles
        if role and role != correct_badge_role]

    # Add and remove roles as necessary.
    if correct_badge_role and not correct_badge_role in current_badge_roles:
        print(f'Adding role {correct_badge_role.name} to {member.name}')
        await member.add_roles(correct_badge_role)
    if roles_to_remove:
        print(f'Removing roles {", ".join(role.name for role in roles_to_remove)} from {member.name}')
        await member.remove_roles(*roles_to_remove)


@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

    guild = client.get_guild(GUILD_ID)

    print('Adjusting roles...')
    for member in guild.members:
        await adjust_badge_roles(member)
    
    print('Done adjusting roles.')


@client.event
async def on_member_update(before: Member, after: Member):
    if before.roles != after.roles:
        year_roles_before = [
            role for role in before.roles
            if role.name.startswith(YEAR_ROLE_PREFIX)]
        year_roles_after = [
            role for role in after.roles
            if role.name.startswith(YEAR_ROLE_PREFIX)]
        
        # Check if the list contains the same roles. This works because the
        # roles appear in the same order.
        if year_roles_before != year_roles_after:
            await adjust_badge_roles(after)


def main():
    client.run(DISCORD_TOKEN)


if __name__ == '__main__':
    main()