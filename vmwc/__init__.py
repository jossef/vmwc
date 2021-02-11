import logging
import random
import requests
import time
import datetime
import sys

# ----------------------------------
# Patch the urlib3 annoying warnings
# this is done because the ESXi server has a self-signed certificate in most cases

requests.packages.urllib3.disable_warnings()
import ssl

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass

# ----------------------------------
# Try import pyvmomi
try:
    import pyVmomi
    import pyVim
    from pyVim import connect
    from pyVmomi import vim, vmodl

except Exception as e:
    print ('failed to import pyVmomi.', e)
    sys.exit(1)


# ----------------------------------


class VMWareClient(object):
    def __init__(self, host, username, password, port=443, verify=False):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.verify = verify

    def __enter__(self):

        ssl_context = None
        try:
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
            if not self.verify:
                ssl_context.verify_mode = ssl.CERT_NONE
        except:
            pass

        self._session = pyVim.connect.SmartConnect(host=self.host, user=self.username, pwd=self.password, port=self.port, sslContext=ssl_context)
        self._content = self._session.RetrieveContent()

        return self

    def __exit__(self, type, value, traceback):
        pyVim.connect.Disconnect(self._session)

    def get_virtual_machines(self):
        for virtual_machine in self._iterate_virtual_machines():
            yield VirtualMachine(self, virtual_machine)

    def revert_to_snapshot(self, vm_name, snapshot_name):

        virtual_machine = self.get_virtual_machine(vm_name)
        if not virtual_machine:
            raise Exception('virtual machine "{0}" does not exist'.format(vm_name))

        snapshot = virtual_machine.get_snapshot(snapshot_name)
        if not snapshot:
            raise Exception('virtual machine "{0}" does not have a snapshot named "{1}"'.format(vm_name, snapshot_name))

        snapshot.revert()

    def _iterate_virtual_machines(self):
        children = self._content.rootFolder.childEntity
        for child in children:
            if hasattr(child, 'vmFolder'):
                datacenter = child
            else:
                continue

            vm_folder = datacenter.vmFolder
            folder_entities = vm_folder.childEntity
            for virtual_machine in self._iterate_folder(folder_entities):
                yield virtual_machine

    def _is_folder(self, item):
        return hasattr(item, 'childEntity')

    def _is_virtual_machine(self, item):
        return hasattr(item, 'summary')

    def _iterate_folder(self, folder):
        for item in folder:

            if self._is_folder(item):
                for virtual_machine in self._iterate_folder(item.childEntity):
                    yield virtual_machine

            elif self._is_virtual_machine(item):
                yield item

            else:
                logging.warning('Unsupported item "{item}". skipping'.format(item=item))

    def wait(self, task):

        filter_spec = vmodl.query.PropertyCollector.FilterSpec()
        filter_spec.objectSet = [vmodl.query.PropertyCollector.ObjectSpec(obj=task)]
        filter_spec.propSet = [vmodl.query.PropertyCollector.PropertySpec(type=vim.Task, pathSet=[], all=True)]
        filter_instance = self._content.propertyCollector.CreateFilter(filter_spec, True)
        try:
            updates_version = None
            task_state = None

            while True:
                updates_info = self._content.propertyCollector.WaitForUpdates(updates_version)
                updates_version = updates_info.version

                for filter_set in updates_info.filterSet:
                    for object_set in filter_set.objectSet:
                        current_task = object_set.obj

                        for change in object_set.changeSet:
                            if change.name == 'info':
                                task_state = change.val.state
                            elif change.name == 'info.state':
                                task_state = change.val
                            else:
                                continue

                            # Check if this task is our given task
                            if str(current_task) != str(task):
                                # Probably another task... Sometimes there's noise, we'll ignore it and move to the next one
                                continue

                            if task_state == vim.TaskInfo.State.success:
                                return
                            elif task_state == vim.TaskInfo.State.error:
                                raise Exception(current_task.info.error)
                            else:
                                # Probably still in progress, ignore
                                pass

                time.sleep(0.1)

        finally:
            if filter_instance:
                filter_instance.Destroy()

    def get_datastores(self):

        # Search for all ESXi hosts
        objview = self._content.viewManager.CreateContainerView(self._content.rootFolder, [vim.HostSystem], True)
        esxi_hosts = objview.view
        objview.Destroy()

        for esxi_host in esxi_hosts:

            # All Filesystems on ESXi host
            storage_system = esxi_host.configManager.storageSystem
            host_file_sys_vol_mount_info = storage_system.fileSystemVolumeInfo.mountInfo

            for host_mount_info in host_file_sys_vol_mount_info:

                # Extract only VMFS volumes
                if host_mount_info.volume.type != "VMFS":
                    continue

                datastore = {
                    'name': host_mount_info.volume.name,
                    'disks': [item.diskName for item in host_mount_info.volume.extent],
                    'uuid': host_mount_info.volume.uuid,
                    'capacity': host_mount_info.volume.capacity,
                    'vmfs_version': host_mount_info.volume.version,
                    'local': host_mount_info.volume.local,
                    'ssd': host_mount_info.volume.ssd
                }

                yield datastore

    def set_server_datetime(self, new_value=None):

        if not new_value:
            new_value = datetime.datetime.now()

        esxi_host = self._get_single_esxi_host()
        date_time_manager = esxi_host.configManager.dateTimeSystem
        date_time_manager.UpdateDateTime(new_value)

    def get_server_datetime(self):
        esxi_host = self._get_single_esxi_host()
        date_time_manager = esxi_host.configManager.dateTimeSystem
        return date_time_manager.QueryDateTime()

    def get_licenses(self):

        licenses = self._content.licenseManager.licenses
        for item in licenses:

            if not item.licenseKey:
                continue

            yield item.licenseKey

    def delete_all_licenses(self):
        for license in self.get_licenses():
            self._content.licenseManager.RemoveLicense(license)

    def replace_license(self, license):
        self._content.licenseManager.UpdateLicense(license)

    def get_services(self):

        objview = self._content.viewManager.CreateContainerView(self._content.rootFolder, [vim.HostSystem], True)
        esxi_hosts = objview.view
        objview.Destroy()

        for esxi_host in esxi_hosts:

            service_system = esxi_host.configManager.serviceSystem
            services = service_system.serviceInfo.service

            for service in services:
                policy = {
                    'id': service.key,
                    'name': service.label,
                    'running': service.running,
                }

                yield policy

    def start_service(self, service_id):

        objview = self._content.viewManager.CreateContainerView(self._content.rootFolder, [vim.HostSystem], True)
        esxi_hosts = objview.view
        objview.Destroy()

        for esxi_host in esxi_hosts:
            service_system = esxi_host.configManager.serviceSystem
            service_system.StartService(service_id)

    def restart_service(self, service_id):

        objview = self._content.viewManager.CreateContainerView(self._content.rootFolder, [vim.HostSystem], True)
        esxi_hosts = objview.view
        objview.Destroy()

        for esxi_host in esxi_hosts:
            service_system = esxi_host.configManager.serviceSystem
            service_system.RestartService(service_id)

    def stop_service(self, service_id):

        objview = self._content.viewManager.CreateContainerView(self._content.rootFolder, [vim.HostSystem], True)
        esxi_hosts = objview.view
        objview.Destroy()

        for esxi_host in esxi_hosts:
            service_system = esxi_host.configManager.serviceSystem
            service_system.StopService(service_id)

    def enable_ssh(self):
        service_id = 'TSM-SSH'
        self.start_service(service_id)

    def disable_ssh(self):
        service_id = 'TSM-SSH'
        self.stop_service(service_id)

    def _get_single_esxi_host(self):
        objview = self._content.viewManager.CreateContainerView(self._content.rootFolder, [vim.HostSystem], True)
        esxi_hosts = objview.view
        objview.Destroy()

        for esxi_host in esxi_hosts:
            return esxi_host

    def get_physical_interfaces(self):

        esxi_host = self._get_single_esxi_host()
        for pnic in esxi_host.config.network.pnic:
            yield pnic.device

    def _iterate_virtual_switches(self):
        esxi_host = self._get_single_esxi_host()
        for vswitch in esxi_host.config.network.vswitch:
            yield vswitch

    def _get_datastore_reference(self, name):

        objview = self._content.viewManager.CreateContainerView(self._content.rootFolder, [vim.Datastore], True)
        datastore = None
        for item in objview.view:
            if item.name == name:
                datastore = item

        objview.Destroy()

        return datastore

    def new_virtual_machine(self, name, remove_existing=False, cpus=1, ram_mb=512, datastore_name=None, vm_version=8, operating_system_type='ubuntu64Guest', thin_provision=True, disk_size_gb=100, network_name='VM Network', mac_address=None):
        """
        :param name:
        :param cpus:
        :param ram_mb:
        :param datastore_name:
        :param vm_version:
        :param mac_address:
        :param operating_system_type: see full list here - https://www.vmware.com/support/developer/vc-sdk/visdk25pubs/ReferenceGuide/vim.vm.GuestOsDescriptor.GuestOsIdentifier.html
        :return:
        """

        existing_virtual_machine = next((x for x in self.get_virtual_machines() if x.name == name), None)

        if existing_virtual_machine:

            if remove_existing:
                existing_virtual_machine.delete()
            else:
                raise Exception('virtual machine "{0}" already exist'.format(existing_virtual_machine.name))

        datacenter = self._content.rootFolder.childEntity[0]

        if not datastore_name:
            datastore_name = self._get_first_datastore_name()

        # Workaround - It has an issue with '.' for some reason...
        vm_directory_name = name.replace('.', '-')

        datastore_path = '[{datastore_name}] {vm_directory_name}'.format(datastore_name=datastore_name, vm_directory_name=vm_directory_name)
        hosts = datacenter.hostFolder.childEntity
        resource_pool = hosts[0].resourcePool

        vmx_file = vim.vm.FileInfo(logDirectory=None,
                                   snapshotDirectory=None,
                                   suspendDirectory=None,
                                   vmPathName=datastore_path)

        config = vim.vm.ConfigSpec(name=name, memoryMB=ram_mb, numCPUs=cpus,
                                   files=vmx_file, guestId=operating_system_type,
                                   version='vmx-{:02}'.format(vm_version))

        # -----------------------------------
        # Hardware

        unit_number = 0

        scsi, scsi_controller_key = self._add_new_scsi_controller('SCSI-001')
        disk = self._add_new_hard_disk('DISK-001', disk_size_gb, unit_number=unit_number, controller_key=scsi_controller_key, thin_provision=thin_provision, datastore_path=datastore_path, vm_name=name)
        nic = self._add_new_network_interface(network_name, mac_address=mac_address)

        config.deviceChange = [scsi, disk, nic]

        task = datacenter.vmFolder.CreateVM_Task(config=config, pool=resource_pool)
        self.wait(task)
        # -----------------------------------

        # Retrieve Virtual Machine by name (it's unique on a single ESXi server)
        virtual_machine = next((x for x in self.get_virtual_machines() if x.name == name), None)
        return virtual_machine

    def _get_property(self, obj_type, name):
        container = self._content.viewManager.CreateContainerView(self._content.rootFolder, [obj_type], True)
        for item in container.view:
            if item.name == name:
                return item

        return None

    def _add_new_network_interface(self, network_name, adapter_type='vmxnet3', connect_on_power_on=True, connected=True, wake_on_lan_enabled=False, mac_address=None):
        key = random.randint(-4099, -4000)

        network_spec = vim.vm.device.VirtualDeviceSpec()
        network_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add

        if adapter_type == "vmxnet":
            network_spec.device = vim.vm.device.VirtualVmxnet()
        elif adapter_type == "vmxnet2":
            network_spec.device = vim.vm.device.VirtualVmxnet2()
        elif adapter_type == "vmxnet3":
            network_spec.device = vim.vm.device.VirtualVmxnet3()
        elif adapter_type == "e1000":
            network_spec.device = vim.vm.device.VirtualE1000()
        elif adapter_type == "e1000e":
            network_spec.device = vim.vm.device.VirtualE1000e()
        else:
            raise Exception('Unsupported network interface of type "{0}"'.format(adapter_type))

        network_spec.device.key = key
        network_spec.device.addressType = "generated"
        if mac_address:
            network_spec.device.addressType = "manual"
            network_spec.device.macAddress = mac_address
        network_spec.device.backing = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
        network_spec.device.backing.deviceName = network_name
        network_spec.device.backing.network = self._get_property(vim.Network, network_name)
        network_spec.device.wakeOnLanEnabled = wake_on_lan_enabled
        network_spec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
        network_spec.device.connectable.connected = connected
        network_spec.device.connectable.startConnected = connect_on_power_on

        return network_spec

    def _add_new_scsi_controller(self, scsi_controller_label, bus_number=0, bus_sharing=None, adapter_type='lsilogic_sas'):

        key = random.randint(-1050, -1000)

        scsi_spec = vim.vm.device.VirtualDeviceSpec()

        if adapter_type == "lsilogic":
            summary = "LSI Logic"
            scsi_spec.device = vim.vm.device.VirtualLsiLogicController()
        elif adapter_type == "lsilogic_sas":
            summary = "LSI Logic Sas"
            scsi_spec.device = vim.vm.device.VirtualLsiLogicSASController()
        elif adapter_type == "paravirtual":
            summary = "VMware paravirtual SCSI"
            scsi_spec.device = vim.vm.device.ParaVirtualSCSIController()
        else:
            # If type not specified or does not match, show error and return
            if not adapter_type:
                err_msg = "The type of '{0}' has not been specified".format(scsi_controller_label)
            else:
                err_msg = "Cannot create '{0}'. Invalid/unsupported type '{1}'".format(scsi_controller_label, adapter_type)
            raise Exception(err_msg)

        scsi_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add

        scsi_spec.device.key = key
        scsi_spec.device.busNumber = bus_number
        scsi_spec.device.deviceInfo = vim.Description()
        scsi_spec.device.deviceInfo.label = scsi_controller_label
        scsi_spec.device.deviceInfo.summary = summary

        if bus_sharing == "virtual":
            scsi_spec.device.sharedBus = vim.vm.device.VirtualSCSIController.Sharing.virtualSharing

        elif bus_sharing == "physical":
            scsi_spec.device.sharedBus = vim.vm.device.VirtualSCSIController.Sharing.physicalSharing

        else:
            scsi_spec.device.sharedBus = vim.vm.device.VirtualSCSIController.Sharing.noSharing

        return scsi_spec, key

    def _add_new_hard_disk(self, disk_label, size_gb, unit_number, controller_key=1000, thin_provision=True, datastore_path=None, vm_name=None):

        key = random.randint(-2099, -2000)

        size_kb = int(size_gb * 1024.0 * 1024.0)

        disk_spec = vim.vm.device.VirtualDeviceSpec()
        disk_spec.fileOperation = 'create'
        disk_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add

        disk_spec.device = vim.vm.device.VirtualDisk()
        disk_spec.device.key = key
        disk_spec.device.deviceInfo = vim.Description()
        disk_spec.device.deviceInfo.label = disk_label
        disk_spec.device.deviceInfo.summary = "{0} GB".format(size_gb)

        disk_spec.device.backing = vim.vm.device.VirtualDisk.FlatVer2BackingInfo()
        disk_spec.device.backing.thinProvisioned = thin_provision
        disk_spec.device.backing.diskMode = 'persistent'

        disk_spec.device.backing.fileName = '{datastore_path}/{disk_label}.vmdk'.format(datastore_path=datastore_path, disk_label=disk_label)

        disk_spec.device.controllerKey = controller_key
        disk_spec.device.unitNumber = unit_number
        disk_spec.device.capacityInKB = size_kb

        return disk_spec

    def get_virtual_switches(self):
        virtual_switches = self._iterate_virtual_switches()

        for virtual_switch in virtual_switches:
            yield VirtualSwitch(self, virtual_switch)

    def ensure_virtual_switch_exists(self, name):
        if not self.get_virtual_switch(name):
            self.new_virtual_switch(name)

    def get_virtual_switch(self, name):
        virtual_switch = next((x for x in self.get_virtual_switches() if x.name == name), None)
        return virtual_switch

    def get_virtual_machine(self, name):
        virtual_machine = next((x for x in self.get_virtual_machines() if x.name == name), None)
        return virtual_machine

    def new_virtual_switch(self, name, vlan_id=4095, num_ports=128, mtu=4096, allow_promiscuous=True, allow_mac_changes=True, allow_forged_transmits=True):

        # Ensure that a virtual switch does not exists
        existing_virtual_switch = self.get_virtual_switch(name)

        if existing_virtual_switch:
            raise Exception('virtual switch "{0}" already exist. id "{1}"'.format(existing_virtual_switch.name, existing_virtual_switch.id))

        vss_spec = vim.host.VirtualSwitch.Specification()

        vss_spec.numPorts = num_ports
        vss_spec.mtu = mtu

        esxi_host = self._get_single_esxi_host()

        virtual_switch_names = map(lambda x: x.id, self.get_virtual_switches())
        virtual_switch_name = next('vSwitch{0}'.format(i) for i in xrange(0, num_ports) if 'vSwitch{0}'.format(i) not in virtual_switch_names)

        esxi_host.configManager.networkSystem.AddVirtualSwitch(vswitchName=virtual_switch_name, spec=vss_spec)

        port_group_spec = vim.host.PortGroup.Specification()
        port_group_spec.name = name
        port_group_spec.vlanId = vlan_id
        port_group_spec.vswitchName = virtual_switch_name

        port_group_spec.policy = vim.host.NetworkPolicy()
        port_group_spec.policy.security = vim.host.NetworkPolicy.SecurityPolicy()
        port_group_spec.policy.security.allowPromiscuous = allow_promiscuous
        port_group_spec.policy.security.forgedTransmits = allow_forged_transmits
        port_group_spec.policy.security.macChanges = allow_mac_changes

        esxi_host.configManager.networkSystem.AddPortGroup(portgrp=port_group_spec)

        virtual_switch = next(x for x in self.get_virtual_switches() if x.name == name)
        virtual_switch.update(allow_promiscuous=allow_promiscuous, allow_mac_changes=allow_mac_changes, allow_forged_transmits=allow_forged_transmits)
        return virtual_switch

    def _get_first_datastore_name(self):
        datastore = next(self.get_datastores(), None)

        if not datastore:
            raise Exception('There are no datastores available')

        return datastore['name']

    def get_guest_operations_manager(self):
        return self._content.guestOperationsManager


