from dataclasses import dataclass
import json

from discord import app_commands, Client, Guild, Interaction, Member, Message, \
    PermissionOverwrite, TextChannel
if not __debug__:
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


async def log(channel: TextChannel, message: str):
        """Log a message to a channel and print it to the console."""
        await channel.send(message)
        print(message)


class HouseRobot(Client):
    """Custom client."""

    def __init__(self, settings: dict, doorbell_responses: dict,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.settings = settings
        self.doorbell_responses = doorbell_responses

        self.role_affixes = RoleAffixes(
            settings['seniority_badge']['year_role_prefix'],
            settings['seniority_badge']['badge_role_prefix'],
            settings['seniority_badge']['badge_role_suffix'])
        self.status_channel = {}
        self.invite_uses = {}

        self.tree = app_commands.CommandTree(self)


    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')

        for guild in self.guilds:
            try:
                self.status_channel[guild.id] = next(
                    channel for channel in guild.channels
                    if channel.name == self.settings['debug']['status_channel'])
            except StopIteration:
                raise RuntimeError(f"Status channel {self.settings['debug']['status_channel']} not found.")
            status_channel = self.status_channel[guild.id]

            await log(status_channel, "I'm online!")

            await log(status_channel, 'Storing invite uses...')
            self.invite_uses[guild.id] = await get_invite_uses(guild)
            await log(status_channel, 'Done storing invite uses.')

            await log(status_channel, 'Adjusting roles...')
            for member in guild.members:
                await self.adjust_badge_roles(member)
            await log(status_channel, 'Done adjusting roles.')

        @self.tree.command(guilds=self.guilds)
        @app_commands.describe(year='The year of the competition.')
        @app_commands.checks.has_permissions(administrator=True)
        async def setup_channels(interaction: Interaction, year: int):
            """Setup the category with public channels for the robot competition
            at the specified year. Do nothing if the category already exists.
            """

            guild = interaction.guild
            status_channel = self.status_channel[guild.id]
            setup_filename = 'category_setup.json'
            new_role_name = f'Tävlande {year}'
            previous_role_name = f'Tävlande {year - 1}'
            new_category_name = f'Robottävlingen {year}'
            previous_category_name = f'Robottävlingen {year - 1}'

            await log(status_channel, f'Setting up public channels for the Robot Competition {year}...')

            # Parse the settings file.
            try:
                with open(setup_filename, encoding='utf-8') as json_file:
                    setup_json = json.load(json_file)
                    category_json = setup_json['category']
                    channels_json = setup_json['channels']

                    category_roles = []
                    for role_name in category_json['roles']:
                        # Get the role with this name:
                        role = next(
                            (role for role in guild.roles
                             if role.name == role_name),
                            None)
                        if role:
                            category_roles.append(role)
                        else:
                            message = f'Aborted: Could not find the role {role_name}.'
                            await log(status_channel, message)
                            await interaction.response.send_message(message)
                            return

            except FileNotFoundError:
                message = f'Aborted: Could not find the file {setup_filename}.'
                await log(status_channel, message)
                await interaction.response.send_message(message)
                return
            except KeyError:
                message = f'Aborted: The file {setup_filename} is missing required keys.'
                await log(status_channel, message)
                await interaction.response.send_message(message)
                return

            # Abort if the category already exist.
            if any(category.name == new_category_name for category
                   in interaction.guild.categories):
                message = f'Aborted: The category {new_category_name} already exists.'
                await log(status_channel, message)
                await interaction.response.send_message(message)
                return

            await interaction.response.send_message('Creating channels...')

            # Create the competitor role if it doesn't exist.
            new_role = next(
                (role for role in guild.roles if role.name == new_role_name),
                None)
            if new_role:
                await log(status_channel, f'Role {new_role_name} already exists.')
            else:
                new_role = await guild.create_role(name=new_role_name)
                await log(status_channel, f'Created role {new_role_name}.')
            category_roles.append(new_role)

            # If there are roles from previous years, make sure the new role is
            # directly below the previous role.
            previous_role = next(
                (role for role in guild.roles
                 if role.name == previous_role_name),
                None)
            if previous_role:
                await new_role.edit(position=previous_role.position - 1)
                await log(status_channel, f'Role {new_role_name} moved below {previous_role_name}.')

            # Create overwrites for the category to make it private.
            overwrites = {
                role: PermissionOverwrite(read_messages=True, connect=True)
                for role in category_roles
            }
            overwrites[guild.default_role] = PermissionOverwrite(
                read_messages=False)

            # Create the category at the top by default.
            category = await guild.create_category(new_category_name,
                                                   overwrites=overwrites,
                                                   position=0)
            await log(status_channel, f'Created category {new_category_name}.')

            # If there are categories from previous years, make sure the new
            # category is directly above the previous category.
            previous_category = next(
                (category for category in guild.categories
                 if category.name == previous_category_name),
                None)
            if previous_category:
                await category.move(before=previous_category)
                await log(status_channel, f'Category {new_category_name} moved above {previous_category_name}.')

            for channel in channels_json:
                await guild.create_text_channel(
                    name=channel['name'],
                    topic=channel['topic'],
                    category=category)

        await self.sync_commands()


    async def on_member_join(self, member: Member):
        guild = member.guild
        status_channel = self.status_channel[guild.id]

        await log(status_channel, f'{member.name} joined the server.')

        try:
            robot_group_role = next(
                role for role in guild.roles
                if role.name == self.settings['robot_group']['role'])
        except StopIteration:
            raise RuntimeError(f"Robot group role {self.settings['robot_group']['role']} not found.")

        for invite in await guild.invites():
            invite_uses_before = self.invite_uses[guild.id].get(invite.code, 0)

            if invite.uses > invite_uses_before:
                await log(status_channel, f'{member.name} joined using invite {invite.code}')

                # Check if the invite was for joining the robot group.
                if invite.channel.name == self['invites']['destination_channels']['robot_group']:
                    await member.add_roles(robot_group_role)

                    await log(status_channel, f'{member.name} assigned the role "{invite.channel.name}".')
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
        if message.channel.name != self.settings['doorbell']['channel']:
            return

        # Ignore messages from bots. Prevents infinite loops.
        if message.author.bot:
            return

        # Only allow some members to ring the doorbell.
        author_roles = [role.name for role in message.author.roles]
        if not self.settings['doorbell']['allowed_user_role'] in author_roles:
            await message.channel.send(self.doorbell_responses['invalidRole'])
            return

        if __debug__:
            text = 'Doorbell disabled in debug mode.'
            print(text)
            await message.channel.send(text)
        else:
            # Toggle pin to ring door bell.
            pin = DigitalOutputDevice(self.settings['doorbell']['pin'])
            pin.on()
            await sleep(0.5)
            pin.off()

            # Respond to the request to open the door by writing a message in the
            # same channel.
            await message.channel.send(self.doorbell_responses['ok'])

    async def adjust_badge_roles(self, member: Member):
        status_channel = self.status_channel[member.guild.id]

        badge_roles = [
            role for role in member.guild.roles
            if role.name.startswith(self.role_affixes.badge_prefix)
            and role.name.endswith(self.role_affixes.badge_suffix)]

        # Add None to the list of badge roles so that the index correspond to
        # the number of years participated. This works because the roles are
        # retrieved from lowest role to highest.
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
            await log(status_channel, f'Adding role {correct_badge_role.name} to {member.name}')
            await member.add_roles(correct_badge_role)
        if roles_to_remove:
            await log(status_channel, f'Removing roles {", ".join(role.name for role in roles_to_remove)} from {member.name}')
            await member.remove_roles(*roles_to_remove)


    async def sync_commands(self):
        """Sync commands with the guilds."""
        for guild in self.guilds:
            status_channel = self.status_channel[guild.id]

            await log(status_channel, 'Syncing commands...')
            await self.tree.sync(guild=guild)
            await log(status_channel, 'Done syncing commands.')
