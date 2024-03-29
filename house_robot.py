from attr import dataclass

from discord import Client, Member, Message
from gpiozero import DigitalOutputDevice
from asyncio import sleep

@dataclass
class RoleAffixes:
    """Prefixes and suffixes for the roles."""
    year_prefix: str
    badge_prefix: str
    badge_suffix: str


class HouseRobot(Client):
    """Custom client."""

    def __init__(self, guild_id: int, doorbell_pin: int, doorbell_role: str, doorbell_channel_name: str, doorbell_responses: dict, affixes: RoleAffixes, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.guild_id = guild_id
        self.doorbell_role = doorbell_role
        self.doorbell_pin = doorbell_pin
        self.doorbell_channel_name = doorbell_channel_name
        self.doorbell_responses = doorbell_responses
        self.role_affixes = affixes
    

    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')

        guild = self.get_guild(self.guild_id)

        print('Adjusting roles...')
        for member in guild.members:
            await self.adjust_badge_roles(member)
        
        print('Done adjusting roles.')


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
