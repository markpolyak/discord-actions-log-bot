import re
import io
from datetime import datetime

import discord
from discord import File

from settings import BOT_TOKEN, ALLOWED_ROLE, COMMAND_CHANNEL, LOG_CHANNEL, LOGGING_BOT


class LogClient(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    async def on_message(self, message: discord.Message):
        # TODO: Decouple everything
        # TODO: Handle exceptions everywhere

        # Check if user has required role to speak to the bot
        if (message.channel.name != COMMAND_CHANNEL
                or ALLOWED_ROLE not in map(lambda x: x.name, message.author.roles)):
            return

        print(f'Message from {message.author}: {message.content}')

        # Parse message
        query = LogQuery.from_message(message.content)
        print(query)

        guild = message.channel.guild

        log_channel = None
        for channel in guild.channels:
            if channel.name == LOG_CHANNEL:
                log_channel = channel
                break

        print(log_channel)

        # Parse messages
        messages = await log_channel.history(after=query.date_start, before=query.date_end, oldest_first=True).flatten()
        messages = [x for x in messages if x.author.name == LOGGING_BOT]
        print(list(map(lambda x: x.embeds[0].description, messages)))

        report: [ReportEntry] = []
        for desc, time in list(map(lambda x: (x.embeds[0].description, x.created_at), messages)):
            groups = re.match(r"\*\*<@!(.+?)>\s(.+?)\s", desc).groups()
            user_id = int(groups[0])
            joined = True if groups[1] == 'joined' else False

            if joined:
                entry = ReportEntry(user_id)
                entry.date_start = time
                report.append(entry)
            else:
                joined_moment = len(report) - 1 - next(
                    (i for i, x in enumerate(reversed(report)) if x.user_id == user_id), None)
                if joined_moment is not None:
                    report[joined_moment].date_end = time
                else:
                    entry = ReportEntry(user_id)
                    entry.date_end = time
                    report.append(entry)

        print(report)

        # Rendering report
        rendered_report = ""
        for entry in report:
            member_name = message.channel.guild.get_member(entry.user_id).nick

            member_time = None
            if entry.date_start is not None and entry.date_end is not None:
                member_time = entry.date_end - entry.date_start

            member_time_str = ""
            if member_time is not None:
                member_time_str = strfdelta(member_time, "{hours}:{minutes}:{seconds}")

            rendered_report += '{}\t{}\t{}\t{}\n'.format(
                member_name,
                # TODO: Find a better way to handle None into str
                entry.date_start.isoformat() if entry.date_start is not None else '',
                entry.date_end.isoformat() if entry.date_end is not None else '',
                member_time_str
            )

        print(rendered_report)

        # Send report back
        # await message.channel.send(rendered_report)
        await message.channel.send(
            file=File(io.StringIO(rendered_report), filename=f'{datetime.now().isoformat()}-{query.channel_name}.tsv'))


class LogQuery:
    channel_name: str
    date_start: datetime
    date_end: datetime

    def __init__(self, channel_name: str, date_start: datetime, date_end: datetime):
        self.channel_name = channel_name
        self.date_start = date_start
        self.date_end = date_end

    @classmethod
    def from_message(cls, message: str) -> 'LogQuery':
        lines = message.splitlines()
        channel_name = lines[0].strip()
        date_start = datetime.fromisoformat(lines[1].strip())
        date_end = datetime.fromisoformat(lines[2].strip())
        return cls(channel_name, date_start, date_end)


class ReportEntry:
    date_start: datetime
    date_end: datetime
    user_id: int

    def __init__(self, user_id):
        # TODO: Fix types
        self.user_id = user_id
        self.date_start = None
        self.date_end = None


def strfdelta(tdelta, fmt):
    d = {"days": tdelta.days}
    d["hours"], rem = divmod(tdelta.seconds, 3600)
    d["minutes"], d["seconds"] = divmod(rem, 60)
    return fmt.format(**d)


if __name__ == '__main__':
    intents = discord.Intents.default()
    intents.members = True
    client = LogClient(intents=intents)
    client.run(BOT_TOKEN)
