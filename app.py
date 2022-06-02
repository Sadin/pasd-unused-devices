from __future__ import annotations

import sys


def csvcheck(filename: str) -> bool:
    if filename.rpartition('.')[2] != 'csv':
        return False
    return True


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise ValueError(
            'application requires 2 filepaths for input,' +
            'Prime CSV path followed by Intune CSV path.')

    paths = (sys.argv[1].strip(), sys.argv[2].strip())

    if not csvcheck(paths[0]) or not csvcheck(paths[1]):
        raise ValueError('One of the files is not a csv')

    # print paths for debug
    print(f'Prime(wireless): {paths[0]}')
    print(f'Endpoint(Intune): {paths[1]}')
