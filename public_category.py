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
        # NOTE: Role.move() and CategoryChannel.move() use their parameters in
        # opposite ways. Read the docs carafully about how the parameters
        # "above" and "before" are treated.
        await year_category.move(before=previous_year_category)
        await log(status_channel,
            f'Moved category {year_category} above the other year categories.')

    return year_category


async def create_channel_overwrites(
    guild: discord.Guild,
    status_channel: discord.TextChannel,
    category_overwrites: dict[
        discord.Role|discord.Member,
        discord.PermissionOverwrite],
    channel_permissions_json: list[dict],
    year_specific_role: discord.Role,
    year_specific_role_prefix: str
) -> dict[discord.Role|discord.Member, discord.PermissionOverwrite]|None:
    """TODO

    Channels automatically inherit permissions from the
    category if no overwrites are specified. It is not possible to
    override inherited permissions, instead all permissions for
    the channel must be specified. We therefore perform a deep
    copy of the category channels before adding or removing
    channel specific permissions.
    
    Return None if it fails.
    """

    # Return an empty dict if there are no permissions to overwrite.
    if not channel_permissions_json:
        return {}

    # Perform deep copy of inherited permissions to be able to overwrite them.
    channel_overwrites = {
        role: discord.PermissionOverwrite.from_pair(*overwrite.pair())
        for role, overwrite in category_overwrites.items()}

    # Add or remove permissions.
    for channel_permission_json in channel_permissions_json:
        role_name = channel_permission_json['role']
        # Get role whose permissions should be overwritten. Parse name for
        # special cases first.
        if role_name == '@everyone':
            role = guild.default_role
        # Special case: year-specific role.
        elif role_name.startswith(year_specific_role_prefix):
            role = year_specific_role
        else:
            role = helpers.get_role_by_name(guild, role_name)
            if not role:
                message = f'Aborted: Could not find the role {role_name}.'
                await log(status_channel, message)
                return None
        # Add/update overwrites for the role.
        # NOTE: PermissionOverwrite.update() takes keyword arguments as:
        #   str: True|False|None
        # where the key has to match an attribute of discord.Permissions:
        #   https://discordpy.readthedocs.io/en/stable/api.html#discord.Permissions
        if not role in channel_overwrites:
            channel_overwrites[role] = discord.PermissionOverwrite()
        add_kwargs = {
            permission: True
            for permission in channel_permission_json['add']}
        remove_kwargs = {
            permission: False
            for permission in channel_permission_json['remove']}
        channel_overwrites[role].update(**add_kwargs, **remove_kwargs)
    return channel_overwrites


async def create_or_update_text_channel(
    category: discord.CategoryChannel,
    status_channel: discord.TextChannel,
    name: str,
    topic: str,
    overwrites: dict[
        discord.Role|discord.Member,
        discord.PermissionOverwrite]
) -> discord.TextChannel:
    channel = helpers.get_text_channel_by_name(category, name)
    if channel:
        await log(status_channel, f'Channel {name} in {category.name} updated.')
        channel = await channel.edit(
            topic=topic,
            overwrites=overwrites)
    else:
        await log(status_channel, f'Channel {name} in {category.name} created.')
        channel = await category.guild.create_text_channel(
            name=name,
            topic=topic,
            overwrites=overwrites,
            category=category)
    return channel
