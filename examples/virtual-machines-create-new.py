#!/usr/bin/env python

from vmc import VMWareClient


def main():
    host = '192.168.1.1'
    username = '<username>'
    password = '<password>'

    with VMWareClient(host, username, password) as client:
        vm = client.new_virtual_machine("Virtual Machine 1", cpus=2, ram_mb=1024, disk_size_gb=20)
        vm.configure_bios(boot_delay=5000, boot_order=['network', 'disk'])
        vm.power_on()


if __name__ == '__main__':
    main()
