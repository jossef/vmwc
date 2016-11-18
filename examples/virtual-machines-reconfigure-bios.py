#!/usr/bin/env python

from vmc import VMWareClient


def main():
    host = '192.168.1.1'
    username = '<username>'
    password = '<password>'

    with VMWareClient(host, username, password) as client:
        for vm in client.get_virtual_machines():
            vm.power_off()

            # Good configuration for PXE boot from lan (you'd like that the network will prioritize pre-disk, the boot delay)
            vm.configure_bios(boot_delay=5000, boot_order=['network', 'disk'])


if __name__ == '__main__':
    main()
