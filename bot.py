import os

import discord
from discord import Member

from dotenv import load_dotenv

load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

YEAR_ROLE_PREFIX = os.getenv('YEAR_ROLE_PREFIX')
BADGE_ROLE_PREFIX = os.getenv('BADGE_ROLE_PREFIX')

FIRST_YEAR_ROLE = os.getenv('FIRST_YEAR_ROLE')
SECOND_YEAR_ROLE = os.getenv('SECOND_YEAR_ROLE')
THIRD_YEAR_OR_MORE_ROLE = os.getenv('THIRD_YEAR_OR_MORE_ROLE')

intents = discord.Intents.default()
intents.members = True

client = discord.Client(intents=intents)


async def adjust_badge_roles(member: Member):
    first_year_role = discord.utils.get(
        member.guild.roles,
        name=FIRST_YEAR_ROLE)
    if not first_year_role:
        raise RuntimeError(f'Role "{FIRST_YEAR_ROLE}" not found')

    second_year_role = discord.utils.get(
        member.guild.roles,
        name=SECOND_YEAR_ROLE)
    if not second_year_role:
        raise RuntimeError(f'Role "{SECOND_YEAR_ROLE}" not found')

    third_year_or_more_role = discord.utils.get(
        member.guild.roles,
        name=THIRD_YEAR_OR_MORE_ROLE)
    if not third_year_or_more_role:
        raise RuntimeError(f'Role "{THIRD_YEAR_OR_MORE_ROLE}" not found')
    
    badge_roles = (
        None,
        first_year_role,
        second_year_role,
        third_year_or_more_role
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
        await member.add_roles(correct_badge_role)
    await member.remove_roles(*roles_to_remove)


@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')


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


client.run(DISCORD_TOKEN)
