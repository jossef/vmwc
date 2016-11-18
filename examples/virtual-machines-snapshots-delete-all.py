#!/usr/bin/env python

from vmc import VMWareClient


def main():
    host = '192.168.1.1'
    username = '<username>'
    password = '<password>'

    print 'WARNING - you must acknowledge that by executing the code below will result in deletion of all snapshots. (remove the "return" statement and re run this script to proceed)'
    return

    with VMWareClient(host, username, password) as client:
        for vm in client.get_virtual_machines():
            print vm.name

            # VMWare gave a specific API to delete all machines. guess this is more efficient instead of iterating all snapshots and delete them 1 by 1
            vm.remove_all_snapshots()


if __name__ == '__main__':
    main()
