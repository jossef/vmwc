#!/usr/bin/env python

from vmwc import VMWareClient


def main():
    host = '192.168.1.1'
    username = '<username>'
    password = '<password>'
    license = 'XXXXX-XXXXX-XXXXX-XXXXX-XXXXX'

    with VMWareClient(host, username, password) as client:
        client.replace_license(license)


if __name__ == '__main__':
    main()
