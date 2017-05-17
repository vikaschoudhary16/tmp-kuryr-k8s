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

from oslo_versionedobjects import base as obj_base
from oslo_versionedobjects import fields as obj_fields

from kuryr_kubernetes.objects import base as k_obj
from kuryr_kubernetes.objects import fields as k_fields


@obj_base.VersionedObjectRegistry.register
class LBaaSLoadBalancer(k_obj.KuryrK8sObjectBase):
    VERSION = '1.0'

    fields = {
        'id': obj_fields.UUIDField(),
        'project_id': obj_fields.StringField(),
        'name': obj_fields.StringField(),
        'ip': obj_fields.IPAddressField(),
        'subnet_id': obj_fields.UUIDField(),
    }


@obj_base.VersionedObjectRegistry.register
class LBaaSListener(k_obj.KuryrK8sObjectBase):
    VERSION = '1.0'

    fields = {
        'id': obj_fields.UUIDField(),
        'project_id': obj_fields.StringField(),
        'name': obj_fields.StringField(),
        'loadbalancer_id': obj_fields.UUIDField(),
        'protocol': obj_fields.StringField(),
        'port': obj_fields.IntegerField(),
    }


@obj_base.VersionedObjectRegistry.register
class LBaaSPool(k_obj.KuryrK8sObjectBase):
    VERSION = '1.0'

    fields = {
        'id': obj_fields.UUIDField(),
        'project_id': obj_fields.StringField(),
        'name': obj_fields.StringField(),
        'loadbalancer_id': obj_fields.UUIDField(),
        'listener_id': obj_fields.UUIDField(),
        'protocol': obj_fields.StringField(),
    }


@obj_base.VersionedObjectRegistry.register
class LBaaSMember(k_obj.KuryrK8sObjectBase):
    VERSION = '1.0'

    fields = {
        'id': obj_fields.UUIDField(),
        'project_id': obj_fields.StringField(),
        'name': obj_fields.StringField(),
        'pool_id': obj_fields.UUIDField(),
        'subnet_id': obj_fields.UUIDField(),
        'ip': obj_fields.IPAddressField(),
        'port': obj_fields.IntegerField(),
    }


@obj_base.VersionedObjectRegistry.register
class LBaaSState(k_obj.KuryrK8sObjectBase):
    VERSION = '1.0'

    fields = {
        'loadbalancer': obj_fields.ObjectField(LBaaSLoadBalancer.__name__,
                                               nullable=True,
                                               default=None),
        'listeners': obj_fields.ListOfObjectsField(LBaaSListener.__name__,
                                                   default=[]),
        'pools': obj_fields.ListOfObjectsField(LBaaSPool.__name__,
                                               default=[]),
        'members': obj_fields.ListOfObjectsField(LBaaSMember.__name__,
                                                 default=[]),
    }


@obj_base.VersionedObjectRegistry.register
class LBaaSPortSpec(k_obj.KuryrK8sObjectBase):
    VERSION = '1.0'

    fields = {
        'name': obj_fields.StringField(nullable=True),
        'protocol': obj_fields.StringField(),
        'port': obj_fields.IntegerField(),
    }


@obj_base.VersionedObjectRegistry.register
class LBaaSServiceSpec(k_obj.KuryrK8sObjectBase):
    VERSION = '1.0'

    fields = {
        'ip': obj_fields.IPAddressField(nullable=True, default=None),
        'ports': obj_fields.ListOfObjectsField(LBaaSPortSpec.__name__,
                                               default=[]),
        'project_id': obj_fields.StringField(nullable=True, default=None),
        'subnet_id': obj_fields.UUIDField(nullable=True, default=None),
        'security_groups_ids': k_fields.ListOfUUIDField(default=[]),
    }
