#!/usr/bin/env python

from vmwc import VMWareClient
import datetime


def main():
    host = '192.168.1.1'
    username = '<username>'
    password = '<password>'

    with VMWareClient(host, username, password) as client:
        new_value = datetime.datetime(2025, 11, 22, 22, 0, 0)
        client.set_server_datetime(new_value)


if __name__ == '__main__':
    main()
