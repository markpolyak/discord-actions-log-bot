# Discord Access Log Export Bot

Export voice channel access logs from Dyno in a TSV format with a simple command.

Settings are located in `settings.py`.

Bot responds to a message containing three params: name of an audio channel to search info about, start and end dates
of log to search in (iso format specified in UTC currently).

Current implementation is pretty rough and mostly MVP. To be improved in the future

## Setting up bot

1. Register your new application at https://discord.com/developers/applications
2. Create a bot for your application
3. Turn on `SERVER MEMBERS INTENT` in your bot. This will allow it to see members of discord channel, which is needed
   to determine people's server nicknames by id
4. Go to `OAuth2 > URL Generator` and generate a link for your bot to add it to channel
   * Check `bot` in `SCOPES`
   * Check in `BOT PERMISSIONS`: `Send Messages`, `Attach Files`, `Read Message History`, and `Read Messages/View Channels`.
   I'm not sure whether we need all of them, it worked for me even without all of them, but I did not test it precisely.
5. Adjust setting to yours. You will need to provide bot token from Discord developer portal (`Bot > Token`), log channel,
   command channel (to communicate with bot) and authorized group to which it will respond to only.