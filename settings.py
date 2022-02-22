# Discord bot token. Can be retrieved at https://discord.com/developers/applications/
# by creating a new bot for an application.
import os
BOT_TOKEN = os.environ['BOT_TOKEN']

# Log channel name
LOG_CHANNEL = 'лог-посещений'

# Channel to listen to for command
COMMAND_CHANNEL = 'посещаемость'

# Role to which bot is allowed to respond to
# TODO: Make it a list
ALLOWED_ROLE = 'staff'

# Bot name that makes a log
LOGGING_BOT = 'Dyno'
