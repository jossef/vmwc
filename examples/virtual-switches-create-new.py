#!/usr/bin/env python

from vmc import VMWareClient


def main():
    host = '192.168.1.1'
    username = '<username>'
    password = '<password>'

    virtual_switch_name = 'Custom Network 1'

    with VMWareClient(host, username, password) as client:
        # Good configuration for traffic recording
        client.new_virtual_switch(virtual_switch_name, allow_promiscuous=True, allow_mac_changes=True, allow_forged_transmits=True)


if __name__ == '__main__':
    main()
