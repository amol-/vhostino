from circus import logger
from circus.plugins import CircusPlugin

from .server import ProxyServer

class VHostino(CircusPlugin):
    name = 'vhostino'

    def __init__(self, endpoint, pubsub_endpoint, check_delay, ssh_server, **config):
        super(VHostino, self).__init__(endpoint, pubsub_endpoint, check_delay, ssh_server, **config)
        self.server = ProxyServer((config.get('host', '0.0.0.0'),
                                   config.get('port', 8000)))

    def handle_recv(self, data):
        pass

    def handle_init(self):
        #we handle initialization in a timeout because
        #during initialization the connection to circus required
        #to use self.call is not available yet.
        self.loop.add_timeout(0, self._initialize_proxy)

    def handle_stop(self):
        self.server.stop()

    def _setup_vhost(self, sockets, worker):
        options = self.call('options', name=worker)
        if not options or options.get('status') != 'ok':
            return
        options = options['options']

        vhost = options.get('vhostino.vhost')
        if vhost == 'True':
            socket = sockets.get(worker)
            if socket:
                logger.info('Vhosting: Registering %s -> %s', worker, socket['port'])
                self.server.config.add_vhost(worker, socket['port'])
                if options.get('vhostino.default_vhost'):
                    logger.info('Vhosting: Default Vhost %s -> %s', worker, socket['port'])
                    self.server.config.set_default(socket['port'])

    def _sockets_by_name(self, sockets):
        sockets_dict = {}
        for socket in sockets:
            sockets_dict[socket['name']] = socket
        return sockets_dict

    def _initialize_proxy(self):
        sockets = self.call('listsockets')
        if not sockets or sockets.get('status') != 'ok':
            return
        sockets = self._sockets_by_name(sockets['sockets'])

        status = self.call('status')
        if not status and status.get('status') != 'ok':
            return

        for worker in status['statuses']:
            self._setup_vhost(sockets, worker)

        self.server.start()

