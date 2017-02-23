import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from brynweb.openstack.client import OpenstackClient, get_admin_credentials
import sys

client = OpenstackClient('warwick', **get_admin_credentials('warwick'))
cinder = client.get_cinder()
print cinder.volumes.list()

cinder.volumes.create(imageRef='3ddcad54-09b9-498e-a893-a98b31f2886f',
                      name="Server boot volume",
                      size=120)


