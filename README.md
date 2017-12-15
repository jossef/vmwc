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

### Examples / Demos

See [examples](examples) directory
 
### History
When I searched for a library to write automation scripts to control my esxi environment, I bumped into [pyvmomi](http://github.com/vmware/pyvmomi). My first impression was "It's too low-level and the general Development Experience doesn't feel easy to use". Therefore, on me break time, I wrote `vmwc` on the base of [pyvmomi](http://github.com/vmware/pyvmomi) to provide a lighter, TL;DR feeling and straight-forward API.

### Remarks
vmwc was developed to control a single esxi machine at a time. However, it should work with vcenter instances as well

### Uploading a new version

```
python setup.py bdist_wheel
twine upload dist/*
```
