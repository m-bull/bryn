
from openstack.client import OpenstackClient
from openstack.models import Tenant
from userdb.models import Team, Region
import sys
import yaml
import pprint
from scripts.list_instances import list_instances

def list_volumes(tenant, instances=None):
    instancehash = dict([(i['id'], i) for i in instances])

    client = OpenstackClient(tenant.region.name,
                             username=tenant.get_auth_username(),
                             password=tenant.auth_password,
                             project_name=tenant.get_tenant_name())

    cinder = client.get_cinder()

    volumes = []
    for v in cinder.volumes.list():
        if v.attachments:
            attached_as = v.attachments[0]['device']
            attached_to = instancehash[v.attachments[0]['server_id']]
        else:
            attached_as = 'n/a'
            attached_to = None

        if v.bootable == 'false':
            volumes.append({'id' : v.id,
                            'name' : v.name,
                            'size' : v.size,
                            'status' : v.status,
                            'attached_as' : attached_as,
                            'attached_to' : attached_to
                           })
    return volumes

def run():
    team = Team.objects.get(pk=1)
    print team
    tenant = Tenant.objects.filter(team=team, region=Region.objects.get(name='bham'))[0]
    print tenant
    list_volumes(tenant, list_instances(tenant))
 
