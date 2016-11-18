#!/usr/bin/env python

from vmc import VMWareClient


def main():
    host = '192.168.1.1'
    username = '<username>'
    password = '<password>'

    with VMWareClient(host, username, password) as client:
        for vm in client.get_virtual_machines():
            print 'powering on "{}" ...'.format(vm.name)
            vm.power_on()


if __name__ == '__main__':
    main()
