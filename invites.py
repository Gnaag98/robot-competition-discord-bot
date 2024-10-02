from discord import Guild, Invite, Member

from bot_logging import log


async def get_invite_uses(guild: Guild):
    """Get the number of uses for each invite in the guild."""
    invite_uses = {}
    for invite in await guild.invites():
        invite_uses[invite.code] = invite.uses
    return invite_uses


async def apply_invite_role(member: Member, invite: Invite,
                            invite_settings: dict,
                            status_channel: str):
    for invite_setting in invite_settings:
        channel = invite_setting['channel']
        role = invite_setting['role']
        if invite.channel.name == channel:
            await member.add_roles(role)
            await log(status_channel, f'{member.name} assigned the role "{invite.channel.name}".')
