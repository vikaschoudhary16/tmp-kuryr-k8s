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

import abc
import six

from kuryr.lib._i18n import _
from stevedore import driver as stv_driver

from kuryr_kubernetes import config

_DRIVER_NAMESPACE_BASE = 'kuryr_kubernetes.controller.drivers'
_DRIVER_MANAGERS = {}


class DriverBase(object):
    """Base class for controller drivers.

    Subclasses must define an *ALIAS* attribute that is used to find a driver
    implementation by `get_instance` class method which utilises
    `stevedore.driver.DriverManager` with the namespace set to
    'kuryr_kubernetes.controller.drivers.*ALIAS*' and the name of
    the driver determined from the '[kubernetes]/*ALIAS*_driver' configuration
    parameter.

    Usage example:

        @six.add_metaclass(abc.ABCMeta)
        class SomeDriverInterface(DriverBase):
            ALIAS = 'driver_alias'

            @abc.abstractmethod
            def some_method(self):
                pass

        driver = SomeDriverInterface.get_instance()
        driver.some_method()
    """

    @classmethod
    def get_instance(cls):
        """Get an implementing driver instance."""

        alias = cls.ALIAS

        try:
            manager = _DRIVER_MANAGERS[alias]
        except KeyError:
            name = config.CONF.kubernetes[alias + '_driver']
            manager = stv_driver.DriverManager(
                namespace="%s.%s" % (_DRIVER_NAMESPACE_BASE, alias),
                name=name,
                invoke_on_load=True)
            _DRIVER_MANAGERS[alias] = manager

        driver = manager.driver
        if not isinstance(driver, cls):
            raise TypeError(_("Invalid %(alias)r driver type: %(driver)s, "
                              "must be a subclass of %(type)s") % {
                                'alias': alias,
                                'driver': driver.__class__.__name__,
                                'type': cls})
        return driver


@six.add_metaclass(abc.ABCMeta)
class PodProjectDriver(DriverBase):
    """Provides an OpenStack project ID for Kubernetes Pod ports."""

    ALIAS = 'pod_project'

    @abc.abstractmethod
    def get_project(self, pod):
        """Get an OpenStack project ID for Kubernetes Pod ports.

        :param pod: dict containing Kubernetes Pod object
        :return: project ID
        """

        raise NotImplementedError()


@six.add_metaclass(abc.ABCMeta)
class ServiceProjectDriver(DriverBase):
    """Provides an OpenStack project ID for Kubernetes Services."""

    ALIAS = 'service_project'

    @abc.abstractmethod
    def get_project(self, service):
        """Get an OpenStack project ID for Kubernetes Service.

        :param service: dict containing Kubernetes Service object
        :return: project ID
        """

        raise NotImplementedError()


@six.add_metaclass(abc.ABCMeta)
class PodSubnetsDriver(DriverBase):
    """Provides subnets for Kubernetes Pods."""

    ALIAS = 'pod_subnets'

    @abc.abstractmethod
    def get_subnets(self, pod, project_id):
        """Get subnets for Pod.

        :param pod: dict containing Kubernetes Pod object
        :param project_id: OpenStack project ID
        :return: dict containing the mapping 'subnet_id' -> 'network' for all
                 the subnets we want to create ports on, where 'network' is an
                 `os_vif.network.Network` object containing a single
                 `os_vif.subnet.Subnet` object corresponding to the 'subnet_id'
        """
        raise NotImplementedError()


@six.add_metaclass(abc.ABCMeta)
class ServiceSubnetsDriver(DriverBase):
    """Provides subnets for Kubernetes Services."""

    ALIAS = 'service_subnets'

    @abc.abstractmethod
    def get_subnets(self, service, project_id):
        """Get subnets for Service.

        :param service: dict containing Kubernetes Pod object
        :param project_id: OpenStack project ID
        :return: dict containing the mapping 'subnet_id' -> 'network' for all
                 the subnets we want to create ports on, where 'network' is an
                 `os_vif.network.Network` object containing a single
                 `os_vif.subnet.Subnet` object corresponding to the 'subnet_id'
        """
        raise NotImplementedError()


@six.add_metaclass(abc.ABCMeta)
class PodSecurityGroupsDriver(DriverBase):
    """Provides security groups for Kubernetes Pods."""

    ALIAS = 'pod_security_groups'

    @abc.abstractmethod
    def get_security_groups(self, pod, project_id):
        """Get a list of security groups' IDs for Pod.

        :param pod: dict containing Kubernetes Pod object
        :param project_id: OpenStack project ID
        :return: list containing security groups' IDs
        """
        raise NotImplementedError()


@six.add_metaclass(abc.ABCMeta)
class ServiceSecurityGroupsDriver(DriverBase):
    """Provides security groups for Kubernetes Services."""

    ALIAS = 'service_security_groups'

    @abc.abstractmethod
    def get_security_groups(self, service, project_id):
        """Get a list of security groups' IDs for Service.

        :param service: dict containing Kubernetes Service object
        :param project_id: OpenStack project ID
        :return: list containing security groups' IDs
        """
        raise NotImplementedError()


