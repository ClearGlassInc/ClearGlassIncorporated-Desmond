from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

A = DummyAuthorizer()
A.add_user('lab-user', 'LabOnly-Invalid', '/srv/ftp', perm='elr')
A.add_anonymous('/srv/ftp', perm='elr')
H = FTPHandler
H.authorizer = A
H.banner = 'HydraGuard Lab FTP Fixture'
H.passive_ports = range(30000, 30005)
H.timeout = 5
FTPServer(('0.0.0.0', 21), H).serve_forever()
