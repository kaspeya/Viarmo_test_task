import json
import logging

from google.oauth2.service_account import Credentials
from googleapiclient import discovery
from utils import InvalidResponseError, retries_on

GOOGLE_N_RETRIES = 4
GOOGLE_PAUSE_DURATION_SECONDS = 1


class GdriveClient(object):
    def __init__(self, service_account_creds_file, spreadsheet_id, list_name):
        self.auth_info = {}
        with open(service_account_creds_file, 'rb') as fh:
            self.auth_info = json.load(fh)

        logging.debug(f'Creds file {service_account_creds_file} has been read')

        self.gservice = discovery.build(
            'sheets', 'v4', credentials=Credentials.from_service_account_info(
                info=self.auth_info,
                scopes=[
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/drive'
                ]))

        self.spreadsheet_id = spreadsheet_id
        self.list_name = list_name

        logging.info(f'Gdrive client configured: \n\tspreadsheet id {self.spreadsheet_id}, \n\tlist name {self.list_name}')

    @retries_on(num=GOOGLE_N_RETRIES, sleep_time_seconds=GOOGLE_PAUSE_DURATION_SECONDS)
    def get_current_table(self):

        logging.debug(f'Getting current table from google service, '
                      f'spreadsheet id {self.spreadsheet_id}, list name {self.list_name}')
        raw_response = self.gservice.spreadsheets().values().get(spreadsheetId=self.spreadsheet_id,
                                                                 range=f'{self.list_name}').execute()

        table_current = raw_response.get('values')

        if len(table_current) < 2:
            raise InvalidResponseError('Gdrive client has not found table or data in table to proceed')

        logging.info(f'Got current table response, n_rows = {len(table_current)}')
        return table_current

    @retries_on(num=GOOGLE_N_RETRIES, sleep_time_seconds=GOOGLE_PAUSE_DURATION_SECONDS)
    def push_updated_table(self, table_updated):
        logging.info(
            f'Getting to push table to google service, n_rows = {len(table_updated)}')

        body = {
            'valueInputOption': 'USER_ENTERED',  # RAW USER_ENTERED INPUT_VALUE_OPTION_UNSPECIFIED
            'data': [{
                'range': f'{self.list_name}',
                'values': table_updated,
                'majorDimension': 'ROWS',
            }],
            'includeValuesInResponse': False,
        }

        update_response = self.gservice.spreadsheets().values().batchUpdate(spreadsheetId=self.spreadsheet_id,
                                                                            body=body).execute()

        if 'totalUpdatedSheets' not in update_response or int(update_response['totalUpdatedSheets']) < 1:
            raise InvalidResponseError('Gdrive client failed to push merged table')

        return update_response
