#!/usr/bin/env python

from vmc import VMWareClient


def main():
    host = '192.168.1.1'
    username = '<username>'
    password = '<password>'

    print 'WARNING - you must acknowledge that by executing the code below will result in deletion of all switches. (remove the "return" statement and re run this script to proceed)'
    return

    with VMWareClient(host, username, password) as client:
        for vs in client.get_virtual_switches():
            vs.delete()


if __name__ == '__main__':
    main()
