from __future__ import annotations

import sys

import pandas as pd
from bs4 import BeautifulSoup


def csvcheck(filename: str) -> bool:
    if filename.rpartition('.')[2] != 'csv':
        return False
    return True


def convert_to_xlsx(filepath: str) -> str:
    with open(filepath) as xml_file:
        filename = 'conditioned_skyward.xlsx'
        soup = BeautifulSoup(xml_file.read(), 'xml')
        writer = pd.ExcelWriter(filename)
        for sheet in soup.findAll('Worksheet'):
            sheet_as_list = []
            for row in sheet.findAll('Row'):
                sheet_as_list.append(
                    [cell.Data.text if cell.Data
                        else '' for cell in row.findAll('Cell')])
            pd.DataFrame(sheet_as_list).to_excel(
                writer, sheet_name=sheet.attrs['ss:Name'],
                index=False, header=False)

        writer.save()
        return filename


if __name__ == '__main__':
    if len(sys.argv) != 4:
        raise ValueError(
            'application requires 2 filepaths for input,' +
            'Prime CSV path followed by Intune CSV path.')

    paths = (sys.argv[1].strip(), sys.argv[2].strip(), sys.argv[3].strip())

    if not csvcheck(paths[0]) or not csvcheck(paths[1]):
        raise ValueError('One of the files is not a csv')

    # import CSVs from input paramaters as dataframes
    # prime data has header information that can be ignored,
    # start import at row index 8
    primeData = pd.read_csv(paths[0], header=8)
    intuneData = pd.read_csv(paths[1])

    # workaround for bad output data from skyward
    skywardData = pd.read_excel(convert_to_xlsx(paths[2]))

    columnFilter = ['Vendor', 'IP Address', 'AP Name',
                    '802.11 State', 'SSID', 'Profile', 'Protocol',
                    'AP Map Location', 'OS']

    # print paths for debug
    print(f'Prime(wireless): {paths[0]}')
    print(f'Endpoint(Intune): {paths[1]}')

    # filter out colons from MAC addresses in prime data
    print('Filter out semicolons for merge...')
    primeData['MAC Address'] = primeData['MAC Address'].str.replace(
        ':', '').str.upper()
    print('Rename "Last Association Time" column to "Last Seen"...')
    # rename last association time due to lengthy name
    primeData = primeData.rename(
        columns={'Last Association Time': 'Last Seen'})
    primeData['Last Seen'] = primeData['Last Seen'].str.replace(
        'EDT', '')

    print('Rename "Wi-Fi MAC" column to "MAC Address"...')
    # rename intuneData MAC Address column to match for merge
    intuneData = intuneData.rename(columns={'Wi-Fi MAC': 'MAC Address'})

    print('Inner join on MAC Address...')
    # merge dataframes on MAC Address
    mergedData = pd.merge(primeData, intuneData,
                          on='MAC Address').drop(columns=columnFilter)

    mergedData = mergedData.sort_values('Last check-in')
    mergedData['Last Seen'] = pd.to_datetime(
        mergedData['Last Seen'])
    mergedData['Last check-in'] = pd.to_datetime(mergedData['Last check-in'])

    print(skywardData)