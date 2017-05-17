========================
Team and repository tags
========================

.. image:: http://governance.openstack.org/badges/kuryr-kubernetes.svg
    :target: http://governance.openstack.org/reference/tags/index.html

.. Change things from this point on

===============================
kuryr-kubernetes
===============================

Kubernetes integration with OpenStack networking

The OpenStack Kuryr project enables native Neutron-based networking in
Kubernetes. With Kuryr-Kubernetes it's now possible to choose to run both
OpenStack VMs and Kubernetes Pods on the same Neutron network if your workloads
require it or to use different segments and, for example, route between them.

* Free software: Apache license
* Documentation: http://docs.openstack.org/developer/kuryr-kubernetes
* Source: http://git.openstack.org/cgit/openstack/kuryr-kubernetes
* Bugs: http://bugs.launchpad.net/kuryr-kubernetes
* Overview and demo: http://superuser.openstack.org/articles/networking-kubernetes-kuryr


Configuring Kuryr
~~~~~~~~~~~~~~~~~

Generate sample config, `etc/kuryr.conf.sample`, running the following::

    $ ./tools/generate_config_file_samples.sh


Rename and copy config file at required path::

    $ cp etc/kuryr.conf.sample /etc/kuryr/kuryr.conf


Edit Neutron section in `/etc/kuryr/kuryr.conf`, replace ADMIN_PASSWORD::

    [neutron]
    auth_url = http://127.0.0.1:35357/v3/
    username = admin
    user_domain_name = Default
    password = ADMIN_PASSWORD
    project_name = service
    project_domain_name = Default
    auth_type = password


In the same file uncomment the `bindir` parameter with the path to the Kuryr
vif binding executables. For example, if you installed it on Debian or Ubuntu::

    [DEFAULT]
    bindir = /usr/local/libexec/kuryr


How to try out nested-pods locally
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Following are the instructions for an all-in-one setup where K8s will also be
running inside the same Nova VM in which Kuryr-controller and Kuryr-cni will be
running. 4GB memory and 2 vCPUs, is the minimum resource requirement for the VM:

1. To install OpenStack services run devstack with ``devstack/local.conf.pod-in-vm.undercloud.sample``.
   Ensure that "trunk" service plugin is enabled in ``/etc/neutron/neutron.conf``::

    [DEFAULT]
    service_plugins = neutron.services.l3_router.l3_router_plugin.L3RouterPlugin,neutron.services.trunk.plugin.TrunkPlugin

2. Launch a VM with `Neutron trunk port. <https://wiki.openstack.org/wiki/Neutron/TrunkPort>`_
3. Inside VM, install and setup Kubernetes along with Kuryr using devstack:
    - Since undercloud Neutron will be used by pods, neutron services should be
      disabled in localrc.
    - git clone kuryr-kubernetes at ``/opt/stack/``.
    - In the ``devstack/plugin.sh``, comment out `configure_neutron_defaults <https://github.com/openstack/kuryr-kubernetes/blob/master/devstack/plugin.sh#L453>`_.
      This method is getting UUID of default Neutron resources project, pod_subnet etc. using local neutron client
      and setting those values in ``/etc/kuryr/kuryr.conf``.
      This will not work at the moment because Neutron is running remotely. Thats why this is being commented out
      and manually these variables will be configured in ``/etc/kuryr/kuryr.conf``
    - Run devstack with ``devstack/local.conf.pod-in-vm.overcloud.sample``.
4. Once devstack is done and all services are up inside VM:
    - Configure ``/etc/kuryr/kuryr.conf`` to set UUID of Neutron resources from undercloud Neutron::

       [neutron_defaults]
       ovs_bridge = br-int
       pod_security_groups = <UNDERCLOUD_DEFAULT_SG_UUID>
       pod_subnet = <UNDERCLOUD_SUBNET_FOR_PODS_UUID>
       project = <UNDERCLOUD_DEFAULT_PROJECT_UUID>
       worker_nodes_subnet = <UNDERCLOUD_SUBNET_WORKER_NODES_UUID>

    - Configure “pod_vif_driver” as “nested-vlan”::

       [kubernetes]
       pod_vif_driver = nested-vlan

    - Configure binding section::

       [binding]
       driver = kuryr.lib.binding.drivers.vlan
       link_iface = <VM interface name eg. eth0>

    - Restart kuryr-k8s-controller from within devstack screen.

Now launch pods using kubectl, Undercloud Neutron will serve the networking.


How to watch K8S api-server over HTTPS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Add absolute path of client side cert file and key file for K8S server in kuryr.conf::

    [kubernetes]
    api_root = https://your_server_address:server_ssl_port
    ssl_client_crt_file = <absolute file path eg. /etc/kubernetes/admin.crt>
    ssl_client_key_file = <absolute file path eg. /etc/kubernetes/admin.key>

If server ssl certification verification is also to be enabled, add absolute path to the ca cert::

    [kubernetes]
    ssl_ca_crt_file = <absolute file path eg. /etc/kubernetes/ca.crt>
    ssl_verify_server_crt = True

If want to query HTTPS K8S api server with "--insecure" mode::

    [kubernetes]
    ssl_verify_server_crt = False


Features
--------

* TODO

Contribution guidelines
-----------------------
For the process of new feature addition, refer to the `Kuryr Policy <https://wiki.openstack.org/wiki/Kuryr#Kuryr_Policies>`_
