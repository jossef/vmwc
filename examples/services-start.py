#!/usr/bin/env python

from vmwc import VMWareClient


def main():
    host = '192.168.1.1'
    username = '<username>'
    password = '<password>'

    service_id = 'TSM-SSH'

    with VMWareClient(host, username, password) as client:
        client.start_service(service_id)


if __name__ == '__main__':
    main()
