#!/usr/bin/env python

from vmwc import VMWareClient


def main():
    host = '192.168.1.1'
    username = '<username>'
    password = '<password>'

    remote_file_path = 'C:\\file.txt'
    download_path = '/tmp/downloaded_file.txt'

    with VMWareClient(host, username, password) as client:
        for vm in client.get_virtual_machines():
            print 'downloading "{}" from {}...'.format(remote_file_path, vm.name)
            try:
                size = vm.download_file(remote_file_path, download_path)
                print 'successfully downloaded {} bytes'.format(size)
            except Exception as e:
                'Failed to download file: {}'.format(e)

if __name__ == '__main__':
    main()
