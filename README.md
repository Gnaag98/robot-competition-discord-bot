# robot-competition-bot
Discord bot for the Robot Competition at Umeå University.

The Robot Competition is a yearly competition hosted by the students of the
Master of Science Programme in Engineering Physics at Umeå University.

All primary communication is done through a Discord server. The Discord bot
automates various aspects of the server, and implements other related
services like a doorbell system for the workshop.

## Doorbell
The contestants are allowed to use a workshop accessible by university students.
However, since anyone can participate, not only university students, those
without access need a way to be let inside. We therefore use a doorbell system.

The bot is assumed to be running on a Raspberry Pi so that GPIO pins are
accessible. One of the pins are connected to a physical doorbell mounted in
the workshop. The doorbell will ring if a member writes in as specific channel.

## settings.json
This file need to be created by duplicating `settings_template.json` and
renaming it to `settings.json`. In this file you will enter the secret Discord
token. Therefore, this file should **NOT** be shared or synced in any way.

### `discord_token`
Enter the token generated in the Discord Developer Portal. Make sure to **not**
share this token.

### `debug`
Specify the status channel in which the Discord bot will print log and error
messages.

### `invites`
This is used to assign roles to new users depending on which channel they
entered via. Each entry in `invites`, is an object with a `channel` and a `role`
key. The `channel` specifies which channel the user was invited to. This should
match the channel in the created invite to that user. The user is then assigned
the role specified by `role`.

### `doorbell`
The doorbell is a physically connected doorbell that rings when a message is
written in a specific channel, specified by `channel`. When the doorbell is
triggered a short pulse is sent to the specified `pin`. If `allowed_user_role`
is an empty string all memobers are allowed to trigger the doorbell. Otherwise
only the memobers with the specified role will be allowed to trigger the
doorbell.

### `seniority_badge`
Contestants are automatically given cosmetic roles depending on how many years
they have participated. First year participants get a green name, second years
get a blue name and those who have participated at least three years get a
purple name.

The years competed are counted using `year_role_prefix`, that count how many
roles the user has that matches the prefix, e.g, the prefix *Competition* would
match the roles *Competition 2024*, *Competition 2025*, etc.

To assigne the correct cosmetic role, the three cosmetic roles should all have
matching prefixes and a suffixes, specified by `badge_role_prefix` and
`badge_role_suffix` respectively. Make sure to order the roles by seinority in
ascending order, i.e the most senior role above the others.

## Run bot on startup
To run the bot when the Raspberry Pi starts, a cron job can be used. Here is an
example of how to do that.

1. Create a script called `run_bot.sh` that contains the following:
```bash
cd /absolute/path/to/the/repository # Replace with actual absolute path.
. .venv/bin/activate # Assuming .venv is your virtual environment directory.
python -O main.py
```
2. Run `crontab -e` in a terminal. This opens up a file for scheduling tasks.
3. Paste the following at the bottom of the file:
```
@reboot bash /absolute/path/to/run_bot.sh # Replace with actual absolute path.
```
4. Save the file by pressing **CTRL+X** then **y** then the enter key.
