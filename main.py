from __future__ import annotations

import googleSheet
from googleSheet import GoogleSheetParser

import logging

import datetime
import re
import io
from datetime import datetime, timezone, timedelta

import discord
from discord import File
from discord.ext.commands import has_permissions, MissingPermissions
from discord.ext import commands
#from discord.ext import bot

from settings import BOT_TOKEN, ALLOWED_ROLE, COMMAND_CHANNEL, LOG_CHANNEL, LOGGING_BOT, MIN_TIME_DELTA


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s :: %(levelname)s :: %(message)s')
logger = logging.getLogger(__name__)

Min_Time_Delta=None

class LogClient(discord.Client):
    async def on_ready(self):
        logger.info("Logged on as %s!", self.user)

    #@bot.command ( name = 'send' )
    #@bot.has_permissions( administrator = True )
    #@bot.bot_has_permissions( administrator = True )
    async def on_message(self, message: discord.Message):
        """
        React on message, if Format is right, than perform actions of atendance
        
        :param message: object of discord.Message
     
        :returns: file or result of sending to Google Sheet    
        """
        # TODO: Handle exceptions everywhere
        global Min_Time_Delta
        # Check if user has required role to speak to the bot
        if (message.channel.name != COMMAND_CHANNEL
                or ALLOWED_ROLE not in map(lambda x: x.name, message.author.roles)):
            return
        await message.channel.send("Please, wait for results...")  
        
        logger.info("Message from %s: %s", message.author, message.content)


        # Parse message
        query = ''
        try:
            query = LogQuery.from_message(message.content)
        except Exception as ex:
            await message.channel.send(ex)   
            return
        guild = message.channel.guild
        # Get channel with logs
        log_channel = None
        for channel in guild.channels:
            if channel.name == LOG_CHANNEL:
                log_channel = channel
                break
        
        # check mistakes before parse maessages (get massages history - is long process)
                
        
        # Render a report
        #if query.channel_name.lower()==NAME_HELP_COMMAND.lower()
            #endHelp(message)
            #return
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
        elif query.output_type == 'google':
            if (query.id_google_sheet==None or query.id_google_sheet.strip() == ''):
                await message.channel.send("Wrong Parameters. For google sheet you need set google sheet ID.")
                await message.channel.send('You can find it in your table url')
                return                
            if f'{query.date_end:%y.%m.%d}'!= f'{query.date_start:%y.%m.%d}':
                await message.channel.send("Not equal start and end dates - can' set atendance to google sheet")
                return 
            if (query.min_attendance_minutes!=None):
                if (query.min_attendance_minutes.isnumeric() and int(str(query.min_attendance_minutes))>0):
                    Min_Time_Delta=timedelta(minutes=int(query.min_attendance_minutes))
                else:
                    await message.channel.send('Min attendance minutes must be an integer value (not a string), larger than 0!') 
                    return
            else:
                Min_Time_Delta=timedelta(minutes=MIN_TIME_DELTA)
        #elif (query.channel_name) == NAME_HELP_COMMAND):
        #    await message.channel.send("Hello, i'm attendance bot. I'll help you to get attendance. Let's check out my functions:")
        #    help_emb = discord.Embed( title = ''
               
        else:
            logger.error("Unknown output format %s", query.output_type)
            await message.channel.send(f"Unknown output format {query.output_type}")
            return
        
        # Get messages and parse them
        messages = await \
            get_log(log_channel, query)
        logger.info("Retrieved %d messages", len(messages))
        report = parse_log(messages, query, guild)
        
            
        if query.output_type != 'google':
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
        else:     
            totalErrorsDiscord=[] #  for errors from discord
            totalErrors=[] #  for errors from parser and googleSheet
            totalWarnings=[] # for warning from parser and googleSheet
            totalInfo=[] #  for user, which don't spend enough time
            totalResult='None result'
            renderDict={}
            for entry in report:            
                member = message.channel.guild.get_member(entry.user_id)   
                if member:
                    member_name = member.display_name
                else:
                    logger.error("Unknown user with id %d", entry.user_id)    
                    totalErrorsDiscord.append("Error: unknown user with id " + str(entry.user_id) + " in discord")
                    # For unknown id - is not neccessary to show errors in result doument
                    continue
                entry.setUniqueFromRenderInDict(member_name, query, renderDict)
            # clear, when not in delta Time
            totalInfo, renderDict = compareToArrayRenderDictByMinTimeDelta(renderDict)
            if (len(renderDict)<=0):
                await message.channel.send("Nothing was found according to your request...")
                await message.channel.send("Try to varify name of your channel  or range of dates!")  
                return
            # convert to nick
            try:
                googleSheetParser = GoogleSheetParser()
                totalResult, totalWarnings, totalErrors = googleSheetParser.setAttendanceFromNicksToGoogleSheet(f'{query.date_end:%d.%m}', renderDict, query.id_google_sheet)
            except Exception as ex:
                await message.channel.send(ex)
                return
            if (totalResult==False):
                await message.channel.send("Can't update google sheet")
            else:

                result_emb=None
                result_emb = discord.Embed( title = 'RESULT', colour = discord.Color.green())
                for result in totalResult:
                    result_emb.add_field(name = str(result), value=str(totalResult[result]), inline=False)
                result_emb.add_field(name = "Total Discord Errors", value=str(len(totalErrorsDiscord)), inline=False)
                result_emb.add_field(name = "Total not enough time for attendance ", value=str(len(totalErrorsDiscord)), inline=False)
                await message.channel.send( embed = result_emb)
                """
                result_simple=''
                for result in totalResult:
                    result_simple=result_simple+str(result)+' '+ str(totalResult[result])+'\n'            
                result_simple=result_simple+"Total Discord Errors"+' '+str(len(totalErrorsDiscord))+'\n'
                result_simple=result_simple+"Total not enough time for attendance "+' '+str(len(totalErrorsDiscord))
                await message.channel.send(result_simple)
                """
            # Result for add
            result=('\n'.join(totalErrors)+'\n' if len(totalErrors)>0 else '') + \
                    ('\n'.join(totalWarnings)+'\n' if len(totalWarnings)>0 else '') + \
                    ('\n'.join(totalErrorsDiscord)+'\n' if len(totalErrorsDiscord)>0 else '') + \
                    ('\n'.join(totalInfo) if len(totalInfo)>0 else '')
            if (result!=''):
                # name of File
                filename = f"errors--{query.date_start:%Y-%m-%d_%H-%M-%S}--{query.date_end:%Y-%m-%d_%H-%M-%S}.txt" 
                await message.channel.send(file=File(io.StringIO(result), filename=filename))     

