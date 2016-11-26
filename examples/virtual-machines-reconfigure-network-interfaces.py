#!/usr/bin/env python

from vmwc import VMWareClient


def main():
    host = '192.168.1.1'
    username = '<username>'
    password = '<password>'

    with VMWareClient(host, username, password) as client:
        for vm in client.get_virtual_machines():
            vm.remove_all_network_interfaces()

            vm.add_network_interface('VM Network')  # first NIC, with default the virtual "VM Network" switch
            vm.add_network_interface('VM Network')  # second NIC similar to the prev one
            vm.add_network_interface('Custom Network 1')  # third NIC. this time uses different virtual switch


if __name__ == '__main__':
    main()
