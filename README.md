# Discord Access Log Export Bot

Export voice channel access logs from Dyno in a TSV format with a simple command.

Settings are located in `settings.py`.

Bot responds to a message containing three params: name of an audio channel to search info about, start and end dates
of log to search in (iso format specified in UTC currently).

Current implementation is pretty rough and mostly MVP. To be improved in the future

## Setting up bot

Required: Python 3.10 and dependencies listed in `requirements.txt`.

1. Register your new application at https://discord.com/developers/applications
2. Create a bot for your application
3. Turn on `SERVER MEMBERS INTENT` in your bot. This will allow it to see members of discord channel, which is needed
   to determine people's server nicknames by id
4. Go to `OAuth2 > URL Generator` and generate a link for your bot to add it to channel
   * Check `bot` in `SCOPES`
   * Check in `BOT PERMISSIONS`: `Send Messages`, `Attach Files`, `Read Message History`, and `Read Messages/View Channels`.
   I'm not sure whether we need all of them, it worked for me even without all of them, but I did not test it precisely.
5. Adjust settings to yours. You will need to provide bot token from Discord developer portal (`Bot > Token`), log channel,
   command channel (to communicate with bot) and authorized group to which it will respond to only.
6. Run the bot and set up necessary channels, roles
7. Send a message in the `COMMAND_CHANNEL` containing channel name to take logs from, and two iso datetimes of start and end.
   Example:
   ```
   General
   2022-02-18T00:00:00+03:00
   2022-02-18T02:00:00+03:00
   ```
   Timezone is optional. Timezone of output is currently always UTC.

## Setting up google sheet modification

Required: Python 3.10 and dependencies listed in `requirements.txt`.
Required: setting up bot.

1. In settings you should set variable MIN_TIME_ATTENDANCE - integer in minutes. This variable can help to understand - was the person at the lecture enough time - if not, then we left him, but he will be set in result file in format txt
2. You should create new sheet in Google sheet, if you don't have now. And save id of this sheet in GOOGLE_SPREADHEET_ID in googleSheetSettings.py. 
<i>Condition of the structure:</i>
   + all FIO should be in one column
   + all dates should be in one row
   + all attendance should be in one column for every date
   + Dates must start in col with the cell with text in variable NAME_OF_ATTENDANCE
   + Format of attendance '1' if attend else everything besides '1'
2. Determine settings in settings.py:
   + Format of dates should be determine in variable GOOGLE_FORMAT_DATE

3. Also you need to determine Settings in googleSheetSettings.py
   + FIO column start with variables:
      * COL_STARTS_FIO, which determine col start position of FIO 
      * ROW_STARTS_FIO, which determine row start position of FIO (count from 1)
   + ROW_START_NAME_ATTENDANCE - row, where we can find start of the dates - signal for column is key word variable NAME_OF_ATTENDANCE
   + ROW_START_DATE_ATTENDANCE variable, which determine row position of dates (in what row we should search the dates?)
4. After that you need to create google API and get credentials. Credentials json and token json you should save in path, where project is and set names on variables in set in googleSheetSettings.py:
   + GOOGLE_TOKEN_JSON and GOOGLE_CREDENTIALS_FILE or copy path of this files to variables.
   + GOOGLE_TOKEN_PICKLE - variable of refresh key. After first connection you can forget about refresh token on API every weak - you just need to delete this file, when token get old - program will automaticly refresh token and create pickle file(set in googleSheet)
5. For call this mode in format file you need to set mode <i><b>google</b></i> in place of text format
