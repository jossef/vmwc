.. image:: https://user-images.githubusercontent.com/1287098/28493843-b889ce8e-6f26-11e7-97ec-cc180a760051.png


Simplified VMWare API client for Python
=======================================

vmwc is designed to be the simplest way possible to use VMWare's SDK




.. code-block:: python

    from vmwc import VMWareClient

    host = '192.168.1.1'
    username = '<username>'
    password = '<password>'

    with VMWareClient(host, username, password) as client:
        for vm in client.get_virtual_machines():
            vm.power_on()

Installation
^^^^^^^^^^^^

.. code-block:: python

    pip install vmwc

Examples
^^^^^^^^

- `set server datetime <https://github.com/jossef/vmwc/blob/master/examples/set-server-datetime.py>`_
- `replace license <https://github.com/jossef/vmwc/blob/master/examples/replace-license.py>`_
- `datastores list <https://github.com/jossef/vmwc/blob/master/examples/datastores-list.py>`_
- `virtual machines create new <https://github.com/jossef/vmwc/blob/master/examples/virtual-machines-create-new.py>`_
- `virtual machines delete <https://github.com/jossef/vmwc/blob/master/examples/virtual-machines-delete.py>`_
- `virtual machines list <https://github.com/jossef/vmwc/blob/master/examples/virtual-machines-list.py>`_
- `virtual machines power off <https://github.com/jossef/vmwc/blob/master/examples/virtual-machines-power-off.py>`_
- `virtual machines power on <https://github.com/jossef/vmwc/blob/master/examples/virtual-machines-power-on.py>`_
- `virtual machines shutdown <https://github.com/jossef/vmwc/blob/master/examples/virtual-machines-shutdown.py>`_
- `virtual machines reboot <https://github.com/jossef/vmwc/blob/master/examples/virtual-machines-reboot.py>`_
- `virtual machines reconfigure bios <https://github.com/jossef/vmwc/blob/master/examples/virtual-machines-reconfigure-bios.py>`_
- `virtual machines reconfigure network interfaces <https://github.com/jossef/vmwc/blob/master/examples/virtual-machines-reconfigure-network-interfaces.py>`_
- `virtual machines snapshots delete all <https://github.com/jossef/vmwc/blob/master/examples/virtual-machines-snapshots-delete-all.py>`_
- `virtual machines snapshots delete specific <https://github.com/jossef/vmwc/blob/master/examples/virtual-machines-snapshots-delete-specific.py>`_
- `virtual machines snapshots revert <https://github.com/jossef/vmwc/blob/master/examples/virtual-machines-snapshots-revert.py>`_
- `virtual machines snapshots list  <https://github.com/jossef/vmwc/blob/master/examples/virtual-machines-snapshots-list.py>`_
- `virtual machines snapshots new <https://github.com/jossef/vmwc/blob/master/examples/virtual-machines-snapshots-new.py>`_
- `virtual switches create new <https://github.com/jossef/vmwc/blob/master/examples/virtual-switches-create-new.py>`_
- `virtual switches delete <https://github.com/jossef/vmwc/blob/master/examples/virtual-switches-delete.py>`_
- `virtual switches list <https://github.com/jossef/vmwc/blob/master/examples/virtual-switches-list.py>`_




History
^^^^^^^

When I searched for a library to write automation scripts to control my esxi environment, I bumped into `pyvmomi <http://github.com/vmware/pyvmomi>`_
. My first impression was "It's too low-level and the general Development Experience doesn't feel easy to use". Therefore, on me break time, I wrote `vmwc` on the base of  `pyvmomi <http://github.com/vmware/pyvmomi>`_ to provide a lighter, TL;DR feeling and straight-forward API.

Remarks
^^^^^^^

vmwc was developed to control a single esxi machine at a time. However, it should work with vcenter instances as well

