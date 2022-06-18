# Discord bot token. Can be retrieved at https://discord.com/developers/applications/
# by creating a new bot for an application.
import os

# path to crefential file
GOOGLE_CREDENTIALS_FILE = 'credentials.json'

# path to token.pickle
GOOGLE_TOKEN_PICKLE='token.pickle'

#id SHEET (you need to save list on one sheet or change this id for current)
GOOGLE_SPREADSHEET_ID = 'your_spreadsheet_id'

# name of part, where attendance in google sheet - on 0 zero row!
NAME_OF_ATTENDANCE = 'Посещаемость лекций'

# row, where start name attendance (from 1)
ROW_START_NAME_ATTENDANCE=1

# row, where start date (from 1)
ROW_START_Date_ATTENDANCE=2

# col where start FIOs (from 1)
COL_START_FIOS=2

# row where start FIOs (from 1)
ROW_START_FIOS=3
