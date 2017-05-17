# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

# from kuryr.lib import constants
# from kuryr.lib import utils
from kuryr_kubernetes.cni.binding import base as b_base
from kuryr_kubernetes import config


class VlanDriver(object):
    def connect(self, vif, ifname, netns):
        h_ipdb = b_base.get_ipdb()
        c_ipdb = b_base.get_ipdb(netns)

        # NOTE(vikasc): Ideally 'ifname' should be used here but instead a
        # temporary name is being used while creating the device for container
        # in host network namespace. This is because cni expects only 'eth0'
        # as interface name and if host already has an interface named 'eth0',
        # device creation will fail with 'already exists' error.
        temp_name = vif.vif_name

        # TODO(vikasc): evaluate whether we should have stevedore
        #               driver for getting the link device.
        vm_iface_name = config.CONF.binding.link_iface
        vlan_id = vif.vlan_id

        with h_ipdb.create(ifname=temp_name,
                           link=h_ipdb.interfaces[vm_iface_name],
                           kind='vlan', vlan_id=vlan_id) as iface:
            iface.net_ns_fd = netns

        with c_ipdb.interfaces[temp_name] as iface:
            iface.ifname = ifname
            iface.mtu = vif.network.mtu
            iface.address = str(vif.address)
            iface.up()

    def disconnect(self, vif, ifname, netns):
        # NOTE(vikasc): device will get deleted with container namespace, so
        # nothing to be done here.
        pass
