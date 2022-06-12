import googleSheetSettings

import re

import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

class GoogleSheet:
    # If modifying these scopes, delete the file token.pickle.
    # We need write access to the spreadsheet: https://developers.google.com/sheets/api/guides/authorizing
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    # row, where start name attendance
    row_start_name_attendance=0

    # row, where start date
    row_start_date_attendance=1

    # col where start FIOs
    col_start_FIOs=1

    # row where start FIOs
    row_start_FIOs=2

    spreadsheet = None

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
                    googleSheetSettings.google_credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(googleSheetSettings.google_token_pickle, 'wb') as token:
                pickle.dump(creds, token)

        service = build('sheets', 'v4', credentials=creds, cache_discovery=False)

        # Call the Sheets API
        self.spreadsheet = service.spreadsheets()


    def get_sheet_names(self):
        """
        Get all sheet names that are present on the spreadsheet
        
        :param spreadsheet: a service.spreadsheets() instance
        :returns: list with sheet names
        """
        sheets = []
        result = self.spreadsheet.get(spreadsheetId=googleSheetSettings.google_spreadsheet_id).execute()
        for s in result['sheets']:
            sheets.append(s.get('properties', {}).get('title'))
        return sheets


    def get_multiple_sheets_data(self, sheets, dimension='COLUMNS'):
        """
        Get data from multiple sheets at once with a batchGet request
        
        :param spreadsheet: a service.spreadsheets() instance
        :param sheets: a list of sheet names for which the data is to be retrieved
        :param dimension: passed to spreadsheet.values().batchGet as a value of majorDimension param. Possible values are 'COLUMNS' or 'ROWS'
        :returns: dict with sheet name as key and data as value
        """
        data = {}
        request = self.spreadsheet.values().batchGet(spreadsheetId=googleSheetSettings.google_spreadsheet_id, ranges=sheets, majorDimension=dimension)
        response = request.execute()
        for i in range(0, len(response.get('valueRanges'))):
            data[sheets[i]] = response.get('valueRanges')[i].get('values')
        return data
      

      
    def find_dates_and_ranges_attandance(self, sheets, multiple_sheets_data):
        """
        Get range array of start and end position lectures for every sheet
        Get array of dates lectures for every sheet
        
        :param sheets: a list of sheet names for which the data is to be retrieved
        :param multiple_sheets_data: a list of data for every sheet in sheets
        """
        startAttandance=[]
        datesAttandance=[]
        for indexSheet in range(len(sheets)):

            datesAttandance.append([])
            sheetData=multiple_sheets_data[sheets[indexSheet]]
            
            # flag of Attandance
            isAttandance=False
            for indexCol in range(len(sheetData)):
                # if not enough rows
                if (len(sheetData[indexCol])-1<self.row_start_date_attendance):
                    continue
                    
                if (isAttandance):
                    if (re.search(r'^[0-3][0-9]\.[0-1][0-9]$', sheetData[indexCol][self.row_start_date_attendance])!=None): 
                        # set exist date
                        print(sheetData[indexCol][self.row_start_date_attendance])
                        datesAttandance[indexSheet].append(sheetData[indexCol][self.row_start_date_attendance])
                    else:
                        break 
                # if wind key-word - is start of attendance
                elif (sheetData[indexCol][self.row_start_name_attendance]==googleSheetSettings.name_of_attendance):
                    startAttandance.append(indexCol)
                    isAttandance=True
                    # set exist date
                    datesAttandance[indexSheet].append(sheetData[indexCol][self.row_start_date_attendance])             
        return (startAttandance, datesAttandance)
    
        

googleTable = GoogleSheet()

sheets=googleTable.get_sheet_names()
print(sheets)


result = googleTable.get_multiple_sheets_data(sheets)
print(result[sheets[0]])

startAttandance, datesAttandance = googleTable.find_dates_and_ranges_attandance(sheets, result)
print(startAttandance)
print(datesAttandance)