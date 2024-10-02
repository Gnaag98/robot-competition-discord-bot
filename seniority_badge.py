from dataclasses import dataclass

from discord import Member

from bot_logging import log


@dataclass
class RoleAffixes:
    """Prefixes and suffixes for the roles."""
    year_prefix: str
    badge_prefix: str
    badge_suffix: str


async def adjust_badge_roles(member: Member, role_affixes: RoleAffixes,
                             status_channel: str):
    badge_roles = [
        role for role in member.guild.roles
        if role.name.startswith(role_affixes.badge_prefix)
        and role.name.endswith(role_affixes.badge_suffix)]

    # Add None to the list of badge roles so that the index correspond to
    # the number of years participated.
    # XXX: This works because the roles are retrieved from lowest role to
    # highest.
    badge_roles = (
        None,
        *badge_roles
    )

    current_year_roles = [
        role for role in member.roles
        if role.name.startswith(role_affixes.year_prefix)]

    # Clamp the badge index to the valid range [0, len(badge_roles))
    badge_role_index = min(len(current_year_roles), len(badge_roles))

    # Choose the correct role based on the number of years participated.
    correct_badge_role = badge_roles[badge_role_index]

    current_badge_roles = [
        role for role in member.roles
        if role.name.startswith(role_affixes.badge_prefix)]

    roles_to_remove = [
        role for role in current_badge_roles
        if role and role != correct_badge_role]

    # Add and remove roles as necessary.
    if correct_badge_role and not correct_badge_role in current_badge_roles:
        await log(status_channel, f'Adding role {correct_badge_role.name} to {member.name}')
        await member.add_roles(correct_badge_role)
    if roles_to_remove:
        await log(status_channel, f'Removing roles {", ".join(role.name for role in roles_to_remove)} from {member.name}')
        await member.remove_roles(*roles_to_remove)