@six.add_metaclass(abc.ABCMeta)
class PodVIFDriver(DriverBase):
    """Manages Neutron ports to provide VIFs for Kubernetes Pods."""

    ALIAS = 'pod_vif'

    @abc.abstractmethod
    def request_vif(self, pod, project_id, subnets, security_groups):
        """Links Neutron port to pod and returns it as VIF object.

        Implementing drivers must ensure the Neutron port satisfying the
        requested parameters is present and is valid for specified `pod`. It
        is up to the implementing drivers to either create new ports on each
        request or reuse available ports when possible.

        Implementing drivers may return a VIF object with its `active` field
        set to 'False' to indicate that Neutron port requires additional
        actions to enable network connectivity after VIF is plugged (e.g.
        setting up OpenFlow and/or iptables rules by OpenVSwitch agent). In
        that case the Controller will call driver's `activate_vif` method
        and the CNI plugin will block until it receives activation
        confirmation from the Controller.

        :param pod: dict containing Kubernetes Pod object
        :param project_id: OpenStack project ID
        :param subnets: dict containing subnet mapping as returned by
                        `PodSubnetsDriver.get_subnets`. If multiple entries
                        are present in that mapping, it is guaranteed that
                        all entries have the same value of `Network.id`.
        :param security_groups: list containing security groups' IDs as
                                returned by
                                `PodSecurityGroupsDriver.get_security_groups`
        :return: VIF object
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def release_vif(self, pod, vif):
        """Unlinks Neutron port corresponding to VIF object from pod.

        Implementing drivers must ensure the port is either deleted or made
        available for reuse by `PodVIFDriver.request_vif`.

        :param pod: dict containing Kubernetes Pod object
        :param vif: VIF object as returned by `PodVIFDriver.request_vif`
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def activate_vif(self, pod, vif):
        """Updates VIF to become active.

        Implementing drivers should update the specified `vif` object's
        `active` field to 'True' but must ensure that the corresponding
        Neutron port is fully configured (i.e. the container using the `vif`
        can access the requested network resources).

        Implementing drivers may raise `ResourceNotReady` exception to
        indicate that port activation should be retried later which will
        cause `activate_vif` to be called again with the same arguments.

        This method may be called before, after or while the VIF is being
        plugged by the CNI plugin.

        :param pod: dict containing Kubernetes Pod object
        :param vif: VIF object as returned by `PodVIFDriver.request_vif`
        """
        raise NotImplementedError()


@six.add_metaclass(abc.ABCMeta)
class LBaaSDriver(DriverBase):
    """Manages Neutron/Octavia load balancer to support Kubernetes Services."""

    ALIAS = 'endpoints_lbaas'

    @abc.abstractmethod
    def ensure_loadbalancer(self, endpoints, project_id, subnet_id, ip,
                            security_groups_ids):
        """Get or create load balancer.

        :param endpoints: dict containing K8s Endpoints object
        :param project_id: OpenStack project ID
        :param subnet_id: Neutron subnet ID to host load balancer
        :param ip: IP of the load balancer
        :param security_groups_ids: security groups that should be allowed
                                    access to the load balancer
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def release_loadbalancer(self, endpoints, loadbalancer):
        """Release load balancer.

        Should return without errors if load balancer does not exist (e.g.
        already deleted).

        :param endpoints: dict containing K8s Endpoints object
        :param loadbalancer: `LBaaSLoadBalancer` object
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def ensure_listener(self, endpoints, loadbalancer, protocol, port):
        """Get or create listener.

        :param endpoints: dict containing K8s Endpoints object
        :param loadbalancer: `LBaaSLoadBalancer` object
        :param protocol: listener's protocol (only TCP is supported for now)
        :param port: listener's port
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def release_listener(self, endpoints, loadbalancer, listener):
        """Release listener.

        Should return without errors if listener or load balancer does not
        exist (e.g. already deleted).

        :param endpoints: dict containing K8s Endpoints object
        :param loadbalancer: `LBaaSLoadBalancer` object
        :param listener: `LBaaSListener` object
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def ensure_pool(self, endpoints, loadbalancer, listener):
        """Get or create pool.

        :param endpoints: dict containing K8s Endpoints object
        :param loadbalancer: `LBaaSLoadBalancer` object
        :param listener: `LBaaSListener` object
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def release_pool(self, endpoints, loadbalancer, pool):
        """Release pool.

        Should return without errors if pool or load balancer does not exist
        (e.g. already deleted).

        :param endpoints: dict containing K8s Endpoints object
        :param loadbalancer: `LBaaSLoadBalancer` object
        :param pool: `LBaaSPool` object
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def ensure_member(self, endpoints, loadbalancer, pool,
                      subnet_id, ip, port, target_ref):
        """Get or create member.

        :param endpoints: dict containing K8s Endpoints object
        :param loadbalancer: `LBaaSLoadBalancer` object
        :param pool: `LBaaSPool` object
        :param subnet_id: Neutron subnet ID of the target
        :param ip: target's IP (e.g. Pod's IP)
        :param port: target port
        :param target_ref: Kubernetes ObjectReference of the target (e.g.
                           Pod reference)
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def release_member(self, endpoints, loadbalancer, member):
        """Release member.

        Should return without errors if memberor load balancer does not exist
        (e.g. already deleted).

        :param endpoints: dict containing K8s Endpoints object
        :param loadbalancer: `LBaaSLoadBalancer` object
        :param member: `LBaaSMember` object
        """
        raise NotImplementedError()
