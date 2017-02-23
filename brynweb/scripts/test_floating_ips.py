import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from django.contrib.auth.models import User
from userdb.models import Team, Region
from openstack.client import OpenstackClient, get_admin_credentials
from openstack.models import Tenant, get_tenant_for_team

def run():
    t = Team.objects.get(pk=1)
    tenant = get_tenant_for_team(t, Region.objects.get(name='bham'))
    client = OpenstackClient(tenant.region.name,
                             username=tenant.get_auth_username(),
                             password=tenant.auth_password,
                             project_name=tenant.get_tenant_name())
    nova = client.get_nova()
    for ip in nova.floating_ips.list():
        if ip.fixed_ip is None and ip.instance_id is None:
            print ip