class VirtualMachine(object):
    def __init__(self, esx_client, raw_virtual_machine):

        self._client = esx_client
        self._raw_virtual_machine = raw_virtual_machine
        self._tools_credentials = None
        self.name = raw_virtual_machine.name
        self.uuid = raw_virtual_machine.summary.config.uuid

    def get_snapshots(self):
        if not self._raw_virtual_machine.snapshot:
            return

        snapshots = self._raw_virtual_machine.snapshot.rootSnapshotList
        for snapshot in self._iterate_snapshots(snapshots):
            yield snapshot

    def _iterate_snapshots(self, snapshots):
        for snapshot in snapshots:
            yield Snapshot(self._client, snapshot)

        child_snapshots = map(lambda x: x.childSnapshotList, snapshots)
        for child_snapshot in child_snapshots:
            for snapshot in self._iterate_snapshots(child_snapshot):
                yield snapshot

    def _iterate_network_interfaces(self):
        for hardware_device in self._raw_virtual_machine.config.hardware.device:
            if isinstance(hardware_device, vim.vm.device.VirtualEthernetCard):
                yield hardware_device

    def _iterate_disks(self):
        for hardware_device in self._raw_virtual_machine.config.hardware.device:
            if isinstance(hardware_device, vim.vm.device.VirtualDisk):
                yield hardware_device

    def power_on(self, verify_state=True):

        if verify_state:
            self.refresh()
            if self.is_powered_on():
                return

        task = self._raw_virtual_machine.PowerOnVM_Task()
        self._client.wait(task)

    def rename(self, new_name):
        task = self._raw_virtual_machine.Rename_Task(new_name)
        self._client.wait(task)
        self.name = new_name

    def shutdown(self, verify_state=True):

        if verify_state:
            self.refresh()
            if self.is_powered_off():
                return

        self._raw_virtual_machine.ShutdownGuest()

    def power_off(self, verify_state=True):

        if verify_state:
            self.refresh()
            if self.is_powered_off():
                return

        task = self._raw_virtual_machine.PowerOffVM_Task()
        self._client.wait(task)

    def reboot(self):
        task = self._raw_virtual_machine.ResetVM_Task()
        self._client.wait(task)

    def remove_all_snapshots(self, consolidate=False):
        task = self._raw_virtual_machine.RemoveAllSnapshots_Task(consolidate)
        self._client.wait(task)

    def delete(self):
        task = self._raw_virtual_machine.Destroy_Task()
        self._client.wait(task)

    def take_snapshot(self, name, description="", memory=False, try_persist_disk=True):
        task = self._raw_virtual_machine.CreateSnapshot(name, description, memory, try_persist_disk)
        self._client.wait(task)

    def configure_bios(self, enter_bios=None, boot_delay=None, boot_order=None):
        spec = vim.vm.ConfigSpec()
        spec.bootOptions = vim.vm.BootOptions()

        if boot_order is not None:
            spec.bootOptions.bootOrder = []

            for device in boot_order:

                if device == 'network':
                    first_network_interface = next(self._iterate_network_interfaces(), None)
                    if not first_network_interface:
                        raise Exception('There is no network interface to boot from. you need to configure at least 1 network interface first')

                    boot_device = vim.vm.BootOptions.BootableEthernetDevice(deviceKey=first_network_interface.key)

                elif device == 'disk':
                    first_disk = next(self._iterate_disks(), None)
                    if not first_disk:
                        raise Exception('There is no disks to boot from. you need to configure at least 1 disk first')

                    boot_device = vim.vm.BootOptions.BootableDiskDevice(deviceKey=first_disk.key)

                elif device == 'cdrom':
                    boot_device = vim.vm.BootOptions.BootableCdromDevice()

                else:
                    raise Exception('device "{}" is not supported'.format(device))

                spec.bootOptions.bootOrder.append(boot_device)

        if boot_delay is not None:
            spec.bootOptions.bootDelay = boot_delay

        if enter_bios is not None:
            spec.bootOptions.enterBIOSSetup = enter_bios

        task = self._raw_virtual_machine.ReconfigVM_Task(spec=spec)
        self._client.wait(task)

    def refresh(self):

        virtual_machine = next((x for x in self._client.get_virtual_machines() if x.uuid == self.uuid), None)
        if not virtual_machine:
            raise Exception('Virtual Machine "{}" is missing'.format(self.name))

        self.__dict__.update(virtual_machine.__dict__)

    def is_powered_on(self):
        return self._raw_virtual_machine.runtime.powerState == 'poweredOn'

    def is_powered_off(self):
        return self._raw_virtual_machine.runtime.powerState == 'poweredOff'

    def is_suspended(self):
        return self._raw_virtual_machine.runtime.powerState == 'suspended'

    def remove_all_network_interfaces(self):

        spec = vim.vm.ConfigSpec()
        spec.deviceChange = []

        for network_interface in self._iterate_network_interfaces():
            virtual_nic_spec = vim.vm.device.VirtualDeviceSpec()
            virtual_nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.remove
            virtual_nic_spec.device = network_interface

            spec.deviceChange.append(virtual_nic_spec)

        task = self._raw_virtual_machine.ReconfigVM_Task(spec=spec)
        self._client.wait(task)

    def add_network_interface(self, network_name, adapter_type='vmxnet3'):

        network_spec = self._client._add_new_network_interface(network_name, adapter_type)

        spec = vim.vm.ConfigSpec()
        spec.deviceChange = [network_spec]
        task = self._raw_virtual_machine.ReconfigVM_Task(spec=spec)
        self._client.wait(task)

    def get_network_interfaces(self):

        for network_interface in self._iterate_network_interfaces():
            yield {
                "mac_address": network_interface.macAddress,
                "label": network_interface.deviceInfo.label,
                "network": network_interface.deviceInfo.summary
            }

    def get_snapshot(self, name):
        snapshot = next((x for x in self.get_snapshots() if x.name == name), None)
        return snapshot

    def get_tools_status(self):
        return self._raw_virtual_machine.guest.toolsStatus

    def is_tools_working_properly(self):
        tools_status = self.get_tools_status()
        return (tools_status != "toolsNotInstalled" and
                tools_status != "toolsNotRunning")

    def vmware_tools_login(self, username, password):
        self._tools_credentials = vim.vm.guest.NamePasswordAuthentication(username=username,
                                                                          password=password)

    def vmware_tools_execute_process(self, program_path, working_directory, arguments="", environment_variables=None):
        self._ensure_vmware_tools_logged_in()

        spec = vim.vm.guest.ProcessManager.ProgramSpec(programPath=program_path,
                                                       arguments=arguments,
                                                       workingDirectory=working_directory,
                                                       envVariables=environment_variables)

        self._client.get_guest_operations_manager().processManager.StartProgramInGuest(vm=self._raw_virtual_machine,
                                                                                       auth=self._tools_credentials,
                                                                                       spec=spec)

    def _ensure_vmware_tools_logged_in(self):
        if self._tools_credentials is None:
            raise Exception("VMWare tools login is required in order to use this functionality")

    def vmware_tools_upload_file(self, local_file_path, remote_file_path):
        self._ensure_vmware_tools_logged_in()

        with open(local_file_path, "rb") as fin:
            data = fin.read()

        file_attributes = vim.vm.guest.FileManager.FileAttributes()
        url = self._client.get_guest_operations_manager().fileManager.InitiateFileTransferToGuest(vm=self._raw_virtual_machine,
                                                                                                  auth=self._tools_credentials,
                                                                                                  guestFilePath=remote_file_path,
                                                                                                  fileAttributes=file_attributes,
                                                                                                  fileSize=len(data),
                                                                                                  overwrite=True)

        url = self._normalize_url(url)
        r = requests.put(url, data=data, verify=False)
        r.raise_for_status()

    def _normalize_url(self, url):
        return url.replace("https://*", "https://" + self._client.host)

    def vmware_tools_download_file(self, local_file_path, remote_file_path, chunk_size=1024):
        self._ensure_vmware_tools_logged_in()

        fti = self._client.get_guest_operations_manager().fileManager.InitiateFileTransferFromGuest(vm=self._raw_virtual_machine,
                                                                                                    auth=self._tools_credentials,
                                                                                                    guestFilePath=remote_file_path)

        url = self._normalize_url(fti.url)
        r = requests.get(url, verify=self._client.verify)
        r.raise_for_status()

        size = 0
        with open(local_file_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    size += len(chunk)
        return size

    def vmware_tools_create_temporary_directory(self, prefix, suffix=""):
        self._ensure_vmware_tools_logged_in()

        temporary_directory = self._client.get_guest_operations_manager().fileManager.CreateTemporaryDirectoryInGuest(vm=self._raw_virtual_machine,
                                                                                                                      auth=self._tools_credentials,
                                                                                                                      prefix=prefix,
                                                                                                                      suffix=suffix)
        return temporary_directory

    def vmware_tools_list_processes(self, pids=None, max_retries=5, retry_delay_seconds=5):
        self._ensure_vmware_tools_logged_in()

        attempt = 0
        while True:
            try:
                response = self._client.get_guest_operations_manager().processManager.ListProcessesInGuest(vm=self._raw_virtual_machine,
                                                                                                           auth=self._tools_credentials,
                                                                                                           pids=pids)
                return response
            except:
                attempt += 1
                if attempt > max_retries:
                    raise
                time.sleep(retry_delay_seconds)


class VirtualSwitch(object):
    def __init__(self, esx_client, raw_virtual_switch):
        self._esx_client = esx_client
        self._raw_virtual_switch = raw_virtual_switch
        self.id = raw_virtual_switch.name
        self.name = self._parse_name(raw_virtual_switch)
        self.mtu = raw_virtual_switch.mtu
        self.key = raw_virtual_switch.key

    def delete(self):
        esxi_host = self._esx_client._get_single_esxi_host()
        esxi_host.configManager.networkSystem.RemoveVirtualSwitch(vswitchName=self.id)

    def update(self, allow_promiscuous=None, allow_mac_changes=None, allow_forged_transmits=None, mtu=None):
        dirty = False

        spec = self._raw_virtual_switch.spec
        if allow_promiscuous is not None:
            dirty = True
            spec.policy.security.allowPromiscuous = allow_promiscuous

        if allow_mac_changes is not None:
            dirty = True
            spec.policy.security.macChanges = allow_mac_changes

        if allow_forged_transmits is not None:
            dirty = True
            spec.policy.security.forgedTransmits = allow_forged_transmits

        if mtu is not None:
            dirty = True
            spec.mtu = mtu

        if dirty:
            esxi_host = self._esx_client._get_single_esxi_host()
            esxi_host.configManager.networkSystem.UpdateVirtualSwitch(vswitchName=self.id, spec=spec)

    @staticmethod
    def _parse_name(raw_virtual_switch):

        if not raw_virtual_switch.portgroup:
            return ''

        if not len(raw_virtual_switch.portgroup):
            return ''

        name = raw_virtual_switch.portgroup[0]
        name = name.split('-')[-1]
        return name


class Snapshot(object):
    def __init__(self, esx_client, raw_snapshot):
        self._esx_client = esx_client
        self._raw_snapshot = raw_snapshot
        self.id = raw_snapshot.id
        self.name = raw_snapshot.name
        self.description = raw_snapshot.description
        self.timestamp = raw_snapshot.createTime
        self.is_powered_on = raw_snapshot.state == 'poweredOn'

    def rename(self, name, description):
        task = self._raw_snapshot.snapshot.RenameSnapshot(name, description)
        self._esx_client.wait(task)

    def revert(self):
        task = self._raw_snapshot.snapshot.RevertToSnapshot_Task()
        self._esx_client.wait(task)

    def delete(self, remove_children=True):
        task = self._raw_snapshot.snapshot.RemoveSnapshot_Task(remove_children)
        self._esx_client.wait(task)
