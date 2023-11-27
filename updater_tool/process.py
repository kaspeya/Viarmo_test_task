import logging
import re
from typing import List

import pandas as pd
import toml
from gdrive_client import GdriveClient
from log import init_console_log, init_file_log
from yamarket_parser import YaMarketParser


def update_current_table(
        table_current: List[List[any]],
        link_field: str,
        reserved_fields: List[str],
        parsed_records: List[dict]
) -> List[List[any]]:
    """Merging old table with new data gathered from yandex market

    1. Right join old table and new data
    2. Merge the result with immutable, 'reserved' columns

    :param table_current: table extracted from google drive
    :param link_field: name of column contains links
    :param reserved_fields: names of immutable columns in extracted table
    :param parsed_records: data extracted from yandex market
    :return:
    """
    df_old = pd.DataFrame(table_current[1:], columns=[s.lower() for s in table_current[0]])
    df_actual = pd.DataFrame.from_records(parsed_records)

    columns_no_reserve = df_old.columns.to_list()

    for rf in reserved_fields:
        if rf.lower() in columns_no_reserve:
            columns_no_reserve.remove(rf.lower())

    common_fields = [ac for ac in columns_no_reserve if ac in df_actual.columns]

    df_reserved = df_old[[link_field.lower()] + [rf.lower() for rf in reserved_fields]]

    df_updated = df_old[columns_no_reserve] \
        .merge(df_actual, on=common_fields, how='right') \
        .merge(df_reserved, on=link_field.lower(), how='left') \
        .fillna('')

    return [[col.capitalize() for col in df_updated.columns]] + df_updated.values.tolist()


def process(
        spreadsheet_link: str,
        spreadsheet_list_name: str,
        link_field: str,
        reserved_fields: List[str],
        service_account_creds_file: str
) -> None:
    """
    Spreadsheet processing pipeline

    1. Get current table from Google Drive
    2. Get data from yandex market via Selenium
    3. Merge current table and updated data
    4. Save merged table to google drive

    :param spreadsheet_link: Link to google spreadsheet
    :param spreadsheet_list_name: Name of list in spreadsheet, where table is placed
    :param link_field: Name of column with links
    :param reserved_fields: List of fields in spreadsheet which would be not modified and saved after overall updating
    :param service_account_creds_file: Path to service account creds file (json format)
    :return: None
    """
    spreadsheet_id = re.findall(r'https:\/\/docs.google.com\/spreadsheets\/d\/([^\/]*)/', f'{spreadsheet_link}/')[0]

    logging.info(f'Start processing spreadsheet_id: {spreadsheet_id}')

    gdrive_client = GdriveClient(service_account_creds_file=service_account_creds_file,
                                 spreadsheet_id=spreadsheet_id,
                                 list_name=spreadsheet_list_name)

    yamarket_parser = YaMarketParser()
    yamarket_parser.prepare()

    table_current = gdrive_client.get_current_table()

    links_to_parse = [row[0] for row in table_current[1:]]

    parsed_records = []
    for link in links_to_parse:
        parsed_records.append(yamarket_parser.parse_yamarket_page(link, link_field))

    yamarket_parser.quit()

    table_updated = update_current_table(table_current, link_field, reserved_fields, parsed_records)

    update_table_response = gdrive_client.push_updated_table(table_updated)
    logging.info(f'Processing finished for spreadsheet_id: {spreadsheet_id}')
    return


if __name__ == '__main__':

    init_console_log(level='INFO')
    init_file_log(activity='updater', path='/logs/', level='DEBUG')

    config = toml.load('/config/config.toml')
    logging.info('Config file loaded')

    process(**config['google-spreadsheet'])
