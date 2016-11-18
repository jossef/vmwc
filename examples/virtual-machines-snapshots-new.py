#!/usr/bin/env python

from vmc import VMWareClient


def main():
    host = '192.168.1.1'
    username = '<username>'
    password = '<password>'

    snapshot_name = 'MY-AWESOME-SNAPSHOT'

    with VMWareClient(host, username, password) as client:
        for vm in client.get_virtual_machines():
            print 'taking a snapshot for "{}" named "{}" ...'.format(vm.name, snapshot_name)
            vm.take_snapshot(snapshot_name, memory=False)


if __name__ == '__main__':
    main()
