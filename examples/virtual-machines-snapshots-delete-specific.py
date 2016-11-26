#!/usr/bin/env python

from vmwc import VMWareClient


def main():
    host = '192.168.1.1'
    username = '<username>'
    password = '<password>'

    snapshot_name = 'MY-AWESOME-SNAPSHOT'
    
    print 'WARNING - you must acknowledge that by executing the code below will result in deletion of all snapshots. (remove the "return" statement and re run this script to proceed)'
    return

    with VMWareClient(host, username, password) as client:
        for vm in client.get_virtual_machines():
            for snapshot in vm.get_snapshots():
                if snapshot.name == snapshot_name:
                    snapshot.delete()


if __name__ == '__main__':
    main()
