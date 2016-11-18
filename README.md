![banner-01](https://cloud.githubusercontent.com/assets/1287098/20438501/9abc0c50-adc0-11e6-845c-e4fef798a0d7.png)

## Simplified VMWare API client for Python

vmc is designed to be the simplest way possible to use VMWare's API


```python

from vmc import VMWareClient

host = '192.168.1.1'
username = '<username>'
password = '<password>'

with VMWareClient(host, username, password) as client:
    for vm in client.get_virtual_machines():
        vm.power_on()

```

### Installation

```
pip install vmc
```

### Examples


 - [datastores list](examples/datastores-list.py)
 - [virtual machines create new](examples/virtual-machines-create-new.py)
 - [virtual machines delete](examples/virtual-machines-delete.py)
 - [virtual machines list](examples/virtual-machines-list.py)
 - [virtual machines power off](examples/virtual-machines-power-off.py)
 - [virtual machines power on](examples/virtual-machines-power-on.py)
 - [virtual machines reboot](examples/virtual-machines-reboot.py)
 - [virtual machines reconfigure bios](examples/virtual-machines-reconfigure-bios.py)
 - [virtual machines reconfigure network interfaces](examples/virtual-machines-reconfigure-network-interfaces.py)
 - [virtual machines snapshots delete all](examples/virtual-machines-snapshots-delete-all.py)
 - [virtual machines snapshots delete specific](examples/virtual-machines-snapshots-delete-specific.py)
 - [virtual machines snapshots list ](examples/virtual-machines-snapshots-list.py)
 - [virtual machines snapshots new](examples/virtual-machines-snapshots-new.py)
 - [virtual switches create new](examples/virtual-switches-create-new.py)
 - [virtual switches delete](examples/virtual-switches-delete.py)
 - [virtual switches list](examples/virtual-switches-list.py)
