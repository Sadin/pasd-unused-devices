from __future__ import annotations

import sys
from datetime import date

import pandas as pd
from bs4 import BeautifulSoup


def csvcheck(filename: str) -> bool:
    if filename.rpartition('.')[2] != 'csv':
        return False
    return True


def convert_to_xlsx(filepath: str) -> str:
    with open(filepath) as xml_file:
        print('Skyward data incorrect format, parsing to xlsx...')
        filename = 'conditioned_skyward.xlsx'
        soup = BeautifulSoup(xml_file.read(), 'xml')
        writer = pd.ExcelWriter(filename)
        for sheet in soup.findAll('Worksheet'):
            print('Sheet found...')
            sheet_as_list = []
            for row in sheet.findAll('Row'):
                sheet_as_list.append(
                    [cell.Data.text if cell.Data
                        else '' for cell in row.findAll('Cell')])
            print(str(len(sheet_as_list)) + ' rows processed...')
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

    primeFilter = ['Vendor', 'IP Address', 'AP Name',
                   '802.11 State', 'SSID', 'Profile', 'Protocol',
                   'AP Map Location']
    intuneFilter = ['Enrollment date', 'EAS activation ID',
                    'Azure AD Device ID', 'Manufacturer',
                    'EAS activated', 'IMEI', 'Last EAS sync time',
                    'EAS reason', 'EAS status',
                    'Compliance grace period expiration',
                    'Security patch level', 'MEID', 'Subscriber carrier',
                    'Total storage', 'Free storage', 'Management name',
                    'Category', 'UserId', 'Primary user UPN',
                    'Primary user email address', 'Primary user display name',
                    'Managed by', 'Ownership', 'Device state', 'Supervised',
                    'Encrypted', 'OS', 'SkuFamily', 'CellularTechnology',
                    'ProcessorArchitecture', 'EID', 'TPMManufacturerId',
                    'TPMManufacturerVersion', 'Phone number',
                    'ICCID', 'JoinType']
    skywardFilter = ['HR #']

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

    print('Exclude columns from primeData using user-defined filter ...')
    primeData.drop(columns=primeFilter, inplace=True)
    print(primeData.columns)

    print('Exclude columns from intuneData using user-defined filter ...')
    intuneData.drop(columns=intuneFilter, inplace=True)
    print(intuneData.columns)

    print('Exclude columns from skywardData using user-defined filter ...')
    skywardData.drop(columns=skywardFilter, inplace=True)
    print(skywardData.columns)

    print('Inner join on MAC Address...')
    # merge dataframes on MAC Address
    activeComputers = pd.merge(primeData, intuneData,
                               on='MAC Address')

    activeComputers = activeComputers.sort_values('Last check-in')
    activeComputers['Last Seen'] = pd.to_datetime(
        activeComputers['Last Seen'])
    activeComputers['Last check-in'] = pd.to_datetime(
        activeComputers['Last check-in'])

    # rename skyward column for merge
    skywardData = skywardData.rename(
        columns={'Serial Number': 'Serial number'})

    print('Join skyward data to AD/Prime exports via service tag ...')
    mergedData = pd.merge(activeComputers, skywardData,
                          on='Serial number', how='left')

    print('Exporting result...')
    # export data
    mergedData.to_excel(
        f'export_{date.today().strftime("%b-%d-%Y")}.xlsx', index=False)
