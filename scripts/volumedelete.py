import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from brynweb.openstack.client import OpenstackClient, get_admin_credentials
import sys

client = OpenstackClient('warwick', **get_admin_credentials('warwick'))
cinder = client.get_cinder()
for v in cinder.volumes.list():
    print v
    print v.__dict__

    if v.name.startswith('bryn:'):
        print v


