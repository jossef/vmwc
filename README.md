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
