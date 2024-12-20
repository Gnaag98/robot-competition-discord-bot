import json

from discord import app_commands, Client, Interaction, Member, Message, \
    PermissionOverwrite

from doorbell import check_doorbell
from invites import apply_invite_role, get_invite_uses
from bot_logging import log
from seniority_badge import RoleAffixes, adjust_badge_roles


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
            # Get channel used to log status messages.
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
                await adjust_badge_roles(member, self.role_affixes, status_channel)
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

            # Get the robot group role.
            robot_group_role = next(
                (role for role in guild.roles
                    if role.name == 'Robotgruppen'),
                None)
            if not robot_group_role:
                message = f'Aborted: Could not find the Robot group role.'
                await log(status_channel, message)
                await interaction.response.send_message(message)
                return

            # Create the competitor role if it doesn't exist.
            competitors_role = next(
                (role for role in guild.roles if role.name == new_role_name),
                None)
            if competitors_role:
                await log(status_channel, f'Role {new_role_name} already exists.')
            else:
                competitors_role = await guild.create_role(name=new_role_name)
                await log(status_channel, f'Created role {new_role_name}.')
            # If there are roles from previous years, make sure the new role is
            # directly below the previous role.
            previous_role = next(
                (role for role in guild.roles
                 if role.name == previous_role_name),
                None)
            if previous_role:
                await competitors_role.edit(position=previous_role.position - 1)
                await log(status_channel, f'Role {new_role_name} moved below {previous_role_name}.')

            # Create overwrites for the category that can be synched with its channels.
            category_overwrites = {
                robot_group_role: PermissionOverwrite(
                    view_channel=True, connect=True, send_messages=True, speak=True),
                competitors_role: PermissionOverwrite(
                    view_channel=True, connect=True),
                guild.default_role: PermissionOverwrite(
                    view_channel=False, connect=False, send_messages=False, speak=False)
            }

            # Parse the settings file into a dict.
            try:
                with open(setup_filename, encoding='utf-8') as json_file:
                    setup_json = json.load(json_file)
                    channels_json = setup_json['channels']
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
            # Create the category at the top by default.
            await interaction.response.send_message('Creating channels...')
            category = await guild.create_category(new_category_name,
                                                   overwrites=category_overwrites)

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

            # Add channels to category.
            for channel_json in channels_json:
                channel_name: str = channel_json['name']
                channel_topic: str = channel_json['topic']
                channel_overwrites = {}
                # Only adjust overwrites if there are any permissions to add or remove.
                if 'permissions' in channel_json and channel_json['permissions']:
                    # Perform deep copy of overwrites.
                    for role, overwrite in category_overwrites.items():
                        channel_overwrites[role] = PermissionOverwrite.from_pair(*overwrite.pair())
                for channel_permission_json in channel_json['permissions']:
                    role_name = channel_permission_json['role']
                    if role_name == '@everyone':
                        role = guild.default_role
                    elif role_name == 'Tävlande20XX':
                        role = competitors_role
                    else:
                        role = next(
                            (role for role in guild.roles
                            if role.name == role_name),
                            None)
                        if not role:
                            message = f'Aborted: Could not find the role {role_name}.'
                            await log(status_channel, message)
                            await interaction.response.send_message(message)
                            return
                    
                    add_kwargs = {attribute: True for attribute in channel_permission_json['add']}
                    remove_kwargs = {attribute: False for attribute in channel_permission_json['remove']}
                    if not role in channel_overwrites:
                        channel_overwrites[role] = PermissionOverwrite()
                    channel_overwrites[role].update(**add_kwargs, **remove_kwargs)
                await guild.create_text_channel(
                    name=channel_name,
                    topic=channel_topic,
                    overwrites=channel_overwrites,
                    category=category)
            """ try:
                public_readonly_channels_json = channels_json['public_readonly']
                competitors_readonly_channels_json = channels_json['competitors_readonly']
                competitors_channels_json = channels_json['competitors']
                private_channels_json = channels_json['private']
            except KeyError:
                message = f'Aborted: The file {setup_filename} is missing required keys for the channels.'
                await log(status_channel, message)
                await interaction.response.send_message(message)
                return
            for channel in public_readonly_channels_json:
                await guild.create_text_channel(
                    name=channel['name'],
                    topic=channel['topic'],
                    category=category) """

        await self.sync_commands()

        await log(status_channel, "I'm ready!")


    async def on_member_join(self, member: Member):
        guild = member.guild
        status_channel = self.status_channel[guild.id]

        await log(status_channel, f'{member.name} joined the server.')

        for invite in await guild.invites():
            invite_uses_before = self.invite_uses[guild.id].get(invite.code, 0)

            # Check if the user joined via this invite.
            if invite.uses > invite_uses_before:
                await log(status_channel, f'{member.name} joined using invite {invite.code}')
                await apply_invite_role(member=member, invite=invite,
                                  invite_settings=self.settings['invites'],
                                  status_channel=status_channel)
                # Make sure new competitors get a seniority badge.
                await adjust_badge_roles(member, self.role_affixes, status_channel)
                # The invite was found. No need to check the rest.
                break

        # Update the invite uses for the next member join event.
        self.invite_uses[guild.id] = await get_invite_uses(guild)


    async def on_member_update(self, member_before: Member, member_after: Member):
        guild = member_after.guild
        status_channel = self.status_channel[guild.id]

        if member_before.roles != member_after.roles:
            # It is possible the seniority badge need to be updated.
            await adjust_badge_roles(member_after, self.role_affixes, status_channel)


    async def on_message(self, message: Message):
        # Ignore messages from bots. Prevents infinite loops.
        if message.author.bot:
            return
        
        await check_doorbell(message=message, doorbell_settings=self.settings['doorbell'],
                       doorbell_responses=self.doorbell_responses)


    async def sync_commands(self):
        """Sync commands with the guilds."""
        for guild in self.guilds:
            status_channel = self.status_channel[guild.id]

            await log(status_channel, 'Syncing commands...')
            await self.tree.sync(guild=guild)
            await log(status_channel, 'Done syncing commands.')
