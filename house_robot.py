from attr import dataclass

from discord import Client, Member, Message, Guild
from gpiozero import DigitalOutputDevice
from asyncio import sleep

@dataclass
class RoleAffixes:
    """Prefixes and suffixes for the roles."""
    year_prefix: str
    badge_prefix: str
    badge_suffix: str


async def get_invite_uses(guild: Guild):
    """Get the number of uses for each invite in the guild."""
    invite_uses = {}
    for invite in await guild.invites():
        invite_uses[invite.code] = invite.uses
    return invite_uses


class HouseRobot(Client):
    """Custom client."""

    def __init__(self, doorbell_pin: int, doorbell_role: str,
                 doorbell_channel_name: str, doorbell_responses: dict,
                 affixes: RoleAffixes, robot_group_role_name: str,
                 invite_channel_robot_group: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.doorbell_role = doorbell_role
        self.doorbell_pin = doorbell_pin
        self.doorbell_channel_name = doorbell_channel_name
        self.doorbell_responses = doorbell_responses

        self.role_affixes = affixes

        self.robot_group_role_name = robot_group_role_name

        self.invite_channel_robot_group = invite_channel_robot_group
        self.invite_uses = {}


    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')

        for guild in self.guilds:
            print('Storing invite uses...')
            self.invite_uses[guild.id] = await get_invite_uses(guild)
            print('Done storing invite uses.')

            print('Adjusting roles...')
            for member in guild.members:
                await self.adjust_badge_roles(member)
            print('Done adjusting roles.')


    async def on_member_join(self, member: Member):
        print(f'{member.name} joined the server.')

        guild = member.guild

        try:
            robot_group_role = next(
                role for role in guild.roles
                if role.name == self.robot_group_role_name)
        except StopIteration:
            raise RuntimeError(f'Role {self.robot_group_role_name} not found.')

        for invite in await guild.invites():
            invite_uses_before = self.invite_uses[guild.id].get(invite.code, 0)

            if invite.uses > invite_uses_before:
                print(f'{member.name} joined using invite {invite.code}')

                # Check if the invite was for joining the robot group.
                if invite.channel.name == self.invite_channel_robot_group:
                    await member.add_roles(robot_group_role)

                    print(f'{member.name} assigned the role {self.invite_channel_robot_group}.')
                    await self.adjust_badge_roles(member)
                break
        
        # Update the invite uses for the next member join event.
        self.invite_uses[guild.id] = await get_invite_uses(guild)


    async def on_member_update(self, before: Member, after: Member):
        if before.roles != after.roles:
            year_roles_before = [
                role for role in before.roles
                if role.name.startswith(self.role_affixes.year_prefix)]
            year_roles_after = [
                role for role in after.roles
                if role.name.startswith(self.role_affixes.year_prefix)]
            
            # Check if the list contains the same roles. This works because the
            # roles appear in the same order.
            if year_roles_before != year_roles_after:
                await self.adjust_badge_roles(after)


    async def on_message(self, message: Message):
        # Ignore messages from other channels.
        if message.channel.name != self.doorbell_channel_name:
            return
        
        # Ignore messages from bots. Prevents infinite loops.
        if message.author.bot:
            return

        # Only allow some members to ring the doorbell.
        author_roles = [role.name for role in message.author.roles]
        if not self.doorbell_role in author_roles:
            await message.channel.send(self.doorbell_responses['invalidRole'])
            return

        # Toggle pin to ring door bell.
        pin = DigitalOutputDevice(self.doorbell_pin)
        pin.on()
        await sleep(0.5)
        pin.off()

        # Respond to the request to open the door by writing a message in the same channel.
        await message.channel.send(self.doorbell_responses['ok'])
    

    async def adjust_badge_roles(self, member: Member):
        badge_roles = [
            role for role in member.guild.roles
            if role.name.startswith(self.role_affixes.badge_prefix)
            and role.name.endswith(self.role_affixes.badge_suffix)]

        # Add None to the list of badge roles so that the index correspond to the
        # number of years participated. This works because the roles are retrieved
        # from lowest role to highest.
        badge_roles = (
            None,
            *badge_roles
        )
        
        current_year_roles = [
            role for role in member.roles
            if role.name.startswith(self.role_affixes.year_prefix)]

        # Clamp the badge index to the valid range [0, len(badge_roles))
        badge_role_index = min(len(current_year_roles), len(badge_roles))

        # Choose the correct role based on the number of years participated.
        correct_badge_role = badge_roles[badge_role_index]

        current_badge_roles = [
            role for role in member.roles
            if role.name.startswith(self.role_affixes.badge_prefix)]

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
