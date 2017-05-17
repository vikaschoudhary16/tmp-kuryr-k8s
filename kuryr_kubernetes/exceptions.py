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


class K8sClientException(Exception):
    pass


class IntegrityError(RuntimeError):
    pass


class ResourceNotReady(Exception):
    def __init__(self, resource):
        super(ResourceNotReady, self).__init__("Resource not ready: %r"
                                               % resource)


class CNIError(Exception):
    pass


def format_msg(exception):
    return "%s: %s" % (exception.__class__.__name__, exception)


class K8sNodeTrunkPortFailure(Exception):
    """Exception represents that error is related to K8s node trunk port

    This exception is thrown when Neutron port for k8s node could
    not be found using subnet ID and IP address OR neutron port is
    not associated to a Neutron vlan trunk.
    """
