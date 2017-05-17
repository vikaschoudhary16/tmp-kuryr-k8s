# Copyright (c) 2016 Mirantis, Inc.
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

import mock

from kuryr.lib import constants as kl_const
from neutronclient.common import exceptions as n_exc

from kuryr_kubernetes.controller.drivers import generic_vif
from kuryr_kubernetes import exceptions as k_exc
from kuryr_kubernetes.tests import base as test_base
from kuryr_kubernetes.tests.unit import kuryr_fixtures as k_fix


class GenericPodVIFDriver(test_base.TestCase):

    @mock.patch('kuryr_kubernetes.os_vif_util.neutron_to_osvif_vif')
    def test_request_vif(self, m_to_vif):
        cls = generic_vif.GenericPodVIFDriver
        m_driver = mock.Mock(spec=cls)
        neutron = self.useFixture(k_fix.MockNeutronClient()).client

        pod = mock.sentinel.pod
        project_id = mock.sentinel.project_id
        subnets = mock.sentinel.subnets
        security_groups = mock.sentinel.security_groups
        port = mock.sentinel.port
        port_request = mock.sentinel.port_request
        vif = mock.sentinel.vif
        vif_plugin = mock.sentinel.vif_plugin

        m_to_vif.return_value = vif
        m_driver._get_port_request.return_value = port_request
        m_driver._get_vif_plugin.return_value = vif_plugin
        neutron.create_port.return_value = {'port': port}

        self.assertEqual(vif, cls.request_vif(m_driver, pod, project_id,
                                              subnets, security_groups))

        m_driver._get_port_request.assert_called_once_with(
            pod, project_id, subnets, security_groups)
        neutron.create_port.assert_called_once_with(port_request)
        m_driver._get_vif_plugin.assert_called_once_with(port)
        m_to_vif.assert_called_once_with(vif_plugin, port, subnets)

    def test_release_vif(self):
        cls = generic_vif.GenericPodVIFDriver
        m_driver = mock.Mock(spec=cls)
        neutron = self.useFixture(k_fix.MockNeutronClient()).client

        pod = mock.sentinel.pod
        vif = mock.Mock()

        cls.release_vif(m_driver, pod, vif)

        neutron.delete_port.assert_called_once_with(vif.id)

    def test_release_vif_not_found(self):
        cls = generic_vif.GenericPodVIFDriver
        m_driver = mock.Mock(spec=cls)
        neutron = self.useFixture(k_fix.MockNeutronClient()).client

        pod = mock.sentinel.pod
        vif = mock.Mock()
        neutron.delete_port.side_effect = n_exc.PortNotFoundClient

        cls.release_vif(m_driver, pod, vif)

        neutron.delete_port.assert_called_once_with(vif.id)

    def test_activate_vif(self):
        cls = generic_vif.GenericPodVIFDriver
        m_driver = mock.Mock(spec=cls)
        neutron = self.useFixture(k_fix.MockNeutronClient()).client

        pod = mock.sentinel.pod
        vif = mock.Mock()
        vif.active = False
        port = mock.MagicMock()

        port.__getitem__.return_value = kl_const.PORT_STATUS_ACTIVE
        neutron.show_port.return_value = {'port': port}

        cls.activate_vif(m_driver, pod, vif)

        neutron.show_port.assert_called_once_with(vif.id)
        self.assertTrue(vif.active)

    def test_activate_vif_active(self):
        cls = generic_vif.GenericPodVIFDriver
        m_driver = mock.Mock(spec=cls)
        neutron = self.useFixture(k_fix.MockNeutronClient()).client

        pod = mock.sentinel.pod
        vif = mock.Mock()
        vif.active = True

        cls.activate_vif(m_driver, pod, vif)

        neutron.show_port.assert_not_called()

    def test_activate_vif_not_ready(self):
        cls = generic_vif.GenericPodVIFDriver
        m_driver = mock.Mock(spec=cls)
        neutron = self.useFixture(k_fix.MockNeutronClient()).client

        pod = mock.sentinel.pod
        vif = mock.Mock()
        vif.active = False
        port = mock.MagicMock()

        port.__getitem__.return_value = kl_const.PORT_STATUS_DOWN
        neutron.show_port.return_value = {'port': port}

        self.assertRaises(k_exc.ResourceNotReady, cls.activate_vif,
                          m_driver, pod, vif)

    def _test_get_port_request(self, m_to_fips, security_groups):
        cls = generic_vif.GenericPodVIFDriver
        m_driver = mock.Mock(spec=cls)

        pod = mock.sentinel.pod
        project_id = mock.sentinel.project_id
        subnets = mock.sentinel.subnets
        port_name = mock.sentinel.port_name
        network_id = mock.sentinel.network_id
        fixed_ips = mock.sentinel.fixed_ips
        device_id = mock.sentinel.device_id
        host_id = mock.sentinel.host_id

        m_driver._get_port_name.return_value = port_name
        m_driver._get_network_id.return_value = network_id
        m_to_fips.return_value = fixed_ips
        m_driver._get_device_id.return_value = device_id
        m_driver._get_host_id.return_value = host_id

        expected = {'port': {'project_id': project_id,
                             'name': port_name,
                             'network_id': network_id,
                             'fixed_ips': fixed_ips,
                             'device_owner': kl_const.DEVICE_OWNER,
                             'device_id': device_id,
                             'admin_state_up': True,
                             'binding:host_id': host_id}}

        if security_groups:
            expected['port']['security_groups'] = security_groups

        ret = cls._get_port_request(m_driver, pod, project_id, subnets,
                                    security_groups)

        self.assertEqual(expected, ret)
        m_driver._get_port_name.assert_called_once_with(pod)
        m_driver._get_network_id.assert_called_once_with(subnets)
        m_to_fips.assert_called_once_with(subnets)
        m_driver._get_device_id.assert_called_once_with(pod)
        m_driver._get_host_id.assert_called_once_with(pod)

    @mock.patch('kuryr_kubernetes.os_vif_util.osvif_to_neutron_fixed_ips')
    def test_get_port_request(self, m_to_fips):
        security_groups = mock.sentinel.security_groups
        self._test_get_port_request(m_to_fips, security_groups)

    @mock.patch('kuryr_kubernetes.os_vif_util.osvif_to_neutron_fixed_ips')
    def test_get_port_request_no_sg(self, m_to_fips):
        security_groups = []
        self._test_get_port_request(m_to_fips, security_groups)

    def test_get_vif_plugin(self):
        cls = generic_vif.GenericPodVIFDriver
        m_driver = mock.Mock(spec=cls)
        vif_plugin = mock.sentinel.vif_plugin
        port = {'binding:vif_type': vif_plugin}

        self.assertEqual(vif_plugin, cls._get_vif_plugin(m_driver, port))

    @mock.patch('kuryr_kubernetes.os_vif_util.osvif_to_neutron_network_ids')
    def test_get_network_id(self, m_to_net_ids):
        cls = generic_vif.GenericPodVIFDriver
        m_driver = mock.Mock(spec=cls)
        subnets = mock.sentinel.subnets
        network_id = mock.sentinel.network_id
        m_to_net_ids.return_value = [network_id]

        self.assertEqual(network_id, cls._get_network_id(m_driver, subnets))
        m_to_net_ids.assert_called_once_with(subnets)

    @mock.patch('kuryr_kubernetes.os_vif_util.osvif_to_neutron_network_ids')
    def test_get_network_id_invalid(self, m_to_net_ids):
        cls = generic_vif.GenericPodVIFDriver
        m_driver = mock.Mock(spec=cls)
        subnets = mock.sentinel.subnets
        m_to_net_ids.return_value = []

        self.assertRaises(k_exc.IntegrityError, cls._get_network_id, m_driver,
                          subnets)

    def test_get_port_name(self):
        cls = generic_vif.GenericPodVIFDriver
        m_driver = mock.Mock(spec=cls)
        pod_name = mock.sentinel.pod_name
        pod = {'metadata': {'name': pod_name}}

        self.assertEqual(pod_name, cls._get_port_name(m_driver, pod))

    def test_get_device_id(self):
        cls = generic_vif.GenericPodVIFDriver
        m_driver = mock.Mock(spec=cls)
        pod_uid = mock.sentinel.pod_uid
        pod = {'metadata': {'uid': pod_uid}}

        self.assertEqual(pod_uid, cls._get_device_id(m_driver, pod))

    def test_get_host_id(self):
        cls = generic_vif.GenericPodVIFDriver
        m_driver = mock.Mock(spec=cls)
        node = mock.sentinel.pod_uid
        pod = {'spec': {'nodeName': node}}

        self.assertEqual(node, cls._get_host_id(m_driver, pod))
