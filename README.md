![banner-01](https://user-images.githubusercontent.com/1287098/28493843-b889ce8e-6f26-11e7-97ec-cc180a760051.png)

## Simpler VMWare SDK client for Python

vmwc is designed to be the simplest way possible to use VMWare's SDK


```python

from vmwc import VMWareClient

host = '192.168.1.1'
username = '<username>'
password = '<password>'

with VMWareClient(host, username, password) as client:
    for vm in client.get_virtual_machines():
        vm.power_on()

```

### Installation

```
pip install vmwc
```

### Examples


 - [datastores list](examples/datastores-list.py)
 - [virtual machines create new](examples/virtual-machines-create-new.py)
 - [virtual machines delete](examples/virtual-machines-delete.py)
 - [virtual machines list](examples/virtual-machines-list.py)
 - [virtual machines download file](examples/virtual-machines-download-file.py)
 - [virtual machines power off](examples/virtual-machines-power-off.py)
 - [virtual machines power on](examples/virtual-machines-power-on.py)
 - [virtual machines reboot](examples/virtual-machines-reboot.py)
 - [virtual machines reconfigure bios](examples/virtual-machines-reconfigure-bios.py)
 - [virtual machines reconfigure network interfaces](examples/virtual-machines-reconfigure-network-interfaces.py)
 - [virtual machines snapshots delete all](examples/virtual-machines-snapshots-delete-all.py)
 - [virtual machines snapshots delete specific](examples/virtual-machines-snapshots-delete-specific.py)
 - [virtual machines snapshots revert](examples/virtual-machines-snapshots-revert.py)
 - [virtual machines snapshots list ](examples/virtual-machines-snapshots-list.py)
 - [virtual machines snapshots new](examples/virtual-machines-snapshots-new.py)
 - [virtual switches create new](examples/virtual-switches-create-new.py)
 - [virtual switches delete](examples/virtual-switches-delete.py)
 - [virtual switches list](examples/virtual-switches-list.py)
 
 
### History
When I searched for a library to write automation scripts to control my esxi environment, I bumped into [pyvmomi](http://github.com/vmware/pyvmomi). My first impression was "It's too low-level and the general Development Experience doesn't feel easy to use". Therefore, on me break time, I wrote `vmwc` on the base of [pyvmomi](http://github.com/vmware/pyvmomi) to provide a lighter, TL;DR feeling and straight-forward API.

### Remarks
vmwc was developed to control a single esxi machine at a time. However, it should work with vcenter instances as well

