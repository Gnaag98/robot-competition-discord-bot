import discord

from bot_logging import log
import helpers

async def create_year_role(
    guild: discord.Guild,
    status_channel: discord.TextChannel,
    year: int,
    year_role_prefix: str
) -> discord.Role:
    """Create the year specific competitor role, if it does not exist.
    
    Returns the role, pre-existing or not.
    """

    year_role_name = f'{year_role_prefix} {year}'

    # Check for an existing role.
    year_role = helpers.get_role_by_name(guild, year_role_name)

    # Create the role if it doesn't exist.
    if year_role:
        await log(status_channel, f'Role {year_role_name} already exists.')
    else:
        year_role = await guild.create_role(name=year_role_name)
        await log(status_channel, f'Role {year_role_name} created.')

    # If there are roles from previous years, place the role below those.
    previous_year_role = helpers.get_first_role_by_prefix(
        guild, year_role_prefix, year_role)
    if previous_year_role:
        # NOTE: Role.move() and CategoryChannel.move() use their parameters in
        # opposite ways. Read the docs carafully about how the parameters
        # "above" and "before" are treated.
        await year_role.move(above=previous_year_role)
        await log(status_channel, 
            f'Moved role {year_role_name} below the other year roles.')

    return year_role


async def create_year_category(
    guild: discord.Guild,
    status_channel: discord.TextChannel,
    year: int,
    year_category_prefix: str,
    category_overwrites: dict[
        discord.Role|discord.Member,
        discord.PermissionOverwrite]
) -> discord.CategoryChannel:
    """TODO"""

    year_category_name = f'{year_category_prefix} {year}'

    year_category = helpers.get_category_by_name(guild, year_category_name)

    # Create the category if it doesn't exist.
    if year_category:
        await log(status_channel, f'Category {year_category_name} already exists.')
    else:
        year_category = await guild.create_category(year_category_name,
            overwrites=category_overwrites)
        await log(status_channel, f'Category {year_category_name} created.')
    
    # If there are categories from previous years, place the category above
    # those.
    previous_year_category = helpers.get_first_category_by_prefix(
        guild, year_category_prefix, year_category)
    if previous_year_category:
        print('Yay')
        # NOTE: Role.move() and CategoryChannel.move() use their parameters in
        # opposite ways. Read the docs carafully about how the parameters
        # "above" and "before" are treated.
        await year_category.move(before=previous_year_category)
        await log(status_channel,
            f'Moved category {year_category} above the other year categories.')

    return year_category
