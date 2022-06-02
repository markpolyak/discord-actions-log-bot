from __future__ import annotations

import logging

import datetime
import re
import io
from datetime import datetime, timezone, timedelta

import discord
from discord import File

from settings import BOT_TOKEN, ALLOWED_ROLE, COMMAND_CHANNEL, LOG_CHANNEL, LOGGING_BOT


logging.basicConfig(level=logging.INFO, format='%(asctime)s :: %(levelname)s :: %(message)s')
logger = logging.getLogger(__name__)


class LogClient(discord.Client):
    async def on_ready(self):
        logger.info("Logged on as %s!", self.user)

    async def on_message(self, message: discord.Message):
        # TODO: Handle exceptions everywhere

        # Check if user has required role to speak to the bot
        if (message.channel.name != COMMAND_CHANNEL
                or ALLOWED_ROLE not in map(lambda x: x.name, message.author.roles)):
            return

        logger.info("Message from %s: %s", message.author, message.content)

        # Parse message
        query = LogQuery.from_message(message.content)

        guild = message.channel.guild

        # Get channel with logs
        log_channel = None
        for channel in guild.channels:
            if channel.name == LOG_CHANNEL:
                log_channel = channel
                break

        # Get messages and parse them
        messages = await \
            get_log(log_channel, query)
        logger.info("Retrieved %d messages", len(messages))
        report = parse_log(messages, query, guild)

        # Render a report
        if query.output_type == 'tsv':
            sep = '\t'
        elif query.output_type == 'csv':
            sep = ','
        elif query.output_type == 'excel':
            sep = ';'
            query.output_type = 'csv'
        elif query.output_type == 'txt':
            sep = '\t'
            query.output_type = 'txt'
        else:
            logger.error("Unknown output format %s", query.output_type)
            await message.channel.send(f"Unknown output format {query.output_type}")
            return
        # TODO: Do we need to optimize user names queries here?
        rendered_report = f"\ufeffname{sep}joined_at{sep}left_at{sep}time_spent\n"
        for entry in report:
            member = message.channel.guild.get_member(entry.user_id)
            if member:
                member_name = member.display_name
            else:
                member_name = f"Unknown <{entry.user_id}>"
                logger.error("Unknown user with id %d", entry.user_id)
            rendered_report += entry.render(member_name, sep=sep)

        # Send the report as file
        filename = f"{query.date_start:%Y-%m-%d_%H-%M-%S}--{query.date_end:%Y-%m-%d_%H-%M-%S}--{query.channel_name}.{query.output_type}" #noqa
        await message.channel.send(
            file=File(io.StringIO(rendered_report), filename=filename))


async def get_log(log_channel: discord.TextChannel, query: LogQuery) -> [discord.Message]:
    messages = await log_channel.history(
        limit=None,
        after=convert_to_utc(query.date_start),
        before=convert_to_utc(query.date_end),
        oldest_first=True
    ).flatten()

    return [x for x in messages if x.author.name == LOGGING_BOT]


def convert_to_utc(dt: datetime) -> datetime:
    offset = dt.utcoffset()
    return dt.replace(tzinfo=None) - offset


def parse_log(messages: [discord.Message], query: LogQuery, guild: discord.Guild) -> [ReportEntry]:
    report: [ReportEntry] = []

    for desc, time in list(map(lambda x: (x.embeds[0].description, x.created_at), messages)):
        logger.debug("Parsing message %s sent at %s", desc, time)
        match = re.match(r"\*\*<@!?(.+?)>\s(.+?)\s(.+?)[`<]#(.+?)[`>](?:\s->\s[`<]#(.+?)[`>])?", desc)
        if not match:
            logger.error("Unable to parse message \"%s\" sent at %s", desc, time)
            continue
        groups = match.groups()
        user_id = int(groups[0])
        # if groups[1] == 'joined' or (groups[1] == 'switched' and groups[4] == query.channel_name):
        #     joined = True
        if groups[1] == 'left' or (groups[1] == 'switched' and groups[3] == query.channel_name):
            joined = False
        else:
            joined = True
        # check if this log event correspons to the voice channel in question
        logger.info("Message %s, parsed groups are %s", desc, groups)
        channel_list = []
        if groups[3].isnumeric():
            channel_list += [guild.get_channel(int(groups[3])).name]
        else:
            channel_list += [groups[3]]
        if len(groups) > 4 and groups[4] is not None:
            if groups[4].isnumeric():
                channel_list += [guild.get_channel(int(groups[4])).name]
            else:
                channel_list += [groups[4]]
        if query.channel_name not in channel_list:
            continue
        # channel_id = int(groups[3]) if groups[1] != 'switched' else None
        # if channel_id and guild.get_channel(channel_id).name != query.channel_name:
        #     continue
        # # logger.info("Message %s, parsed groups are %s", desc, groups)
        # if groups[1] == 'switched' and query.channel_name not in [groups[3], groups[4]]:
        #     continue

        if time:
            time = time.replace(tzinfo=timezone.utc)

        if joined:
            entry = ReportEntry(user_id)
            entry.date_start = time
            report.append(entry)
        else:
            entry = next((x for x in reversed(report) if x.user_id == user_id), None)
            if entry is None:
                entry = ReportEntry(user_id)
                report.append(entry)
            entry.date_end = time

    return report


class LogQuery:
    channel_name: str
    date_start: datetime
    date_end: datetime
    output_type: str

    def __init__(self, channel_name: str, date_start: datetime, date_end: datetime, output_type: str):
        self.channel_name = channel_name
        self.date_start = date_start
        self.date_end = date_end
        self.output_type = output_type

    @classmethod
    def from_message(cls, message: str) -> LogQuery:
        items = message.replace(',', ';').replace('\n', ';').split(';')
        channel_name = items[0].strip()
        date_start = datetime.fromisoformat(items[1].strip()).astimezone()
        date_end = datetime.fromisoformat(items[2].strip()).astimezone()
        # if len(items) > 3:
        output_type = items[3].strip() if len(items) > 3 else 'txt'
        return cls(channel_name, date_start, date_end, output_type)


class ReportEntry:
    date_start: datetime | None
    date_end: datetime | None
    user_id: int
    user_name: str

    def __init__(self, user_id):
        self.user_id = user_id
        self.date_start = None
        self.date_end = None

    @property
    def elapsed_time(self) -> timedelta | None:
        if self.date_start is not None and self.date_end is not None:
            return self.date_end - self.date_start
        else:
            return None

    def render(self, username: str, sep: str = '\t') -> str:
        elapsed_time_s = ''
        if self.elapsed_time is not None:
            elapsed_time_s = ReportEntry.strfdelta(self.elapsed_time, '{hours:02}:{minutes:02}:{seconds:02}')

        date_start_s = ''
        if self.date_start is not None:
            date_start_s = self.date_start.astimezone().isoformat(sep=' ', timespec='seconds')

        date_end_s = ''
        if self.date_end is not None:
            date_end_s = self.date_end.astimezone().isoformat(sep=' ', timespec='seconds')

        # return f'{username}\t{date_start_s}\t{date_end_s}\t{elapsed_time_s}\n'
        return f'{sep}'.join([username, date_start_s, date_end_s, elapsed_time_s]) + '\n'

    @staticmethod
    def strfdelta(tdelta, fmt):
        d = {'days': tdelta.days}
        d['hours'], rem = divmod(tdelta.seconds, 3600)
        d['minutes'], d['seconds'] = divmod(rem, 60)
        return fmt.format(**d)


if __name__ == '__main__':
    intents = discord.Intents.default()
    intents.members = True
    client = LogClient(intents=intents)
    client.run(BOT_TOKEN)
