from os import chmod
from Crypto.PublicKey import RSA

key = RSA.generate(2048)
with open("/tmp/private.key", 'w') as content_file:
    chmod("/tmp/private.key", 0600)
    content_file.write(key.exportKey('PEM'))
pubkey = key.publickey()
with open("/tmp/public.key", 'w') as content_file:
    content_file.write(pubkey.exportKey('OpenSSH'))
