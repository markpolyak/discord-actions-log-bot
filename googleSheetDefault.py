import googleSheetSettings

import re
import math

import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

class GoogleSheet:
    # If modifying these scopes, delete the file token.pickle.
    # We need write access to the __spreadsheet: https://developers.google.com/sheets/api/guides/authorizing
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    # row, where start name atendance
    _row_start_name_atendance=0

    # row, where start date
    _row_start_date_atendance=1

    # col where start FIOs
    _col_start_FIOs=1

    # row where start FIOs
    _row_start_FIOs=2

    # rows begin in google Sheet with 1, not 0
    _shift_rows=1

    # length English Words 26-1
    _len_English_Sub=26
  
    # our Sheets
    __spreadsheet = None
    

    def __init__(self):
        """
        Performs authentication and creates a service.spreadsheets() instance
        
        :returns: service.spreadsheets() instance
        """
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(googleSheetSettings.google_token_pickle):
            with open(googleSheetSettings.google_token_pickle, 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    googleSheetSettings.google_credentials_file, self.SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(googleSheetSettings.google_token_pickle, 'wb') as token:
                pickle.dump(creds, token)

        service = build('sheets', 'v4', credentials=creds, cache_discovery=False)

        # Call the Sheets API
        self.__spreadsheet = service.spreadsheets()


    def _get_sheet_names(self):
        """
        Get all sheet names that are present on the spreadsheet
        
        :param __spreadsheet: a service.__spreadsheets() instance
        :returns: list with sheet names
        """
        sheets = []
        result = self.__spreadsheet.get(spreadsheetId=googleSheetSettings.google_spreadsheet_id).execute()
        for s in result['sheets']:
            sheets.append(s.get('properties', {}).get('title'))
        return sheets


    def _get_multiple_sheets_data(self, sheets, dimension='COLUMNS'):
        """
        Get data from multiple sheets at once with a batchGet request
        
        :param __spreadsheet: a service.__spreadsheets() instance
        :param sheets: a list of sheet names for which the data is to be retrieved
        :param dimension: passed to __spreadsheet.values().batchGet as a value of majorDimension param. Possible values are 'COLUMNS' or 'ROWS'
        :returns: dict with sheet name as key and data as value
        """
        data = {}
        request = self.__spreadsheet.values().batchGet(spreadsheetId=googleSheetSettings.google_spreadsheet_id, ranges=sheets, majorDimension=dimension)
        response = request.execute()
        for i in range(0, len(response.get('valueRanges'))):
            data[sheets[i]] = response.get('valueRanges')[i].get('values')
        return data
      

      
    def _find_dates_and_ranges_atendance(self, sheets, multiple_sheets_data):
        """
        Get range array of start and end position lectures for every sheet
        Get array of dates lectures for every sheet
        
        :param sheets: a list of sheet names for which the data is to be retrieved
        :param multiple_sheets_data: a list of data for every sheet in sheets
        :returns:   startatendance - array of horizontal position, where dates start
                    datesatendance - array of arrays of all dates in every sheet
        
        """
        startatendance=[]
        datesatendance=[]
        for indexSheet in range(len(sheets)):

            datesatendance.append([])
            sheetData=multiple_sheets_data[sheets[indexSheet]]
            
            # flag of atendance
            isatendance=False
            for indexCol in range(len(sheetData)):
                # if not enough rows
                if (len(sheetData[indexCol])-1<self._row_start_date_atendance):
                    continue
                    
                if (isatendance):
                    if (re.search(r'^[0-3][0-9]\.[0-1][0-9]$', sheetData[indexCol][self._row_start_date_atendance])!=None): 
                        # set exist date
                        datesatendance[indexSheet].append(sheetData[indexCol][self._row_start_date_atendance])
                    else:
                        break 
                # if wind key-word - is start of atendance
                elif (sheetData[indexCol][self._row_start_name_atendance]==googleSheetSettings.name_of_atendance):
                    startatendance.append(indexCol)
                    isatendance=True
                    # set exist date
                    datesatendance[indexSheet].append(sheetData[indexCol][self._row_start_date_atendance])             
        return (startatendance, datesatendance)
    
    def _find_FIOs(self, sheets, multiple_sheets_data):
        """
        Parse multiple_sheets_data and get array of FIO students for every sheet
        
        :param sheets: a list of sheet names for which the data is to be retrieved
        :param multiple_sheets_data: a list of data for every sheet in sheets
        :returns: array of FIO for every sheet
        """
 
        sheetsFIOs=[]
        for indexSheet in range(len(sheets)):
            sheetData=multiple_sheets_data[sheets[indexSheet]]
            FIOs=sheetData[self._col_start_FIOs]
            
            # delete upper rows
            if (len(FIOs)>self._row_start_FIOs):
                del FIOs[0 : self._row_start_FIOs]
            sheetsFIOs.append(FIOs)
        return sheetsFIOs   
    
    def _get_col_date(self, date, dates, startDate):
        """
        Get col date position in googleSheet
        
        !Attention date format dd.mm
        
        :param date: the date of lecture
        :param dates: all dates, which we have for current sheet
        :param startDate: index col, where start the dates    
        :returns: in dates horizontal position of date
        """
        
        try:
            return dates.index(date)+startDate
        except:
            return -1

    
    def _get_all_col_dates(self, date, dates, startDates, sheets):
        """
        Get col date position in googleSheet for all sheets
        
        :param date: the date of lecture
        :param dates: all dates, which we have for current sheet
        :param startDate: index col, where start the dates    
        :param sheets: a list of sheet names for which the data is to be retrieved
        :returns: in dates horizontal position of all dates
        """

        colPositionDates = []
        
        for indexSheet in range(len(sheets)):
            colDate=self._get_col_date(date, dates[indexSheet], startDates[indexSheet])
                        # if date not exist for group

            colPositionDates.append(colDate)
        return colPositionDates

    def _get_atendances(self, colPositionDates, sheets, multiple_sheets_data):
        """
        Get array of atendance for All date and sheet
        
        :param colPositionDates: col date position in googleSheet for all sheets
        :param sheets: a list of sheet names for which the data is to be retrieved
        :param multiple_sheets_data: a list of data for every sheet in sheets
        :returns: array of atendance for all sheets, which we have
        """
        
        atendances=[]
        for indexSheet in range(len(sheets)):
            # get sheet Data by name Sheet
            sheetData=multiple_sheets_data[sheets[indexSheet]]
            
            # get col with attandance Data
            atendanceSheet=sheetData[colPositionDates[indexSheet]]
            # delete upper rows, which dont have info about attandance
            for index in range(0, self._row_start_date_atendance+1):
                if (len(atendanceSheet)<=0):
                    break;
                del atendanceSheet[0]
            
            # delete not used info in bottom isn't necessary - check fucntion - _convert_atendances_to_standart  
                
            # save attandance without upper rows
            atendances.append(atendanceSheet)

        return atendances
        
    def _convert_atendances_to_standart(self, atendances, lenArray):
        """
        Convert atendances to similar size with equal by index element in lenArray
        
        :param atendances: non convert attandance for ALL sheets
        :param lenArray: FIO arrays for ALL sheets 
        :returns: array of attandance, converted to length of lenArray
        """
        convertAtendances=[]

        for indexSheet in range(len(lenArray)):        
            convertAtendanceSheet = [0]*lenArray[indexSheet]
            for index in range(len(atendances[indexSheet])):
                if (index>=lenArray[indexSheet]):
                    break
                # set value only for 1
                if (atendances[indexSheet][index]=='1'):
                    convertAtendanceSheet[index]=1
            
            convertAtendances.append(convertAtendanceSheet)   
        
        return convertAtendances
    
    def _dropInfoWthoutDate(self, infoArray, colPositionDates):
        """
        Delete all coloumns in infoArray where for current index not exist horizontal position of the date in colPositionDates
        
        :param infoArray: array of info, like arr of groups or array of arrays FIO or atendance
        :param colPositionDates: array of horizontal position of the date - if not exist, than have value -1
        :returns: array with remove cols from infoArray, which have by index in colPositionDates value -1
        """
        actualInfo=[]
        lenArray=len(infoArray)
        for indexSheet in range(len(colPositionDates)):
            if (colPositionDates[indexSheet]>=0):
                if (indexSheet<lenArray):
                    actualInfo.append(infoArray[indexSheet])
        return actualInfo
        
    def _getSizeOfArraysInArray(self, infoArray):
        """
        Find sizes for all arrays in infoArray
        
        !Attention: Not correct result if not array (if string, int...)
        
        :param infoArray: array of info, like arr of groups or array of arrays FIO or atendance
        :returns: array of sizes elements (arrays) in infoArray 
        """   
    
        lenArray=[]
        for array in infoArray:
            lenArray.append(len(array))
        return lenArray

    
    def getAllAtendanceInfoByDate(self, date):
        """
        Get all necessary info by googleSheetSettings, static params and date.
        
        !Attention: if we dont have any information, than returns: [] for all param
        
        :param date: non convert attandance for ALL sheets
        :param FIOs: FIO arrays for ALL sheets 
        :returns:   sheets - names of all sheets (equal groups)
                    FIOs - array of array FIO for every group
                    colPositionDates - array of horizontal position of the date and Atendances
                    atendances - array of array atendances for avery group              
        """
        
        # get all sheets
        # sheets are equal groups
        sheets=self._get_sheet_names()

        # get all info in every sheet
        result = self._get_multiple_sheets_data(sheets)
        
        # get start position of dates and atendance, and also dates
        startAtendance, datesAtendance = self._find_dates_and_ranges_atendance(sheets, result)
        
        # get horizontal position of date for attandance for all sheets
        colPositionDates = self._get_all_col_dates(date, datesAtendance, startAtendance, sheets)
        print(colPositionDates)
        # Convert to actual info
        sheets = self._dropInfoWthoutDate(sheets, colPositionDates)
        colPositionDates = self._dropInfoWthoutDate(colPositionDates, colPositionDates)  
        
        # get FIOs for every sheet
        FIOs = self._find_FIOs(sheets, result)

        lenArray = self._getSizeOfArraysInArray(FIOs)

        # get attandances for every sheet
        atendances = self._get_atendances(colPositionDates, sheets, result)
        
        # get convert atendances for every sheet        
        atendances = self._convert_atendances_to_standart(atendances, lenArray)
        
        return (sheets, FIOs, colPositionDates, atendances)



    # get standart print of range
    def getRange(self, nameList, startCol, startRow, endCol, endRow):
        return str(nameList)+'!'+str(startCol)+str(startRow)+':'+str(endCol)+str(endRow)
    
    
    def _getColNameFromColInt(self, col):
        row=''
        while (col>0):
            row=chr(ord('A')+int(col%self._len_English_Sub))+row
            col=math.floor(col/self._len_English_Sub)
        return row
      
       
    def _convertToSendAtendance(self, rowAtendanse):
        colAtendanse=[]
        for atendance in rowAtendanse:
            if (atendance==0):
                colAtendanse.append([''])   
            else:
                colAtendanse.append([atendance])                
        return colAtendanse
    
    
    def _updateAttendanseSheet(self, nameList, col, startRow, endRow, atendanse):
        print(col)
        atendanse=self._convertToSendAtendance(atendanse)
        col=self._getColNameFromColInt(col)
        print(atendanse)
        print(self.getRange(nameList, col, startRow, col, endRow))
        data = [{
            'range': self.getRange(nameList, col, startRow, col, endRow),
            'values': atendanse
        }]
        body = {
            'valueInputOption': 'RAW', # USER_ENTERED
            'data': data
        }
        result = self.__spreadsheet.values().batchUpdate(spreadsheetId=googleSheetSettings.google_spreadsheet_id, body=body).execute()
        print('{0} cells updated.'.format(result.get('totalUpdatedCells')))

        
       
    def setAllAtendancesSheet(self, sheets, colPositionDate, atendances):
        for index in range(len(sheets)):
            self._updateAttendanseSheet(sheets[index], 
                colPositionDate[index], 
                self._row_start_date_atendance+self._shift_rows+1, 
                self._row_start_date_atendance+self._shift_rows+len(atendances[index]), 
                atendances[index])
              
        

# Body Of some external Function
googleTable=None
try:
    googleTable = GoogleSheet()
except:
    print('Something wrong with the connection to GoogleSheet...')

groups=[]
FIOs=[]
startAtendances=[]
atendances=[]

#try:
groups, FIOs, startAtendances, atendances =  googleTable.getAllAtendanceInfoByDate('09.04')
#except Exception:
#    print('Something wrong with the connection to GoogleSheet or some mistake...')
    
print(groups)
print(FIOs)
print(startAtendances)
print(atendances)

googleTable.setAllAtendancesSheet(groups, startAtendances, atendances)