async def get_log(log_channel: discord.TextChannel, query: LogQuery) -> [discord.Message]:
    """
    React on message, if Format is right, than perform actions of atendance
    
    :info: -> [discord.Message] need to send discord.Message
    
    :param message: object of discord.Message
    
    :returns: file or result of sending to Google Sheet    
    """
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
    """
    React on message, if Format is right, than perform actions of atendance
    
    :param messages: Array of messages between start and end date
    :param LogQuery: object of parse user message info
    :param guild: information about channels

    :returns: array of Objects reportEntry   
    """
    report: [ReportEntry] = []

    for desc, time in list(map(lambda x: (x.embeds[0].description, x.created_at), messages)):
        logger.debug("Parsing message %s sent at %s", desc, time)
        match = re.match(r"\*\*<@!?(.+?)>\s(.+?)\s(.+?)[`<]#(.+?)[`>](?:\s->\s[`<]#(.+?)[`>])?", desc)
        if not match:
            logger.error("Unable to parse message \"%s\" sent at %s", desc, time)
            continue
        groups = match.groups()
        user_id = int(groups[0])
        # check if this log event correspons to the voice channel in question
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
        # is user joining or leaving voice channel?
        if groups[1] == 'left' or (groups[1] == 'switched' and channel_list[0] == query.channel_name):
            joined = False
        else:
            joined = True

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
    id_google_sheet: str | None
    min_attendance_minutes: str | None

    def __init__(self, channel_name: str, date_start: datetime, date_end: datetime, output_type: str, id_google_sheet: str | None, min_attendance_minutes: str | None):
        self.channel_name = channel_name
        self.date_start = date_start
        self.date_end = date_end
        self.output_type = output_type
        self.id_google_sheet = id_google_sheet
        self.min_attendance_minutes =  min_attendance_minutes

    @classmethod
    def from_message(cls, message: str) -> LogQuery:
        items = message.replace(',', ';').replace('\n', ';').split(';')
        channel_name=''
        date_start=''
        date_end=''
        output_type=''
        try:
            channel_name = items[0].strip()
            date_start = datetime.fromisoformat(items[1].strip()).astimezone()
            date_end = datetime.fromisoformat(items[2].strip()).astimezone()
            output_type = items[3].strip().lower() if len(items) > 3 else 'txt'
            id_google_sheet = items[4].strip() if len(items) > 4 else None  
            min_attendance_minutes = items[5].strip() if len(items) > 5 else None  
        except Exception as ex:
            raise Exception("Wrong format of message try to use this format: {name channel}, yyyy-mm-dd hh:mm, yyyy-mm-dd hh:mm, {file format}}.")
        return cls(channel_name, date_start, date_end, output_type, id_google_sheet, min_attendance_minutes)


class ReportEntry:
    date_start: datetime | None
    date_end: datetime | None
    user_id: int
    user_name: str

    def __init__(self, user_id):
        self.user_id = user_id
        self.date_start = None
        self.date_end = None

    def elapsed_time_withBorders(self, dateStartMessage, dateEndMessage) -> timedelta:    
        if self.date_start is not None and self.date_end is not None:
            return self.date_end - self.date_start
        elif self.date_start is not None and self.date_end is None:
            return dateEndMessage - self.date_start
        elif self.date_start is None and self.date_end is not None:
            return self.date_end - dateStartMessage       
        else:
            return timedelta(0)
    
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


    # for result query google sheet - set unique:
    # renderDict is changing
    def setUniqueFromRenderInDict(self, username: str, query: LogQuery, renderDict: dict):
       if username in renderDict:
            renderDict[username]+=self.elapsed_time_withBorders(query.date_start, query.date_end)
       else:
            renderDict[username]=self.elapsed_time_withBorders(query.date_start, query.date_end)

    @staticmethod
    def strfdelta(tdelta, fmt):
        d = {'days': tdelta.days}
        d['hours'], rem = divmod(tdelta.seconds, 3600)
        d['minutes'], d['seconds'] = divmod(rem, 60)
        return fmt.format(**d)

# clear all names in dict, which don't have need Time and compare to array of names
def compareToArrayRenderDictByMinTimeDelta(renderDict:dict):
    renderArray=[]
    totalInfo=[]
    for username in renderDict:
        if renderDict[username]>=Min_Time_Delta:
            renderArray.append(username)
        else:
            totalInfo.append("Person with nick '" +str(username) + "' was not enough time in lectures: " + \
                ReportEntry.strfdelta(renderDict[username], '{hours:02}:{minutes:02}:{seconds:02}'))
    return totalInfo, renderArray
            
#def sendHelp(message: discord.Message)
#    try:
#        with open(nameFile, encoding='utf-8') as file:
#            nicks = [row.strip() for row in file]


if __name__ == '__main__':
    intents = discord.Intents.default()
    intents.members = True
    client = LogClient(intents=intents)
    client.run(BOT_TOKEN)
